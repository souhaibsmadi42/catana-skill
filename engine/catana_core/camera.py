"""Camera movement library: lookup, text detection, prompt phrases and combination checks."""
import re
from .data import camera_movements

SPEED_WORDS = {
    "slow": ["slow", "slowly", "gentle", "gently", "subtle", "graceful", "languid", "unhurried", "calm"],
    "fast": ["fast", "quick", "quickly", "rapid", "rapidly", "aggressive", "energetic", "snappy", "dynamic"],
    "medium": ["medium", "steady", "moderate"],
}


def all_moves():
    return camera_movements()


def get(name):
    """Look up a move by id, name or alias (case-insensitive). Returns the dict or None."""
    if not name:
        return None
    key = name.strip().lower().replace("_", " ")
    for m in camera_movements():
        if key in (m["id"].replace("_", " "), m["name"].lower()) or key in m["aliases"]:
            return m
    return None


def _alias_index():
    idx = []
    for m in camera_movements():
        for a in set(m["aliases"] + [m["name"].lower(), m["id"].replace("_", " ")]):
            idx.append((a.lower(), m["id"]))
    idx.sort(key=lambda x: -len(x[0]))   # longest first so "dolly in" beats "dolly"
    return idx


def find_in_text(text):
    """Return [{'id', 'speed', 'match'}] for camera moves mentioned in free text (longest alias wins, no overlaps)."""
    low = " " + (text or "").lower() + " "
    taken = []
    found = []
    for alias, mid in _alias_index():
        for m in re.finditer(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", low):
            a, b = m.span()
            if any(a < tb and b > ta for ta, tb in taken):
                continue
            taken.append((a, b))
            window = re.split(r"[,;.:]|\bthen\b|\band\b|\bwith\b", low[max(0, a - 30):a])[-1]   # speed words of this clause only
            speed = None
            for sp, words in SPEED_WORDS.items():
                if any(re.search(r"\b" + w + r"\b", window) for w in words):
                    speed = sp
            if mid not in [f["id"] for f in found]:
                found.append({"id": mid, "speed": speed or "slow", "match": alias, "pos": a})
    found.sort(key=lambda f: f["pos"])
    for f in found:
        f.pop("pos")
    return found


def phrase(move, speed="slow", **kw):
    """Canonical prompt phrase for a move, with {speed}/{direction}/{from}/{to} filled."""
    m = get(move) if isinstance(move, str) else move
    if not m:
        raise KeyError(f"unknown camera movement: {move}")
    vals = {"speed": speed or "slow", "direction": kw.get("direction") or "up",
            "from": kw.get("from") or "nearest element", "to": kw.get("to") or "main subject"}
    out = m["prompt_phrase"]
    for k, v in vals.items():
        out = out.replace("{" + k + "}", v)
    return out[0].upper() + out[1:]


def check_combo(ids, duration=None):
    """Validate a set of simultaneous moves. Returns a list of issue dicts (severity, message, fix)."""
    issues = []
    moves = []
    for i in ids:
        m = get(i)
        if not m:
            issues.append({"severity": "error", "message": f"unknown camera movement '{i}'",
                           "fix": "use an id from the camera library (scripts/catana.py camera list)"})
        else:
            moves.append(m)
    seen = set()
    for a in moves:
        for b in moves:
            if a["id"] < b["id"] and (b["id"] in a["conflicts"] or a["id"] in b["conflicts"]):
                key = (a["id"], b["id"])
                if key not in seen:
                    seen.add(key)
                    issues.append({"severity": "error", "message": f"'{a['name']}' conflicts with '{b['name']}'",
                                   "fix": f"keep one of them; good partners for {a['name']}: {', '.join(a['combos']) or 'none'}"})
    real = [m for m in moves if m["id"] not in ("rack_focus", "dutch_angle")]
    if len(real) > 2:
        issues.append({"severity": "warning", "message": f"{len(real)} simultaneous camera moves — video models follow one or two reliably",
                       "fix": "keep the primary move plus at most one secondary (e.g. dolly in + tilt up), or split into shots"})
    if duration:
        for m in moves:
            if duration < m["min_seconds"]:
                issues.append({"severity": "warning", "message": f"'{m['name']}' needs about {m['min_seconds']} s to read; clip is {duration:g} s",
                               "fix": f"lengthen the clip to {m['min_seconds']} s or choose a shorter move"})
    return issues
