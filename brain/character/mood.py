"""Mood calculator (Bauplan Charakter, Phase 4).

The mood has three axes from -1 to +1: Stimmung, Energie and Gereiztheit. It starts at the
baseline from the profile. Every recorded factor (an event such as "smalltalk" or a state
such as "akku_niedrig") pushes the axes in its direction with its weight and strength and
fades linearly to nothing over its fading time. Events add up; for a state only the latest
report counts. The result is clamped to the scale.

The mood is deterministic: the same events at the same times give the same mood, there is
no randomness. Its reason names the two or three strongest factors as a sentence, e.g.
"schon die dritte Smalltalk-Frage heute und Akku bei 12 %". Every recorded factor goes to
the event log with the resulting mood and reason, and `from_log` rebuilds the mood from
there after a restart. In serious situations the mood for the answer is set to neutral.
"""

import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from brain.eventlog import parse_ts

AXES = ("stimmung", "energie", "gereiztheit")
NEUTRAL_REASON = "nichts Besonderes"
DAMPED_REASON = "ernstes Thema, Laune für die Antwort neutral"
MIN_SHARE = 0.05  # weaker factors are left out of the reason
MAX_REASONS = 3
_ORDINALS = {
    1: "erste",
    2: "zweite",
    3: "dritte",
    4: "vierte",
    5: "fünfte",
    6: "sechste",
    7: "siebte",
    8: "achte",
    9: "neunte",
    10: "zehnte",
    11: "elfte",
    12: "zwölfte",
}
_PLACEHOLDER = re.compile(r"\{(wert|anzahl|ordinal)\}")


class MoodError(ValueError):
    """A factor that the profile does not know, or a strength or value out of bounds."""


@dataclass(frozen=True)
class Mood:
    stimmung: float
    energie: float
    gereiztheit: float
    reason: str
    factors: tuple = ()  # (factor, share) for the factors named in the reason
    damped: bool = False

    def axes(self):
        return {axis: getattr(self, axis) for axis in AXES}


@dataclass(frozen=True)
class _Entry:
    factor: str
    at: datetime
    strength: float
    value: object


def german_ordinal(number):
    return _ORDINALS.get(number, f"{number}.")


def _utc_now():
    return datetime.now(UTC)


def _clamp(value):
    return max(-1.0, min(1.0, value))


def _format_value(value):
    if isinstance(value, float):
        return f"{value:g}".replace(".", ",")
    return str(value)


def _join(parts):
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " und " + parts[-1]


def _check_strength(strength):
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not 0 <= strength <= 1:
        raise MoodError("Stärke muss eine Zahl zwischen 0 und 1 sein")


def _check_value(value):
    if value is None:
        return
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return
    if isinstance(value, str) and len(value) <= 40:
        return
    raise MoodError("Wert muss eine Zahl oder ein kurzer Text sein")


class MoodEngine:
    def __init__(self, profile, log=None, clock=_utc_now, timezone="Europe/Berlin"):
        settings = profile["laune"]
        self._factors = settings["faktoren"]
        self._baseline = {axis: float(settings["grundlinie"][axis]) for axis in AXES}
        self._serious = tuple(term.lower() for term in settings["ernste_themen"])
        self._log = log
        self._zone = ZoneInfo(timezone)
        self.clock = clock
        self._entries = []
        self._counts = {}  # (factor, local date) -> how often it was recorded that day

    @classmethod
    def from_log(cls, profile, log, *, clock=_utc_now, timezone="Europe/Berlin"):
        """Rebuild the mood from the `character.mood` events of the event log."""
        engine = cls(profile, log=log, clock=clock, timezone=timezone)
        now = clock()
        longest = max(spec["abklingzeit_min"] for spec in engine._factors.values())
        local_midnight = now.astimezone(engine._zone).replace(hour=0, minute=0, second=0, microsecond=0)
        start = min(now - timedelta(minutes=longest), local_midnight.astimezone(UTC))
        for event in log.iter_events(types=["character.mood"], start=start):
            payload = event.get("payload", {})
            try:
                engine._add(payload.get("faktor"), parse_ts(event["ts"]), payload.get("wert"), payload.get("staerke"))
            except (MoodError, TypeError, ValueError):
                continue  # a factor that was removed from the profile, or a damaged entry
        return engine

    def record(self, factor, *, value=None, strength=1.0):
        """Record an event or a new state and log the resulting mood with its reason."""
        self._add(factor, self.clock(), value, strength)
        mood = self.current()
        if self._log is not None:
            payload = {
                "faktor": factor,
                "staerke": strength,
                "laune": {axis: round(level, 4) for axis, level in mood.axes().items()},
                "grund": mood.reason,
            }
            if value is not None:
                payload["wert"] = value
            self._log.append("character.mood", payload, intent="mood.record")
        return mood

    def _add(self, factor, at, value, strength):
        spec = self._factors.get(factor)
        if spec is None:
            raise MoodError(f"Laune-Faktor {factor!r} unbekannt")
        _check_strength(strength)
        _check_value(value)
        if spec["art"] == "zustand":
            self._entries = [entry for entry in self._entries if entry.factor != factor]
        self._entries.append(_Entry(factor, at, float(strength), value))
        day = at.astimezone(self._zone).date()
        self._counts[(factor, day)] = self._counts.get((factor, day), 0) + 1
        self._forget_before(at)

    def _forget_before(self, now):
        self._entries = [
            entry
            for entry in self._entries
            if now - entry.at < timedelta(minutes=self._factors[entry.factor]["abklingzeit_min"])
        ]
        yesterday = now.astimezone(self._zone).date() - timedelta(days=1)
        self._counts = {key: count for key, count in self._counts.items() if key[1] >= yesterday}

    def current(self):
        now = self.clock()
        totals = dict(self._baseline)
        shares: dict[str, float] = {}
        for entry in self._entries:
            spec = self._factors[entry.factor]
            age_min = max(0.0, (now - entry.at).total_seconds() / 60)
            remaining = 1.0 - age_min / spec["abklingzeit_min"]
            if remaining <= 0:
                continue
            for axis, direction in spec["richtung"].items():
                push = spec["gewicht"] * direction * entry.strength * remaining
                totals[axis] += push
                shares[entry.factor] = shares.get(entry.factor, 0.0) + abs(push)
        ranked = sorted(
            ((share, name) for name, share in shares.items() if share >= MIN_SHARE),
            key=lambda item: (-item[0], item[1]),
        )[:MAX_REASONS]
        reason = _join([self._describe(name, now) for _, name in ranked]) or NEUTRAL_REASON
        levels = {axis: _clamp(round(level, 6)) for axis, level in totals.items()}
        return Mood(**levels, reason=reason, factors=tuple((name, round(share, 6)) for share, name in ranked))

    def _describe(self, name, now):
        latest = next((entry for entry in reversed(self._entries) if entry.factor == name), None)
        count = self._counts.get((name, now.astimezone(self._zone).date()), 0)
        values = {
            "wert": _format_value(latest.value) if latest is not None and latest.value is not None else "?",
            "anzahl": str(count),
            "ordinal": german_ordinal(count),
        }
        return _PLACEHOLDER.sub(lambda match: values[match.group(1)], self._factors[name]["grund"])

    def for_answer(self, text="", *, serious=False):
        """The mood to answer with: neutral when the topic is serious (Bauplan 4.4)."""
        lowered = text.lower()
        if serious or any(term in lowered for term in self._serious):
            return Mood(0.0, 0.0, 0.0, DAMPED_REASON, (), damped=True)
        return self.current()
