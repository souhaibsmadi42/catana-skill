"""AI Director: idea -> production plan -> compiled, consistent shot prompts + storyboard.

new_plan(idea, ...)  builds a plan skeleton: concept slots, continuity bible, scenes and shots sized to the target
                     duration with the domain's beat structure and pacing, camera moves pre-assigned so the edit varies.
compile_plan(plan)   applies the bible to every shot, renders a keyframe image prompt + a video prompt per shot,
                     a voiceover/SFX plan, lints every shot and the whole sequence.
to_markdown(...)     the storyboard / shot list document.

Claude writes the creative content into the plan (concept, visual direction, per-shot subject/action, VO lines);
the engine guarantees structure, timing maths, continuity wording and validation.
"""
import copy
import math
from .data import presets, platforms
from .spec import ShotSpec
from . import prompt_engine as pe
from . import qc
from . import camera as cam

BEATS = {
    "architecture": [("establish", "aerial_reveal", "the location at scale"), ("approach", "dolly_in", "arriving at the entrance"),
                     ("threshold", "steadicam", "crossing into the interior"), ("flow", "parallax", "the main living space and its light"),
                     ("detail", "push_in", "a signature material or junction"), ("life", "tracking", "a human moment that sells the lifestyle"),
                     ("hero", "crane_up", "the hero wide view of the whole property"), ("end_card", "static", "logo / address / call to action")],
    "product": [("hook", "whip_pan", "a striking first frame of the product"), ("reveal", "orbit_360", "the full product, hero lighting"),
                ("detail", "push_in", "macro of the defining material or feature"), ("use", "tracking", "the product in use"),
                ("benefit", "rack_focus", "the payoff the customer feels"), ("hero", "dolly_out", "the packshot"),
                ("end_card", "static", "brand, offer, call to action")],
    "ugc": [("hook", "handheld", "a scroll-stopping line to camera"), ("problem", "handheld", "the relatable problem"),
            ("product", "handheld", "introducing the product naturally"), ("demo", "handheld", "showing it working"),
            ("result", "handheld", "the honest result / reaction"), ("cta", "handheld", "the call to action")],
    "social": [("hook", "push_in", "the hook in the first 1.5 s"), ("payoff", "whip_pan", "the promised payoff"),
               ("proof", "tracking", "proof or detail"), ("cta", "static", "call to action / loop point")],
    "cinematic": [("opening_image", "aerial_reveal", "the world"), ("setup", "dolly_in", "the protagonist in their world"),
                  ("inciting", "push_in", "the moment that changes things"), ("escalation", "tracking", "pursuit / rising stakes"),
                  ("climax", "arc", "the decisive moment"), ("resolution", "crane_up", "the new world")],
    "fashion": [("hook", "tracking", "the silhouette in motion"), ("look", "arc", "the full look"), ("detail", "push_in", "fabric, trims, accessory"),
                ("attitude", "handheld", "the character of the wearer"), ("hero", "dolly_out", "the campaign frame"), ("end_card", "static", "brand / collection")],
    "character": [("intro", "push_in", "who they are"), ("action", "tracking", "what they do"), ("emotion", "push_in", "what they feel"), ("hero", "arc", "the defining image")],
    "concept_art": [("establish", "aerial_reveal", "the world"), ("explore", "parallax", "its layers"), ("wonder", "crane_up", "its scale")],
    "automotive": [("hook", "fpv_drone", "the car bursting into frame"), ("reveal", "tracking", "the car in motion at speed"),
                   ("design", "arc", "the silhouette and signature design lines"), ("detail", "push_in", "a wheel, light or badge detail"),
                   ("interior", "steadicam", "the cockpit and the driver's hands"), ("hero", "aerial_reveal", "the car on the open road at scale"),
                   ("end_card", "static", "model name, offer, call to action")],
    "food": [("hook", "push_in", "the most appetizing moment"), ("ingredients", "top_down", "the fresh ingredients"),
             ("craft", "tracking", "the cooking or pouring action"), ("detail", "rack_focus", "texture, steam, drip"),
             ("hero", "arc", "the finished dish or drink"), ("end_card", "static", "brand, offer, where to get it")],
    "general": [("open", "dolly_in", "the opening image"), ("develop", "tracking", "development"), ("highlight", "arc", "the highlight"), ("close", "dolly_out", "the closing image")],
}
TRANSITIONS = {"hook": "hard cut on the beat", "end_card": "dip to brand colour", "cta": "hard cut", "reveal": "light flash / whip",
               "hero": "match cut", "establish": "fade in from black", "opening_image": "fade in from black"}


def _skeleton_shots(base, domain, beats, n_shots, speed):
    shots = []
    for i in range(n_shots):
        if n_shots >= len(beats):
            bi = min(int(i * len(beats) / n_shots), len(beats) - 1)
        else:                                       # fewer shots than beats: keep the first and last beat (hook / end card)
            bi = round(i * (len(beats) - 1) / max(1, n_shots - 1))
        beat, move, purpose = beats[bi]
        first_of_beat = i == 0 or shots[-1]["beat"] != beat
        if i > 0 and shots[-1]["beat"] == beat and domain != "ugc":  # vary the move within a beat (UGC stays handheld phone)
            alt = [c for c in (cam.get(move)["combos"] or ["push_in"]) if c != "static"] or ["push_in"]
            move = alt[(i - 1) % len(alt)]
        shots.append({
            "id": f"S{i + 1:02d}", "beat": beat, "purpose": purpose, "duration": 0.0,
            "subject": f"{base.subject} — {purpose}" if beat not in ("end_card", "cta") else f"{purpose} for {base.subject}, clean negative space for text",
            "action": "" if beat not in ("end_card", "cta") else "the frame settles and holds, only gentle ambient light movement",
            "environment": "", "camera_moves": [{"id": move, "speed": speed}],
            "characters": [], "vo": "", "sfx": "", "transition_out": TRANSITIONS.get(beat, "cut on action") if first_of_beat or beat in ("end_card", "cta") else "cut on action",
            "references": [],
        })
    return shots


def new_plan(idea, duration=None, platform=None, domain=None, aspect=None, title=None):
    if not idea or not idea.strip():
        raise ValueError("new_plan needs an idea")
    base = pe.enhance(idea, domain=domain, modality="video")
    domain = base.domain
    plat = platform or base.technical.get("platform")
    pspec = platforms()["platforms"].get(plat) if plat else None
    if plat and not pspec:
        raise ValueError(f"unknown platform {plat!r}")
    aspect = aspect or (pspec["aspect_ratio"] if pspec else base.technical.get("aspect_ratio", "16:9"))
    duration = float(duration or (pspec["ideal_seconds"][1] if pspec else {"architecture": 45, "product": 20, "ugc": 25, "social": 15,
                                                                           "cinematic": 60, "fashion": 20}.get(domain, 30)))
    lo, hi = presets()[domain].get("shot_seconds", [3, 5])
    beats = BEATS.get(domain, BEATS["general"])
    avg = (lo + hi) / 2
    n_shots = min(24, max(1, round(duration / avg)))
    if n_shots < len(beats) and duration >= len(beats) * lo:
        n_shots = len(beats)
    speed = "medium" if domain in ("social", "ugc") else "slow"
    while True:                                                        # fewest cuts lost: drop shots until every move fits
        shots = _skeleton_shots(base, domain, beats, n_shots, speed)
        needs = [max(lo, cam.get(s["camera_moves"][0]["id"])["min_seconds"]) for s in shots]
        if sum(needs) <= duration + 1e-6 or n_shots == 1:
            break
        n_shots -= 1
    spare = max(0.0, duration - sum(needs))
    for s, need in zip(shots, needs):                                  # distribute spare time in proportion to need
        s["duration"] = round(need + spare * need / sum(needs), 2)
    shots[-1]["duration"] = round(duration - sum(x["duration"] for x in shots[:-1]), 2)
    return {
        "title": title or base.subject[:60], "idea": idea, "domain": domain, "platform": plat, "aspect_ratio": aspect,
        "duration": duration, "fps": (pspec or {}).get("fps", 24 if domain == "cinematic" else 30),
        "concept": "", "visual_direction": "", "logline": "",
        "bible": {
            "characters": {}, "products": {}, "locations": {},
            "style": base.style, "grade": base.color, "palette": "", "lens_package": base.lens, "lighting": base.lighting,
            "negative": [],
        },
        "sound": {"music": "", "sfx_style": "", "vo_voice": "", "vo_direction": "", "provider": "voice_studio"},
        "scenes": [{"id": "SC1", "name": "main", "shots": shots}],
        "edit": {"sequence": [s["id"] for s in shots], "notes": ""},
        "_todo": "Claude: fill concept, visual_direction, logline, bible (characters/products/locations/palette), and per shot: "
                 "subject, action, environment, vo, sfx. Use @id tokens to reference bible entries.",
    }


def _shot_spec(plan, shot, defaults):
    sp = copy.deepcopy(defaults)
    sp.id = shot["id"]
    sp.subject = shot.get("subject") or sp.subject
    sp.motion = shot.get("action") or sp.motion
    if shot.get("environment"):
        sp.environment = shot["environment"]
    sp.camera_moves = [dict(m) for m in shot.get("camera_moves", [])] or sp.camera_moves
    sp.characters = list(shot.get("characters", []))
    sp.references = list(shot.get("references", []))
    sp.technical = dict(sp.technical, aspect_ratio=plan["aspect_ratio"], duration=float(shot.get("duration") or 5),
                        fps=plan.get("fps", 30))
    if plan.get("platform"):
        sp.technical["platform"] = plan["platform"]
    if shot.get("lens"):
        sp.lens = shot["lens"]                  # per-shot override (e.g. a tighter interior lens); bible lens package otherwise
    if shot.get("lighting"):
        sp.lighting = shot["lighting"]          # per-shot override (e.g. a deliberate day-to-night beat); bible lighting otherwise
    if shot.get("time_of_day"):
        sp.technical["time_of_day"] = shot["time_of_day"]
    sp.notes = shot.get("notes", "")
    return sp.validate()


def compile_plan(plan):
    """Return {'shots': [...], 'sequence_qc', 'voiceover', 'edl'} — every shot with keyframe + video prompts and its QC."""
    if not plan.get("scenes"):
        raise ValueError("plan has no scenes")
    defaults = pe.enhance(plan["idea"], domain=plan["domain"], modality="video")
    defaults.style = plan["bible"].get("style") or defaults.style
    defaults.lens = plan["bible"].get("lens_package") or defaults.lens
    defaults.lighting = plan["bible"].get("lighting") or defaults.lighting
    out, specs, t = [], [], 0.0
    for scene in plan["scenes"]:
        for shot in scene["shots"]:
            spec = pe.apply_bible(_shot_spec(plan, shot, defaults), plan["bible"])
            still = spec.copy()
            still.modality = "image"
            still.camera_moves = []
            still.motion = ""
            still.technical = {k: v for k, v in spec.technical.items() if k in ("aspect_ratio", "platform", "time_of_day")}
            vid = pe.render(spec, negative_mode="separate")
            img = pe.render(still, negative_mode="separate")
            report = qc.lint(spec)
            out.append({"id": shot["id"], "scene": scene["id"], "beat": shot.get("beat"), "start": round(t, 2),
                        "duration": spec.technical["duration"], "camera": [m["id"] for m in spec.camera_moves],
                        "keyframe_prompt": img["prompt"], "video_prompt": vid["prompt"], "negative_prompt": vid["negative_prompt"],
                        "params": vid["params"], "vo": shot.get("vo", ""), "sfx": shot.get("sfx", ""),
                        "transition_out": shot.get("transition_out", "cut"), "qc": {"score": report["score"], "grade": report["grade"],
                                                                                     "ready": report["ready"], "issues": report["issues"]}})
            specs.append(spec)
            t += spec.technical["duration"]
    seq = qc.lint_sequence(specs, target_duration=plan.get("duration"), bible=plan["bible"])
    vo = voiceover_plan(plan, out)
    edl = [{"id": s["id"], "in": s["start"], "out": round(s["start"] + s["duration"], 2), "transition": s["transition_out"]} for s in out]
    return {"title": plan["title"], "aspect_ratio": plan["aspect_ratio"], "total_seconds": round(t, 2), "shots": out,
            "sequence_qc": seq, "voiceover": vo, "edl": edl}


WORDS_PER_SECOND = 2.5   # conversational English VO; VoiceStudio /tools/rate-fit gives the exact fit when available


def voiceover_plan(plan, compiled_shots):
    lines = []
    for s in compiled_shots:
        if s.get("vo"):
            words = len(s["vo"].split())
            need = words / WORDS_PER_SECOND
            lines.append({"shot": s["id"], "start": s["start"], "slot": s["duration"], "text": s["vo"], "words": words,
                          "estimated_seconds": round(need, 2), "fits": need <= s["duration"] * 0.95,
                          "fix": "" if need <= s["duration"] * 0.95 else
                          f"trim to about {int(s['duration'] * 0.95 * WORDS_PER_SECOND)} words or lengthen the shot"})
    snd = plan.get("sound", {})
    return {"provider": snd.get("provider", "voice_studio"), "voice": snd.get("vo_voice", ""), "direction": snd.get("vo_direction", ""),
            "lines": lines, "script": " ".join(l["text"] for l in lines)}


def to_markdown(plan, compiled):
    L = [f"# {plan['title']}", "",
         f"**Format:** {plan['aspect_ratio']} · {compiled['total_seconds']:g} s · {plan.get('fps', 30)} fps"
         + (f" · {platforms()['platforms'][plan['platform']]['label']}" if plan.get("platform") else "") + f" · domain: {plan['domain']}", ""]
    for k, label in (("logline", "Logline"), ("concept", "Creative concept"), ("visual_direction", "Visual direction")):
        if plan.get(k):
            L += [f"## {label}", "", plan[k], ""]
    b = plan["bible"]
    L += ["## Continuity bible", "", f"- **Style:** {b.get('style', '')}", f"- **Grade:** {b.get('grade', '')}",
          f"- **Lens package:** {b.get('lens_package', '')}", f"- **Lighting:** {b.get('lighting', '')}"]
    if b.get("palette"):
        L.append(f"- **Palette:** {b['palette']}")
    for group in ("characters", "products", "locations"):
        for k, v in (b.get(group) or {}).items():
            L.append(f"- **@{k}** ({group[:-1]}): {v}")
    L += ["", "## Shot list", "", "| # | Beat | Time | Dur | Camera | Transition | QC |", "|---|---|---|---|---|---|---|"]
    for s in compiled["shots"]:
        L.append(f"| {s['id']} | {s['beat']} | {s['start']:g}s | {s['duration']:g}s | {', '.join(s['camera'])} | {s['transition_out']} | {s['qc']['grade']} ({s['qc']['score']}) |")
    L += ["", "## Storyboard", ""]
    for s in compiled["shots"]:
        L += [f"### {s['id']} — {s['beat']} ({s['start']:g}–{s['start'] + s['duration']:g} s)", "",
              f"**Keyframe (image) prompt**", "", "```", s["keyframe_prompt"], "```", "",
              f"**Video prompt**", "", "```", s["video_prompt"], "```", ""]
        if s["negative_prompt"]:
            L += [f"**Negative:** {s['negative_prompt']}", ""]
        if s["vo"]:
            L += [f"**VO:** {s['vo']}", ""]
        if s["sfx"]:
            L += [f"**SFX:** {s['sfx']}", ""]
        warn = [i for i in s["qc"]["issues"] if i["severity"] != "info"]
        if warn:
            L += ["**QC:**"] + [f"- {i['severity']}: {i['message']} → {i['fix']}" for i in warn] + [""]
    snd = plan.get("sound", {})
    L += ["## Sound", "", f"- **Music:** {snd.get('music') or '(user track — CATANA does not generate music)'}",
          f"- **SFX:** {snd.get('sfx_style') or 'procedural SFX on cuts (catana motion mixer) or described per shot'}",
          f"- **Voiceover:** {compiled['voiceover']['provider']}" + (f", voice {snd['vo_voice']}" if snd.get("vo_voice") else "")]
    for l in compiled["voiceover"]["lines"]:
        flag = "" if l["fits"] else f" ⚠ {l['fix']}"
        L.append(f"  - {l['shot']} @ {l['start']:g}s: “{l['text']}” (~{l['estimated_seconds']:g}s / slot {l['slot']:g}s){flag}")
    L += ["", "## Edit sequence", ""] + [f"{i + 1}. {e['id']} {e['in']:g}–{e['out']:g} s → {e['transition']}" for i, e in enumerate(compiled["edl"])]
    sq = compiled["sequence_qc"]
    L += ["", "## Sequence QC", "", "Ready." if sq["ready"] and not sq["issues"] else ""]
    L += [f"- {i['severity']}: {i['message']} → {i['fix']}" for i in sq["issues"]]
    return "\n".join(L).rstrip() + "\n"
