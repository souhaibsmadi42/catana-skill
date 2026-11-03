#!/usr/bin/env python3
"""CATANA command-line engine (standard library only).

  enhance "<request>" [--domain d] [--modality image|video] [--aspect r] [--duration s] [--platform p] [--provider p] [--inline-negative] [--json]
  lint <spec.json> [--provider p] [--model m] [--platform p]
  camera list | show <move> | find "<text>" | check <move> <move> ... [--duration s] | phrase <move> [--speed slow]
  select --op <op> [--available a,b] [--duration s] [--aspect r] [--policy free_first|free_only|best_quality] [--approved-paid] [--prefer p]
  next --attempts <attempts.json> --op <op> [--available ...]      decide retry / fallback / ask / prompt-only
  classify-error "<message>"
  log --file runs.jsonl --provider p --op o --status succeeded|failed|prompt_only|submitted [--asset A ...] [--job-id J] [--error E] [--prompt P]
  pack <spec.json|plan.json> --out <dir>                             write a prompt pack (nothing is generated)
  plan new "<idea>" [--duration s] [--platform p] [--domain d] [--aspect r] --out plan.json
  plan compile <plan.json> [--out dir]                               keyframe + video prompts, VO plan, EDL, storyboard.md, QC
  voice health | voices | archetypes [q] | describe "<voice description>" | fit "<text>" --seconds s [--lang en]
  voice speak "<text>"|--file script.txt --out vo.wav [--voice v] [--instructions "..."] [--speed 1.0] [--language en] [--duration s]
  voice plan <compiled.json> --out-dir dir [--voice v]               render every VO line of a compiled plan (+ build/vo.json for the mixer)
  providers [--detect]                                               list providers (and detect local ones)
  platforms | presets
  docs                                                               regenerate docs/CAMERA_MOVEMENTS.md from data
Exit codes: 0 ok · 1 QC errors / not ready · 2 usage or input error · 3 provider unavailable.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "engine"))

from catana_core import camera as cam                      # noqa: E402
from catana_core import prompt_engine as pe                # noqa: E402
from catana_core import qc                                 # noqa: E402
from catana_core import providers as pv                    # noqa: E402
from catana_core import director                           # noqa: E402
from catana_core.data import presets, platforms            # noqa: E402
from catana_core.spec import ShotSpec, SpecError           # noqa: E402


def out(obj, as_json=True):
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    else:
        print(obj)


def load_json(path):
    try:
        with open(path, encoding="utf8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise SystemExit(_err(f"no such file: {path}"))
    except ValueError as e:
        raise SystemExit(_err(f"{path} is not valid JSON: {e}"))


def _err(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    return code


def cmd_enhance(a):
    ov = {"technical": {}}
    if a.aspect:
        ov["technical"]["aspect_ratio"] = a.aspect
    if a.duration:
        ov["technical"]["duration"] = a.duration
    if a.platform:
        ps = platforms()["platforms"].get(a.platform)
        if not ps:
            return _err(f"unknown platform {a.platform!r}; see `catana.py platforms`")
        ov["technical"]["platform"] = a.platform
        ov["technical"].setdefault("aspect_ratio", ps["aspect_ratio"])
    spec = pe.enhance(a.request, domain=a.domain, modality=a.modality, overrides=ov)
    r = pe.render(spec, negative_mode="inline" if a.inline_negative else "separate")
    report = qc.lint(spec, provider=a.provider, platform=a.platform)
    if a.json:
        out({"spec": spec.to_dict(), "render": r, "qc": report})
    else:
        print(f"[{spec.modality} · {spec.domain} · {spec.technical.get('aspect_ratio')}"
              + (f" · {spec.technical['duration']:g}s" if spec.technical.get("duration") else "") + f"]  QC {report['grade']} ({report['score']})\n")
        print("PROMPT\n" + r["prompt"] + "\n")
        if r["negative_prompt"]:
            print("NEGATIVE\n" + r["negative_prompt"] + "\n")
        print("PARAMS " + json.dumps(r["params"]))
        for i in report["issues"]:
            print(f"  {i['severity']:7} {i['check']}: {i['message']} -> {i['fix']}")
    return 0


def cmd_lint(a):
    d = load_json(a.spec)
    try:
        report = qc.lint(d, provider=a.provider, model=a.model, platform=a.platform)
    except SpecError as e:
        return _err(str(e))
    out(report)
    return 0 if report["ready"] else 1


def cmd_camera(a):
    if a.action == "list":
        for m in cam.all_moves():
            print(f"{m['id']:14} {m['name']:22} {m['category']:11} min {m['min_seconds']}s  — {m['definition']}")
        return 0
    if a.action == "show":
        m = cam.get(" ".join(a.args))
        if not m:
            return _err(f"unknown movement {' '.join(a.args)!r}")
        out(m)
        return 0
    if a.action == "find":
        out(cam.find_in_text(" ".join(a.args)))
        return 0
    if a.action == "check":
        issues = cam.check_combo(a.args, a.duration)
        out({"moves": a.args, "ok": not any(i["severity"] == "error" for i in issues), "issues": issues})
        return 0 if not any(i["severity"] == "error" for i in issues) else 1
    if a.action == "phrase":
        if not a.args or not cam.get(a.args[0]):
            return _err("phrase needs a known movement id")
        print(cam.phrase(a.args[0], a.speed))
        return 0
    return _err("camera list | show | find | check | phrase")


def _available(a):
    av = set(x.strip() for x in (a.available or "").split(",") if x.strip())
    if getattr(a, "detect", False) or not av:
        av |= set(pv.local_available())
    return sorted(av)


def cmd_select(a):
    try:
        out(pv.select(a.op, _available(a), duration=a.duration, aspect=a.aspect, policy=a.policy,
                      approved_paid=a.approved_paid, prefer=a.prefer))
    except ValueError as e:
        return _err(str(e))
    return 0


def cmd_next(a):
    attempts = load_json(a.attempts)
    ranked = pv.select(a.op, _available(a), policy=a.policy)["ranked"]
    out(pv.next_action(attempts, ranked))
    return 0


def cmd_log(a):
    try:
        rec = pv.RunLog(a.file).append(a.provider, a.op, a.status, assets=a.asset, job_id=a.job_id, prompt=a.prompt,
                                       error=a.error, model=a.model, cost=a.cost, run_id=a.run_id, note=a.note)
    except ValueError as e:
        return _err(str(e))
    out(rec)
    return 0


def cmd_pack(a):
    d = load_json(a.source)
    adapter = pv.PromptOnlyAdapter(a.out)
    if "scenes" in d:
        comp = director.compile_plan(d)
        files = []
        for s in comp["shots"]:
            files += adapter.execute({"id": s["id"], "operation": "t2v", "prompt": s["video_prompt"], "negative_prompt": s["negative_prompt"],
                                      "params": s["params"], "keyframe_prompt": s["keyframe_prompt"], "text": s["vo"]}).assets
        md = os.path.join(a.out, "storyboard.md")
        with open(md, "w", encoding="utf8") as f:
            f.write(director.to_markdown(d, comp))
        out({"status": "prompt_only", "files": files + [md], "note": "nothing was generated"})
        return 0
    try:
        spec = ShotSpec.from_dict(d)
    except SpecError as e:
        return _err(str(e))
    r = pe.render(spec)
    res = adapter.execute({"id": spec.id or "shot", "operation": qc.needed_operation(spec), "prompt": r["prompt"],
                           "negative_prompt": r["negative_prompt"], "params": r["params"]})
    out({"status": res.status, "files": res.assets, "note": "nothing was generated"})
    return 0


def cmd_plan(a):
    if a.action == "new":
        if not a.args:
            return _err("plan new needs an idea")
        try:
            p = director.new_plan(" ".join(a.args), duration=a.duration, platform=a.platform, domain=a.domain, aspect=a.aspect)
        except ValueError as e:
            return _err(str(e))
        if a.out:
            with open(a.out, "w", encoding="utf8") as f:
                json.dump(p, f, indent=2, ensure_ascii=False)
            print(f"wrote {a.out}: {len(p['scenes'][0]['shots'])} shots, {p['duration']:g} s, {p['aspect_ratio']} — fill the creative fields, then `plan compile`")
        else:
            out(p)
        return 0
    if a.action == "compile":
        if not a.args:
            return _err("plan compile needs plan.json")
        p = load_json(a.args[0])
        comp = director.compile_plan(p)
        if a.out:
            os.makedirs(a.out, exist_ok=True)
            with open(os.path.join(a.out, "compiled.json"), "w", encoding="utf8") as f:
                json.dump(comp, f, indent=2, ensure_ascii=False)
            with open(os.path.join(a.out, "storyboard.md"), "w", encoding="utf8") as f:
                f.write(director.to_markdown(p, comp))
            bad = [s["id"] for s in comp["shots"] if not s["qc"]["ready"]]
            print(f"wrote {a.out}/compiled.json and storyboard.md — {len(comp['shots'])} shots, {comp['total_seconds']:g} s; "
                  f"shots needing fixes: {', '.join(bad) or 'none'}; sequence ready: {comp['sequence_qc']['ready']}")
        else:
            out(comp)
        ok = comp["sequence_qc"]["ready"] and all(s["qc"]["ready"] for s in comp["shots"])
        return 0 if ok else 1
    return _err("plan new | compile")


def cmd_voice(a):
    from catana_core.voice_studio import VoiceStudio, VoiceStudioError
    vs = VoiceStudio(base_url=a.url)
    try:
        if a.action == "health":
            out({"url": vs.base_url, "health": vs.health()})
        elif a.action == "voices":
            out(vs.voices())
        elif a.action == "archetypes":
            out(vs.archetypes(q=" ".join(a.args) or None))
        elif a.action == "describe":
            out(vs.describe_voice(" ".join(a.args)))
        elif a.action == "fit":
            if not a.seconds:
                return _err("fit needs --seconds")
            out(vs.rate_fit(" ".join(a.args), a.seconds, a.lang))
        elif a.action == "speak":
            text = open(a.file, encoding="utf8").read() if a.file else " ".join(a.args)
            if not a.out:
                return _err("speak needs --out file.wav")
            r = vs.speech(text, a.out, voice=a.voice, instructions=a.instructions, speed=a.speed, language=a.language, duration=a.duration)
            if a.log:
                pv.RunLog(a.log).append("voice_studio", "tts", "succeeded", assets=[r["path"]], prompt=text,
                                        params={"voice": a.voice, "speed": a.speed, "instructions": a.instructions})
            out(r)
        elif a.action == "plan":
            comp = load_json(a.args[0])
            os.makedirs(a.out_dir, exist_ok=True)
            cues, results = [], []
            for line in comp["voiceover"]["lines"]:
                path = os.path.join(a.out_dir, f"vo_{line['shot']}.wav")
                r = vs.speech(line["text"], path, voice=a.voice or comp["voiceover"].get("voice") or "default",
                              instructions=comp["voiceover"].get("direction") or None, speed=a.speed)
                cues.append({"t": line["start"] + 0.15, "file": os.path.abspath(path), "gain": 1.0})
                results.append(r)
            with open(os.path.join(a.out_dir, "vo.json"), "w", encoding="utf8") as f:
                json.dump({"cues": cues}, f, indent=2)
            out({"rendered": len(results), "cues": os.path.join(a.out_dir, "vo.json"), "files": [r["path"] for r in results]})
        else:
            return _err("voice health | voices | archetypes | describe | fit | speak | plan")
    except VoiceStudioError as e:
        if a.log and a.action == "speak":
            pv.RunLog(a.log).append("voice_studio", "tts", "failed", error=f"{e.category}: {e}")
        print(json.dumps({"error": str(e), "category": e.category}, indent=2), file=sys.stderr)
        return 3 if e.category == "unavailable" else 2
    return 0


def cmd_providers(a):
    m = pv.manifest()
    det = pv.local_available() if a.detect else None
    rows = []
    for name, p in m["providers"].items():
        rows.append({"provider": name, "label": p["label"], "kind": p["kind"], "cost": p["cost"], "verified": p.get("verified"),
                     "operations": p["operations"], **({"detected_here": name in det} if det is not None else {})})
    out({"policy": m["policy"]["cost_policy_default"], "providers": rows})
    return 0


def cmd_docs(a):
    path = os.path.join(ROOT, "docs", "CAMERA_MOVEMENTS.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    L = ["# Camera movement library", "",
         "> Generated from `data/camera_movements.json` by `python scripts/catana.py docs` — edit the JSON, not this file.", "",
         "Every move lists its definition, best use, camera and subject behaviour, an example prompt, common mistakes and",
         "recommended combinations. `min` is the shortest clip in which the move reads cleanly. The engine uses the same data",
         "to phrase moves in prompts (`catana.py camera phrase dolly_in`) and to reject conflicting combinations",
         "(`catana.py camera check orbit_360 tracking`).", "", "| Move | Id | Category | Min | Best for |", "|---|---|---|---|---|"]
    for m in cam.all_moves():
        L.append(f"| [{m['name']}](#{m['id'].replace('_', '-')}) | `{m['id']}` | {m['category']} | {m['min_seconds']} s | {m['best_for'][0]} |")
    for m in cam.all_moves():
        L += ["", f"<a id=\"{m['id'].replace('_', '-')}\"></a>", f"## {m['name']} (`{m['id']}`)", "",
              f"**Definition.** {m['definition']}", "", f"**Best use cases.** {'; '.join(m['best_for'])}.", "",
              f"**Camera behaviour.** {m['camera_behavior']}", "", f"**Subject behaviour.** {m['subject_behavior']}", "",
              "**Example prompt.**", "", f"> {m['example_prompt']}", "",
              "**Common mistakes.**", ""] + [f"- {x}" for x in m["common_mistakes"]] + [
              "", f"**Recommended combinations.** {', '.join('`' + c + '`' for c in m['combos']) or '—'}"
              + (f" · **Conflicts with:** {', '.join('`' + c + '`' for c in m['conflicts'])}" if m["conflicts"] else ""),
              "", f"Aliases the engine recognises: {', '.join(m['aliases'])}."]
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", os.path.relpath(path, ROOT))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="catana.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("enhance"); p.add_argument("request"); p.add_argument("--domain", choices=sorted(presets()))
    p.add_argument("--modality", choices=["image", "video"]); p.add_argument("--aspect"); p.add_argument("--duration", type=float)
    p.add_argument("--platform"); p.add_argument("--provider"); p.add_argument("--inline-negative", action="store_true"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("lint"); p.add_argument("spec"); p.add_argument("--provider"); p.add_argument("--model"); p.add_argument("--platform")
    p = sub.add_parser("camera"); p.add_argument("action", choices=["list", "show", "find", "check", "phrase"]); p.add_argument("args", nargs="*")
    p.add_argument("--duration", type=float); p.add_argument("--speed", default="slow", choices=["slow", "medium", "fast"])
    for name in ("select", "next"):
        p = sub.add_parser(name); p.add_argument("--op", required=True); p.add_argument("--available", default="")
        p.add_argument("--policy", choices=["free_first", "free_only", "best_quality"]); p.add_argument("--detect", action="store_true")
        if name == "select":
            p.add_argument("--duration", type=float); p.add_argument("--aspect"); p.add_argument("--approved-paid", action="store_true"); p.add_argument("--prefer")
        else:
            p.add_argument("--attempts", required=True)
    p = sub.add_parser("classify-error"); p.add_argument("message")
    p = sub.add_parser("log"); p.add_argument("--file", required=True); p.add_argument("--provider", required=True); p.add_argument("--op", required=True)
    p.add_argument("--status", required=True); p.add_argument("--asset", action="append"); p.add_argument("--job-id"); p.add_argument("--error")
    p.add_argument("--prompt"); p.add_argument("--model"); p.add_argument("--cost"); p.add_argument("--run-id"); p.add_argument("--note")
    p = sub.add_parser("pack"); p.add_argument("source"); p.add_argument("--out", required=True)
    p = sub.add_parser("plan"); p.add_argument("action", choices=["new", "compile"]); p.add_argument("args", nargs="*")
    p.add_argument("--duration", type=float); p.add_argument("--platform"); p.add_argument("--domain", choices=sorted(presets())); p.add_argument("--aspect"); p.add_argument("--out")
    p = sub.add_parser("voice"); p.add_argument("action", choices=["health", "voices", "archetypes", "describe", "fit", "speak", "plan"]); p.add_argument("args", nargs="*")
    p.add_argument("--url"); p.add_argument("--out"); p.add_argument("--out-dir", default="build/vo"); p.add_argument("--file"); p.add_argument("--voice", default="default")
    p.add_argument("--instructions"); p.add_argument("--speed", type=float, default=1.0); p.add_argument("--language"); p.add_argument("--duration", type=float)
    p.add_argument("--seconds", type=float); p.add_argument("--lang", default="en"); p.add_argument("--log")
    p = sub.add_parser("providers"); p.add_argument("--detect", action="store_true")
    sub.add_parser("platforms"); sub.add_parser("presets"); sub.add_parser("docs")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "classify-error":
            out({"category": pv.classify_error(a.message)}); return 0
        if a.cmd == "platforms":
            out(platforms()["platforms"]); return 0
        if a.cmd == "presets":
            out({k: v["label"] for k, v in presets().items()}); return 0
        return {"enhance": cmd_enhance, "lint": cmd_lint, "camera": cmd_camera, "select": cmd_select, "next": cmd_next, "log": cmd_log,
                "pack": cmd_pack, "plan": cmd_plan, "voice": cmd_voice, "providers": cmd_providers, "docs": cmd_docs}[a.cmd](a)
    except (ValueError, SpecError) as e:
        return _err(str(e))


if __name__ == "__main__":
    sys.exit(main())
