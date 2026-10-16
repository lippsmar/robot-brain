"""Patterns in the cube's surroundings (Bauplan Daten, Phase 9).

9.1 finds, from the last four weeks in the data lake, where Marvin usually is when, how loud
and warm it is at each place, and when the battery runs low. 9.2 compares today with the
usual values of a place ("heute lauter als sonst"). 9.3: patterns about Marvin are personal
(`pii`), stay local, are shown on "Was weißt du über meinen Alltag?" and can be deleted.

Patterns are computed, not stored. Deleting one puts its key on a deny list in a small local
database, so it does not come back, until Marvin restores it. The measurements behind it stay
in the data lake; deleting those is a separate step that needs Marvin's release (Annahme
16.10.2026).

Thresholds (Annahme 16.10.2026): a pattern needs at least 3 days of data; a place counts for an
hour when the cube was there on at least half of the days; the battery is low below 20 %;
today differs from usual by at least 3 dB or 1.5 °C, with at least 3 values today. "Usual" means
the same hours on the same kind of day (weekday or weekend). All days are local days.
"""

import os
import re
import sqlite3
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from brain.datalake import UNTERWEGS
from brain.eventlog import format_ts
from brain.zahlen import zahl

MIN_TAGE = 3
ANTEIL = 0.5
AKKU_KNAPP = 20.0
FENSTER_TAGE = 28
MIN_HEUTE = 3
# channel: (unit, decimals, smallest difference worth mentioning, word for more, word for less)
VERGLEICH = {
    "lautstaerke": ("dB", 0, 3.0, "lauter", "leiser"),
    "zuluft_temp": ("°C", 1, 1.5, "wärmer", "kälter"),
}
_GRUPPEN = ("werktags", "am Wochenende")
_KEY = re.compile(r"ort:(werktags|am Wochenende):.{1,40}|umgebung:.{1,40}|akku:knapp", re.DOTALL)


class MusterError(Exception):
    """Unknown pattern key or missing note."""


@dataclass(frozen=True)
class Muster:
    key: str
    text: str
    pii: bool = True


def _utc_now():
    return datetime.now(UTC)


def _local(hour, zone):
    return datetime.fromisoformat(f"{hour}:00:00+00:00").astimezone(zone)


def _gruppe(local):
    return _GRUPPEN[0] if local.weekday() < 5 else _GRUPPEN[1]


def _stunden(lake, channel, start, end, place, zone):
    """(local hour start, mean, count) of the good values of one channel at one place."""
    return [(_local(s.hour, zone), s.mean, s.count) for s in lake.hourly(channel, start, end, place=place)]


def _mittel(hours):
    return sum(mean * count for _, mean, count in hours) / sum(count for _, _, count in hours)


def _ranges(hours):
    """Consecutive hours as (first, last) pairs."""
    result: list[list[int]] = []
    for hour in hours:
        if result and hour == result[-1][1] + 1:
            result[-1][1] = hour
        else:
            result.append([hour, hour])
    return [(first, last) for first, last in result]


def _orte(lake, start, end, zone):
    seen = defaultdict(set)  # (place, group, local hour) -> dates
    days: dict[str, set] = {group: set() for group in _GRUPPEN}
    for hour, place in lake.places_by_hour(start, end):
        local = _local(hour, zone)
        group = _gruppe(local)
        days[group].add(local.date())
        if place != UNTERWEGS:
            seen[(place, group, local.hour)].add(local.date())
    result = []
    for group in _GRUPPEN:
        total = len(days[group])
        if total < MIN_TAGE:
            continue
        for place in sorted({p for p, g, _ in seen if g == group}):
            hours = sorted(
                h for (p, g, h), dates in seen.items() if p == place and g == group and len(dates) >= ANTEIL * total
            )
            if not hours:
                continue
            dates = set().union(*(seen[(place, group, h)] for h in hours))
            spans = " und ".join(f"{first}–{last + 1}" for first, last in _ranges(hours))
            text = f"{group[0].upper()}{group[1:]} meist {spans} Uhr: {place} (an {len(dates)} von {total} Tagen)"
            result.append(Muster(f"ort:{group}:{place}", text))
    return result


def _umgebung(lake, start, end, zone):
    places = sorted({place for _, place in lake.places_by_hour(start, end)} - {UNTERWEGS})
    result = []
    for place in places:
        parts, days = [], 0
        for channel, unit, digits in (("lautstaerke", "dB", 0), ("zuluft_temp", "°C", 1)):
            hours = _stunden(lake, channel, start, end, place, zone)
            channel_days = len({local.date() for local, _, _ in hours})
            if channel_days >= MIN_TAGE:
                parts.append(f"{zahl(_mittel(hours), digits)} {unit}")
                days = max(days, channel_days)
        if parts:
            result.append(Muster(f"umgebung:{place}", f"{place}: im Schnitt {' und '.join(parts)} (an {days} Tagen)"))
    return result


def _akku(lake, start, end, zone):
    """When the battery runs low: the hour each low phase starts, so a phase over midnight counts once."""
    days: set = set()
    first_low: dict = {}
    previous_low = None
    for stats in lake.hourly("akku", start, end):
        local = _local(stats.hour, zone)
        days.add(local.date())
        if stats.minimum < AKKU_KNAPP:
            if previous_low is None or local - previous_low > timedelta(hours=1):
                first_low.setdefault(local.date(), local.hour)
            previous_low = local
    if len(first_low) < MIN_TAGE:
        return []
    hour = statistics.median_low(first_low.values())
    text = f"Akku: an {len(first_low)} von {len(days)} Tagen unter {zahl(AKKU_KNAPP)} %, meist gegen {hour} Uhr"
    return [Muster("akku:knapp", text)]


def finde_muster(lake, now, *, tage=FENSTER_TAGE, timezone="Europe/Berlin"):
    """Patterns from the last `tage` days (daily and weekly run, Bauplan Daten 9.1)."""
    zone = ZoneInfo(timezone)
    start, end = now - timedelta(days=tage), now
    return _orte(lake, start, end, zone) + _umgebung(lake, start, end, zone) + _akku(lake, start, end, zone)


def heute_vs_sonst(lake, now, ort, *, tage=FENSTER_TAGE, timezone="Europe/Berlin"):
    """How today at a place differs from the same hours on the same kind of day (Bauplan Daten 9.2)."""
    if ort == UNTERWEGS:
        return []
    zone = ZoneInfo(timezone)
    local_now = now.astimezone(zone)
    midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
    result = []
    for channel, (unit, digits, smallest, more, less) in VERGLEICH.items():
        today = _stunden(lake, channel, midnight, now, ort, zone)
        if sum(count for _, _, count in today) < MIN_HEUTE:
            continue
        hours = {local.hour for local, _, _ in today}
        usual = [
            row
            for row in _stunden(lake, channel, midnight - timedelta(days=tage), midnight, ort, zone)
            if row[0].hour in hours and _gruppe(row[0]) == _gruppe(local_now)
        ]
        if len({local.date() for local, _, _ in usual}) < MIN_TAGE:
            continue
        today_mean, usual_mean = _mittel(today), _mittel(usual)
        difference = today_mean - usual_mean
        if abs(difference) >= smallest:
            word = more if difference > 0 else less
            text = f"{ort}: heute {word} als sonst ({zahl(today_mean, digits)} statt {zahl(usual_mean, digits)} {unit})"
            result.append(Muster(f"heute:{ort}:{channel}", text))
    return result


class MusterListe:
    """Patterns minus the ones Marvin deleted; the deny list lives in its own local file."""

    def __init__(self, path, log=None, clock=_utc_now):
        self._path = Path(path)
        if not self._path.exists():
            os.close(os.open(self._path, os.O_CREAT | os.O_RDWR, 0o600))  # only Schlaubi's account
        self._log = log
        self._clock = clock
        self._conn = sqlite3.connect(self._path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS geloescht"
            " (key TEXT PRIMARY KEY, ts TEXT NOT NULL, vermerk TEXT NOT NULL) STRICT"
        )
        self._conn.commit()

    def close(self):
        self._conn.close()

    def _event(self, intent, payload):
        if self._log is not None:
            self._log.append("agent.action", payload, intent=intent, pii=True)

    def _deleted(self):
        return {row[0] for row in self._conn.execute("SELECT key FROM geloescht")}

    def aktuell(self, lake, now, **options):
        deleted = self._deleted()
        return [muster for muster in finde_muster(lake, now, **options) if muster.key not in deleted]

    @staticmethod
    def _check_key(key):
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            raise MusterError(f"Unbekanntes Muster {key!r}")

    def loeschen(self, key, *, vermerk):
        self._check_key(key)
        if not isinstance(vermerk, str) or not vermerk.strip() or len(vermerk) > 200:
            raise MusterError("Vermerk muss ein Text mit 1 bis 200 Zeichen sein")
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO geloescht (key, ts, vermerk) VALUES (?, ?, ?)",
                (key, format_ts(self._clock()), vermerk),
            )
        self._event("patterns.deleted", {"muster": key, "vermerk": vermerk})

    def zurueckholen(self, key):
        """Brings a deleted pattern back; False if it was not deleted (nothing is logged then)."""
        self._check_key(key)
        with self._conn:
            restored = self._conn.execute("DELETE FROM geloescht WHERE key = ?", (key,)).rowcount
        if restored:
            self._event("patterns.restored", {"muster": key})
        return bool(restored)

    def uebersicht(self, lake, now):
        """Answer to "Was weißt du über meinen Alltag?" (Bauplan Daten 9.3)."""
        alle = finde_muster(lake, now)
        deleted = self._deleted()
        found = [muster for muster in alle if muster.key not in deleted]
        self._event("patterns.shown", {"anzahl": len(found), "geloescht": len(alle) - len(found)})
        if not alle:
            return f"Noch keine Muster. Dafür brauche ich Daten von mindestens {MIN_TAGE} Tagen."
        if not found:
            return "Alle Muster, die ich erkannt habe, hast du gelöscht. Sag „zurückholen“, dann zeige ich sie wieder."
        lines = ["Das weiß ich über deinen Alltag (bleibt lokal):"]
        lines += [f"- {muster.text}" for muster in found]
        lines.append("Sag mir, welches Muster ich löschen soll.")
        return "\n".join(lines)
