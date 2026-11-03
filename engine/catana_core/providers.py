"""Provider orchestration: capability matching, cost policy, retry/fallback decisions and an honest run log.

Creative direction (spec + prompt) is provider-agnostic; execution goes to a provider chosen here.

Connectors (Higgsfield, Runway, ElevenLabs) are MCP tools that only Claude can call, so for them this module
*decides* (select / next_action) and *records* (RunLog) while Claude executes the tool call.
Local providers (voice_studio over HTTP, catana_motion, prompt_only) also have adapters that execute directly,
driven by Orchestrator.run().

Rules enforced here:
  * a result is 'succeeded' only with a returned asset (path / URL / id) — RunLog refuses anything else
  * paid providers need explicit approval (cost policy), never auto-selected under 'free_only'
  * billing / content-policy / invalid-input errors stop and ask; transient errors retry with backoff
  * when nothing can execute, the fallback is prompt_only (status 'prompt_only', never 'succeeded')
"""
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field

from .data import providers as _manifest

FREE = ("free", "user_reports_free")
AUDIO_OPS = {"tts", "voice_design", "sfx", "music", "voice_convert", "transcribe", "dub"}


def manifest():
    return _manifest()


def provider(name):
    p = manifest()["providers"].get(name)
    if not p:
        raise KeyError(f"unknown provider {name!r}; known: {', '.join(manifest()['providers'])}")
    return p


def is_free(name):
    return provider(name)["cost"] in FREE


# ------------------------------------------------------------------ availability
def local_available():
    """Detect locally executable providers (no network calls except VoiceStudio's localhost health check)."""
    out = ["prompt_only"]
    try:
        from .voice_studio import VoiceStudio
        if VoiceStudio(timeout=3).available():
            out.append("voice_studio")
    except Exception:
        pass
    if shutil.which("node") and _chrome_present():
        out.append("catana_motion")
    return out


def _chrome_present():
    if os.environ.get("CHROME") and os.path.exists(os.environ["CHROME"]):
        return True
    cands = ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "C:/Program Files/Google/Chrome/Application/chrome.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe"]
    if any(os.path.exists(c) for c in cands):
        return True
    return os.path.isdir("/opt/pw-browsers")


# ------------------------------------------------------------------ selection
def select(op, available, duration=None, aspect=None, refs=0, policy=None, approved_paid=False, prefer=None):
    """Rank providers for an operation.

    available: names of providers present in this session (connectors Claude can see + local_available()).
    Returns {'op', 'policy', 'ranked': [{provider, cost, requires_approval, reasons}], 'rejected': [{provider, reason}]}.
    """
    m = manifest()
    if op not in m["operations"]:
        raise ValueError(f"unknown operation {op!r}; known: {', '.join(m['operations'])}")
    audio_ops = AUDIO_OPS
    policy = policy or (m["policy"].get("audio_cost_policy") if op in audio_ops else None) or m["policy"]["cost_policy_default"]
    if policy not in m["policy"]["cost_policies"]:
        raise ValueError(f"unknown cost policy {policy!r}")
    available = set(available or []) | {"prompt_only"}
    ranked, rejected = [], []
    pref = m["policy"]["audio_preference"]
    for name, p in m["providers"].items():
        if name not in available:
            rejected.append({"provider": name, "reason": "not available in this session"})
            continue
        if op not in p["operations"]:
            rejected.append({"provider": name, "reason": f"does not support {op}"})
            continue
        lim = p.get("limits", {})
        if duration and op in ("t2v", "i2v", "first_last", "multi_ref_video", "v2v", "extend_video", "multi_shot") \
                and lim.get("video_seconds_max") and duration > lim["video_seconds_max"]:
            rejected.append({"provider": name, "reason": f"max {lim['video_seconds_max']} s per generation"})
            continue
        if name == "catana_motion" and duration and lim.get("duration_seconds") and not (lim["duration_seconds"][0] <= duration <= lim["duration_seconds"][1]):
            rejected.append({"provider": name, "reason": "duration outside 1–600 s"})
            continue
        if aspect and lim.get("aspect_ratios") and aspect not in lim["aspect_ratios"]:
            rejected.append({"provider": name, "reason": f"aspect {aspect} not in {', '.join(lim['aspect_ratios'])}"})
            continue
        free = p["cost"] in FREE
        if policy == "free_only" and not free:
            rejected.append({"provider": name, "reason": "paid provider excluded by free_only policy"})
            continue
        reasons = []
        if free:
            reasons.append("free")
        if p.get("verified"):
            reasons.append("capabilities verified")
        if prefer == name:
            reasons.append("user preference")
        if op in audio_ops and name in pref:
            reasons.append("preferred audio provider" if pref.index(name) == 0 else "")
        ranked.append({"provider": name, "label": p["label"], "cost": p["cost"],
                       "requires_approval": (not free) and not approved_paid,
                       "reasons": [r for r in reasons if r]})

    def key(r):
        n = r["provider"]
        export_last = 1 if n == "prompt_only" else 0
        user_pref = 0 if prefer == n else 1
        audio_rank = pref.index(n) if (op in audio_ops and n in pref) else len(pref)
        cost_rank = 0 if (policy != "best_quality" and r["cost"] in FREE) else 1
        verified = 0 if manifest()["providers"][n].get("verified") else 1
        if policy == "best_quality":
            return (export_last, user_pref, audio_rank, verified, cost_rank)
        return (export_last, user_pref, audio_rank, cost_rank, verified)
    ranked.sort(key=key)
    return {"op": op, "policy": policy, "ranked": ranked, "rejected": rejected}


# ------------------------------------------------------------------ errors and next action
ERROR_PATTERNS = [
    ("insufficient_credits", r"insufficient.{0,20}credit|not enough credit|out of credits|balance (is )?(too low|0)|credits?: ?0\b|402"),
    ("paid_plan_required", r"paid[_ ]plan[_ ]required|upgrade (your )?plan|requires a paid|free plan"),
    ("content_policy", r"content polic|moderation|nsfw|safety (system|filter)|not allowed by polic"),
    ("auth", r"\b401\b|\b403\b|unauthori[sz]ed|forbidden|api[_ ]?key|not authenticated|invalid token|missing key|no key"),
    ("rate_limited", r"\b429\b|rate.?limit|too many requests|quota exceeded"),
    ("timeout", r"timed? ?out|timeout|deadline exceeded"),
    ("unavailable", r"not reachable|connection refused|econnrefused|service unavailable|\b503\b|not running"),
    ("server_error", r"\b5\d\d\b|internal server error|bad gateway|upstream"),
    ("network", r"network|econnreset|connection reset|dns|getaddrinfo|socket"),
    ("invalid_input", r"\b400\b|\b404\b|\b409\b|\b422\b|invalid|validation|unsupported|not supported|must be|required"),
]


def classify_error(message):
    m = (message or "").lower()
    for cat, pat in ERROR_PATTERNS:
        if re.search(pat, m):
            return cat
    return "unknown"


def next_action(attempts, ranked, max_retries=None):
    """Decide what to do after the latest attempt.

    attempts: [{'provider', 'status': 'succeeded'|'failed', 'error_category'}] oldest first.
    ranked:   output of select()['ranked'].
    Returns {'action': 'run'|'retry'|'fallback'|'ask_approval'|'fix_input'|'stop'|'prompt_only'|'done', 'provider', 'wait', 'reason'}.
    """
    pol = manifest()["policy"]
    max_retries = pol["retry"]["max_retries"] if max_retries is None else max_retries
    backoff = pol["retry"]["backoff_seconds"]
    order = [r for r in ranked]
    if not attempts:
        first = order[0] if order else None
        if not first:
            return {"action": "prompt_only", "provider": "prompt_only", "wait": 0, "reason": "no provider supports this operation"}
        if first["requires_approval"]:
            return {"action": "ask_approval", "provider": first["provider"], "wait": 0,
                    "reason": f"{first['label']} costs credits: quote the price and get the user's explicit OK first"}
        return {"action": "run", "provider": first["provider"], "wait": 0, "reason": "best ranked provider"}
    last = attempts[-1]
    if last["status"] == "succeeded":
        return {"action": "done", "provider": last["provider"], "wait": 0, "reason": "succeeded"}
    if last["status"] == "prompt_only":
        return {"action": "done", "provider": "prompt_only", "wait": 0, "reason": "prompt pack written; nothing was generated"}
    cat = last.get("error_category") or "unknown"
    same = [a for a in attempts if a["provider"] == last["provider"] and a["status"] == "failed"]
    if cat in pol["retry"]["retryable"] and len(same) <= max_retries:
        return {"action": "retry", "provider": last["provider"], "wait": backoff[min(len(same) - 1, len(backoff) - 1)],
                "reason": f"{cat}: transient, retry {len(same)}/{max_retries}"}
    if cat == "invalid_input":
        return {"action": "fix_input", "provider": last["provider"], "wait": 0,
                "reason": "the provider rejected the request: fix the prompt/params (run qc lint), don't switch providers"}
    if cat in pol["never_auto_fallback_on"]:
        return {"action": "stop", "provider": last["provider"], "wait": 0,
                "reason": f"{cat}: tell the user and ask how to proceed — never silently switch to another paid provider"}
    tried = {a["provider"] for a in attempts}
    for r in order:
        if r["provider"] in tried or r["provider"] == "prompt_only":
            continue
        if r["requires_approval"]:
            return {"action": "ask_approval", "provider": r["provider"], "wait": 0,
                    "reason": f"{last['provider']} failed ({cat}); next option {r['label']} costs credits — ask first"}
        return {"action": "fallback", "provider": r["provider"], "wait": 0, "reason": f"{last['provider']} failed ({cat})"}
    return {"action": "prompt_only", "provider": "prompt_only", "wait": 0,
            "reason": f"no provider left after {last['provider']} failed ({cat}); deliver the prompt pack and say nothing was generated"}


# ------------------------------------------------------------------ run log
STATUSES = ("succeeded", "failed", "prompt_only", "submitted")


class RunLog:
    """Append-only JSONL record of every execution attempt (settings preserved for reproduction)."""

    def __init__(self, path):
        self.path = path

    def append(self, provider_name, operation, status, assets=None, job_id=None, prompt=None, params=None, model=None,
               error=None, cost=None, spec_hash=None, run_id=None, note=None):
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        assets = list(assets or [])
        if status == "succeeded" and not assets and not job_id:
            raise ValueError("refusing to log 'succeeded' without an asset path/URL or provider job id")
        if status == "submitted" and not job_id:
            raise ValueError("a submitted job needs the provider's job id")
        if status == "failed" and not error:
            raise ValueError("a failed attempt needs the error message")
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "run_id": run_id or uuid.uuid4().hex[:10],
               "provider": provider_name, "model": model, "operation": operation, "status": status, "assets": assets,
               "job_id": job_id, "prompt": prompt, "params": params or {}, "spec_hash": spec_hash, "cost": cost,
               "error": error, "error_category": classify_error(error) if error else None, "note": note}
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "a", encoding="utf8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def records(self, run_id=None):
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path, encoding="utf8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if run_id is None or r["run_id"] == run_id:
                        out.append(r)
        return out


# ------------------------------------------------------------------ adapters (locally executable providers)
@dataclass
class Result:
    status: str                      # succeeded | failed | prompt_only
    assets: list = field(default_factory=list)
    error: str = ""
    job_id: str = ""
    meta: dict = field(default_factory=dict)


class Adapter:
    name = "base"

    def execute(self, job):
        raise NotImplementedError


class PromptOnlyAdapter(Adapter):
    """Writes the production-ready prompt pack. Always available; never claims a generation."""
    name = "prompt_only"

    def __init__(self, out_dir):
        self.out_dir = out_dir

    def execute(self, job):
        os.makedirs(self.out_dir, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", (job.get("id") or job.get("operation", "job")).lower()).strip("-") or "job"
        jp = os.path.join(self.out_dir, f"{slug}.json")
        mp = os.path.join(self.out_dir, f"{slug}.md")
        with open(jp, "w", encoding="utf8") as f:
            json.dump(job, f, indent=2, ensure_ascii=False)
        lines = [f"# {job.get('id') or job.get('operation')}", "", f"Operation: `{job.get('operation')}`  ", "Status: **prompt only — nothing was generated**", ""]
        if job.get("prompt"):
            lines += ["## Prompt", "", "```", job["prompt"], "```", ""]
        if job.get("negative_prompt"):
            lines += ["## Negative prompt", "", "```", job["negative_prompt"], "```", ""]
        if job.get("params"):
            lines += ["## Settings", "", "```json", json.dumps(job["params"], indent=2), "```", ""]
        if job.get("text"):
            lines += ["## Voiceover script", "", job["text"], ""]
        with open(mp, "w", encoding="utf8") as f:
            f.write("\n".join(lines))
        return Result("prompt_only", [mp, jp])


class VoiceStudioAdapter(Adapter):
    """Voiceover through the user's local VoiceStudio (free)."""
    name = "voice_studio"

    def __init__(self, out_dir, client=None):
        from .voice_studio import VoiceStudio
        self.out_dir = out_dir
        self.client = client or VoiceStudio()

    def execute(self, job):
        from .voice_studio import VoiceStudioError
        if job.get("operation") != "tts":
            return Result("failed", error=f"invalid: voice_studio adapter only runs tts, got {job.get('operation')}")
        out = os.path.join(self.out_dir, (job.get("id") or "voiceover") + "." + job.get("format", "wav"))
        try:
            r = self.client.speech(job["text"], out, voice=job.get("voice", "default"), model=job.get("model", "omnivoice"),
                                   instructions=job.get("instructions"), instruct=job.get("instruct"), speed=job.get("speed", 1.0),
                                   language=job.get("language"), duration=job.get("duration"), seed=job.get("seed"))
        except VoiceStudioError as e:
            return Result("failed", error=f"{e.category}: {e}")
        return Result("succeeded", [r["path"]], meta=r)


class Orchestrator:
    """Runs a job through ranked local adapters with retry/fallback, logging every attempt."""

    def __init__(self, adapters, log, sleep=time.sleep):
        self.adapters = adapters   # {provider_name: Adapter}
        self.log = log
        self.sleep = sleep

    def run(self, job, ranked, approved=()):
        attempts, run_id = [], uuid.uuid4().hex[:10]
        ranked = [dict(r, requires_approval=r["requires_approval"] and r["provider"] not in approved) for r in ranked]
        while True:
            step = next_action(attempts, ranked)
            if step["action"] == "done":
                return {"status": attempts[-1]["status"], "attempts": attempts, "run_id": run_id, "final": attempts[-1]}
            if step["action"] in ("ask_approval", "stop", "fix_input"):
                return {"status": "needs_user", "action": step, "attempts": attempts, "run_id": run_id}
            name = step["provider"]
            if step["action"] == "prompt_only" or name not in self.adapters:
                if name != "prompt_only" and name not in self.adapters:
                    attempts.append({"provider": name, "status": "failed", "error_category": "unavailable",
                                     "error": "no executable adapter here (connector: Claude executes it)"})
                    continue
                name = "prompt_only"
            if step["wait"]:
                self.sleep(step["wait"])
            res = self.adapters[name].execute(job)
            cat = classify_error(res.error) if res.status == "failed" else None
            self.log.append(name, job.get("operation"), res.status, assets=res.assets, job_id=res.job_id or None,
                            prompt=job.get("prompt") or job.get("text"), params=job.get("params"), error=res.error or None, run_id=run_id)
            attempts.append({"provider": name, "status": res.status, "error_category": cat, "error": res.error, "assets": res.assets})
            if len(attempts) > 12:
                return {"status": "failed", "attempts": attempts, "run_id": run_id, "reason": "too many attempts"}


def detect_motion_project(path):
    return os.path.exists(os.path.join(path, "render.mjs")) and os.path.exists(os.path.join(path, "src", "scenes.js"))


def render_motion(project_dir, out_name="master_noaudio.mp4", workers=4, timeout=3600):
    """Render a CATANA motion film (local, free). Returns Result with the MP4 path."""
    if not detect_motion_project(project_dir):
        return Result("failed", error=f"invalid: {project_dir} is not a CATANA motion project (scripts/new_film.py creates one)")
    try:
        p = subprocess.run(["node", "render.mjs", "video", "--workers", str(workers), "--name", out_name], cwd=project_dir,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return Result("failed", error="timeout: render exceeded the time limit")
    out = os.path.join(project_dir, "out", out_name)
    if p.returncode != 0 or not os.path.exists(out):
        return Result("failed", error=f"render failed: {(p.stderr or p.stdout)[-600:]}")
    return Result("succeeded", [out])
