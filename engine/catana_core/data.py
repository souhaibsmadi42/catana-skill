"""Load the JSON data files that drive the engine (single source for engine, linter and docs)."""
import json
import os
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.environ.get("CATANA_DATA") or os.path.join(ROOT, "data")


@lru_cache(maxsize=None)
def load(name):
    path = os.path.join(DATA_DIR, name if name.endswith(".json") else name + ".json")
    with open(path, encoding="utf8") as f:
        return json.load(f)


def presets():
    return load("presets")["domains"]


def camera_movements():
    return load("camera_movements")["movements"]


def platforms():
    return load("platforms")


def providers():
    return load("providers")
