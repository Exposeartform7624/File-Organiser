"""
rules.py - custom rule engine.

Rules live in rules.json as an ordered list. The first rule whose
conditions all match wins; its `destination` (relative to the output base
folder) is where the file gets moved. If nothing matches, the file goes to
the "Unsorted" folder.
"""
import json
import time
from pathlib import Path

RULES_PATH = Path(__file__).parent / "rules.json"

DEFAULT_RULES = [
    {
        "name": "Images",
        "extensions": ["jpg", "jpeg", "png", "gif", "webp", "heic", "bmp"],
        "name_contains": None,
        "min_size_kb": None,
        "max_size_kb": None,
        "older_than_days": None,
        "destination": "Images"
    },
    {
        "name": "Videos",
        "extensions": ["mp4", "mov", "avi", "mkv", "webm"],
        "name_contains": None,
        "min_size_kb": None,
        "max_size_kb": None,
        "older_than_days": None,
        "destination": "Videos"
    },
    {
        "name": "Documents",
        "extensions": ["pdf", "doc", "docx", "txt", "md", "xlsx", "pptx"],
        "name_contains": None,
        "min_size_kb": None,
        "max_size_kb": None,
        "older_than_days": None,
        "destination": "Documents"
    }
]


def load_rules():
    if not RULES_PATH.exists():
        save_rules(DEFAULT_RULES)
        return DEFAULT_RULES
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_rules(rules):
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)


def _matches(rule: dict, file_path: Path) -> bool:
    try:
        stat = file_path.stat()
    except FileNotFoundError:
        return False

    ext = file_path.suffix.lower().lstrip(".")
    exts = rule.get("extensions")
    if exts:
        if ext not in [e.lower().lstrip(".") for e in exts]:
            return False

    name_contains = rule.get("name_contains")
    if name_contains:
        if name_contains.lower() not in file_path.name.lower():
            return False

    size_kb = stat.st_size / 1024
    min_size = rule.get("min_size_kb")
    if min_size is not None and size_kb < min_size:
        return False
    max_size = rule.get("max_size_kb")
    if max_size is not None and size_kb > max_size:
        return False

    older_than_days = rule.get("older_than_days")
    if older_than_days is not None:
        age_days = (time.time() - stat.st_mtime) / 86400
        if age_days < older_than_days:
            return False

    return True


def classify(file_path: Path, rules: list) -> tuple[str, str]:
    """Returns (rule_name_or_None, destination_subfolder)."""
    for rule in rules:
        if _matches(rule, file_path):
            return rule["name"], rule["destination"]
    return None, "Unsorted"
