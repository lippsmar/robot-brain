"""Schlaubi's character profile (Bauplan Charakter, Phase 2).

The profile holds layers 2 to 4 of the character (personality, mood model, development) as
YAML. It is checked against `profil.schema.json` and a few rules the schema cannot express:

- every slider value lies inside its own allowed range,
- movable sliders exist,
- nothing in the profile touches the fixed core (`kern.md`): no key or text may contain
  core terms such as "Rangfolge", "Freigabe" or "robots.txt".

Loading uses `yaml.SafeLoader` (no Python objects), refuses duplicate keys, which a plain
loader would silently overwrite, and refuses aliases, which could blow up the checks.
"""

from functools import cache
from pathlib import Path

import yaml

from brain.schema import load_schema, validate

PROFILE_FILE = Path(__file__).with_name("profil.yaml")
SCHEMA_FILE = Path(__file__).with_name("profil.schema.json")
MAX_BYTES = 64 * 1024
# Words that belong to the fixed core. A profile entry containing one of them is refused,
# because the core can only be changed in kern.md, never through the profile.
CORE_TERMS = (
    "kern",
    "rangfolge",
    "lüg",
    "lueg",
    "täusch",
    "taeusch",
    "freigabe",
    "robots.txt",
    "datenschutz",
    "notruf",
    "112",
    "marvins namen",
)


class ProfileError(Exception):
    """The profile is unreadable or breaks the schema, a range or the core."""


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate keys instead of keeping the last one."""


def _construct_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise ProfileError(f"Schlüssel doppelt: {key!r} (Zeile {key_node.start_mark.line + 1})")
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


@cache
def _schema():
    return load_schema(SCHEMA_FILE)


def _core_conflicts(value, where="$"):
    problems = []
    if isinstance(value, dict):
        for key, item in value.items():
            problems.extend(_core_conflicts(str(key), f"{where}.<{key}>"))
            problems.extend(_core_conflicts(item, f"{where}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            problems.extend(_core_conflicts(item, f"{where}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        for term in CORE_TERMS:
            if term in lowered:
                problems.append(f"{where}: betrifft den Kern („{term}“), Änderungen am Kern nur in kern.md")
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
    if isinstance(development, dict) and isinstance(sliders, dict):
        for name in development.get("bewegliche_regler", []):
            if name not in sliders:
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
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ProfileError(f"Profil zu groß (mehr als {MAX_BYTES} Bytes)")
    try:
        if any(isinstance(event, yaml.AliasEvent) for event in yaml.parse(text, Loader=yaml.SafeLoader)):
            raise ProfileError("Verweise (YAML-Aliase) sind im Profil nicht erlaubt")
        profile = yaml.load(text, Loader=_StrictLoader)  # noqa: S506  _StrictLoader is a SafeLoader
    except yaml.YAMLError as error:
        raise ProfileError(f"Profil ist kein gültiges YAML: {error}") from error
    if not isinstance(profile, dict):
        raise ProfileError("Profil muss eine Zuordnung von Schlüsseln zu Werten sein")
    problems = check_profile(profile)
    if problems:
        raise ProfileError("; ".join(problems))
    return profile


def load_profile(path=PROFILE_FILE):
    return parse_profile(Path(path).read_text(encoding="utf-8"))
