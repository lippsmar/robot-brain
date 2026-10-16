"""Cooling check for the cube (Bauplan Daten, Phase 3; Bauplan Körper 8a.4).

Looks at the last hour in the data lake: supply air (Zuluft) against exhaust air (Abluft),
chip and modem temperature, and the chip trend. Warns when the chip reaches 70 °C or the
Pi throttles. `CoolingWatch` writes the warning once per hot phase to the event log, where
the notifier passes it to Marvin, and adds the mood factor "temperatur_hoch". When things
are fine again, it logs that too.

The supply and exhaust sensors may differ a little even side by side; that offset is
measured before installation (Bauplan Körper 8a.4) and passed as `abgleich`.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from brain.eventlog import parse_ts
from brain.zahlen import zahl

WARN_CHIP_C = 70.0
WINDOW = timedelta(hours=1)


@dataclass(frozen=True)
class CoolingStatus:
    chip_temp: float | None
    modem_temp: float | None
    zuluft: float | None
    abluft: float | None
    differenz: float | None  # exhaust minus supply minus offset
    trend_chip: float | None  # °C per hour over the last hour
    drosselung: bool
    warnung: bool
    gruende: tuple = ()
    hinweis: str = ""


def _utc_now():
    return datetime.now(UTC)


def _latest(rows):
    return rows[-1].value if rows else None


def _slope_per_hour(rows):
    """Least-squares slope of the values over time, in units per hour."""
    if len(rows) < 2:
        return None
    hours = [parse_ts(row.ts).timestamp() / 3600 for row in rows]
    values = [row.value for row in rows]
    mean_hour = sum(hours) / len(hours)
    mean_value = sum(values) / len(values)
    spread = sum((hour - mean_hour) ** 2 for hour in hours)
    if spread == 0:
        return None
    return sum((hour - mean_hour) * (value - mean_value) for hour, value in zip(hours, values, strict=True)) / spread


def assess(lake, now, *, warn_at=WARN_CHIP_C, abgleich=0.0):
    """Cooling status from the good readings of the last hour."""
    start, end = now - WINDOW, now + timedelta(minutes=1)
    chip = lake.readings("chip_temp", start, end)
    chip_temp = _latest(chip)
    modem_temp = _latest(lake.readings("modem_temp", start, end))
    supply = _latest(lake.readings("zuluft_temp", start, end))
    exhaust = _latest(lake.readings("abluft_temp", start, end))
    throttled = _latest(lake.readings("chip_drosselung", start, end)) == 1.0
    difference = exhaust - supply - abgleich if supply is not None and exhaust is not None else None
    reasons = []
    if chip_temp is not None and chip_temp >= warn_at:
        reasons.append(f"Chip {zahl(chip_temp)} °C, Grenze {zahl(warn_at)} °C")
    if throttled:
        reasons.append("der Pi drosselt")
    known = (chip_temp, modem_temp, supply, exhaust)
    hint = "" if any(value is not None for value in known) else "keine aktuellen Messwerte"
    return CoolingStatus(
        chip_temp,
        modem_temp,
        supply,
        exhaust,
        difference,
        _slope_per_hour(chip),
        throttled,
        bool(reasons),
        tuple(reasons),
        hint,
    )


class CoolingWatch:
    """Checks the cooling and warns once per hot phase (event log and mood)."""

    def __init__(self, lake, log, *, mood=None, clock=_utc_now, warn_at=WARN_CHIP_C, abgleich=0.0):
        self._lake = lake
        self._log = log
        self._mood = mood
        self._clock = clock
        self._warn_at = warn_at
        self._abgleich = abgleich
        self._warned = False

    def check(self):
        status = assess(self._lake, self._clock(), warn_at=self._warn_at, abgleich=self._abgleich)
        if status.warnung and not self._warned:
            payload = {"gruende": list(status.gruende), "chip_temp": status.chip_temp, "drosselung": status.drosselung}
            self._log.append("safety.alert", payload, intent="cooling.warn", result="Warnung an Marvin")
            if self._mood is not None and status.chip_temp is not None:
                # 60 °C counts as normal, from 80 °C the factor is at full strength (Annahme 16.10.2026)
                strength = min(1.0, max(0.5, (status.chip_temp - 60.0) / 20.0))
                self._mood.record("temperatur_hoch", value=round(status.chip_temp, 1), strength=strength)
            self._warned = True
        elif not status.warnung and self._warned:
            self._log.append(
                "system.health", {"chip_temp": status.chip_temp}, intent="cooling.ok", result="Kühlung wieder im Rahmen"
            )
            self._warned = False
        return status
