"""Tests for the deadline run with keep protection (Bauplan Gehirn 10.5, Design Gehirn 7)."""

import pytest

from brain.fristen import FRISTEN, Fristen, FristenError
from brain.memory import Memory, MemoryStoreError


@pytest.fixture
def memory(tmp_path, log, clock):
    store = Memory(tmp_path / "memory.db", log=log, clock=clock)
    yield store
    store.close()


@pytest.fixture
def fristen(memory, log, clock):
    return Fristen(memory, log=log, clock=clock)


def alt_gespraech(memory, clock, text="Marvin: Hallo\nSchlaubi: Na?", tage=400):
    """A conversation entry from `tage` days ago; the clock is moved back to now afterwards."""
    jetzt = clock.now
    clock.advance(days=-tage)
    uid = memory.remember(text, kind="gespraech", source="gespraech:telegram", pii=True)
    clock.now = jetzt
    return uid


def uebernehmen(memory, uid, **anders):
    """Stands in for the daily consolidation: a summary that names its sources with `aus:<uid>`."""
    felder = {"kind": "zusammenfassung", "source": "konsolidierung"} | anders
    return memory.remember("Zusammenfassung", tags=[f"aus:{uid}"], **felder)


def test_deadlines_follow_the_design():
    assert FRISTEN == {"gespraech": 365, "mail": 30, "rohseite": 90}


def test_unimportant_old_entry_that_was_taken_over_can_be_deleted(fristen, memory, clock):
    uid = alt_gespraech(memory, clock)
    uebernehmen(memory, uid)

    bericht = fristen.pruefen()

    assert [f.uid for f in bericht.loeschbar] == [uid]


def test_young_entries_are_left_alone(fristen, memory, clock):
    uid = alt_gespraech(memory, clock, tage=100)
    uebernehmen(memory, uid)

    bericht = fristen.pruefen()

    assert uid not in {f.uid for f in bericht.alle()}


def test_entry_marked_keep_stays(fristen, memory, clock):
    uid = alt_gespraech(memory, clock)
    uebernehmen(memory, uid)
    memory.keep(uid)

    bericht = fristen.pruefen()

    assert [(f.uid, f.grund) for f in bericht.bleibt] == [(uid, "merken")]
    assert bericht.loeschbar == []


def test_nothing_is_deleted_before_it_was_taken_over_into_knowledge(fristen, memory, clock):
    uid = alt_gespraech(memory, clock)

    bericht = fristen.pruefen()

    assert [f.uid for f in bericht.wartet] == [uid]
    assert bericht.loeschbar == []


def test_doubtful_entry_goes_on_the_should_it_stay_list(fristen, memory, clock):
    uid = alt_gespraech(memory, clock)
    uebernehmen(memory, uid)
    andere = alt_gespraech(memory, clock, text="Marvin: Anderes")
    memory.dispute(uid, andere, "widerspricht sich")

    bericht = fristen.pruefen()

    assert uid in {f.uid for f in bericht.soll_bleiben}


def test_importance_check_can_be_replaced(memory, log, clock):
    wichtig = alt_gespraech(memory, clock, text="Marvin: Mein Geburtstag ist im Mai")
    unwichtig = alt_gespraech(memory, clock, text="Marvin: Hallo")
    for uid in (wichtig, unwichtig):
        uebernehmen(memory, uid)
    fristen = Fristen(memory, log=log, clock=clock, wichtig=lambda hit: "ja" if "Geburtstag" in hit.content else "nein")

    bericht = fristen.pruefen()

    assert [f.uid for f in bericht.loeschbar] == [unwichtig]
    assert [(f.uid, f.grund) for f in bericht.bleibt] == [(wichtig, "wichtig")]


def test_other_kinds_have_their_own_deadline_and_need_no_takeover(fristen, memory, clock):
    jetzt = clock.now
    clock.advance(days=-40)
    mail = memory.remember("Fremde Mail: Angebot", kind="mail", source="mail:fremd")
    memory.remember("Notiz ohne Frist", kind="notiz", source="marvin")
    clock.now = jetzt

    bericht = fristen.pruefen()

    assert [f.uid for f in bericht.loeschbar] == [mail]


def test_deleting_needs_marvin_and_only_takes_what_is_allowed(fristen, memory, clock):
    weg = alt_gespraech(memory, clock)
    uebernehmen(memory, weg)
    geschuetzt = alt_gespraech(memory, clock, text="Marvin: merk dir das")
    uebernehmen(memory, geschuetzt)
    memory.keep(geschuetzt)
    jung = memory.remember("frisch", kind="gespraech", source="gespraech:telegram")

    with pytest.raises(FristenError):
        fristen.loeschen([weg], approved_by="claude")
    geloescht = fristen.loeschen([weg, geschuetzt, jung], approved_by="marvin")

    assert geloescht == [weg]
    assert memory.get(weg) is None
    assert memory.get(geschuetzt) is not None and memory.get(jung) is not None
    assert [d["uid"] for d in memory.deletions()] == [weg]


def test_marvin_may_delete_from_the_should_it_stay_list(fristen, memory, clock):
    uid = alt_gespraech(memory, clock)
    uebernehmen(memory, uid)
    andere = alt_gespraech(memory, clock, text="Marvin: Anderes")
    uebernehmen(memory, andere)
    memory.dispute(uid, andere, "widerspricht sich")

    assert fristen.loeschen([uid], approved_by="marvin") == []  # a blanket yes is not enough
    assert fristen.loeschen([uid], approved_by="marvin", auch_unsichere=True) == [uid]


def test_run_and_deletion_are_logged_without_content(fristen, memory, clock, log):
    uid = alt_gespraech(memory, clock, text="Marvin: geheimes Rezept")
    uebernehmen(memory, uid)

    fristen.pruefen()
    fristen.loeschen([uid], approved_by="marvin")

    events = [e for e in log.events() if e["intent"].startswith("fristen.")]
    assert [e["intent"] for e in events] == ["fristen.pruefen", "fristen.loeschen"]
    assert events[0]["payload"]["loeschbar"] == 1
    assert "Rezept" not in str(events)


@pytest.mark.parametrize(
    "anders",
    [{"source": "fremd"}, {"kind": "notiz"}, {"origin": "anderer-schlaubi"}],
)
def test_only_own_summaries_count_as_taken_over(fristen, memory, clock, anders):
    uid = alt_gespraech(memory, clock)
    uebernehmen(memory, uid, **anders)

    assert [f.uid for f in fristen.pruefen().wartet] == [uid]


def test_archived_summary_does_not_count(fristen, memory, clock):
    uid = alt_gespraech(memory, clock)
    memory.forget(uebernehmen(memory, uid), "falsch zusammengefasst")

    assert [f.uid for f in fristen.pruefen().wartet] == [uid]


def test_uids_as_text_are_refused_and_any_iterable_is_counted_once(fristen, memory, clock, log):
    uid = alt_gespraech(memory, clock)
    uebernehmen(memory, uid)

    with pytest.raises(FristenError):
        fristen.loeschen(uid, approved_by="marvin")
    assert fristen.loeschen((u for u in [uid, uid]), approved_by="marvin") == [uid]
    event = [e for e in log.events() if e["intent"] == "fristen.loeschen"][-1]
    assert event["payload"] == {"angefragt": 1, "geloescht": 1, "fehler": 0}


def test_a_failing_deletion_does_not_stop_the_others_and_is_logged(fristen, memory, clock, log, monkeypatch):
    erste, zweite = alt_gespraech(memory, clock), alt_gespraech(memory, clock, text="Marvin: Zwei")
    for uid in (erste, zweite):
        uebernehmen(memory, uid)
    echt = memory.delete

    def wackelt(uid, **kwargs):
        if uid == erste:
            raise MemoryStoreError("gerade gesperrt")
        return echt(uid, **kwargs)

    monkeypatch.setattr(memory, "delete", wackelt)

    assert fristen.loeschen([erste, zweite], approved_by="marvin") == [zweite]
    event = [e for e in log.events() if e["intent"] == "fristen.loeschen"][-1]
    assert event["payload"] == {"angefragt": 2, "geloescht": 1, "fehler": 1}


def test_young_entries_cannot_be_deleted_even_with_marvins_yes(fristen, memory):
    frisch = memory.remember("Fremde Mail von heute", kind="mail", source="mail:fremd")

    assert fristen.loeschen([frisch], approved_by="marvin") == []
    assert memory.get(frisch) is not None
