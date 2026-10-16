"""The "Sofort" tier: everything Schlaubi needs right now, kept in memory (Bauplan Lakehouse 1.4).

Marvin, 16.10.2026: day parameters, running projects and the reaction to speech must be fast.
A bundle of parts is built once (at start and in the morning) and then refreshed part by part
when something changes, so reading it costs no database work at all (goal: under 10 ms).

Every source is a function `now -> (value, pii)`. A failing source leaves its part with an error
note and does not stop the others. `standard_quellen` wires the parts that exist today: state,
today's values, today vs. usual, cooling, active knowledge packs, the "merken" list and, when a
budget guard is given, the budget. Recent conversations join when they are stored (Bauplan
Gehirn 10.5).
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from brain.context import zustand
from brain.cooling import assess
from brain.datalake import CHANNELS, UNTERWEGS
from brain.eventlog import format_ts
from brain.patterns import heute_vs_sonst


class SofortError(Exception):
    """Unknown part."""


@dataclass(frozen=True)
class Teil:
    name: str
    wert: Any
    pii: bool
    stand: str
    fehler: str | None = None


@dataclass(frozen=True)
class Tageswert:
    kanal: str
    einheit: str
    letzter: float
    minimum: float
    maximum: float
    anzahl: int


def _utc_now():
    return datetime.now(UTC)


def heutige_werte(lake, now, *, timezone="Europe/Berlin"):
    """Last, lowest and highest good value of each channel since local midnight, and whether any is pii."""
    zone = ZoneInfo(timezone)
    local = now.astimezone(zone)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
    end = now + timedelta(minutes=1)
    werte, pii = {}, False
    for kanal, (einheit, _low, _high) in CHANNELS.items():
        readings = [r for r in lake.readings(kanal, start, end) if r.value is not None]
        if not readings:
            continue
        values = [r.value for r in readings]
        werte[kanal] = Tageswert(kanal, einheit, values[-1], min(values), max(values), len(values))
        pii = pii or any(r.pii for r in readings)
    return werte, pii


class Sofort:
    def __init__(self, quellen, clock=_utc_now):
        self._quellen = dict(quellen)
        self._clock = clock
        self._teile: dict[str, Teil] = {}

    def _hole(self, name):
        now = self._clock()
        try:
            wert, pii = self._quellen[name](now)
            teil = Teil(name, wert, bool(pii), format_ts(now))
        except Exception as error:  # one broken source must not empty the whole bundle
            teil = Teil(name, None, False, format_ts(now), f"{type(error).__name__}: {error}")
        self._teile[name] = teil

    def aufbauen(self):
        """Build every part (at start and in the morning)."""
        for name in self._quellen:
            self._hole(name)

    def nachfuehren(self, *namen):
        """Refresh only the named parts, e.g. after new readings or a used pack."""
        unknown = [name for name in namen if name not in self._quellen]
        if unknown:
            raise SofortError(f"unbekannte Teile: {', '.join(unknown)}")
        for name in namen:
            self._hole(name)

    def teil(self, name):
        return self._teile[name]

    def buendel(self):
        """All parts as they were last built; a copy, so callers cannot change the tier."""
        return dict(self._teile)


def standard_quellen(*, lake, wissen, memory=None, budget=None, gespraech=lambda: False, timezone="Europe/Berlin"):
    """Sources for the parts that exist today (Design Lakehouse 5)."""

    def lage(now):
        z = zustand(lake, now, gespraech=gespraech(), timezone=timezone)
        return z, z.pii

    def heute(now):
        return heutige_werte(lake, now, timezone=timezone)

    def anders(now):
        ort = zustand(lake, now, timezone=timezone).ort or UNTERWEGS
        muster = heute_vs_sonst(lake, now, ort, timezone=timezone)
        return muster, any(m.pii for m in muster)

    def kuehlung(now):
        return assess(lake, now), False

    def pakete(now):
        aktiv = wissen.aktive()
        return aktiv, any(p.pii for p in aktiv)

    quellen = {
        "zustand": lage,
        "heute": heute,
        "anders_als_sonst": anders,
        "kuehlung": kuehlung,
        "aktive_pakete": pakete,
    }
    if memory is not None:

        def merkliste(now):
            hits = memory.merkliste()
            return hits, any(hit.pii for hit in hits)

        quellen["merkliste"] = merkliste
    if budget is not None:
        quellen["budget"] = lambda now: (budget.status(), False)
    return quellen
