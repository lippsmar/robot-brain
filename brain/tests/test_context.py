"""Tests for the cube's current state (Bauplan Daten, Phase 6.2)."""

from datetime import UTC, datetime, timedelta

import pytest

from brain.context import tageszeit, zustand
from brain.datalake import UNTERWEGS, DataLake

NOW = datetime(2026, 10, 15, 8, 30, tzinfo=UTC)  # 10:30 in Berlin (summer time)


@pytest.fixture
def lake(tmp_path, clock):
    lake = DataLake(tmp_path / "lake.db", clock=clock)
    yield lake
    lake.close()


@pytest.mark.parametrize(
    ("hour", "expected"),
    [(3, "Nacht"), (6, "Morgen"), (10, "Vormittag"), (12, "Mittag"), (15, "Nachmittag"), (19, "Abend"), (23, "Nacht")],
)
def test_time_of_day_in_local_time(hour, expected):
    berlin_summer = datetime(2026, 7, 1, hour, 0, tzinfo=UTC) - timedelta(hours=2)

    assert tageszeit(berlin_summer) == expected


def test_the_state_from_the_latest_batch(lake):
    lake.name_place("HeimNetz", "Zuhause")
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=1), {"akku": 64, "wlan_signal": -55}, wlan="HeimNetz")

    state = zustand(lake, NOW, gespraech=True)

    assert (state.tageszeit, state.ort, state.akku, state.verbindung, state.gespraech) == (
        "Vormittag",
        "Zuhause",
        64.0,
        "WLAN",
        True,
    )
    assert state.text() == "Vormittag, Ort Zuhause, Akku 64 %, Verbindung WLAN, gerade im Gespräch"


def test_switching_between_named_wlans_gives_the_right_place(lake):
    lake.name_place("HeimNetz", "Zuhause")
    lake.name_place("ArbeitNetz", "Büro")
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=3), {"wlan_signal": -50}, wlan="HeimNetz")
    lake.ingest("wuerfel-1", 2, NOW - timedelta(minutes=1), {"wlan_signal": -60}, wlan="ArbeitNetz")

    assert zustand(lake, NOW).ort == "Büro"


def test_an_unknown_wlan_means_unterwegs(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=1), {"wlan_signal": -60}, wlan="CafeGast")

    assert zustand(lake, NOW).ort == UNTERWEGS


def test_lte_is_recognised(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=1), {"lte_signal": -90, "akku": 40})

    state = zustand(lake, NOW)
    assert (state.verbindung, state.ort) == ("LTE", UNTERWEGS)


def test_the_latest_batch_decides_the_connection(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=3), {"wlan_signal": -60}, wlan="CafeGast")
    lake.ingest("wuerfel-1", 2, NOW - timedelta(minutes=1), {"lte_signal": -90})

    assert zustand(lake, NOW).verbindung == "LTE"


def test_with_both_signals_in_one_batch_wlan_wins(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=1), {"wlan_signal": -60, "lte_signal": -90})

    assert zustand(lake, NOW).verbindung == "WLAN"


def test_a_batch_without_signal_keeps_the_last_known_connection(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=3), {"lte_signal": -90})
    lake.ingest("wuerfel-1", 2, NOW - timedelta(minutes=1), {"akku": 40})

    assert zustand(lake, NOW).verbindung == "LTE"


def test_fresh_data_without_any_signal_gives_an_unknown_connection(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=1), {"akku": 40})

    assert zustand(lake, NOW).verbindung == "unbekannt"


def test_old_data_is_not_a_current_state(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=20), {"akku": 64, "wlan_signal": -55})

    state = zustand(lake, NOW)

    assert (state.ort, state.akku, state.verbindung) == (None, None, "keine aktuellen Daten")
    assert state.text() == "Vormittag, Ort unbekannt, Akku unbekannt, Verbindung keine aktuellen Daten"


def test_a_failed_battery_reading_is_not_shown_as_a_value(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=2), {"akku": 50})
    lake.ingest("wuerfel-1", 2, NOW - timedelta(minutes=1), {"akku": None})

    assert zustand(lake, NOW).akku == 50.0


def test_the_freshness_window_can_be_changed(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=20), {"akku": 64})

    assert zustand(lake, NOW, frisch=timedelta(minutes=30)).akku == 64.0


def test_another_time_zone(lake):
    assert zustand(lake, NOW, timezone="America/New_York").tageszeit == "Nacht"  # 4:30 there


def test_a_known_place_marks_the_state_as_personal(lake):
    lake.ingest("wuerfel-1", 1, NOW - timedelta(minutes=1), {"akku": 40})

    assert zustand(lake, NOW).pii
    assert not zustand(lake, NOW + timedelta(hours=1)).pii
