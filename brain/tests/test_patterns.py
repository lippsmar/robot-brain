"""Tests for pattern finding (Bauplan Daten, Phase 9)."""

import os
from datetime import UTC, datetime, timedelta

import pytest

from brain.datalake import DataLake
from brain.patterns import MusterError, MusterListe, finde_muster, heute_vs_sonst


def heute(lake, now, ort):
    return [m.text for m in heute_vs_sonst(lake, now, ort)]


FIRST_DAY = datetime(2026, 10, 5, tzinfo=UTC)  # a Monday; Berlin is UTC+2 until 25.10.2026
NOW = datetime(2026, 10, 19, 6, 0, tzinfo=UTC)  # Monday morning after two weeks


def two_weeks(lake):
    """Weekdays 9–17 Uhr in the office, evenings at home, weekends at home; the battery runs low around 16 Uhr."""
    lake.name_place("ArbeitNetz", "Büro")
    lake.name_place("HeimNetz", "Zuhause")
    seq = 0
    for day in range(14):
        date = FIRST_DAY + timedelta(days=day)
        weekday = date.weekday() < 5
        slots = []
        if weekday:
            slots += [(7, 15, "ArbeitNetz", 55.0, 22.0), (16, 20, "HeimNetz", 40.0, 21.0)]
        else:
            slots += [(9, 15, "HeimNetz", 38.0, 21.0)]
        for start, end, wlan, noise, temp in slots:
            for quarter in range((end - start) * 4):
                ts = date + timedelta(hours=start, minutes=15 * quarter)
                values = {"lautstaerke": noise, "zuluft_temp": temp}
                if weekday and wlan == "ArbeitNetz":
                    values["akku"] = max(0.0, 100.0 - 11.0 * quarter / 4)  # below 20 % from 14:30 UTC
                seq += 1
                lake.ingest("wuerfel-1", seq, ts, values, wlan=wlan)
    return seq


@pytest.fixture(scope="module")
def filled(tmp_path_factory):
    path = tmp_path_factory.mktemp("lake") / "lake.db"
    lake = DataLake(path, clock=lambda: NOW)
    two_weeks(lake)
    lake.close()
    return path


@pytest.fixture
def lake(filled, tmp_path, clock):
    copy = tmp_path / "lake.db"
    copy.write_bytes(filled.read_bytes())
    lake = DataLake(copy, clock=clock)
    yield lake
    lake.close()


@pytest.fixture
def liste(tmp_path, log, clock):
    liste = MusterListe(tmp_path / "muster.db", log=log, clock=clock)
    yield liste
    liste.close()


def texts(found):
    return {m.key: m.text for m in found}


def test_two_weeks_give_at_least_three_true_patterns(lake):
    found = texts(finde_muster(lake, NOW))

    assert found["ort:werktags:Büro"] == "Werktags meist 9–17 Uhr: Büro (an 10 von 10 Tagen)"
    assert found["ort:werktags:Zuhause"] == "Werktags meist 18–22 Uhr: Zuhause (an 10 von 10 Tagen)"
    assert found["ort:am Wochenende:Zuhause"] == "Am Wochenende meist 11–17 Uhr: Zuhause (an 4 von 4 Tagen)"
    assert found["umgebung:Büro"] == "Büro: im Schnitt 55 dB und 22 °C (an 10 Tagen)"
    assert found["akku:knapp"] == "Akku: an 10 von 10 Tagen unter 20 %, meist gegen 16 Uhr"
    assert len(found) >= 3


def test_all_patterns_about_marvin_are_personal(lake):
    assert all(m.pii for m in finde_muster(lake, NOW))


def test_too_few_days_give_no_pattern(tmp_path, clock):
    lake = DataLake(tmp_path / "short.db", clock=clock)
    lake.name_place("ArbeitNetz", "Büro")
    for day in range(2):
        ts = FIRST_DAY + timedelta(days=day, hours=8)
        lake.ingest("wuerfel-1", day + 1, ts, {"lautstaerke": 50}, wlan="ArbeitNetz")

    assert finde_muster(lake, FIRST_DAY + timedelta(days=3)) == []
    lake.close()


def test_rare_visits_are_not_a_pattern(lake):
    lake.name_place("CafeNetz", "Café")
    lake.ingest("wuerfel-1", 10_000, datetime(2026, 10, 14, 10, 0, tzinfo=UTC), {"lautstaerke": 60}, wlan="CafeNetz")

    assert not any("Café" in key for key in texts(finde_muster(lake, NOW)))


def test_unterwegs_is_never_a_place_pattern(tmp_path, clock):
    lake = DataLake(tmp_path / "away.db", clock=clock)
    for day in range(5):
        lake.ingest("wuerfel-1", day + 1, FIRST_DAY + timedelta(days=day, hours=8), {"lautstaerke": 50})

    assert finde_muster(lake, FIRST_DAY + timedelta(days=6)) == []
    lake.close()


def test_the_window_limits_the_data(lake):
    assert finde_muster(lake, NOW + timedelta(days=60)) == []
    assert finde_muster(lake, NOW, tage=2) == []  # only the weekend: too few days


def test_today_louder_than_usual(lake):
    now = NOW + timedelta(hours=4)  # Monday 12 Uhr local
    for quarter in range(8):
        lake.ingest(
            "wuerfel-1",
            20_000 + quarter,
            NOW + timedelta(hours=1, minutes=15 * quarter),
            {"lautstaerke": 65.0, "zuluft_temp": 22.2},
            wlan="ArbeitNetz",
        )

    assert heute(lake, now, "Büro") == ["Büro: heute lauter als sonst (65 statt 55 dB)"]


def test_today_warmer_and_quieter(lake):
    for quarter in range(8):
        lake.ingest(
            "wuerfel-1",
            20_000 + quarter,
            NOW + timedelta(hours=1, minutes=15 * quarter),
            {"lautstaerke": 50.0, "zuluft_temp": 25.0},
            wlan="ArbeitNetz",
        )

    assert heute(lake, NOW + timedelta(hours=4), "Büro") == [
        "Büro: heute leiser als sonst (50 statt 55 dB)",
        "Büro: heute wärmer als sonst (25 statt 22 °C)",
    ]


def test_a_single_loud_moment_today_says_nothing(lake):
    lake.ingest("wuerfel-1", 20_000, NOW + timedelta(hours=1), {"lautstaerke": 80.0}, wlan="ArbeitNetz")

    assert heute(lake, NOW + timedelta(hours=4), "Büro") == []


def test_unterwegs_is_never_compared(lake):
    for seq, hours in enumerate((-119, -95, -71, 1, 1.25, 1.5), start=30_000):  # Wed to Fri 9 Uhr, today 9 Uhr
        noise = 80.0 if hours > 0 else 50.0
        lake.ingest("wuerfel-1", seq, NOW + timedelta(hours=hours), {"lautstaerke": noise})

    assert heute(lake, NOW + timedelta(hours=4), "unterwegs") == []


def test_small_differences_and_missing_data_say_nothing(lake):
    lake.ingest("wuerfel-1", 20_000, NOW + timedelta(hours=1), {"lautstaerke": 56.0}, wlan="ArbeitNetz")

    now = NOW + timedelta(hours=4)
    assert heute(lake, now, "Büro") == []
    assert heute(lake, now, "Café") == []
    assert heute(lake, now, "unterwegs") == []


def test_marvin_deletes_a_pattern(lake, liste, log):
    liste.loeschen("akku:knapp", vermerk="Marvin per Telegram")

    assert "akku:knapp" not in texts(liste.aktuell(lake, NOW))
    event = log.events()[-1]
    assert (event["type"], event["intent"], event["pii"]) == ("agent.action", "patterns.deleted", True)


def test_a_deleted_pattern_stays_deleted_after_restart(lake, liste, tmp_path, clock):
    liste.loeschen("umgebung:Büro", vermerk="Test")
    liste.close()

    again = MusterListe(tmp_path / "muster.db", clock=clock)
    assert "umgebung:Büro" not in texts(again.aktuell(lake, NOW))
    again.close()


def test_a_deleted_pattern_can_be_brought_back(lake, liste, log):
    liste.loeschen("akku:knapp", vermerk="Test")
    liste.zurueckholen("akku:knapp")

    assert "akku:knapp" in texts(liste.aktuell(lake, NOW))
    assert log.events()[-1]["intent"] == "patterns.restored"


@pytest.mark.parametrize(
    "key", ["", "irgendwas", "akku:", "ort:werktags", "x" * 200, "akku:knapp\n", "umgebung:" + "x" * 41, None]
)
def test_unknown_keys_are_refused(liste, key):
    with pytest.raises(MusterError):
        liste.loeschen(key, vermerk="Test")


def test_overview_for_what_do_you_know_about_my_day(lake, liste, log):
    liste.loeschen("umgebung:Zuhause", vermerk="Test")

    text = liste.uebersicht(lake, NOW)

    assert text.startswith("Das weiß ich über deinen Alltag (bleibt lokal):")
    assert "- Werktags meist 9–17 Uhr: Büro (an 10 von 10 Tagen)" in text
    assert "Zuhause: im Schnitt" not in text
    assert "löschen" in text
    event = log.events()[-1]
    assert (event["intent"], event["pii"]) == ("patterns.shown", True)


def test_overview_without_patterns(tmp_path, liste, clock):
    empty = DataLake(tmp_path / "empty.db", clock=clock)

    assert "Noch keine Muster" in liste.uebersicht(empty, NOW)
    empty.close()


def test_the_list_file_is_private(liste, tmp_path):
    assert os.stat(tmp_path / "muster.db").st_mode & 0o777 == 0o600


def test_interrupted_hours_are_shown_as_two_spans(tmp_path, clock):
    lake = DataLake(tmp_path / "split.db", clock=clock)
    lake.name_place("ArbeitNetz", "Büro")
    lake.name_place("KantineNetz", "Kantine")
    seq = 0
    for day in range(3):
        for hour, wlan in ((7, "ArbeitNetz"), (8, "KantineNetz"), (9, "ArbeitNetz")):
            seq += 1
            lake.ingest("wuerfel-1", seq, FIRST_DAY + timedelta(days=day, hours=hour), {"licht": 300}, wlan=wlan)

    found = texts(finde_muster(lake, FIRST_DAY + timedelta(days=4)))

    assert found["ort:werktags:Büro"] == "Werktags meist 9–10 und 11–12 Uhr: Büro (an 3 von 3 Tagen)"
    assert found["ort:werktags:Kantine"] == "Werktags meist 10–11 Uhr: Kantine (an 3 von 3 Tagen)"
    lake.close()


def test_place_names_with_a_colon_can_be_deleted(liste):
    liste.loeschen("umgebung:Büro: 2. Stock", vermerk="Test")


def test_the_battery_hour_is_the_typical_one(tmp_path, clock):
    lake = DataLake(tmp_path / "akku.db", clock=clock)
    for day, low_hour in enumerate((12, 14, 14, 16)):  # UTC; 14 UTC is 16 Uhr in Berlin
        date = FIRST_DAY + timedelta(days=day)
        lake.ingest("wuerfel-1", 3 * day + 1, date + timedelta(hours=10), {"akku": 80})
        lake.ingest("wuerfel-1", 3 * day + 2, date + timedelta(hours=low_hour), {"akku": 15})
        lake.ingest("wuerfel-1", 3 * day + 3, date + timedelta(hours=low_hour + 3), {"akku": 5})  # still low later

    assert texts(finde_muster(lake, FIRST_DAY + timedelta(days=5)))["akku:knapp"] == (
        "Akku: an 4 von 4 Tagen unter 20 %, meist gegen 16 Uhr"
    )
    lake.close()


def test_comparison_results_are_personal(lake):
    for quarter in range(8):
        ts = NOW + timedelta(hours=1, minutes=15 * quarter)
        lake.ingest("wuerfel-1", 20_000 + quarter, ts, {"lautstaerke": 65.0}, wlan="ArbeitNetz")

    (result,) = heute_vs_sonst(lake, NOW + timedelta(hours=4), "Büro")
    assert (result.key, result.pii) == ("heute:Büro:lautstaerke", True)


def test_today_is_compared_with_the_same_hours(tmp_path, clock):
    """Quiet mornings and loud afternoons: a quiet morning today is normal."""
    lake = DataLake(tmp_path / "hours.db", clock=clock)
    lake.name_place("ArbeitNetz", "Büro")
    seq = 0
    for day in range(5):  # Monday to Friday
        for hour, noise in ((7, 50.0), (8, 50.0), (12, 60.0), (13, 60.0)):
            seq += 1
            lake.ingest(
                "wuerfel-1", seq, FIRST_DAY + timedelta(days=day, hours=hour), {"lautstaerke": noise}, wlan="ArbeitNetz"
            )
    monday = FIRST_DAY + timedelta(days=7)
    for minute in (0, 15, 30):
        seq += 1
        lake.ingest(
            "wuerfel-1", seq, monday + timedelta(hours=7, minutes=minute), {"lautstaerke": 50.0}, wlan="ArbeitNetz"
        )

    assert heute(lake, monday + timedelta(hours=8), "Büro") == []
    lake.close()


def test_a_weekend_is_compared_with_weekends(tmp_path, clock):
    """Loud weekday mornings at home must not make a normal Sunday morning look quiet."""
    lake = DataLake(tmp_path / "weekend.db", clock=clock)
    lake.name_place("HeimNetz", "Zuhause")
    seq = 0
    for day in range(13):  # Monday 5.10. to Saturday 17.10.
        noise = 50.0 if (FIRST_DAY + timedelta(days=day)).weekday() < 5 else 38.0
        for minute in (0, 30):
            seq += 1
            ts = FIRST_DAY + timedelta(days=day, hours=9, minutes=minute)
            lake.ingest("wuerfel-1", seq, ts, {"lautstaerke": noise}, wlan="HeimNetz")
    sunday = FIRST_DAY + timedelta(days=13, hours=9)
    for minute in (0, 15, 30):
        seq += 1
        lake.ingest("wuerfel-1", seq, sunday + timedelta(minutes=minute), {"lautstaerke": 38.0}, wlan="HeimNetz")

    assert heute(lake, sunday + timedelta(hours=1), "Zuhause") == []
    lake.close()


def test_temperatures_keep_one_decimal(lake):
    for quarter in range(8):
        ts = NOW + timedelta(hours=1, minutes=15 * quarter)
        lake.ingest("wuerfel-1", 20_000 + quarter, ts, {"zuluft_temp": 23.6 + 0.05 * (quarter % 2)}, wlan="ArbeitNetz")

    assert heute(lake, NOW + timedelta(hours=4), "Büro") == ["Büro: heute wärmer als sonst (23,6 statt 22 °C)"]


def test_a_low_battery_over_midnight_counts_once(tmp_path, clock):
    lake = DataLake(tmp_path / "night.db", clock=clock)
    seq = 0
    for day in range(5):
        for hour in range(18, 26):  # 20 Uhr to 3 Uhr local; low from 22 Uhr local (20 UTC)
            seq += 1
            value = 50.0 if hour < 20 else 10.0
            lake.ingest("wuerfel-1", seq, FIRST_DAY + timedelta(days=day, hours=hour), {"akku": value})
        seq += 1
        lake.ingest("wuerfel-1", seq, FIRST_DAY + timedelta(days=day + 1, hours=4), {"akku": 90.0})  # charged

    found = texts(finde_muster(lake, FIRST_DAY + timedelta(days=7)))

    assert found["akku:knapp"] == "Akku: an 5 von 6 Tagen unter 20 %, meist gegen 22 Uhr"
    lake.close()


def test_overview_when_marvin_deleted_everything(lake, liste):
    for muster in finde_muster(lake, NOW):
        liste.loeschen(muster.key, vermerk="Test")

    assert "hast du gelöscht" in liste.uebersicht(lake, NOW)


def test_restoring_something_never_deleted_changes_nothing(liste, log):
    before = len(log.events())

    assert liste.zurueckholen("akku:knapp") is False
    assert len(log.events()) == before
    with pytest.raises(MusterError):
        liste.zurueckholen("quatsch")


@pytest.mark.parametrize("vermerk", ["", "   ", None, "x" * 201])
def test_a_deletion_needs_a_note(liste, vermerk):
    with pytest.raises(MusterError, match="Vermerk"):
        liste.loeschen("akku:knapp", vermerk=vermerk)


def test_place_names_with_a_line_break_can_be_deleted(liste):
    liste.loeschen("umgebung:Büro\n2", vermerk="Test")


def test_the_average_weights_every_value(tmp_path, clock):
    lake = DataLake(tmp_path / "weights.db", clock=clock)
    lake.name_place("ArbeitNetz", "Büro")
    seq = 0
    for day in range(3):
        for minute, hour, noise in ((0, 7, 50.0), (20, 7, 50.0), (40, 7, 50.0), (0, 8, 30.0)):
            seq += 1
            ts = FIRST_DAY + timedelta(days=day, hours=hour, minutes=minute)
            lake.ingest("wuerfel-1", seq, ts, {"lautstaerke": noise}, wlan="ArbeitNetz")

    assert (
        texts(finde_muster(lake, FIRST_DAY + timedelta(days=4)))["umgebung:Büro"]
        == "Büro: im Schnitt 45 dB (an 3 Tagen)"
    )
    lake.close()


def test_short_visits_count_as_a_place(lake):
    """Marvin, 16.10.2026: a place also counts for short stays, e.g. a café."""
    lake.name_place("CafeNetz", "Café")
    for seq, (day, hour) in enumerate(((6, 13), (8, 14), (14, 13)), start=40_000):  # Tue, Thu, Wed; one reading each
        ts = datetime(2026, 10, day, hour, 30, tzinfo=UTC)
        lake.ingest("wuerfel-1", seq, ts, {"lautstaerke": 62.0}, wlan="CafeNetz")

    found = texts(finde_muster(lake, NOW))

    assert found["besuch:Café"] == "Café: an 3 Tagen besucht, meist werktags gegen 15 Uhr"
    assert "besuch:Büro" not in found  # already a pattern by time of day


def test_regular_short_visits_also_get_a_time_of_day(lake):
    lake.name_place("CafeNetz", "Café")
    for seq, day in enumerate((3, 10, 17), start=40_000):  # three Saturdays, 10 Uhr local
        lake.ingest("wuerfel-1", seq, datetime(2026, 10, day, 8, 0, tzinfo=UTC), {"lautstaerke": 62.0}, wlan="CafeNetz")

    found = texts(finde_muster(lake, NOW))

    assert found["ort:am Wochenende:Café"] == "Am Wochenende meist 10–11 Uhr: Café (an 3 von 5 Tagen)"
    assert "besuch:Café" not in found


def test_visits_on_mixed_days(tmp_path, clock):
    lake = DataLake(tmp_path / "mixed.db", clock=clock)
    lake.name_place("CafeNetz", "Café")
    for seq, (day, hour) in enumerate(((5, 14), (8, 12), (10, 14), (11, 15)), start=1):  # Mo, Do, Sa, So (UTC)
        lake.ingest("wuerfel-1", seq, datetime(2026, 10, day, hour, 0, tzinfo=UTC), {"licht": 300}, wlan="CafeNetz")

    found = texts(finde_muster(lake, NOW))

    assert found["besuch:Café"] == "Café: an 4 Tagen besucht, werktags wie am Wochenende, meist gegen 16 Uhr"
    lake.close()


def test_a_visit_pattern_can_be_deleted(lake, liste):
    lake.name_place("CafeNetz", "Café")
    for seq, (day, hour) in enumerate(((6, 13), (8, 14), (14, 13)), start=40_000):
        lake.ingest("wuerfel-1", seq, datetime(2026, 10, day, hour, 30, tzinfo=UTC), {"licht": 300}, wlan="CafeNetz")

    liste.loeschen("besuch:Café", vermerk="Marvin per Telegram")

    assert "besuch:Café" not in texts(liste.aktuell(lake, NOW))
    assert "Café: an 3 Tagen" not in liste.uebersicht(lake, NOW)


def test_deleting_the_time_pattern_does_not_bring_the_place_back_as_a_visit(lake, liste):
    lake.name_place("CafeNetz", "Café")
    for seq, day in enumerate((3, 10, 17), start=40_000):
        lake.ingest("wuerfel-1", seq, datetime(2026, 10, day, 8, 0, tzinfo=UTC), {"licht": 300}, wlan="CafeNetz")

    liste.loeschen("ort:am Wochenende:Café", vermerk="Test")

    found = texts(liste.aktuell(lake, NOW))
    assert not any(key in found for key in ("ort:am Wochenende:Café", "besuch:Café"))
