"""Tests for the cooling check (Bauplan Daten, Phase 3; Bauplan Körper 8a.4)."""

from datetime import UTC, datetime, timedelta

import pytest

from brain.character.mood import MoodEngine
from brain.character.profile import load_profile
from brain.cooling import WARN_CHIP_C, CoolingWatch, assess
from brain.datalake import DataLake

NOW = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)


@pytest.fixture
def lake(tmp_path, clock):
    lake = DataLake(tmp_path / "lake.db", clock=clock)
    yield lake
    lake.close()


def feed(lake, minutes_ago, seq, **values):
    lake.ingest("wuerfel-1", seq, NOW - timedelta(minutes=minutes_ago), values)


def test_normal_operation_gives_no_warning(lake):
    feed(lake, 1, 1, chip_temp=55.0, modem_temp=48.0, zuluft_temp=22.0, abluft_temp=25.5, chip_drosselung=0)

    status = assess(lake, NOW)

    assert not status.warnung
    assert (status.chip_temp, status.modem_temp) == (55.0, 48.0)
    assert status.differenz == pytest.approx(3.5)
    assert status.gruende == ()


def test_the_sensor_offset_from_the_side_by_side_check_is_applied(lake):
    feed(lake, 1, 1, zuluft_temp=22.0, abluft_temp=25.5)

    assert assess(lake, NOW, abgleich=0.3).differenz == pytest.approx(3.2)


def test_a_hot_chip_gives_a_warning(lake):
    feed(lake, 1, 1, chip_temp=WARN_CHIP_C + 0.5)

    status = assess(lake, NOW)

    assert status.warnung
    assert any("70" in reason for reason in status.gruende)


def test_a_lowered_limit_triggers_the_warning(lake):
    feed(lake, 1, 1, chip_temp=55.0)

    assert assess(lake, NOW, warn_at=50.0).warnung


def test_throttling_gives_a_warning(lake):
    feed(lake, 1, 1, chip_temp=60.0, chip_drosselung=1)

    status = assess(lake, NOW)

    assert status.warnung
    assert status.drosselung
    assert any("drosselt" in reason for reason in status.gruende)


def test_the_trend_of_the_last_hour(lake):
    for seq, minutes_ago in enumerate(range(60, -1, -10), start=1):
        feed(lake, minutes_ago, seq, chip_temp=56.0 - minutes_ago / 10)  # +1 °C every 10 minutes

    assert assess(lake, NOW).trend_chip == pytest.approx(6.0)


def test_old_and_implausible_values_are_ignored(lake):
    feed(lake, 120, 1, chip_temp=80.0)  # two hours old
    feed(lake, 2, 2, chip_temp=300.0)  # implausible, marked by the data lake

    status = assess(lake, NOW)

    assert status.chip_temp is None
    assert not status.warnung
    assert "keine aktuellen Messwerte" in status.hinweis


def test_the_watch_warns_once_per_hot_phase(lake, log, clock):
    clock.now = NOW
    watch = CoolingWatch(lake, log, clock=clock)
    feed(lake, 3, 1, chip_temp=72.0)

    watch.check()
    watch.check()
    alerts = [e for e in log.events() if e["type"] == "safety.alert"]
    assert len(alerts) == 1
    assert alerts[0]["intent"] == "cooling.warn"

    clock.now = NOW + timedelta(minutes=70)  # the hot reading has left the window
    lake.ingest("wuerfel-1", 2, NOW + timedelta(minutes=69), {"chip_temp": 58.0})
    watch.check()
    assert log.events()[-1]["intent"] == "cooling.ok"

    lake.ingest("wuerfel-1", 3, NOW + timedelta(minutes=70), {"chip_temp": 71.0})
    watch.check()
    assert len([e for e in log.events() if e["type"] == "safety.alert"]) == 2


def test_a_warning_also_moves_the_mood(lake, log, clock):
    clock.now = NOW
    mood = MoodEngine(load_profile(), clock=clock)
    watch = CoolingWatch(lake, log, mood=mood, clock=clock)
    feed(lake, 1, 1, chip_temp=74.0)

    watch.check()

    current = mood.current()
    assert current.energie < 0
    assert "74 °C im Würfel" in current.reason


def test_both_pressure_sensors_agree(lake):
    feed(lake, 1, 1, zuluft_druck=1012.4, abluft_druck=1012.6)

    status = assess(lake, NOW, druck_abgleich=0.1)

    assert status.druck_differenz == pytest.approx(0.1)
    assert not status.sensor_verdacht


def test_a_pressure_gap_makes_a_sensor_suspect(lake):
    for seq, minutes_ago in enumerate((9, 6, 3, 1), start=1):
        feed(lake, minutes_ago, seq, zuluft_druck=1012.0, abluft_druck=1014.5)

    status = assess(lake, NOW)

    assert status.sensor_verdacht
    assert "Drucksensoren weichen um 2,5 hPa ab" in status.hinweis
    assert not status.warnung  # a sensor problem is not overheating


def test_a_single_odd_pressure_reading_is_not_enough(lake):
    for seq, minutes_ago in enumerate((9, 6, 3), start=1):
        feed(lake, minutes_ago, seq, zuluft_druck=1012.0, abluft_druck=1012.2)
    feed(lake, 1, 4, zuluft_druck=1012.0, abluft_druck=1015.0)

    assert not assess(lake, NOW).sensor_verdacht  # mean of the last 10 minutes: 0.9 hPa


def test_old_pressure_readings_are_not_compared(lake):
    feed(lake, 30, 1, zuluft_druck=1012.0, abluft_druck=1016.0)

    status = assess(lake, NOW)
    assert (status.druck_differenz, status.sensor_verdacht) == (None, False)


def test_the_watch_reports_a_suspect_sensor_once(lake, log, clock):
    clock.now = NOW
    watch = CoolingWatch(lake, log, clock=clock)
    feed(lake, 2, 1, zuluft_druck=1012.0, abluft_druck=1015.0)

    watch.check()
    watch.check()
    suspects = [e for e in log.events() if e["intent"] == "cooling.sensor_suspect"]
    assert len(suspects) == 1
    assert suspects[0]["type"] == "safety.alert"

    clock.now = NOW + timedelta(minutes=20)
    lake.ingest("wuerfel-1", 2, NOW + timedelta(minutes=19), {"zuluft_druck": 1012.0, "abluft_druck": 1012.1})
    watch.check()
    assert log.events()[-1]["intent"] == "cooling.sensor_ok"


def test_a_pressure_sensor_without_valid_values_is_suspect(lake):
    feed(lake, 2, 1, zuluft_druck=None, abluft_druck=1012.0)  # sensor error from the cube

    status = assess(lake, NOW)

    assert status.sensor_verdacht
    assert "Zuluft (BMP280) liefert keine gültigen Werte" in status.hinweis


def test_the_pressure_hint_is_added_to_other_hints(lake):
    feed(lake, 2, 1, zuluft_druck=1012.0, abluft_druck=1015.0)

    assert assess(lake, NOW).hinweis.startswith("keine aktuellen Messwerte; Drucksensoren weichen um 3 hPa ab")


def test_the_all_clear_needs_a_clear_margin(lake, log, clock):
    watch = CoolingWatch(lake, log, clock=clock)
    for step, gap in enumerate((1.2, 0.9, 1.1, 0.5)):
        clock.now = NOW + timedelta(minutes=20 * step)
        ts = clock.now - timedelta(minutes=1)
        lake.ingest("wuerfel-1", step + 1, ts, {"zuluft_druck": 1012.0, "abluft_druck": 1012.0 + gap})
        watch.check()

    intents = [e["intent"] for e in log.events() if e["intent"].startswith("cooling.sensor")]
    assert intents == ["cooling.sensor_suspect", "cooling.sensor_ok"]
