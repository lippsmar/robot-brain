"""Tests for the memory core (Bauplan Gehirn 10.2 and 10.2a, Memory Core rules)."""

import sqlite3

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from brain.memory import Memory, MemoryStoreError


@pytest.fixture
def memory(tmp_path, log, clock):
    mem = Memory(tmp_path / "memory.db", log=log, origin="gehirn", clock=clock)
    yield mem
    mem.close()


def uids(hits):
    return [hit.uid for hit in hits]


# --- remember and recall ----------------------------------------------------------


def test_remembered_fact_can_be_recalled_with_provenance(memory):
    uid = memory.remember(
        "Die Zuluft wird mit einem BMP280 gemessen.",
        kind="fact",
        source="docs/bauplan-koerper-v1.md",
        source_rating="A",
        confidence=0.9,
        tags=["sensor", "kuehlung"],
    )
    hits = memory.recall("BMP280")

    assert uids(hits) == [uid]
    hit = hits[0]
    assert hit.source == "docs/bauplan-koerper-v1.md"
    assert hit.source_rating == "A"
    assert hit.confidence == pytest.approx(0.9)
    assert hit.origin == "gehirn"
    assert hit.ts == "2026-10-15T12:00:00.000Z"
    assert hit.status == "active"
    assert hit.keep is False
    assert hit.shareable is False
    assert hit.tags == ["sensor", "kuehlung"]
    assert hit.schema_version == "entry/1.0"


def test_umlauts_and_case_do_not_matter(memory):
    uid = memory.remember("Kühlung über Zuluft und Abluft", kind="fact", source="marvin")
    assert uids(memory.recall("kuhlung")) == [uid]
    assert uids(memory.recall("KÜHLUNG")) == [uid]


def test_parts_of_german_compound_words_are_found(memory):
    uid = memory.remember("Die Gehäusekühlung läuft gut.", kind="fact", source="marvin")
    assert uids(memory.recall("Kühlung")) == [uid]


def test_better_matches_come_first(memory):
    weak = memory.remember("Notiz zum Gehäuse aus Holz.", kind="note", source="marvin")
    strong = memory.remember(
        "Holz für das Gehäuse: Holz aus Marvins Bestand, Holzrahmen.", kind="note", source="marvin"
    )
    hits = memory.recall("Holz Gehäuse")
    assert uids(hits)[:2] == [strong, weak]


def test_nothing_found_returns_an_empty_list(memory):
    memory.remember("Marvin mag Rennräder.", kind="interest", source="marvin")
    assert memory.recall("Quantenphysik") == []
    assert memory.recall("   ") == []


def test_query_syntax_cannot_break_the_search(memory):
    memory.remember("Ein ganz normaler Satz.", kind="note", source="marvin")
    for query in ['"', "NEAR(", "a OR", "*", "-x", "(Satz"]:
        memory.recall(query)  # must not raise


def test_recall_respects_the_limit(memory):
    for n in range(8):
        memory.remember(f"Messwert Nummer {n} vom Lichtsensor", kind="note", source="sensor")
    assert len(memory.recall("Lichtsensor", limit=3)) == 3


# --- validation ------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"content": ""},
        {"content": "   "},
        {"confidence": 1.5},
        {"confidence": -0.1},
        {"source_rating": "E"},
        {"kind": ""},
        {"source": ""},
        {"trust": 2.0},
    ],
)
def test_invalid_entries_are_rejected(memory, kwargs):
    entry = {"content": "Ein Fakt.", "kind": "fact", "source": "marvin"}
    entry.update(kwargs)
    with pytest.raises(MemoryStoreError):
        memory.remember(**entry)


@pytest.mark.parametrize(
    "content",
    ["Der Key ist sk-ant-api03-abcdefghijklmnop", "-----BEGIN RSA PRIVATE KEY----- abc"],
)
def test_secrets_are_never_stored(memory, content):
    with pytest.raises(MemoryStoreError, match="secret"):
        memory.remember(content, kind="note", source="marvin")


# --- append-only -----------------------------------------------------------------


def test_entries_cannot_be_changed_directly(memory, tmp_path):
    uid = memory.remember("Unveränderlich.", kind="fact", source="marvin")
    memory.keep(uid)  # so that the marks table has a row to change
    raw = sqlite3.connect(tmp_path / "memory.db")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        raw.execute("UPDATE entries SET content = 'anders'")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        raw.execute("DELETE FROM entries")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        raw.execute("UPDATE marks SET mark = 'keep'")
    raw.close()


def test_a_correction_is_a_new_entry_that_replaces_the_old(memory):
    old = memory.remember("Der Würfel ist 12 cm groß.", kind="fact", source="marvin")
    new = memory.correct(old, "Der Würfel ist 10 cm groß.", source="marvin")

    assert uids(memory.recall("Würfel groß")) == [new]
    replaced = memory.get(old)
    assert replaced.status == "replaced"
    assert memory.get(new).replaces == old


# --- keep, archive, dispute -------------------------------------------------------------


def test_keep_marks_an_entry_as_protected(memory):
    uid = memory.remember("Marvins Lieblingsfarbe ist Blau.", kind="preference", source="marvin", pii=True)
    memory.keep(uid)
    assert memory.get(uid).keep is True


def test_forget_archives_instead_of_deleting(memory):
    uid = memory.remember("Alter Plan mit Kamera im Würfel.", kind="note", source="marvin")
    memory.forget(uid, reason="ersetzt durch Abstandssensor")

    assert memory.recall("Kamera") == []
    archived = memory.recall("Kamera", include_archived=True)
    assert uids(archived) == [uid] and archived[0].status == "archived"
    assert memory.get(uid) is not None


def test_contradicting_entries_are_disputed(memory):
    a = memory.remember("Der Pi Zero hat zwei USB-Anschlüsse.", kind="fact", source="web:a", source_rating="C")
    b = memory.remember("Der Pi Zero hat einen freien USB-Anschluss.", kind="fact", source="web:b", source_rating="B")
    memory.dispute(a, b, reason="Widerspruch Anzahl USB")
    assert memory.get(a).status == "disputed"
    assert memory.get(b).status == "disputed"


def test_confirm_marks_an_entry_as_confirmed(memory):
    uid = memory.remember("Der VL53L8CX misst bis 4 m.", kind="fact", source="web:st", source_rating="A")
    memory.confirm(uid, reason="zweite Quelle Pololu")
    assert memory.get(uid).status == "confirmed"


# --- deleting (only with Marvin's approval) ---------------------------------------------------


def test_delete_needs_marvins_approval(memory):
    uid = memory.remember("Etwas Privates.", kind="note", source="marvin", pii=True)
    with pytest.raises(MemoryStoreError, match="approval"):
        memory.delete(uid, reason="Test", approved_by="schlaubi")


def test_delete_with_approval_removes_the_entry_everywhere(memory, tmp_path):
    uid = memory.remember("Etwas sehr Privates über Lisa.", kind="note", source="marvin", pii=True)
    memory.keep(uid)
    with pytest.raises(MemoryStoreError, match="keep"):
        memory.delete(uid, reason="Löschwunsch", approved_by="marvin")
    memory.delete(uid, reason="Löschwunsch", approved_by="marvin", override_keep=True)

    assert memory.get(uid) is None
    assert memory.recall("Lisa", include_archived=True) == []
    raw = sqlite3.connect(tmp_path / "memory.db")
    dumped = "\n".join(raw.iterdump())
    raw.close()
    assert "Lisa" not in dumped
    assert memory.deletions()[0]["uid"] == uid


# --- scopes: Marvin, guests -----------------------------------------------------------


def test_guests_only_see_shareable_entries_without_personal_data(memory):
    private = memory.remember("Marvin war heute müde beim Radfahren.", kind="note", source="marvin", pii=True)
    shareable = memory.remember("Radfahren im Herbst: Licht ist Pflicht.", kind="fact", source="web:x", shareable=True)
    both = memory.remember(
        "Marvin fährt Rad, das darf jeder wissen.", kind="note", source="marvin", pii=True, shareable=True
    )

    assert set(uids(memory.recall("Radfahren Rad", scope="marvin"))) == {private, shareable, both}
    assert uids(memory.recall("Radfahren Rad", scope="guest")) == [shareable]


def test_unknown_scope_is_rejected(memory):
    with pytest.raises(MemoryStoreError):
        memory.recall("x", scope="everyone")


# --- inbox for entries from other hosts (Version 2 prepared) -----------------------------------


def test_entries_from_a_host_wait_in_the_inbox_until_accepted(memory):
    item = memory.enqueue(
        {"content": "Notiz vom Arbeitslaptop.", "kind": "note", "source": "marvin"}, origin="host:arbeitslaptop"
    )
    assert [i["id"] for i in memory.pending()] == [item]
    assert memory.recall("Arbeitslaptop") == []

    uid = memory.accept(item)
    assert memory.pending() == []
    assert memory.get(uid).origin == "host:arbeitslaptop"


def test_invalid_inbox_items_are_rejected_with_reason(memory):
    item = memory.enqueue({"content": "", "kind": "note", "source": "marvin"}, origin="host:x")
    with pytest.raises(MemoryStoreError):
        memory.accept(item)
    memory.reject(item, reason="leer")
    assert memory.pending() == []


# --- logging and integrity ---------------------------------------------------------------------


def test_memory_changes_are_logged_without_their_content(memory, log, tmp_path):
    uid = memory.remember("Geheimer Spitzname: Hummel.", kind="note", source="marvin", pii=True)
    memory.keep(uid)
    memory.forget(uid, reason="Test")

    events = [e for e in log.events() if e["type"] == "memory.write"]
    assert [e["payload"]["op"] for e in events] == ["remember", "keep", "forget"]
    assert all(e["payload"]["uid"] == uid for e in events)
    assert events[0]["pii"] is True
    log_text = "".join(p.read_text(encoding="utf-8") for p in (tmp_path / "events").glob("*.jsonl"))
    assert "Hummel" not in log_text


def test_integrity_check_reports_ok(memory):
    memory.remember("Alles in Ordnung.", kind="note", source="marvin")
    assert memory.check() == {"integrity": "ok", "fts": "ok"}


def test_reopening_keeps_everything(tmp_path, log, clock):
    first = Memory(tmp_path / "memory.db", log=log, origin="gehirn", clock=clock)
    uid = first.remember("Bleibt nach dem Neustart.", kind="fact", source="marvin")
    first.close()
    second = Memory(tmp_path / "memory.db", log=log, origin="gehirn", clock=clock)
    assert uids(second.recall("Neustart")) == [uid]
    second.close()


words = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu")), min_size=4, max_size=12)


@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(word=words)
def test_every_remembered_word_can_be_found(memory, word):
    uid = memory.remember(f"Testeintrag {word} Ende", kind="note", source="test")
    assert uid in uids(memory.recall(word, limit=50, include_archived=True))


# --- error paths and small operations ---------------------------------------------------------


def test_restore_makes_an_archived_entry_visible_again(memory):
    uid = memory.remember("Zwischenzeitlich archiviert.", kind="note", source="marvin")
    memory.forget(uid, reason="Test")
    memory.restore(uid, reason="doch wichtig")
    assert uids(memory.recall("archiviert")) == [uid]


def test_operations_on_unknown_entries_fail(memory):
    for operation in (memory.keep, lambda uid: memory.forget(uid, reason="x"), lambda uid: memory.confirm(uid, "x")):
        with pytest.raises(MemoryStoreError, match="no entry"):
            operation("unknown-uid")
    assert memory.get("unknown-uid") is None


def test_recall_can_filter_by_kind(memory):
    fact = memory.remember("Licht im Büro ist hell.", kind="fact", source="sensor")
    memory.remember("Licht ausmachen nicht vergessen.", kind="note", source="marvin")
    assert uids(memory.recall("Licht", kind="fact")) == [fact]


@pytest.mark.parametrize(
    "payload",
    [
        {"content": "x", "kind": "note", "source": "marvin", "evil": 1},
        {"content": "nur Inhalt"},
    ],
)
def test_inbox_items_with_wrong_fields_cannot_be_accepted(memory, payload):
    item = memory.enqueue(payload, origin="host:x")
    with pytest.raises(MemoryStoreError):
        memory.accept(item)
    assert [i["id"] for i in memory.pending()] == [item]


def test_inbox_refuses_secrets_and_non_objects(memory):
    with pytest.raises(MemoryStoreError, match="secret"):
        memory.enqueue({"content": "x", "kind": "note", "source": "marvin", "api_key": "y"}, origin="host:x")
    with pytest.raises(MemoryStoreError):
        memory.enqueue(["keine", "Liste"], origin="host:x")
    with pytest.raises(MemoryStoreError, match="no pending"):
        memory.accept(999)


def test_the_database_file_is_only_readable_by_the_owner(memory, tmp_path):
    memory.remember("Privat.", kind="note", source="marvin")
    assert (tmp_path / "memory.db").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    ("stored", "query"),
    [
        ("Die Straße zum Bäcker", "Strasse"),
        ("Die Strasse zum Bäcker", "Straße"),
        ("Kühlung über Zuluft", "Kuehlung"),
        ("Aepfel aus dem Garten", "Äpfel"),
        ("Größe des Würfels", "groesse"),
    ],
)
def test_german_spellings_find_each_other(memory, stored, query):
    uid = memory.remember(stored, kind="note", source="marvin")
    assert uids(memory.recall(query)) == [uid]


def test_replace_cannot_overwrite_entries_or_marks(memory, tmp_path):
    uid = memory.remember("Original.", kind="fact", source="marvin")
    memory.keep(uid)
    raw = sqlite3.connect(tmp_path / "memory.db")  # a plain connection without our settings
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        raw.execute(
            "INSERT OR REPLACE INTO entries (id, uid, ts, kind, content, source, origin, search_text, schema_version)"
            " VALUES (1, ?, 'x', 'fact', 'Fälschung', 'x', 'x', 'x', 'entry/1.0')",
            (uid,),
        )
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        raw.execute("INSERT OR REPLACE INTO marks (id, uid, ts, mark) VALUES (1, 'x', 'x', 'archived')")
    raw.close()
    assert memory.get(uid).content == "Original."


def test_columns_have_strict_types(memory, tmp_path):
    raw = sqlite3.connect(tmp_path / "memory.db")
    with pytest.raises(sqlite3.DatabaseError, match="cannot store"):
        raw.execute(
            "INSERT INTO entries (uid, ts, kind, content, source, origin, search_text, schema_version, confidence)"
            " VALUES ('u', 'x', 'fact', 'x', 'x', 'x', 'x', 'entry/1.0', 'hoch')"
        )
    raw.close()


@settings(max_examples=200, deadline=None)
@given(text=st.text(max_size=40))
def test_normalizing_twice_changes_nothing(text):
    """Idempotence of the spelling normalizer (property catalog: normalizers)."""
    from brain.memory import normalize_german

    once = normalize_german(text)
    assert normalize_german(once) == once
    assert not set("äöüß") & set(once)


# --- findings of the code review (15.10.2026) -----------------------------------------------


def test_inbox_items_one_after_another_can_all_be_processed(memory):
    first = memory.enqueue({"content": "Erste Notiz.", "kind": "note", "source": "marvin"}, origin="host:a")
    memory.accept(first)
    second = memory.enqueue({"content": "Zweite Notiz.", "kind": "note", "source": "marvin"}, origin="host:a")
    assert second != first
    memory.accept(second)
    third = memory.enqueue({"content": "Dritte Notiz.", "kind": "note", "source": "marvin"}, origin="host:a")
    memory.reject(third, reason="doppelt")
    assert memory.pending() == []


def test_the_daily_check_leaves_no_lock_behind(memory, tmp_path, log, clock):
    memory.remember("Etwas.", kind="note", source="marvin")
    assert memory.check()["fts"] == "ok"
    other = Memory(tmp_path / "memory.db", log=log, origin="host:b", clock=clock)
    other.remember("Von einem zweiten Prozess.", kind="note", source="marvin")  # must not be locked
    other.close()


def test_hidden_entries_do_not_push_visible_ones_out_of_the_search(memory):
    for n in range(60):
        memory.remember(f"Licht Licht Licht privat {n}", kind="note", source="marvin", pii=True)
    shared = memory.remember("Licht im Flur ist kaputt.", kind="fact", source="marvin", shareable=True)
    assert uids(memory.recall("Licht", scope="guest")) == [shared]
    assert uids(memory.recall("Licht", kind="fact")) == [shared]


def test_archived_entries_do_not_push_active_ones_out_of_the_search(memory):
    for n in range(60):
        old = memory.remember(f"Sensor Sensor Sensor alt {n}", kind="note", source="marvin")
        memory.forget(old, reason="veraltet")
    active = memory.remember("Sensor für Abstand ist der VL53L8CX.", kind="fact", source="marvin")
    assert uids(memory.recall("Sensor")) == [active]


def test_delete_is_logged_even_when_the_wal_cannot_be_flushed(memory, log, tmp_path):
    uid = memory.remember("Telefonnummer von Lisa: 0123 456.", kind="note", source="marvin", pii=True)
    reader = sqlite3.connect(tmp_path / "memory.db")
    reader.execute("BEGIN")
    reader.execute("SELECT count(*) FROM entries").fetchone()  # an open read snapshot elsewhere
    result = memory.delete(uid, reason="Löschwunsch", approved_by="marvin")
    reader.rollback()
    reader.close()

    assert result == {"wal_flushed": False}
    ops = [(e["payload"]["op"], e["payload"].get("wal_flushed")) for e in log.events() if e["type"] == "memory.write"]
    assert ops[-2:] == [("delete", None), ("compact", False)]


def test_a_correction_does_not_inherit_the_old_sources_rating(memory):
    old = memory.remember(
        "Der Sensor misst bis 4 m.",
        kind="fact",
        source="web:st.com",
        source_rating="A",
        confidence=0.95,
        contributor="host:arbeitslaptop",
        trust=0.9,
        tags=["sensor"],
    )
    new = memory.get(memory.correct(old, "Der Sensor misst bis 3 m.", source="web:forum"))
    assert (new.source_rating, new.confidence, new.contributor, new.trust) == (None, None, None, None)
    assert new.kind == "fact" and new.tags == ["sensor"]


def test_a_database_from_another_version_is_not_opened_silently(tmp_path, log, clock):
    Memory(tmp_path / "memory.db", log=log, clock=clock).close()
    raw = sqlite3.connect(tmp_path / "memory.db")
    raw.execute("PRAGMA user_version = 99")
    raw.close()
    with pytest.raises(MemoryStoreError, match="migration"):
        Memory(tmp_path / "memory.db", log=log, clock=clock)


def test_decomposed_umlauts_are_found(memory):
    uid = memory.remember("Kühlung im Gehäuse", kind="note", source="marvin")  # ü as u + combining mark
    assert uids(memory.recall("Kuehlung")) == [uid]


def test_deleted_words_are_gone_from_the_word_index(memory, tmp_path):
    uid = memory.remember("Lisa wohnt in Mainz.", kind="note", source="marvin", pii=True)
    memory.delete(uid, reason="Löschwunsch", approved_by="marvin")
    assert memory.check() == {"integrity": "ok", "fts": "ok"}
    raw = sqlite3.connect(tmp_path / "memory.db")
    raw.execute("CREATE VIRTUAL TABLE temp.words_vocab USING fts5vocab(main, entries_words, 'row')")
    terms = {row[0] for row in raw.execute("SELECT term FROM temp.words_vocab")}
    raw.close()
    assert not {"lisa", "mainz"} & terms
