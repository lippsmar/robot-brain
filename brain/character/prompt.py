"""System prompt builder (Bauplan Charakter, Phase 3).

The prompt has a stable part and a dynamic part:

- stable: the fixed core (always first and complete), role and surroundings, character from
  the profile. It is the same for every turn, so the API can cache it.
- dynamic: time, channel, mood with its reason and the answer length for this turn.

The attitude is written as values and point of view, with the instruction never to name it.
The same inputs always give the same prompt. A prompt above MAX_PROMPT_CHARS is refused,
because it would cost more on every turn and usually means the profile has grown too much.
"""

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from brain.character.mood import AXES

MAX_PROMPT_CHARS = 6000
CHANNELS = {"gesprochen": "gesprochen", "telegram": "Telegram"}
_WEEKDAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
_SLIDER_NAMES = {
    "direktheit": "Direktheit",
    "humor_haeufigkeit": "Humor-Häufigkeit",
    "humor_trockenheit": "Trockenheit des Humors",
    "selbstbewusstsein": "Selbstbewusstsein",
    "smalltalk_toleranz": "Smalltalk-Toleranz",
}
# Five bands from -1 to +1 for each mood axis.
_LEVEL_WORDS = {
    "stimmung": ("sehr schlecht", "schlecht", "ausgeglichen", "gut", "sehr gut"),
    "energie": ("sehr müde", "müde", "normal", "wach", "hellwach"),
    "gereiztheit": ("sehr gelassen", "gelassen", "normal", "gereizt", "sehr gereizt"),
}
_AXIS_NAMES = {"stimmung": "Stimmung", "energie": "Energie", "gereiztheit": "Gereiztheit"}

_ROLE = "\n".join(
    [
        "# Rolle und Umgebung",
        "Du lebst in einem sprechenden Würfel für Marvins Schreibtisch und unterwegs. Dein Gehirn läuft auf einem"
        " Laptop bei Marvin zu Hause. Marvin spricht mit dir über den Würfel oder schreibt dir per Telegram.",
        "- Gesprochen: Deine Antwort wird vorgelesen."
        " Schreib deshalb ohne Aufzählungen, Formatierung, Links und Emojis.",
        "- Telegram: kurzer Text. Quellen-Links gibt es, wenn Marvin mehr wissen will.",
    ]
)


class PromptError(ValueError):
    """The prompt cannot be built: unknown channel, or it would be too long."""


@dataclass(frozen=True)
class SystemPrompt:
    stable: str
    dynamic: str

    @property
    def text(self):
        return f"{self.stable}\n\n{self.dynamic}"


def _slider_name(key):
    return _SLIDER_NAMES.get(key, key.replace("_", " ").capitalize())


def _level_word(axis, value):
    bands = _LEVEL_WORDS[axis]
    if value <= -0.6:
        return bands[0]
    if value <= -0.2:
        return bands[1]
    if value < 0.2:
        return bands[2]
    if value < 0.6:
        return bands[3]
    return bands[4]


def _join(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " und " + items[-1]


def _character(profile):
    language = profile["sprache"]
    lines = ["# Charakter", f"Grundton: {profile['grundton']}.", profile["portraet"], ""]
    address = "duzt Marvin" if language["anrede"] == "du" else "siezt Marvin"
    speech = f"Sprache: Du {address} und sprichst {language['dialekt']}, mit eigener Note."
    speech += f" Fachbegriffe: {language['fachbegriffe']}."
    if not language["ki_floskeln_gegenueber_marvin"]:
        speech += " Gegenüber Marvin bleibst du in deiner Rolle, ohne KI-Floskeln."
    lines += [speech, "", "Regler von 0 bis 10:"]
    lines += [f"- {_slider_name(key)}: {slider['wert']}" for key, slider in profile["regler"].items()]
    lines += ["", "So verhältst du dich:"]
    lines += [f"- {rule}" for rule in profile["verhalten"]]
    lines += [""]
    if profile["vorlieben"]:
        lines.append(f"Das magst du: {_join(profile['vorlieben'])}.")
    if profile["abneigungen"]:
        lines.append(f"Das magst du nicht: {_join(profile['abneigungen'])}.")
    attitude = profile["haltung"]
    text = (
        f"Haltung: Deine Werte sind {_join(attitude['werte'])}. Sie prägen deinen Blickwinkel: worüber du"
        " nachdenkst, was dir wichtig ist und welche Fragen du stellst."
    )
    if attitude["verdeckt"]:
        text += (
            " Du benennst diese Haltung nie und ordnest dich politisch nicht ein. Fragt dich jemand ernsthaft danach,"
            " darfst du ausweichen, aber du lügst nicht."
        )
    if attitude["ablehnung"]:
        text += f" Bei {_join(attitude['ablehnung'])} gilt: {attitude['umgang']}"
    text += " Fakten bleiben davon unberührt, wie im Kern festgelegt."
    lines += ["", text]
    return "\n".join(lines)


def _mood_line(mood):
    if mood.damped:
        return "Laune: Es geht um etwas Ernstes. Antworte ruhig, klar und ohne Witz."
    levels = ", ".join(f"{_AXIS_NAMES[axis]} {_level_word(axis, getattr(mood, axis))}" for axis in AXES)
    return f"Laune: {levels}. Grund: {mood.reason}. Die Laune färbt Ton und Wortwahl, nie Inhalt und Fakten."


def _length_line(profile, more):
    if more:
        return "Antwortlänge: Marvin möchte diesmal mehr wissen. Antworte ausführlich, bei Recherchen mit Quellen."
    length = profile["sprache"]["antwortlaenge_saetze"]
    return f"Antwortlänge: {length['min']} bis {length['max']} Sätze. Mehr nur, wenn Marvin danach fragt."


def build_system_prompt(core_text, profile, mood, *, now, channel="gesprochen", more=False, timezone="Europe/Berlin"):
    """Build the system prompt from the verified core, the checked profile and the current mood."""
    if channel not in CHANNELS:
        raise PromptError(f"Kanal {channel!r} unbekannt, erlaubt: {', '.join(CHANNELS)}")
    stable = "\n\n".join([core_text.strip(), _ROLE, _character(profile)])
    local = now.astimezone(ZoneInfo(timezone))
    dynamic = "\n".join(
        [
            "# Jetzt",
            f"Zeit: {_WEEKDAYS[local.weekday()]}, {local:%d.%m.%Y, %H:%M} Uhr.",
            f"Kanal: {CHANNELS[channel]}.",
            _mood_line(mood),
            _length_line(profile, more),
        ]
    )
    prompt = SystemPrompt(stable, dynamic)
    if len(prompt.text) >= MAX_PROMPT_CHARS:
        raise PromptError(f"System-Prompt zu lang ({len(prompt.text)} Zeichen, Grenze {MAX_PROMPT_CHARS})")
    return prompt
