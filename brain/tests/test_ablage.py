"""Tests for the document store (Bauplan Lakehouse 1.5)."""

import hashlib
import json
import stat
from pathlib import Path

import pytest

from brain.ablage import Ablage, AblageError, abschnitte
from brain.katalog import Katalog
from brain.memory import Memory
from brain.wissen import Wissen

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def katalog(tmp_path, clock):
    store = Katalog(tmp_path / "katalog.db", clock=clock)
    yield store
    store.close()


@pytest.fixture
def wissen(tmp_path, clock):
    memory = Memory(tmp_path / "memory.db", clock=clock)
    store = Wissen(tmp_path / "wissen.db", memory, clock=clock)
    yield store
    store.close()
    memory.close()


@pytest.fixture
def ablage(tmp_path, katalog, wissen, log, clock):
    return Ablage(tmp_path / "rohdaten", katalog, wissen=wissen, log=log, clock=clock)


def test_document_is_stored_by_month_with_metadata_and_catalog_entry(ablage, katalog, tmp_path):
    daten = b"%PDF-1.7 Datenblatt BMP280"

    dok = ablage.ablegen(daten, name="BMP280 Datenblatt.pdf", quelle="https://example.org/bmp280.pdf", lizenz="unklar")

    sha = hashlib.sha256(daten).hexdigest()
    assert dok.neu is True and dok.pruefsumme == sha
    assert dok.pfad.parent == tmp_path / "rohdaten" / "dokumente" / "2026" / "10"
    assert dok.pfad.name == f"{sha[:16]}-BMP280_Datenblatt.pdf"
    assert dok.pfad.read_bytes() == daten
    assert stat.S_IMODE(dok.pfad.stat().st_mode) == 0o600
    meta = json.loads(dok.pfad.with_name(dok.pfad.name + ".meta.json").read_text(encoding="utf-8"))
    assert meta == {
        "name": "BMP280 Datenblatt.pdf",
        "quelle": "https://example.org/bmp280.pdf",
        "abrufzeit": "2026-10-15T12:00:00.000Z",
        "pii": False,
        "lizenz": "unklar",
        "pruefsumme": sha,
        "groesse": len(daten),
    }
    eintrag = katalog.aktuell(f"dokument:{sha}")
    assert (eintrag.format, eintrag.anzahl, eintrag.pruefsumme) == ("pdf", 1, sha)
    assert eintrag.ort == "dokumente/2026/10/" + dok.pfad.name


def test_same_document_twice_is_recognised(ablage, clock):
    erste = ablage.ablegen(b"gleich", name="a.txt", quelle="x")
    clock.advance(days=40)

    zweite = ablage.ablegen(b"gleich", name="b.txt", quelle="y")

    assert zweite.neu is False
    assert zweite.pfad == erste.pfad


def test_text_goes_into_a_knowledge_pack(ablage, wissen):
    pid = wissen.anlegen("Sensoren")

    ablage.ablegen(
        b"...",
        name="notiz.txt",
        quelle="Marvin",
        text="Der BMP280 misst den Luftdruck.\n\nDer BH1750 misst das Licht.",
        paket=pid,
    )

    treffer = wissen.suche("Luftdruck")
    assert [(t.paket.name, t.quelle) for t in treffer] == [("Sensoren", "Marvin (notiz.txt)")]
    assert len(wissen.abschnitte(pid)) == 1  # both short paragraphs fit into one section


def test_store_inside_the_repository_is_refused(katalog):
    with pytest.raises(AblageError):
        Ablage(REPO / "data" / "raw", katalog)


@pytest.mark.parametrize("name", ["", "../../etc/passwd", "a/b.txt", ".."])
def test_names_cannot_leave_the_store(ablage, tmp_path, name):
    dok = ablage.ablegen(b"inhalt " + name.encode(), name=name, quelle="x")

    assert dok.pfad.resolve().is_relative_to((tmp_path / "rohdaten").resolve())
    assert "/" not in dok.pfad.name


def test_storing_is_logged(ablage, log):
    ablage.ablegen(b"privat", name="brief.txt", quelle="Marvin", pii=True)

    event = log.events()[-1]
    assert event["intent"] == "ablage.ablegen"
    assert event["pii"] is True


def test_sections_follow_paragraphs_and_join_short_ones():
    absatz = ("Satz eins ist hier. " * 30).strip()  # 599 characters
    text = f"{absatz}\n\n{absatz}\n\nKurz."

    teile = abschnitte(text, max_zeichen=700)

    assert teile == [absatz, f"{absatz}\n\nKurz."]


def test_long_paragraph_is_cut_at_sentence_ends():
    text = "Erster Satz mit Inhalt. " * 10  # about 240 characters

    teile = abschnitte(text, max_zeichen=100)

    assert all(len(teil) <= 100 for teil in teile)
    assert all(teil.endswith("Inhalt.") for teil in teile)
    assert " ".join(teile) == text.strip()


def test_one_endless_sentence_is_cut_hard():
    teile = abschnitte("x" * 2500, max_zeichen=1000)

    assert [len(teil) for teil in teile] == [1000, 1000, 500]


def test_empty_text_gives_no_sections():
    assert abschnitte("  \n\n ") == []


def test_only_the_file_name_of_a_path_is_kept(ablage):
    dok = ablage.ablegen(b"datenblatt", name="downloads/sensoren/BH1750.pdf", quelle="x")

    assert dok.pfad.name.endswith("-BH1750.pdf")


def test_known_document_can_still_go_into_another_pack(ablage, wissen):
    a = wissen.anlegen("Sensoren")
    b = wissen.anlegen("Wetter")
    text = "Der BMP280 misst den Luftdruck."

    ablage.ablegen(b"datenblatt", name="bmp.pdf", quelle="x", text=text, paket=a)
    dok = ablage.ablegen(b"datenblatt", name="bmp.pdf", quelle="x", text=text, paket=b)
    ablage.ablegen(b"datenblatt", name="bmp.pdf", quelle="x", text=text, paket=b)

    assert dok.neu is False
    assert wissen.abschnitte(a) == [text]
    assert wissen.abschnitte(b) == [text]  # the same document is not added twice to one pack


def test_retry_after_a_failed_section_adds_only_what_is_missing(ablage, wissen, monkeypatch):
    pid = wissen.anlegen("Lang")
    text = "Erster Teil.\n\n" + "x" * 1200
    original = wissen.abschnitt
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("Gedächtnis gesperrt")
        return original(*args, **kwargs)

    monkeypatch.setattr(wissen, "abschnitt", flaky)
    with pytest.raises(RuntimeError):
        ablage.ablegen(b"lang", name="l.txt", quelle="x", text=text, paket=pid)

    ablage.ablegen(b"lang", name="l.txt", quelle="x", text=text, paket=pid)

    assert len(wissen.abschnitte(pid)) == len(abschnitte(text))


def test_text_without_knowledge_store_is_refused_before_anything_is_written(katalog, tmp_path):
    ablage = Ablage(tmp_path / "rohdaten", katalog)

    with pytest.raises(AblageError):
        ablage.ablegen(b"x", name="a.txt", quelle="x", text="Text", paket="p-1")

    assert katalog.alle() == []
    assert not (tmp_path / "rohdaten").exists()
