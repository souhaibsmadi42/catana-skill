"""ShotSpec: the structured production spec behind every CATANA prompt.

The 13 fields (in prompt order of importance):
  objective, subject, environment, composition, camera, lens, lighting, materials,
  motion, style, color, technical, negative
plus modality (image | video), domain, camera_moves, references, continuity tags.
"""
from dataclasses import dataclass, field, asdict
import copy
import hashlib
import json

FIELDS = ["objective", "subject", "environment", "composition", "camera", "lens", "lighting",
          "materials", "motion", "style", "color", "technical", "negative"]
TEXT_FIELDS = [f for f in FIELDS if f not in ("technical", "negative")]
MODALITIES = ("image", "video")
REFERENCE_ROLES = ("subject", "character", "product", "style", "composition", "geometry",
                   "environment", "first_frame", "last_frame", "motion")
ASPECT_RATIOS = ("16:9", "9:16", "1:1", "4:5", "5:4", "4:3", "3:4", "3:2", "2:3", "21:9")
SPEEDS = ("slow", "medium", "fast")
INTENSITIES = ("low", "medium", "high")


class SpecError(ValueError):
    pass


@dataclass
class ShotSpec:
    objective: str = ""
    subject: str = ""
    environment: str = ""
    composition: str = ""
    camera: str = ""
    lens: str = ""
    lighting: str = ""
    materials: str = ""
    motion: str = ""
    style: str = ""
    color: str = ""
    technical: dict = field(default_factory=dict)   # aspect_ratio, duration, resolution, fps, seed, platform, motion_intensity, time_of_day
    negative: list = field(default_factory=list)
    modality: str = "image"
    domain: str = "general"
    camera_moves: list = field(default_factory=list)  # [{"id": "dolly_in", "speed": "slow", ...}]
    references: list = field(default_factory=list)    # [{"source": "...", "role": "product", "preserve": [...]}]
    id: str = ""
    characters: list = field(default_factory=list)    # bible ids used in this shot (continuity)
    notes: str = ""

    # ------------------------------------------------------------------ io
    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise SpecError("spec must be a JSON object")
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        unknown = sorted(set(d) - set(known))
        if unknown:
            raise SpecError(f"unknown spec fields: {', '.join(unknown)}")
        s = cls(**copy.deepcopy(known))
        s.validate()
        return s

    def to_dict(self):
        return asdict(self)

    def copy(self):
        return ShotSpec.from_dict(self.to_dict())

    def hash(self):
        return hashlib.sha1(json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()[:12]

    # ------------------------------------------------------------------ validation (types and enums only; quality lives in qc.py)
    def validate(self):
        for f in TEXT_FIELDS:
            if not isinstance(getattr(self, f), str):
                raise SpecError(f"{f} must be a string")
        if self.modality not in MODALITIES:
            raise SpecError(f"modality must be one of {MODALITIES}, got {self.modality!r}")
        if not isinstance(self.technical, dict):
            raise SpecError("technical must be an object")
        if isinstance(self.negative, str):
            self.negative = [n.strip() for n in self.negative.split(",") if n.strip()]
        if not isinstance(self.negative, list):
            raise SpecError("negative must be a list of strings")
        t = self.technical
        ar = t.get("aspect_ratio")
        if ar is not None and ar not in ASPECT_RATIOS:
            raise SpecError(f"technical.aspect_ratio {ar!r} not one of {ASPECT_RATIOS}")
        dur = t.get("duration")
        if dur is not None:
            if not isinstance(dur, (int, float)) or dur <= 0 or dur > 600:
                raise SpecError("technical.duration must be a number of seconds in (0, 600]")
        mi = t.get("motion_intensity")
        if mi is not None and mi not in INTENSITIES:
            raise SpecError(f"technical.motion_intensity must be one of {INTENSITIES}")
        for m in self.camera_moves:
            if not isinstance(m, dict) or "id" not in m:
                raise SpecError("camera_moves entries need an 'id'")
            if m.get("speed", "slow") not in SPEEDS:
                raise SpecError(f"camera move speed must be one of {SPEEDS}")
        for r in self.references:
            if not isinstance(r, dict) or not r.get("source"):
                raise SpecError("references entries need a 'source' (path, URL or media id)")
            if r.get("role", "subject") not in REFERENCE_ROLES:
                raise SpecError(f"reference role must be one of {REFERENCE_ROLES}")
            if not isinstance(r.get("preserve", []), list):
                raise SpecError("reference 'preserve' must be a list")
        return self

    def all_text(self):
        return " ".join([getattr(self, f) for f in TEXT_FIELDS] + [" ".join(self.negative)]).lower()

    def positive_text(self):
        return " ".join(getattr(self, f) for f in TEXT_FIELDS).lower()
