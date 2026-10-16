"""Tests for the catalog of all data sets (Bauplan Lakehouse 1.1)."""

import hashlib
import sqlite3

import pytest

from brain.datalake import DataLake
from brain.katalog import Katalog, KatalogError, pruefsumme_datei


@pytest.fixture
def katalog(tmp_path, log, clock):
    kat = Katalog(tmp_path / "katalog.db", log=log, clock=clock)
    yield kat
    kat.close()


def test_entry_is_stored_and_the_newest_version_counts(katalog, clock):
    katalog.eintragen("dokument:abc", ort="rohdaten/dokumente/2026/10/abc.pdf", format="pdf", anzahl=1, pruefsumme="11")
    clock.advance(minutes=1)
    katalog.eintragen("dokument:abc", ort="rohdaten/dokumente/2026/10/abc.pdf", format="pdf", anzahl=1, pruefsumme="22")

    eintrag = katalog.aktuell("dokument:abc")

    assert eintrag.pruefsumme == "22"
    assert eintrag.ts == "2026-10-15T12:01:00.000Z"
    assert [e.datensatz for e in katalog.alle()] == ["dokument:abc"]
    assert katalog.aktuell("gibt-es-nicht") is None


def test_changed_checksum_is_noticed(katalog):
    katalog.eintragen("dokument:abc", ort="a.pdf", format="pdf", anzahl=1, pruefsumme="11")

    assert katalog.pruefen("dokument:abc", "11") is True
    assert katalog.pruefen("dokument:abc", "99") is False
    with pytest.raises(KatalogError):
        katalog.pruefen("gibt-es-nicht", "11")


def test_data_lake_manifest_becomes_catalog_entries(katalog, tmp_path, clock):
    lake = DataLake(tmp_path / "lake.db", clock=clock)
    lake.name_place("buero-wlan", "Büro")
    lake.ingest("wuerfel", 1, clock(), {"licht": 120.0, "zuluft_temp": 21.5}, wlan="buero-wlan")

    katalog.datalake_eintragen(lake, ort="lake.db")

    licht = katalog.aktuell("datalake:readings:licht")
    assert (licht.anzahl, licht.pii, licht.format) == (1, True, "sqlite")
    assert licht.von == licht.bis == "2026-10-15T12:00:00.000Z"
    assert katalog.aktuell("datalake:sounds").anzahl == 0
    lake.close()


def test_entries_are_append_only(katalog, tmp_path):
    katalog.eintragen("x", ort="x", format="txt", anzahl=1)
    katalog.close()
    conn = sqlite3.connect(tmp_path / "katalog.db")
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE eintraege SET anzahl = 2")
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM eintraege")
    conn.close()


@pytest.mark.parametrize(
    "fields",
    [{"datensatz": ""}, {"anzahl": -1}, {"format": ""}, {"frist": "morgen"}],
)
def test_invalid_entries_are_rejected(katalog, fields):
    values = {"datensatz": "x", "ort": "x", "format": "txt", "anzahl": 1} | fields
    datensatz = values.pop("datensatz")

    with pytest.raises(KatalogError):
        katalog.eintragen(datensatz, **values)


def test_every_entry_is_logged_with_pii(katalog, log):
    katalog.eintragen("x", ort="x", format="txt", anzahl=1, pii=True)

    event = log.events()[-1]
    assert event["intent"] == "katalog.eintragen"
    assert event["pii"] is True


def test_checksum_of_a_file(tmp_path):
    datei = tmp_path / "a.txt"
    datei.write_bytes(b"Schlaubi")

    assert pruefsumme_datei(datei) == hashlib.sha256(b"Schlaubi").hexdigest()


@pytest.mark.parametrize("fields", [{"frist": "90 Tage\n"}, {"anzahl": True}, {"datensatz": "a\nb"}])
def test_sneaky_values_are_rejected(katalog, fields):
    values = {"datensatz": "x", "ort": "x", "format": "txt", "anzahl": 1} | fields
    datensatz = values.pop("datensatz")

    with pytest.raises(KatalogError):
        katalog.eintragen(datensatz, **values)


def test_checksum_check_needs_a_stored_and_a_given_checksum(katalog):
    katalog.eintragen("ohne", ort="x", format="sqlite", anzahl=1)
    katalog.eintragen("mit", ort="x", format="pdf", anzahl=1, pruefsumme="11")

    with pytest.raises(KatalogError):
        katalog.pruefen("ohne", None)
    with pytest.raises(KatalogError):
        katalog.pruefen("mit", None)


def test_unchanged_data_lake_adds_no_new_versions(katalog, tmp_path, clock, log):
    lake = DataLake(tmp_path / "lake.db", clock=clock)
    lake.ingest("wuerfel", 1, clock(), {"licht": 120.0})
    katalog.datalake_eintragen(lake, ort="lake.db")
    before = len(log.events())

    clock.advance(hours=1)
    katalog.datalake_eintragen(lake, ort="lake.db")
    assert len(log.events()) == before

    lake.ingest("wuerfel", 2, clock(), {"licht": 130.0})
    katalog.datalake_eintragen(lake, ort="lake.db")
    assert katalog.aktuell("datalake:readings:licht").anzahl == 2
    lake.close()
