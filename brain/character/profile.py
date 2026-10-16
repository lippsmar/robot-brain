"""Schlaubi's character profile (Bauplan Charakter, Phase 2).

The profile holds layers 2 to 4 of the character (personality, mood model, development) as
YAML. It is checked against `profil.schema.json` and a few rules the schema cannot express:

- every slider value lies inside its own allowed range,
- movable sliders exist,
- nothing in the profile touches the fixed core (`kern.md`): no key or text may contain
  core terms such as "Rangfolge", "Freigabe" or "robots.txt".

Loading goes through `safe_yaml.load_yaml`: SafeLoader only, no duplicate keys, no aliases.
"""

import re
from functools import cache
from pathlib import Path

from brain.character.safe_yaml import YamlError, load_yaml
from brain.schema import load_schema, validate

PROFILE_FILE = Path(__file__).with_name("profil.yaml")
SCHEMA_FILE = Path(__file__).with_name("profil.schema.json")
MAX_BYTES = 64 * 1024
# Words that belong to the fixed core. A profile entry containing one of them is refused,
# because the core can only be changed in kern.md, never through the profile. Whole words only,
# so "Ausflüge" or "Linux-Kernel" are fine.
CORE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bkern\b",
        r"\brangfolge\b",
        r"\blüg\w*",
        r"\blueg\w*",
        r"\btäusch\w*",
        r"\btaeusch\w*",
        r"\bfreigabe\w*",
        r"\brobots\.txt\b",
        r"\bdatenschutz\w*",
        r"\bnotruf\w*",
        r"\b112\b",
        r"\bmarvins\s+namen\b",
    )
)
# Lists of topic words, not rules: they may name such words.
_NOT_SCANNED = {"$.laune.ernste_themen"}


class ProfileError(Exception):
    """The profile is unreadable or breaks the schema, a range or the core."""


@cache
def _schema():
    return load_schema(SCHEMA_FILE)


def _core_conflicts(value, where="$"):
    if where in _NOT_SCANNED:
        return []
    problems = []
    if isinstance(value, dict):
        for key, item in value.items():
            problems.extend(_core_conflicts(str(key).replace("_", " "), f"{where}.<{key}>"))
            problems.extend(_core_conflicts(item, f"{where}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            problems.extend(_core_conflicts(item, f"{where}[{index}]"))
    elif isinstance(value, str):
        for pattern in CORE_PATTERNS:
            match = pattern.search(value)
            if match:
                problems.append(f"{where}: betrifft den Kern („{match.group(0)}“), Änderungen am Kern nur in kern.md")
    return problems


def _range_problems(profile):
    problems = []
    sliders = profile.get("regler")
    if isinstance(sliders, dict):
        for name, slider in sliders.items():
            if not isinstance(slider, dict) or not all(isinstance(slider.get(k), int) for k in ("wert", "min", "max")):
                continue  # the schema reports the shape
            if slider["min"] > slider["max"]:
                problems.append(f"$.regler.{name}: min größer als max")
            elif not slider["min"] <= slider["wert"] <= slider["max"]:
                problems.append(f"$.regler.{name}: Wert {slider['wert']} außerhalb des erlaubten Bereichs")
    development = profile.get("entwicklung")
    movable = development.get("bewegliche_regler") if isinstance(development, dict) else None
    if isinstance(movable, list) and isinstance(sliders, dict):
        for name in movable:
            if isinstance(name, str) and name not in sliders:
                problems.append(f"$.entwicklung.bewegliche_regler: Regler {name!r} unbekannt")
    language = profile.get("sprache")
    length = language.get("antwortlaenge_saetze") if isinstance(language, dict) else None
    if (
        isinstance(length, dict)
        and isinstance(length.get("min"), int)
        and isinstance(length.get("max"), int)
        and length["min"] > length["max"]
    ):
        problems.append("$.sprache.antwortlaenge_saetze: min größer als max")
    return problems


def check_profile(profile):
    """Return a list of problems; an empty list means the profile may be used."""
    problems = validate(profile, _schema())
    if isinstance(profile, dict):
        problems += _range_problems(profile)
    problems += _core_conflicts(profile)
    return problems


def parse_profile(text):
    """Parse and check profile text; raise ProfileError with all problems."""
    try:
        profile = load_yaml(text, max_bytes=MAX_BYTES)
    except YamlError as error:
        raise ProfileError(f"Profil: {error}") from error
    if not isinstance(profile, dict):
        raise ProfileError("Profil muss eine Zuordnung von Schlüsseln zu Werten sein")
    problems = check_profile(profile)
    if problems:
        raise ProfileError("; ".join(problems))
    return profile


def load_profile(path=PROFILE_FILE):
    return parse_profile(Path(path).read_text(encoding="utf-8"))
