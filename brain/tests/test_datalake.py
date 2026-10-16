"""Tests for the data lake on the brain (Bauplan Daten, Phase 7 with 2.2, 6.1 and 8.2)."""

import os
import random
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from brain.datalake import UNTERWEGS, DataLake, LakeError

START = datetime(2026, 10, 15, 8, 0, tzinfo=UTC)


@pytest.fixture
def lake(tmp_path, log, clock):
    lake = DataLake(tmp_path / "lake.db", log=log, clock=clock)
    yield lake
    lake.close()


def minute(n):
    return START + timedelta(minutes=n)


def test_a_batch_is_stored_with_unit_quality_and_place(lake):
    lake.name_place("HeimNetz", "Zuhause")

    result = lake.ingest("wuerfel-1", 1, minute(0), {"zuluft_temp": 21.5, "licht": 320}, wlan="HeimNetz")

    assert result.new
    rows = lake.readings("zuluft_temp", START, minute(60))
    assert [(r.value, r.unit, r.quality, r.place) for r in rows] == [(21.5, "°C", "ok", "Zuhause")]
    assert rows[0].ts == "2026-10-15T08:00:00.000Z"


def test_the_same_batch_sent_twice_is_stored_once(lake):
    lake.ingest("wuerfel-1", 7, minute(0), {"zuluft_temp": 21.5})

    again = lake.ingest("wuerfel-1", 7, minute(0), {"zuluft_temp": 21.5})

    assert not again.new
    assert len(lake.readings("zuluft_temp", START, minute(60))) == 1


def test_an_hour_of_batches_arriving_in_any_order_is_complete(lake):
    numbers = list(range(1, 61))
    random.Random(4).shuffle(numbers)  # noqa: S311  only test data: buffered batches come late and out of order
    for seq in numbers:
        lake.ingest("wuerfel-1", seq, minute(seq - 1), {"zuluft_temp": 20 + seq / 100})

    assert lake.missing("wuerfel-1", 1, 60) == []
    (hour,) = lake.hourly("zuluft_temp", START, minute(60))
    assert hour.count == 60


def test_missing_numbers_are_found(lake):
    for seq in (1, 2, 4, 7):
        lake.ingest("wuerfel-1", seq, minute(seq), {"zuluft_temp": 21.0})

    assert lake.missing("wuerfel-1", 1, 7) == [3, 5, 6]


def test_a_failed_sensor_gives_an_error_instead_of_a_value(lake, log):
    result = lake.ingest("wuerfel-1", 1, minute(0), {"licht": None})

    (row,) = lake.readings("licht", START, minute(60), quality=None)
    assert (row.value, row.quality) == (None, "fehler")
    assert lake.readings("licht", START, minute(60)) == []  # normal queries only see good values
    assert any("licht" in warning for warning in result.warnings)
    event = log.events()[-1]
    assert (event["type"], event["intent"]) == ("error", "datalake.sensor_error")


def test_implausible_values_are_marked(lake):
    lake.ingest("wuerfel-1", 1, minute(0), {"chip_temp": 300.0, "akku": -5})

    qualities = {r.channel: r.quality for r in lake.all_readings(START, minute(60))}
    assert qualities == {"chip_temp": "unplausibel", "akku": "unplausibel"}


def test_unknown_channels_are_reported_and_not_stored(lake):
    result = lake.ingest("wuerfel-1", 1, minute(0), {"zuluft_temp": 21.0, "geheimkanal": 1.0})

    assert any("geheimkanal" in warning for warning in result.warnings)
    assert {r.channel for r in lake.all_readings(START, minute(60))} == {"zuluft_temp"}


def test_places_follow_named_wlans_otherwise_unterwegs(lake):
    lake.name_place("HeimNetz", "Zuhause")
    lake.ingest("wuerfel-1", 1, minute(0), {"licht": 100}, wlan="HeimNetz")
    lake.ingest("wuerfel-1", 2, minute(1), {"licht": 100}, wlan="CafeGast")
    lake.ingest("wuerfel-1", 3, minute(2), {"licht": 100})
    lake.name_place("HeimNetz", "Büro")  # renamed: only later batches get the new name
    lake.ingest("wuerfel-1", 4, minute(3), {"licht": 100}, wlan="HeimNetz")

    places = [r.place for r in lake.readings("licht", START, minute(60))]
    assert places == ["Zuhause", UNTERWEGS, UNTERWEGS, "Büro"]


def test_queries_filter_by_time_place_and_channel(lake):
    lake.name_place("HeimNetz", "Zuhause")
    lake.name_place("ArbeitNetz", "Büro")
    lake.ingest("wuerfel-1", 1, minute(0), {"licht": 100, "zuluft_temp": 20}, wlan="HeimNetz")
    lake.ingest("wuerfel-1", 2, minute(60 * 24), {"licht": 500, "zuluft_temp": 22}, wlan="ArbeitNetz")

    assert [r.value for r in lake.readings("licht", START, minute(60 * 48))] == [100, 500]
    assert [r.value for r in lake.readings("licht", START, minute(60 * 48), place="Büro")] == [500]
    assert [r.value for r in lake.readings("licht", minute(60), minute(60 * 48))] == [500]


def test_hourly_statistics(lake):
    for seq, value in enumerate([20.0, 22.0, 24.0], start=1):
        lake.ingest("wuerfel-1", seq, minute(seq), {"zuluft_temp": value})
    lake.ingest("wuerfel-1", 4, minute(70), {"zuluft_temp": 30.0})

    first, second = lake.hourly("zuluft_temp", START, minute(120))
    assert first.hour == "2026-10-15T08"
    assert (first.minimum, first.maximum, first.count) == (20.0, 24.0, 3)
    assert first.mean == pytest.approx(22.0)
    assert first.std == pytest.approx((8 / 3) ** 0.5)
    assert (second.hour, second.count) == ("2026-10-15T09", 1)


def test_sounds_and_marvins_labels(lake, log):
    lake.ingest(
        "wuerfel-1",
        1,
        minute(0),
        {"lautstaerke": 55},
        sounds=[{"klasse": "Wind", "sicherheit": 0.6, "sprache": False, "stimmen": 0}],
    )
    (sound,) = lake.sounds(START, minute(60))

    lake.label_sound(sound.id, "Regen", vermerk="Marvin per Telegram")

    (labelled,) = lake.sounds(START, minute(60))
    assert (labelled.klasse, labelled.original, labelled.vermerk) == ("Regen", "Wind", "Marvin per Telegram")
    assert log.events()[-1]["intent"] == "datalake.label"


def test_labels_need_an_existing_sound(lake):
    with pytest.raises(LakeError, match="unbekannt"):
        lake.label_sound(999, "Regen", vermerk="Test")


def test_speech_is_only_a_feature_and_personal(lake):
    lake.ingest(
        "wuerfel-1", 1, minute(0), {}, sounds=[{"klasse": "Sprache", "sicherheit": 0.9, "sprache": True, "stimmen": 2}]
    )

    (sound,) = lake.sounds(START, minute(60))
    assert (sound.sprache, sound.stimmen, sound.pii) == (True, 2, True)


def test_records_cannot_be_changed_or_deleted(lake, tmp_path):
    lake.ingest("wuerfel-1", 1, minute(0), {"zuluft_temp": 21.0})
    conn = sqlite3.connect(tmp_path / "lake.db")

    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute("UPDATE readings SET value = 99")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute("DELETE FROM readings")
    conn.close()


def test_the_manifest_lists_counts_time_span_and_personal_data(lake):
    lake.name_place("HeimNetz", "Zuhause")
    lake.ingest("wuerfel-1", 1, minute(0), {"licht": 100}, wlan="HeimNetz")
    lake.ingest("wuerfel-1", 2, minute(5), {"licht": 120})

    manifest = {entry.name: entry for entry in lake.manifest()}

    licht = manifest["readings:licht"]
    assert (licht.count, licht.pii_count) == (2, 1)
    assert (licht.first, licht.last) == ("2026-10-15T08:00:00.000Z", "2026-10-15T08:05:00.000Z")


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (("", 1, minute(0), {}), "Gerät"),
        (("wuerfel 1; DROP", 1, minute(0), {}), "Gerät"),
        (("wuerfel-1", -1, minute(0), {}), "Nummer"),
        (("wuerfel-1", 1, datetime(2026, 10, 15, 8, 0), {}), "Zeitzone"),
        (("wuerfel-1", 1, minute(0), {"zuluft_temp": "warm"}), "Zahl"),
        (("wuerfel-1", 1, minute(0), {"zuluft_temp": float("nan")}), "Zahl"),
    ],
)
def test_invalid_batches_are_refused(lake, args, message):
    with pytest.raises(LakeError, match=message):
        lake.ingest(*args)


@pytest.mark.parametrize(
    "sound",
    [
        {"klasse": "Regen", "sicherheit": 1.5, "sprache": False, "stimmen": 0},
        {"klasse": "Regen", "sicherheit": 0.5, "sprache": False, "stimmen": -1},
        {"klasse": "", "sicherheit": 0.5, "sprache": False, "stimmen": 0},
        {"klasse": "Regen", "sicherheit": 0.5},
    ],
)
def test_invalid_sounds_are_refused(lake, sound):
    with pytest.raises(LakeError):
        lake.ingest("wuerfel-1", 1, minute(0), {}, sounds=[sound])


def test_a_refused_batch_leaves_nothing_behind(lake):
    with pytest.raises(LakeError):
        lake.ingest("wuerfel-1", 1, minute(0), {"zuluft_temp": 21.0}, sounds=[{"klasse": "Regen", "sicherheit": 2}])

    assert lake.all_readings(START, minute(60)) == []


def test_the_database_file_is_private(tmp_path, clock):
    DataLake(tmp_path / "private.db", clock=clock).close()

    assert os.stat(tmp_path / "private.db").st_mode & 0o777 == 0o600


def test_a_database_from_another_version_is_refused(tmp_path, clock):
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA user_version = 99")
    conn.close()

    with pytest.raises(LakeError, match="Version"):
        DataLake(path, clock=clock)


def test_the_latest_label_wins(lake):
    lake.ingest(
        "wuerfel-1", 1, minute(0), {}, sounds=[{"klasse": "Wind", "sicherheit": 0.6, "sprache": False, "stimmen": 0}]
    )
    (sound,) = lake.sounds(START, minute(60))

    lake.label_sound(sound.id, "Regen", vermerk="erste Korrektur")
    lake.label_sound(sound.id, "Hagel", vermerk="doch Hagel")

    (labelled,) = lake.sounds(START, minute(60))
    assert (labelled.klasse, labelled.original, labelled.vermerk) == ("Hagel", "Wind", "doch Hagel")


def test_unterwegs_is_not_a_place_name(lake):
    with pytest.raises(LakeError, match="unterwegs"):
        lake.name_place("IrgendeinNetz", UNTERWEGS)


def test_a_missing_last_number_is_found_too(lake):
    lake.ingest("wuerfel-1", 1, minute(1), {"zuluft_temp": 21.0})
    lake.ingest("wuerfel-1", 2, minute(2), {"zuluft_temp": 21.0})

    assert lake.missing("wuerfel-1", 1, 3) == [3]


def test_places_per_hour_for_pattern_finding(lake):
    lake.name_place("HeimNetz", "Zuhause")
    lake.ingest("wuerfel-1", 1, minute(0), {"licht": 100})
    lake.ingest("wuerfel-1", 2, minute(5), {"licht": 100})
    lake.ingest("wuerfel-1", 3, minute(70), {"licht": None}, wlan="HeimNetz")  # a sensor error still counts

    assert lake.places_by_hour(START, minute(120)) == [
        ("2026-10-15T08", UNTERWEGS),
        ("2026-10-15T09", "Zuhause"),
    ]
    assert lake.places_by_hour(minute(60), minute(120)) == [("2026-10-15T09", "Zuhause")]


def test_time_queries_use_an_index(lake):
    plan = lake._conn.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM readings WHERE ts >= ? AND ts < ?", ("a", "b")
    ).fetchall()

    assert "readings_by_ts" in " ".join(str(row["detail"]) for row in plan)
