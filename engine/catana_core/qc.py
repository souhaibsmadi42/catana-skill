"""Quality control: a prompt validation checklist with actionable fixes, run before any generation.

lint(spec)            -> report for one shot: score, grade, ready, issues[{severity, check, field, message, fix}]
lint_sequence(shots)  -> continuity report across a multi-shot sequence (subject, lighting, aspect, pacing)

Checks: completeness, specificity (no generic filler), camera direction, motion quality, lighting consistency,
composition / aspect ratio, realism / style conflicts, temporal consistency, reference adherence, technical
compatibility (incl. provider limits), negative constraints.
"""
import re
from . import camera as cam
from .data import platforms, providers
from .spec import ShotSpec

PENALTY = {"error": 20, "warning": 8, "info": 2}
VAGUE = ["beautiful", "amazing", "nice", "stunning", "awesome", "good", "great", "gorgeous", "perfect", "best",
         "high quality", "best quality", "masterpiece", "8k", "4k", "ultra detailed", "ultra-detailed", "hyperrealistic",
         "hyper realistic", "really", "trending on artstation", "award winning", "award-winning"]
LIGHT_WORDS = ["key", "rim", "fill", "softbox", "sun", "window", "backlight", "back light", "practical", "neon", "golden hour",
               "blue hour", "overcast", "moonlight", "candle", "lamp", "strip", "bounce", "hard light", "soft light", "daylight",
               "studio", "spotlight", "tungsten", "flare", "shadow", "haze", "volumetric", "led", "sky", "light from", "lit"]
LENS_WORDS = ["mm", "macro", "anamorphic", "wide", "telephoto", "tilt-shift", "fisheye", "prime", "zoom lens", "f/", "smartphone",
              "lens"]
COMPOSITION_WORDS = ["close-up", "close up", "closeup", "medium", "wide", "full-length", "full length", "full body", "centered",
                     "centred", "thirds", "symmetr", "negative space", "framing", "frame", "foreground", "background", "headroom",
                     "leading lines", "golden section", "overhead", "flat lay", "composition", "silhouette", "two-shot", "insert"]
CAMERA_WORDS = ["eye-level", "eye level", "low angle", "high angle", "overhead", "top-down", "bird", "worm", "three-quarter",
                "profile", "front", "dutch", "camera", "handheld", "tripod", "pov", "angle", "height"]
MOTION_VERBS = r"\b(walk|walks|walking|turn|turns|turning|rotat\w*|pour\w*|run\w*|move\w*|moving|drift\w*|sway\w*|flow\w*|" \
               r"rise|rises|rising|fall\w*|open\w*|clos\w*|spin\w*|glid\w*|reach\w*|look\w*|smil\w*|talk\w*|gestur\w*|" \
               r"show\w*|hold\w*|lift\w*|blink\w*|breath\w*|splash\w*|ripple\w*|flicker\w*|unbox\w*|appl\w*|wav\w*|" \
               r"dance\w*|jump\w*|step\w*|enter\w*|exit\w*|emerg\w*|reveal\w*|steam\w*|swirl\w*|float\w*|land\w*|" \
               r"surface\w*|ris\w*|grow\w*|melt\w*|form\w*|transform\w*|unfold\w*|glow\w*|catch\w*|throw\w*|tak\w*|" \
               r"pick\w*|put\w*|place\w*|slid\w*|fly\w*|flies|crash\w*|burst\w*|driv\w*|sail\w*|swim\w*|cycl\w*|rid\w*|climb\w*|" \
               r"present\w*|demonstrat\w*|point\w*|nod\w*|laugh\w*|roll\w*|cruis\w*|rac\w*|speed\w*|hover\w*|crawl\w*|pan\w*|drizzl\w*|drip\w*|sizzl\w*|bounc\w*|shak\w*|wav\w*|sweep\w*)\b"
TOD_GROUPS = {
    "golden_hour": ["golden hour", "sunset", "sunrise"],
    "blue_hour": ["blue hour", "twilight", "dusk"],
    "night": ["night", "moonlight", "midnight", "starlit"],
    "midday": ["midday", "noon", "harsh overhead sun"],
}
STYLE_FAMILIES = {
    "photoreal": ["photorealistic", "photography", "photograph", "photo", "realistic", "35mm film", "cinematic film still"],
    "illustrated": ["cartoon", "anime", "illustration", "watercolor", "watercolour", "oil painting", "pixel art", "vector art",
                    "comic", "cel-shaded", "claymation", "clay", "low poly"],
}


def _issue(issues, severity, check, field, message, fix):
    issues.append({"severity": severity, "check": check, "field": field, "message": message, "fix": fix})


def _has(text, words):
    t = text.lower()
    return any(w in t for w in words)


def _specificity(text):
    """Number of meaningful words left after removing generic filler."""
    t = text.lower()
    for v in sorted(VAGUE, key=len, reverse=True):
        t = re.sub(r"(?<![a-z])" + re.escape(v) + r"(?![a-z])", " ", t)
    return len([w for w in re.findall(r"[a-z0-9'/-]+", t) if len(w) > 2])


def _vague_words(text):
    t = text.lower()
    return [v for v in VAGUE if re.search(r"(?<![a-z])" + re.escape(v) + r"(?![a-z])", t)]


def _time_of_day(text):
    found = set()
    t = text.lower()
    for g, words in TOD_GROUPS.items():
        if any(re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", t) for w in words):
            found.add(g)
    return found


def lint(spec, provider=None, model=None, platform=None):
    if isinstance(spec, dict):
        spec = ShotSpec.from_dict(spec)
    spec.validate()
    issues = []
    video = spec.modality == "video"
    t = spec.technical

    # ---------------------------------------------------------------- completeness + specificity
    required = ["objective", "subject", "environment", "composition", "camera", "lens", "lighting", "materials", "style", "color"]
    if video:
        required.append("motion")
    placed = re.search(r"\b(in|at|on|inside|outside|over|under|beside|against|through|across|by|along|near|around|into|onto|above|below|within)\s+\w", spec.subject.lower())
    for f in required:
        val = getattr(spec, f).strip()
        if not val and f == "environment" and placed:
            continue
        if not val:
            sev = "error" if f in ("subject",) or (video and f == "motion") else "warning"
            _issue(issues, sev, "completeness", f, f"{f} is empty",
                   f"fill {f} (run `catana.py enhance` to get a specific domain default)")
    if spec.subject and _specificity(spec.subject) < 3:
        _issue(issues, "error", "specificity", "subject", f"subject is too thin: {spec.subject!r}",
               "name the subject concretely: what it is, material/finish, size, colour, distinguishing details, action")
    vague = _vague_words(spec.positive_text())
    if vague:
        _issue(issues, "warning", "specificity", "*", f"generic filler words carry no visual information: {', '.join(sorted(set(vague)))}",
               "replace each with a concrete instruction (e.g. 'stunning lighting' -> 'low golden sun raking from the left, long shadows')")
    if spec.lighting and not _has(spec.lighting, LIGHT_WORDS):
        _issue(issues, "warning", "lighting", "lighting", "lighting names no source or direction",
               "state the key source, its direction and quality, plus fill/rim (e.g. 'large softbox key at 45° left, strip rim')")
    if spec.lens and not _has(spec.lens, LENS_WORDS):
        _issue(issues, "warning", "camera", "lens", "lens has no focal length or lens type", "give a focal length and aperture (e.g. '85mm, f/1.8')")
    if spec.composition and not _has(spec.composition, COMPOSITION_WORDS):
        _issue(issues, "warning", "composition", "composition", "composition gives no framing",
               "state shot size and placement (e.g. 'medium close-up, subject on the left third, negative space right')")
    if spec.camera and not _has(spec.camera, CAMERA_WORDS) and not spec.camera_moves:
        _issue(issues, "info", "camera", "camera", "camera gives no angle or height", "add angle/height (e.g. 'low three-quarter angle')")

    # ---------------------------------------------------------------- camera direction
    move_ids = [m["id"] for m in spec.camera_moves]
    # explicit moves win; free text is only scanned when none were given (preset wording like "camera car" must not add moves)
    text_moves = [] if move_ids else [m["id"] for m in cam.find_in_text(" ".join([spec.camera, spec.motion]))]
    all_moves = list(dict.fromkeys(move_ids + text_moves))
    if video:
        if not all_moves:
            _issue(issues, "warning", "camera", "camera_moves", "video has no camera movement or explicit 'static' camera",
                   "pick one move from the library (e.g. slow dolly in) or say 'locked-off static camera'")
        for i in cam.check_combo(all_moves, t.get("duration")):
            _issue(issues, i["severity"], "camera", "camera_moves", i["message"], i["fix"])
    elif move_ids:
        _issue(issues, "info", "camera", "camera_moves", "camera moves are ignored for still images",
               "describe the angle and framing instead, or switch modality to video")

    # ---------------------------------------------------------------- motion quality
    if video:
        motion_text = " ".join([spec.subject, spec.motion])
        if spec.motion and not re.search(MOTION_VERBS, motion_text.lower()):
            _issue(issues, "warning", "motion", "motion", "motion has no concrete action verb",
                   "describe what moves and how (e.g. 'steam curls up from the cup, her hand slowly turns the mug')")
        dur = t.get("duration") or 5
        bare = re.sub(r"\([^)]*\)", "", (spec.motion + ", " + spec.subject).lower())   # actions hide in the subject too
        actions = len([a for a in re.split(r",|;|\bthen\b|\band then\b|\bafter that\b", bare) if re.search(MOTION_VERBS, a)])
        if actions > max(2, int(dur / 2.5) + 1):
            _issue(issues, "warning", "motion", "motion", f"{actions} actions in a {dur:g} s clip — models rush or drop actions",
                   f"keep about one action per 2.5 s ({max(1, int(dur / 2.5))} here) or split into several shots")
        if t.get("motion_intensity") == "high" and dur >= 8 and spec.domain in ("architecture", "product"):
            _issue(issues, "info", "motion", "technical", "high motion intensity on a long architecture/product shot often warps geometry",
                   "use low or medium intensity and let the camera move carry the shot")
        if re.search(r"\b(morph\w*|transform\w* into|turns into|becomes)\b", spec.positive_text()) and "transition" not in spec.positive_text():
            _issue(issues, "info", "temporal", "motion", "a transformation without a described transition tends to flicker",
                   "describe the transition (e.g. 'a seamless wipe of light sweeps across, revealing the night version')")

    # ---------------------------------------------------------------- lighting consistency
    tods = _time_of_day(" ".join([spec.lighting, spec.environment, spec.subject, spec.color]))
    if len(tods) > 1:
        _issue(issues, "error", "lighting", "lighting", f"conflicting times of day: {', '.join(sorted(tods))}",
               "pick one time of day; for a day-to-night change make it a video transition or separate shots")

    # ---------------------------------------------------------------- style / realism
    fams = [f for f, words in STYLE_FAMILIES.items() if _has(spec.style + " " + spec.color, words)]
    if len(fams) > 1:
        _issue(issues, "warning", "realism", "style", "style mixes photoreal and illustrated vocabularies",
               "choose one rendering family (or say explicitly '3D animated film look' / 'photographic')")

    # ---------------------------------------------------------------- composition / aspect / platform
    ar = t.get("aspect_ratio")
    if not ar:
        _issue(issues, "warning", "technical", "technical.aspect_ratio", "no aspect ratio", "set technical.aspect_ratio (16:9, 9:16, 1:1, 4:5…)")
    plat = platform or t.get("platform")
    if plat:
        ps = platforms()["platforms"].get(plat)
        if not ps:
            _issue(issues, "warning", "technical", "technical.platform", f"unknown platform {plat!r}",
                   f"use one of {', '.join(platforms()['platforms'])}")
        elif ar and ps["aspect_ratio"] != ar:
            _issue(issues, "warning", "composition", "technical.aspect_ratio", f"{ps['label']} delivers {ps['aspect_ratio']} but the spec is {ar}",
                   f"set aspect_ratio to {ps['aspect_ratio']} or reframe for the platform")
        if ps and video and t.get("duration") and not (ps["ideal_seconds"][0] * 0.5 <= t["duration"] <= ps["ideal_seconds"][1] * 2):
            _issue(issues, "info", "technical", "technical.duration", f"{t['duration']:g} s is far from the usual {ps['label']} length",
                   f"aim for {ps['ideal_seconds'][0]}–{ps['ideal_seconds'][1]} s total")
    if ar in ("9:16", "4:5", "3:4") and re.search(r"\b(panoram\w*|ultra[- ]wide|wide landscape|horizon to horizon)\b", spec.composition.lower()):
        _issue(issues, "warning", "composition", "composition", f"a panoramic composition fights a vertical {ar} frame",
               "compose vertically: stack foreground, subject and sky, or use a tilt/pedestal to reveal height")

    # ---------------------------------------------------------------- references
    roles = [r.get("role", "subject") for r in spec.references]
    for r in spec.references:
        role = r.get("role", "subject")
        if role in ("first_frame", "last_frame") and not video:
            _issue(issues, "error", "reference", "references", f"a {role} reference only applies to video", "set modality to video or change the role")
        if role in ("subject", "character", "product", "geometry", "composition") and not r.get("preserve"):
            _issue(issues, "warning", "reference", "references", f"{role} reference has no 'preserve' list — the model may reinterpret it",
                   "list what must stay identical (e.g. ['exact product shape', 'label artwork', 'brand colours'])")
    if spec.domain == "architecture" and any(r in roles for r in ("geometry", "subject", "first_frame")):
        keep = " ".join(" ".join(r.get("preserve", [])) for r in spec.references).lower()
        if not any(w in keep for w in ("massing", "geometry", "floors", "window", "facade", "façade", "openings", "structure")):
            _issue(issues, "warning", "reference", "references", "architectural reference without geometry preservation",
                   "preserve 'building massing', 'number of floors', 'window layout', 'roof form' and the reference camera position")
    if roles.count("last_frame") and not roles.count("first_frame"):
        _issue(issues, "info", "reference", "references", "a last frame without a first frame", "add the first frame for a controlled first/last-frame generation")
    if len(spec.characters) > 1 or len(re.findall(r"@[A-Za-z0-9_\-]+", spec.subject)) > 1:
        _issue(issues, "info", "temporal", "characters", "several recurring characters in one shot", "use reference images per character and keep them in separate halves of the frame")

    # ---------------------------------------------------------------- technical compatibility
    if video and not t.get("duration"):
        _issue(issues, "warning", "technical", "technical.duration", "video without a duration", "set technical.duration in seconds")
    if video and t.get("duration", 0) > 15:
        _issue(issues, "info", "technical", "technical.duration", f"{t['duration']:g} s in one generation — consistency drops on long clips",
               "split into 4–10 s shots and assemble in the edit (see the AI Director)")
    if provider:
        _provider_checks(issues, spec, provider, model)

    # ---------------------------------------------------------------- negatives
    if not spec.negative:
        _issue(issues, "warning", "negative", "negative", "no negative constraints", "add the domain negatives (artifacts the model tends to produce)")
    pos = spec.positive_text()
    for n in spec.negative:
        n0 = n.lower().strip()
        if len(n0) > 3 and re.search(r"(?<![a-z])" + re.escape(n0) + r"(?![a-z])", pos):
            _issue(issues, "warning", "negative", "negative", f"'{n}' is both requested and forbidden", f"remove '{n}' from the negatives or from the prompt")

    score = max(0, 100 - sum(PENALTY[i["severity"]] for i in issues))
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
    order = {"error": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda i: order[i["severity"]])
    return {"score": score, "grade": grade, "ready": not any(i["severity"] == "error" for i in issues),
            "counts": {s: sum(1 for i in issues if i["severity"] == s) for s in order}, "issues": issues}


def _provider_checks(issues, spec, provider, model=None):
    prov = providers()["providers"].get(provider)
    if not prov:
        _issue(issues, "error", "technical", "provider", f"unknown provider {provider!r}", f"use one of {', '.join(providers()['providers'])}")
        return
    t = spec.technical
    op = needed_operation(spec)
    if op not in prov["operations"]:
        _issue(issues, "error", "technical", "provider", f"{prov['label']} does not support {op}",
               "pick another provider (`catana.py select --op " + op + "`)")
    lim = prov.get("limits", {})
    m = (prov.get("known_models") or {}).get(model) if model else None
    if m and m.get("seconds") and t.get("duration"):
        lo, hi = m["seconds"]
        if not lo <= t["duration"] <= hi:
            _issue(issues, "error", "technical", "technical.duration", f"{model} accepts {lo}–{hi} s, spec asks {t['duration']:g} s",
                   f"set duration within {lo}–{hi} s or choose another model")
    elif spec.modality == "video" and t.get("duration") and lim.get("video_seconds_max") and t["duration"] > lim["video_seconds_max"]:
        _issue(issues, "error", "technical", "technical.duration", f"{prov['label']} generates at most {lim['video_seconds_max']} s",
               "split the shot or shorten it")
    if lim.get("aspect_ratios") and t.get("aspect_ratio") and t["aspect_ratio"] not in lim["aspect_ratios"]:
        _issue(issues, "warning", "technical", "technical.aspect_ratio", f"{prov['label']} lists {', '.join(lim['aspect_ratios'])}",
               "choose a supported ratio and reframe/crop in the edit")


def needed_operation(spec):
    roles = [r.get("role", "subject") for r in spec.references]
    if spec.modality == "video":
        if "first_frame" in roles and "last_frame" in roles:
            return "first_last"
        if "first_frame" in roles:
            return "i2v"
        if "motion" in roles:
            return "motion_transfer"
        if len(spec.references) >= 1:
            return "multi_ref_video"
        return "t2v"
    if "style" in roles and len(spec.references) == 1:
        return "style_transfer"
    if len(spec.references) > 1:
        return "multi_ref_image"
    if spec.references:
        return "i2i"
    return "t2i"


# ------------------------------------------------------------------ sequences
def lint_sequence(shots, target_duration=None, bible=None):
    """Continuity checks across shots (list of ShotSpec or dicts in edit order)."""
    specs = [s if isinstance(s, ShotSpec) else ShotSpec.from_dict(s) for s in shots]
    issues = []
    if not specs:
        return {"ready": False, "issues": [{"severity": "error", "check": "sequence", "field": "shots", "message": "no shots", "fix": "add shots"}]}
    ars = {s.technical.get("aspect_ratio") for s in specs}
    if len(ars) > 1:
        _issue(issues, "error", "continuity", "technical.aspect_ratio", f"mixed aspect ratios in one sequence: {', '.join(sorted(a for a in ars if a))}",
               "deliver one ratio per sequence (make a separate cut for other platforms)")
    styles = {s.style for s in specs}
    if len(styles) > 1:
        _issue(issues, "warning", "continuity", "style", f"{len(styles)} different style descriptions across shots",
               "lock style and grade in the continuity bible so every shot uses identical wording")
    grades = {s.color for s in specs}
    if len(grades) > 1:
        _issue(issues, "warning", "continuity", "color", "colour grade wording differs between shots", "use the bible's grade for every shot")
    prev_tod = None
    for i, s in enumerate(specs):
        tod = s.technical.get("time_of_day") or (sorted(_time_of_day(s.lighting))[0] if _time_of_day(s.lighting) else None)
        if prev_tod and tod and tod != prev_tod and "transition" not in (s.notes + s.motion).lower():
            _issue(issues, "warning", "continuity", f"shots[{i}].lighting", f"time of day jumps from {prev_tod} to {tod} at shot {i + 1}",
                   "keep lighting continuous within a scene or mark the change as a deliberate transition in notes/motion")
        prev_tod = tod or prev_tod
    for i in range(2, len(specs)):
        a, b, c = ([m["id"] for m in specs[j].camera_moves] for j in (i - 2, i - 1, i))
        if a and a == b == c:
            _issue(issues, "info", "pacing", f"shots[{i}].camera_moves", f"the same camera move ({a[0]}) three shots in a row",
                   "vary the move or the shot size to keep the edit alive")
    if bible and bible.get("characters"):
        for cid, desc in bible["characters"].items():
            uses = [i for i, s in enumerate(specs) if cid in s.characters]
            for i in uses:
                if desc not in specs[i].subject:
                    _issue(issues, "error", "continuity", f"shots[{i}].subject", f"character '{cid}' is not described with the locked bible text",
                           "compile shots through apply_bible() so the description is identical")
    total = sum(s.technical.get("duration", 0) for s in specs if s.modality == "video")
    if target_duration and total and abs(total - target_duration) > max(1.0, 0.15 * target_duration):
        _issue(issues, "warning", "pacing", "technical.duration", f"shots add up to {total:g} s, target is {target_duration:g} s",
               "adjust shot durations or add/remove shots")
    order = {"error": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda i: order[i["severity"]])
    return {"ready": not any(i["severity"] == "error" for i in issues), "total_seconds": total, "issues": issues}
