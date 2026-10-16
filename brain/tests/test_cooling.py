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
