"""Tests for knowledge packs and their life cycle (Bauplan Lakehouse 1.2 and 1.3)."""

import sqlite3

import pytest

from brain.memory import Memory
from brain.wissen import Wissen, WissenError


@pytest.fixture
def memory(tmp_path, log, clock):
    mem = Memory(tmp_path / "memory.db", log=log, clock=clock)
    yield mem
    mem.close()


@pytest.fixture
def wissen(tmp_path, memory, log, clock):
    store = Wissen(tmp_path / "wissen.db", memory, log=log, clock=clock)
    yield store
    store.close()


def namen(pakete):
    return [paket.name for paket in pakete]


# --- packs and sections (1.2) ----------------------------------------------------------


def test_new_pack_rests_until_it_is_used(wissen):
    pid = wissen.anlegen("Kühlung", kurzfassung="Wie der Würfel kühl bleibt.")

    paket = wissen.paket(pid)
    assert (paket.name, paket.kurzfassung, paket.status, paket.projekt) == (
        "Kühlung",
        "Wie der Würfel kühl bleibt.",
        "ruhend",
        False,
    )
    assert paket.letzte_nutzung is None
    assert wissen.aktive() == []


def test_section_is_found_with_its_pack_and_keeps_pii(wissen):
    kuehlung = wissen.anlegen("Kühlung")
    garten = wissen.anlegen("Garten", pii=True)
    wissen.abschnitt(kuehlung, "Der Lüfter läuft ab 60 Grad Chiptemperatur.", quelle="docs/bauplan-koerper-v1.md")
    wissen.abschnitt(garten, "Marvins Tomaten stehen am Südfenster.", quelle="gespraech", pii=True)

    treffer = wissen.suche("Lüfter")

    assert [(t.paket.name, t.text) for t in treffer] == [("Kühlung", "Der Lüfter läuft ab 60 Grad Chiptemperatur.")]
    assert wissen.suche("Tomaten")[0].pii is True


def test_search_reaches_resting_packs_too(wissen):
    pid = wissen.anlegen("Alt")
    wissen.abschnitt(pid, "Lötzinn ohne Blei schmilzt bei etwa 220 Grad.", quelle="recherche")

    assert wissen.paket(pid).status == "ruhend"
    assert namen(t.paket for t in wissen.suche("Lötzinn")) == ["Alt"]


def test_guest_search_sees_only_shareable_packs_without_pii(wissen):
    offen = wissen.anlegen("Physik", teilbar=True)
    wissen.abschnitt(offen, "Wasser kocht auf Meereshöhe bei 100 Grad.", quelle="recherche", teilbar=True)
    alltag = wissen.anlegen("Kochen", teilbar=True)
    wissen.abschnitt(alltag, "Nudelwasser kocht schneller mit Deckel.", quelle="recherche", teilbar=True)
    wissen.abschnitt(alltag, "Marvin kocht gern Nudeln.", quelle="gespraech", pii=True, teilbar=True)
    privat = wissen.anlegen("Privat")
    wissen.abschnitt(privat, "Milch kocht schnell über.", quelle="recherche", teilbar=True)

    texte = [t.text for t in wissen.suche("kocht", scope="guest")]

    assert texte == ["Wasser kocht auf Meereshöhe bei 100 Grad."]
    assert len(wissen.suche("kocht")) == 4


def test_section_of_unknown_pack_is_rejected(wissen):
    with pytest.raises(WissenError):
        wissen.abschnitt("p-gibt-es-nicht", "Text", quelle="x")


def test_pack_with_pii_section_counts_as_pii(wissen):
    pid = wissen.anlegen("Alltag")
    assert wissen.paket(pid).pii is False

    wissen.abschnitt(pid, "Marvin arbeitet dienstags im Büro.", quelle="gespraech", pii=True)

    assert wissen.paket(pid).pii is True


@pytest.mark.parametrize("name", ["", " ", "x" * 81, "zwei\nZeilen"])
def test_bad_names_are_rejected(wissen, name):
    with pytest.raises(WissenError):
        wissen.anlegen(name)


# --- life cycle (1.3) ------------------------------------------------------------------


def test_using_a_pack_makes_it_active(wissen, clock):
    pid = wissen.anlegen("Kühlung")

    assert wissen.nutzen(pid) == []

    paket = wissen.paket(pid)
    assert paket.status == "aktiv"
    assert paket.letzte_nutzung == "2026-10-15T12:00:00.000Z"
    assert namen(wissen.aktive()) == ["Kühlung"]


def test_sixth_pack_pushes_out_the_one_unused_longest(wissen, clock):
    pids = []
    for name in ["A", "B", "C", "D", "E"]:
        pid = wissen.anlegen(name)
        wissen.nutzen(pid)
        pids.append(pid)
        clock.advance(minutes=1)
    wissen.nutzen(pids[0])  # A is fresh again, B is now the oldest
    clock.advance(minutes=1)

    verdraengt = wissen.nutzen(wissen.anlegen("F"))

    assert [wissen.paket(pid).name for pid in verdraengt] == ["B"]
    assert namen(wissen.aktive()) == ["F", "A", "E", "D", "C"]
    assert wissen.paket(pids[1]).status == "ruhend"


def test_running_project_is_never_pushed_out(wissen, clock):
    projekt = wissen.anlegen("Gehäuse")
    wissen.projekt(projekt, True, grund="drei Arbeitsgespräche")
    clock.advance(minutes=1)
    for name in ["A", "B", "C", "D", "E"]:
        wissen.nutzen(wissen.anlegen(name))
        clock.advance(minutes=1)

    assert "Gehäuse" in namen(wissen.aktive())
    assert "A" not in namen(wissen.aktive())
    assert len(wissen.aktive()) == 5


def test_more_running_projects_than_places_stay_active(wissen):
    for name in ["P1", "P2", "P3", "P4", "P5", "P6"]:
        wissen.projekt(wissen.anlegen(name), True, grund="Test")

    assert len(wissen.aktive()) == 6


def test_unused_pack_goes_to_long_term_memory_after_30_days(wissen, clock):
    pid = wissen.anlegen("Kühlung", kurzfassung="alt")
    wissen.nutzen(pid)
    clock.advance(days=29, hours=23)
    assert wissen.pflege() == []

    clock.advance(hours=1)
    assert wissen.pflege() == [pid]

    paket = wissen.paket(pid)
    assert paket.status == "ruhend"
    assert paket.kurzfassung == "alt"  # without a model the old summary stays


def test_resting_pack_gets_a_new_summary_from_the_summarizer(tmp_path, memory, clock):
    gesehen = []

    def kurzfassen(paket, abschnitte):
        gesehen.append((paket.name, abschnitte))
        return "neu"

    store = Wissen(tmp_path / "w.db", memory, clock=clock, kurzfassen=kurzfassen)
    pid = store.anlegen("Kühlung", kurzfassung="alt")
    store.abschnitt(pid, "Lüfter ab 60 Grad.", quelle="x")
    store.nutzen(pid)
    clock.advance(days=30)

    store.pflege()

    assert store.paket(pid).kurzfassung == "neu"
    assert gesehen == [("Kühlung", ["Lüfter ab 60 Grad."])]
    store.close()


def test_running_project_ends_after_30_days_without_work(wissen, clock):
    pid = wissen.anlegen("Gehäuse")
    wissen.projekt(pid, True, grund="Arbeit")
    clock.advance(days=29)
    wissen.pflege()
    assert wissen.paket(pid).projekt is True

    clock.advance(days=1)
    wissen.pflege()

    paket = wissen.paket(pid)
    assert (paket.projekt, paket.status) == (False, "ruhend")


def test_work_on_a_project_keeps_it_running(wissen, clock):
    pid = wissen.anlegen("Gehäuse")
    wissen.projekt(pid, True, grund="Arbeit")
    clock.advance(days=20)
    wissen.nutzen(pid)
    clock.advance(days=20)

    wissen.pflege()

    assert wissen.paket(pid).projekt is True


def test_nothing_is_deleted_and_history_is_append_only(wissen, tmp_path, clock):
    pid = wissen.anlegen("Kühlung")
    wissen.abschnitt(pid, "Lüfter ab 60 Grad.", quelle="x")
    wissen.nutzen(pid)
    clock.advance(days=31)
    wissen.pflege()

    assert wissen.suche("Lüfter")[0].paket.name == "Kühlung"
    wissen.close()
    conn = sqlite3.connect(tmp_path / "wissen.db")
    for table in ("pakete", "ereignisse"):
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute(f"DELETE FROM {table}")
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute(f"UPDATE {table} SET ts = 'x'")
    conn.close()


def test_changes_are_logged(wissen, log):
    pid = wissen.anlegen("Garten", pii=True)
    wissen.nutzen(pid)

    intents = [event["intent"] for event in log.events() if event["intent"].startswith("wissen.")]
    assert intents == ["wissen.anlegen", "wissen.aktiv"]
    assert log.events()[-1]["pii"] is True


def test_unknown_pack_is_an_error(wissen):
    with pytest.raises(WissenError):
        wissen.nutzen("p-gibt-es-nicht")
    with pytest.raises(WissenError):
        wissen.paket("p-gibt-es-nicht")


def test_corrected_section_replaces_the_old_text_in_the_pack(wissen, memory):
    pid = wissen.anlegen("Kühlung")
    uid = wissen.abschnitt(pid, "Lüfter ab 70 Grad.", quelle="x")

    memory.correct(uid, "Lüfter ab 60 Grad.", source="Datenblatt")

    assert wissen.abschnitte(pid) == ["Lüfter ab 60 Grad."]


def test_failing_summarizer_does_not_stop_the_daily_care(tmp_path, memory, log, clock):
    def kurzfassen(paket, abschnitte):
        raise TimeoutError("API antwortet nicht")

    store = Wissen(tmp_path / "w.db", memory, log=log, clock=clock, kurzfassen=kurzfassen)
    a = store.anlegen("A", kurzfassung="alt")
    b = store.anlegen("B")
    store.nutzen(a)
    store.nutzen(b)
    clock.advance(days=30)

    assert sorted(store.pflege()) == sorted([a, b])

    assert store.paket(a).kurzfassung == "alt"
    assert any(event["intent"] == "wissen.kurzfassung_fehler" for event in log.events())
    store.close()


def test_sections_can_carry_extra_tags(wissen):
    pid = wissen.anlegen("Sensoren")
    wissen.abschnitt(pid, "Der BMP280 misst Luftdruck.", quelle="x", tags=["dokument:abc"])

    assert wissen.abschnitte(pid, tag="dokument:abc") == ["Der BMP280 misst Luftdruck."]
    assert wissen.abschnitte(pid, tag="dokument:xyz") == []


def test_active_packs_come_from_their_last_status_only(wissen, clock):
    ids = []
    for name in ["A", "B", "C"]:
        ids.append(wissen.anlegen(name))
    wissen.nutzen(ids[0])
    clock.advance(minutes=1)
    wissen.nutzen(ids[2])

    assert namen(wissen.aktive()) == ["C", "A"]
