"""Prompt engine: natural language -> ShotSpec -> provider-ready prompt.

enhance()  parses a plain request (domain, modality, platform, aspect, duration, camera moves, lighting cues),
           then fills every empty field from the domain preset so no prompt goes out generic.
render()   turns a ShotSpec into an image or video prompt (+ negative prompt + generation params).
apply_bible() injects locked continuity descriptors (characters, products, palette, lens, grade) into a shot.

The parser is deliberately simple and predictable: Claude writes or refines the creative content of the spec; the
engine guarantees structure, specificity defaults, ordering and consistency.
"""
import re
from .data import presets, platforms
from .spec import ShotSpec, ASPECT_RATIOS
from . import camera as cam

# ------------------------------------------------------------------ cue dictionaries
LIGHTING_CUES = [
    ("golden hour", "golden hour sunlight, low warm sun raking across surfaces, long soft shadows, glowing rim light", "golden_hour"),
    ("sunset", "sunset light, warm low sun near the horizon, orange-to-magenta sky gradient, long shadows", "golden_hour"),
    ("sunrise", "sunrise light, soft warm low sun, cool shadows, light morning haze", "golden_hour"),
    ("blue hour", "blue hour twilight, deep blue ambient sky, warm interior and street lights glowing", "blue_hour"),
    ("twilight", "twilight, cobalt sky with the last warm glow on the horizon, practical lights on", "blue_hour"),
    ("dusk", "dusk, fading warm light with deep blue shadows, practical lights switching on", "blue_hour"),
    ("night", "night scene, motivated practical lights and moonlight, deep shadows, specular highlights on wet surfaces", "night"),
    ("moonlight", "cool moonlight from above, silver highlights, deep blue shadows", "night"),
    ("neon", "neon signage casting saturated magenta and cyan light, wet reflective surfaces", "night"),
    ("candlelight", "warm flickering candlelight as the key, deep surrounding darkness", "night"),
    ("overcast", "soft overcast daylight, even diffused light, gentle shadows", "day"),
    ("midday", "high midday sun, crisp hard shadows directly beneath objects", "midday"),
    ("noon", "high noon sun, short hard shadows, bright contrast", "midday"),
    ("studio", "controlled studio lighting: large softbox key, strip-light rim, white bounce fill", "studio"),
    ("backlit", "strong backlight creating a glowing rim around the subject, slight lens flare", None),
    ("low key", "low-key lighting, single hard key, most of the frame in shadow", None),
    ("high key", "high-key lighting, bright and even with minimal shadows", None),
]
VIDEO_WORDS = ["video", "clip", "film", "footage", "reel", "reels", "tiktok", "shorts", "animate", "animated", "animation",
               "commercial", "trailer", "teaser", "b-roll", "broll", "cinematic sequence", "sequence", "spot", "walkthrough",
               "fly-through", "flythrough", "timelapse", "time-lapse", "motion", "moving", "seconds", "sec"]
IMAGE_WORDS = ["photo", "photograph", "photography", "image", "picture", "still", "poster", "render", "rendering",
               "illustration", "wallpaper", "thumbnail", "packshot", "headshot", "portrait photo", "key visual", "flat lay"]
FILLER = re.compile(r"^(please\s+)?(can you\s+)?(create|make|generate|produce|design|build|give me|i need|i want|render|shoot|write)\s+(me\s+)?"
                    r"(a|an|the|some)?\s*", re.I)
LEADING_FORMAT = re.compile(r"^(stunning|beautiful|amazing|high[- ]quality|professional|realistic|photorealistic|cinematic|luxury|"
                            r"premium|epic|short|long|quick|vertical|square|horizontal|\d+\s*(s|sec|second|seconds)|\d+-second)\s+", re.I)
FORMAT_NOUNS = re.compile(r"^((?:[\w-]+\s+){0,3}?)(image|photo|photograph|photography|picture|video|clip|film|reel|reels|tiktok|short|"
                          r"shorts|commercial|ad|advert|advertisement|shot|render|rendering|poster|visual|still|sequence|teaser|"
                          r"trailer|campaign|spot)\s+(of|for|showing|featuring|about|with)\s+", re.I)


def _contains(text, word):
    return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", text) is not None


# ------------------------------------------------------------------ detection
STYLE_DOMAINS = ("ugc",)      # production styles override the subject category (a UGC serum review is UGC, not a packshot)


def detect_domain(text):
    low = text.lower()
    for name in STYLE_DOMAINS:
        if any(_contains(low, k) for k in presets()[name].get("keywords", [])):
            return name
    best, score = "general", 0
    for name, p in presets().items():
        s = sum(len(k.split()) for k in p.get("keywords", []) if _contains(low, k))
        if s > score:
            best, score = name, s
    return best


def detect_platform(text):
    low = text.lower()
    al = platforms()["aliases"]
    for alias in sorted(al, key=len, reverse=True):
        if _contains(low, alias):
            return al[alias]
    return None


def detect_aspect(text):
    m = re.search(r"\b(\d{1,2}):(\d{1,2})\b", text)
    if m and f"{m.group(1)}:{m.group(2)}" in ASPECT_RATIOS:
        return f"{m.group(1)}:{m.group(2)}"
    low = text.lower()
    if _contains(low, "vertical"):
        return "9:16"
    if _contains(low, "square"):
        return "1:1"
    if any(_contains(low, w) for w in ("widescreen", "landscape format", "horizontal")):
        return "16:9"
    return None


def detect_duration(text):
    low = text.lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*(s|sec|secs|second|seconds)\b", low)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*(min|mins|minute|minutes)\b", low)
    if m:
        return float(m.group(1)) * 60
    return None


def detect_modality(text, moves=None):
    low = text.lower()
    v = sum(1 for w in VIDEO_WORDS if _contains(low, w))
    i = sum(1 for w in IMAGE_WORDS if _contains(low, w))
    dynamic = [m for m in (moves or []) if m["id"] not in ("static", "dutch_angle", "top_down")]
    if detect_duration(text):
        v += 2
    v += len(dynamic)
    return "video" if v > i else "image"


def detect_lighting(text):
    low = text.lower()
    for cue, desc, tod in LIGHTING_CUES:
        if _contains(low, cue):
            return desc, tod, cue
    return None, None, None


def clean_subject(text, moves=(), lighting_cue=None):
    """Strip request filler and the cues already captured elsewhere in the spec (format, aspect, duration, camera, light)."""
    s = text.strip().rstrip(".")
    for m in moves:
        s = re.sub(r"(,\s*|\bwith\s+(a\s+)?|\b)((slow|slowly|gentle|subtle|fast|quick|rapid|smooth|steady)\s+)?" + re.escape(m["match"]) + r"\b(\s+shot)?",
                   " ", s, flags=re.I)
    if lighting_cue:
        s = re.sub(r"(,\s*)?\b(at|during|in)?\s*" + re.escape(lighting_cue) + r"\b", " ", s, flags=re.I)
    s = FILLER.sub("", s)
    for _ in range(4):
        s2 = LEADING_FORMAT.sub("", s)
        if s2 == s:
            break
        s = s2
    s = FORMAT_NOUNS.sub("", s)
    s = re.sub(r"\b(in|at|for)\s+(\d{1,2}:\d{1,2})\b", "", s)
    s = re.sub(r"\b\d{1,2}:\d{1,2}\b", "", s)
    s = re.sub(r"\b\d+(\.\d+)?\s*-?\s*(s|sec|secs|second|seconds|min|minutes)\b(\s+long)?", "", s, flags=re.I)
    s = re.sub(r"\s+,", ",", re.sub(r"\s{2,}", " ", s))
    s = re.sub(r"(,\s*){2,}", ", ", s).strip(" ,.-")
    s = re.sub(r"\b(and|with|at|in)$", "", s).strip(" ,.-")
    return s or text.strip()


# ------------------------------------------------------------------ enhance
def enhance(text, domain=None, modality=None, overrides=None):
    """Turn a plain-language request into a fully specified ShotSpec."""
    if not text or not text.strip():
        raise ValueError("enhance() needs a non-empty request")
    overrides = dict(overrides or {})
    moves = cam.find_in_text(text)
    domain = domain or detect_domain(text)
    if domain not in presets():
        raise ValueError(f"unknown domain {domain!r}; choose from {', '.join(presets())}")
    modality = modality or detect_modality(text, moves)
    platform = detect_platform(text)
    p_spec = platforms()["platforms"].get(platform) if platform else None
    if platform and domain == "general" and p_spec and p_spec["aspect_ratio"] == "9:16":
        domain = "social"
    preset = presets()[domain]
    base = presets()["general"]["defaults"]

    technical = {}
    aspect = detect_aspect(text) or (p_spec["aspect_ratio"] if p_spec else None)
    technical["aspect_ratio"] = aspect or ("16:9" if modality == "video" or domain in ("cinematic", "architecture") else "4:5" if domain == "fashion" else "1:1" if domain == "product" else "16:9")
    if platform:
        technical["platform"] = platform
    if modality == "video":
        lo, hi = preset.get("shot_seconds", [3, 5])
        technical["duration"] = detect_duration(text) or float(max(5, hi))
        technical["motion_intensity"] = "high" if any(m["speed"] == "fast" for m in moves) or domain == "social" else "low" if domain in ("architecture", "product", "cinematic") else "medium"
    light_desc, tod, light_cue = detect_lighting(text)
    if tod:
        technical["time_of_day"] = tod

    subject = clean_subject(text, moves, light_cue)
    d = dict(base)
    d.update(preset.get("defaults", {}))
    spec = ShotSpec(
        objective=f"{'Video' if modality == 'video' else 'Image'} — {preset['label']}" + (f" for {p_spec['label']}" if p_spec else "") + f": {subject}",
        subject=subject,
        environment=d.get("environment", ""),
        composition=d["composition"],
        camera=d["camera"],
        lens=d["lens"],
        lighting=light_desc or d["lighting"],
        materials=d["materials"],
        motion=preset.get("motion_default", "") if modality == "video" else "",
        style=d["style"],
        color=d["color"],
        technical=technical,
        negative=list(dict.fromkeys(presets()["general"]["negative"] + preset.get("negative", []))),
        modality=modality,
        domain=domain,
        camera_moves=[{"id": m["id"], "speed": m["speed"]} for m in moves],
    )
    if modality == "video" and not spec.camera_moves:
        default_move = {"product": "orbit_360" if spec.technical["duration"] >= 6 else "push_in", "architecture": "dolly_in",
                        "ugc": "handheld", "social": "push_in", "fashion": "tracking", "character": "push_in",
                        "cinematic": "dolly_in", "concept_art": "aerial_reveal"}.get(domain, "push_in")
        spec.camera_moves = [{"id": default_move, "speed": "slow" if domain != "social" else "medium", "auto": True}]
    for k, v in overrides.items():
        if k == "technical":
            spec.technical.update(v)
        elif hasattr(spec, k):
            setattr(spec, k, v)
        else:
            raise ValueError(f"unknown override {k!r}")
    return spec.validate()


# ------------------------------------------------------------------ continuity bible
def apply_bible(spec, bible):
    """Inject locked descriptors so every shot of a sequence describes characters, products and look identically.

    bible = {"characters": {"maya": "..."}, "products": {...}, "locations": {...}, "palette": "...", "lens_package": "...",
             "lighting": "...", "grade": "...", "style": "...", "negative": [...]}
    Tokens like @maya in any text field are replaced by the locked description; ids in spec.characters are appended.
    """
    if not bible:
        return spec
    s = spec.copy()
    lookup = {}
    for group in ("characters", "products", "locations"):
        for k, v in (bible.get(group) or {}).items():
            lookup[k.lower()] = v
    def sub(text):
        return re.sub(r"@([A-Za-z0-9_\-]+)", lambda m: lookup.get(m.group(1).lower(), m.group(0)), text)
    for f in ("subject", "environment", "motion", "composition"):
        setattr(s, f, sub(getattr(s, f)))
    for cid in s.characters:
        desc = lookup.get(cid.lower())
        if desc and desc not in s.subject:
            s.subject = (s.subject + "; " if s.subject else "") + desc
    if bible.get("style"):
        s.style = bible["style"]
    if bible.get("grade"):
        s.color = bible["grade"] + (f", palette: {bible['palette']}" if bible.get("palette") else "")
    elif bible.get("palette"):
        s.color = f"{s.color}, palette: {bible['palette']}"
    if bible.get("lens_package") and not spec.lens:
        s.lens = bible["lens_package"]
    if bible.get("lighting") and not spec.lighting:
        s.lighting = bible["lighting"]
    neg = list(s.negative) + list(bible.get("negative") or [])
    if s.characters or "@" in spec.subject:
        neg += ["identity drift", "changing face or hairstyle", "changing wardrobe"]
    s.negative = list(dict.fromkeys(neg))
    return s.validate()


# ------------------------------------------------------------------ render
def _sentence(*parts):
    t = ", ".join(p.strip().rstrip(".") for p in parts if p and p.strip())
    return (t[0].upper() + t[1:] + ".") if t else ""


def _preserve_clause(spec):
    out = []
    for r in spec.references:
        role = r.get("role", "subject")
        keep = r.get("preserve") or []
        label = {"first_frame": "the first-frame image", "last_frame": "the last-frame image"}.get(role, f"the {role} reference")
        if keep:
            out.append(f"Keep {', '.join(keep)} exactly as in {label}")
        elif role in ("first_frame", "last_frame"):
            out.append(f"Start from {label} without altering its composition" if role == "first_frame" else f"End exactly on {label}")
        elif role == "style":
            out.append("Match the color, lighting and texture style of the style reference without copying its subject")
    return ". ".join(out) + ("." if out else "")


def render(spec, negative_mode="separate", max_chars=None):
    """Render a ShotSpec to {'prompt', 'negative_prompt', 'params', 'structured'}.

    negative_mode: 'separate' (provider has a negative-prompt field) or 'inline' (append 'Avoid: ...').
    """
    spec.validate()
    t = spec.technical
    moves_txt = " and ".join(cam.phrase(m["id"], m.get("speed", "slow"), direction=m.get("direction"), **{"from": m.get("from"), "to": m.get("to")})
                             for m in spec.camera_moves if cam.get(m["id"]))
    if spec.modality == "video":
        lead = moves_txt or spec.camera
        body = [
            _sentence(lead + ": " + spec.subject if lead else spec.subject, spec.motion),
            _sentence(spec.environment) if spec.environment else "",
            _sentence(spec.composition, spec.camera if moves_txt else "", spec.lens),
            _sentence(spec.lighting),
            _sentence(spec.materials),
            _sentence(spec.style, spec.color),
            _sentence(f"{t.get('motion_intensity', 'medium')} motion intensity",
                      "temporally consistent, no flicker, stable identity and geometry from first to last frame",
                      f"{t['duration']:g}-second shot" if t.get("duration") else ""),
        ]
    else:
        body = [
            _sentence(spec.subject, spec.environment),
            _sentence(spec.composition, spec.camera, spec.lens),
            _sentence(spec.lighting),
            _sentence(spec.materials),
            _sentence(spec.style, spec.color),
        ]
    keep = _preserve_clause(spec)
    if keep:
        body.append(keep)
    prompt = " ".join(b for b in body if b)
    negative = ", ".join(spec.negative)
    if negative_mode == "inline" and negative:
        prompt += f" Avoid: {negative}."
    if max_chars and len(prompt) > max_chars:
        prompt = prompt[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    params = {k: t[k] for k in ("aspect_ratio", "duration", "resolution", "fps", "seed") if k in t}
    if spec.references:
        params["references"] = [{"source": r["source"], "role": r.get("role", "subject")} for r in spec.references]
    return {"prompt": prompt, "negative_prompt": negative if negative_mode == "separate" else "", "params": params,
            "structured": {f: getattr(spec, f) for f in ("objective", "subject", "environment", "composition", "camera", "lens",
                                                           "lighting", "materials", "motion", "style", "color", "technical", "negative")},
            "modality": spec.modality, "domain": spec.domain, "camera_moves": [m["id"] for m in spec.camera_moves]}
