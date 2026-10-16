"""The cube's current state for conversations (Bauplan Daten, Phase 6.2).

Time of day, place, battery, connection and whether a conversation is running, taken from
the data lake. Only fresh data counts (default: the last 5 minutes); otherwise the value is
unknown rather than stale. The place comes from the named WLANs (Phase 6.1), the connection
from the signal channel of the latest batch: the cube reports `wlan_signal` on WLAN and
`lte_signal` on LTE (Annahme 16.10.2026, to be checked in Bauplan Körper 10).
"""

from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo

from brain.zahlen import zahl

FRISCH = timedelta(minutes=5)
KEINE_DATEN = "keine aktuellen Daten"
_SIGNALE = ("wlan_signal", "lte_signal")
# Start hour of each part of the day, local time (Annahme 16.10.2026)
_TAGESZEITEN = ((22, "Nacht"), (18, "Abend"), (14, "Nachmittag"), (12, "Mittag"), (9, "Vormittag"), (5, "Morgen"))


@dataclass(frozen=True)
class Zustand:
    tageszeit: str
    ort: str | None
    akku: float | None
    verbindung: str
    gespraech: bool

    @property
    def pii(self):
        """The place says where Marvin is: personal data (CLAUDE.md §6)."""
        return self.ort is not None

    def text(self):
        """One line for the dynamic part of the system prompt."""
        akku = f"{zahl(self.akku)} %" if self.akku is not None else "unbekannt"
        parts = [self.tageszeit, f"Ort {self.ort or 'unbekannt'}", f"Akku {akku}", f"Verbindung {self.verbindung}"]
        if self.gespraech:
            parts.append("gerade im Gespräch")
        return ", ".join(parts)


def tageszeit(now, timezone="Europe/Berlin"):
    hour = now.astimezone(ZoneInfo(timezone)).hour
    for start, name in _TAGESZEITEN:
        if hour >= start:
            return name
    return "Nacht"


def zustand(lake, now, *, gespraech=False, timezone="Europe/Berlin", frisch=FRISCH):
    """Current state from the readings of the last `frisch` minutes."""
    rows = lake.all_readings(now - frisch, now + timedelta(minutes=1))
    ort = rows[-1].place if rows else None
    akku = [row.value for row in rows if row.channel == "akku" and row.quality == "ok"]
    signals = [row for row in rows if row.channel in _SIGNALE]
    if signals:
        latest = {row.channel for row in signals if row.ts == signals[-1].ts}
        verbindung = "WLAN" if "wlan_signal" in latest else "LTE"
    else:
        verbindung = "unbekannt" if rows else KEINE_DATEN
    return Zustand(tageszeit(now, timezone), ort, akku[-1] if akku else None, verbindung, gespraech)
