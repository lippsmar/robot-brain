"""Tests for the append-only event log (Bauplan Gehirn: every action is logged)."""

import json
import threading
from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from brain.eventlog import GENESIS, EventLog, EventLogError, event_hash
from brain.tests.helpers import FakeClock


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_first_event_starts_the_chain(log, tmp_path):
    event = log.append("agent.action", {"what": "hello"}, intent="greet")

    assert event["seq"] == 0
    assert event["prev"] == GENESIS
    assert event["schema"] == "event/1.2"
    assert event["source"] == "test"
    assert event["ts"] == "2026-10-15T12:00:00.000Z"
    assert event["hash"] == event_hash({k: v for k, v in event.items() if k != "hash"})
    assert read_lines(tmp_path / "events" / "2026-10-15.jsonl") == [event]


def test_events_are_chained_and_numbered(log):
    first = log.append("agent.action", {"n": 1})
    second = log.append("agent.action", {"n": 2})

    assert second["seq"] == 1
    assert second["prev"] == first["hash"]


def test_a_new_instance_continues_the_chain(tmp_path, clock):
    first = EventLog(tmp_path / "events", source="a", clock=clock).append("agent.action", {})
    second = EventLog(tmp_path / "events", source="b", clock=clock).append("agent.action", {})

    assert second["seq"] == first["seq"] + 1
    assert second["prev"] == first["hash"]


def test_a_new_day_starts_a_new_file_but_keeps_the_chain(log, clock, tmp_path):
    first = log.append("agent.action", {})
    clock.advance(days=1)
    second = log.append("agent.action", {})

    assert (tmp_path / "events" / "2026-10-16.jsonl").exists()
    assert second["seq"] == 1
    assert second["prev"] == first["hash"]
    assert log.verify().ok


def test_unknown_type_is_rejected_and_nothing_is_written(log, tmp_path):
    with pytest.raises(EventLogError, match="type"):
        log.append("made.up", {})
    assert not (tmp_path / "events" / "2026-10-15.jsonl").exists()


def test_invalid_optional_field_is_rejected(log):
    with pytest.raises(EventLogError, match="confidence"):
        log.append("agent.decision", {}, confidence=1.5)


@pytest.mark.parametrize(
    "payload",
    [
        {"api_key": "x"},
        {"nested": {"bot_token": "x"}},
        {"sim_pin": "1234"},
        {"Passwort": "geheim"},
        {"note": "key sk-ant-api03-abcdefghijklmnop"},
        {"items": ["-----BEGIN OPENSSH PRIVATE KEY-----"]},
    ],
)
def test_secrets_never_reach_the_log(log, tmp_path, payload):
    with pytest.raises(EventLogError, match="secret"):
        log.append("agent.action", payload)
    assert not (tmp_path / "events" / "2026-10-15.jsonl").exists()


def test_token_counts_are_not_mistaken_for_secrets(log):
    event = log.append("budget.usage", {"input_tokens": 10, "max_tokens": 100})
    assert event["payload"]["input_tokens"] == 10


def test_verify_accepts_a_clean_log(log, clock):
    for n in range(5):
        log.append("agent.action", {"n": n})
        clock.advance(hours=7)
    report = log.verify()
    assert report.ok, report.errors
    assert report.count == 5


def test_verify_detects_a_changed_event(log, tmp_path):
    log.append("agent.action", {"n": 1})
    log.append("agent.action", {"n": 2})
    path = tmp_path / "events" / "2026-10-15.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace('"n":1', '"n":9'), encoding="utf-8")

    report = log.verify()
    assert not report.ok
    assert any("seq 0" in error and "hash" in error for error in report.errors)


def test_verify_detects_a_forged_event_with_a_recomputed_hash(log, tmp_path):
    """Someone changes an event and recomputes its own hash: only the chain shows it."""
    log.append("agent.action", {"n": 1})
    log.append("agent.action", {"n": 2})
    path = tmp_path / "events" / "2026-10-15.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    forged = json.loads(lines[0])
    forged["payload"] = {"n": 9}
    forged["hash"] = event_hash({k: v for k, v in forged.items() if k != "hash"})
    path.write_text(json.dumps(forged) + "\n" + lines[1] + "\n", encoding="utf-8")

    report = log.verify()
    assert not report.ok
    assert any("seq 1" in error and "chain" in error for error in report.errors)


def test_verify_detects_a_removed_event(log, tmp_path):
    for n in range(3):
        log.append("agent.action", {"n": n})
    path = tmp_path / "events" / "2026-10-15.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text(lines[0] + lines[2], encoding="utf-8")

    report = log.verify()
    assert not report.ok
    assert any("seq" in error for error in report.errors)


def test_a_torn_last_line_is_kept_visible_and_logging_continues(log, tmp_path):
    first = log.append("agent.action", {"n": 1})
    path = tmp_path / "events" / "2026-10-15.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"seq": 1, "broken')  # simulated crash in the middle of a write

    nxt = log.append("agent.action", {"n": 2})

    events = log.events()
    assert [e["type"] for e in events] == ["agent.action", "error", "agent.action"]
    assert events[1]["intent"] == "log.torn_line"
    assert events[1]["prev"] == first["hash"]
    assert nxt["prev"] == events[1]["hash"]
    report = log.verify()
    assert not report.ok  # the damaged line stays visible
    assert len(report.errors) == 1 and "line 2" in report.errors[0]


def test_events_can_be_filtered_by_type_and_time(log, clock):
    log.append("agent.action", {"n": 1})
    clock.advance(days=1)
    log.append("budget.usage", {"n": 2})
    clock.advance(days=1)
    log.append("budget.usage", {"n": 3})

    start = datetime(2026, 10, 16, tzinfo=UTC)
    end = datetime(2026, 10, 17, tzinfo=UTC)
    found = list(log.iter_events(types={"budget.usage"}, start=start, end=end))
    assert [e["payload"]["n"] for e in found] == [2]


def test_reading_new_events_incrementally(log):
    log.append("agent.action", {"n": 1})
    cursor = log.cursor()
    first_batch = list(cursor.read_new())
    log.append("agent.action", {"n": 2})
    second_batch = list(cursor.read_new())

    assert [e["payload"]["n"] for e in first_batch] == [1]
    assert [e["payload"]["n"] for e in second_batch] == [2]
    assert list(cursor.read_new()) == []


def test_parallel_writers_do_not_collide(tmp_path, clock):
    def writer(name):
        log = EventLog(tmp_path / "events", source=name, clock=clock)
        for n in range(25):
            log.append("agent.action", {"n": n})

    threads = [threading.Thread(target=writer, args=(f"w{i}",)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    log = EventLog(tmp_path / "events", source="check", clock=clock)
    assert [e["seq"] for e in log.events()] == list(range(100))
    assert log.verify().ok


json_values = st.recursive(
    st.none() | st.booleans() | st.integers(-(10**6), 10**6) | st.text(max_size=20),
    lambda children: (
        st.lists(children, max_size=3) | st.dictionaries(st.sampled_from(["a", "b", "note", "n"]), children, max_size=3)
    ),
    max_leaves=8,
)


@settings(max_examples=40, deadline=None)
@given(
    payloads=st.lists(st.dictionaries(st.sampled_from(["a", "b", "note", "n"]), json_values, max_size=3), max_size=6)
)
def test_any_payloads_round_trip_and_verify(tmp_path_factory, payloads):
    log = EventLog(tmp_path_factory.mktemp("events"), source="prop", clock=FakeClock())
    for payload in payloads:
        log.append("agent.action", payload)

    assert [e["payload"] for e in log.events()] == payloads
    assert log.verify().ok


def test_log_files_are_only_readable_by_the_owner(log, tmp_path):
    log.append("agent.action", {})
    assert (tmp_path / "events").stat().st_mode & 0o777 == 0o700
    assert (tmp_path / "events" / "2026-10-15.jsonl").stat().st_mode & 0o777 == 0o600


def test_a_cursor_can_start_at_a_day(log, clock):
    log.append("agent.action", {"n": 1})
    clock.advance(days=1)
    log.append("agent.action", {"n": 2})
    assert [e["payload"]["n"] for e in log.cursor(since_day="2026-10-16").read_new()] == [2]


def test_without_anchors_a_shortened_log_looks_fine(log, tmp_path):
    """Documents the limit of a hash chain alone; anchors close the gap (next test)."""
    for n in range(3):
        log.append("agent.action", {"n": n})
    path = tmp_path / "events" / "2026-10-15.jsonl"
    path.write_text("".join(path.read_text(encoding="utf-8").splitlines(keepends=True)[:2]), encoding="utf-8")
    assert log.verify().ok


def test_anchors_reveal_a_shortened_log(log, tmp_path):
    for n in range(3):
        log.append("agent.action", {"n": n})
    anchor = log.head()
    assert anchor[0] == 2
    path = tmp_path / "events" / "2026-10-15.jsonl"
    path.write_text("".join(path.read_text(encoding="utf-8").splitlines(keepends=True)[:2]), encoding="utf-8")

    report = log.verify(anchors=[anchor])
    assert not report.ok
    assert "shortened" in report.errors[0]


def test_anchors_reveal_a_completely_rewritten_log(log, tmp_path, clock):
    log.append("agent.action", {"n": 1})
    anchor = log.head()
    (tmp_path / "events" / "2026-10-15.jsonl").unlink()
    log.append("agent.action", {"n": 666})  # a new, internally consistent chain

    assert log.verify().ok
    report = log.verify(anchors=[anchor])
    assert not report.ok
    assert "rewritten" in report.errors[0]


def test_head_of_an_empty_log(log):
    assert log.head() == (-1, GENESIS)
    assert log.verify(anchors=[log.head()]).ok


@settings(max_examples=100, deadline=None)
@given(data=st.dictionaries(st.text(max_size=8), json_values, max_size=6))
def test_the_hash_does_not_depend_on_key_order(data):
    """Determinism: the same event written with another key order must keep its hash."""
    reordered = dict(reversed(list(data.items())))
    assert event_hash(data) == event_hash(reordered)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nan_and_infinity_are_rejected(log, tmp_path, value):
    with pytest.raises(EventLogError):
        log.append("agent.decision", {}, latency_ms=value)
    with pytest.raises(EventLogError):
        log.append("agent.action", {"x": value})
    assert not (tmp_path / "events" / "2026-10-15.jsonl").exists()


def test_a_line_with_nan_counts_as_damaged(log, tmp_path):
    log.append("agent.action", {"n": 1})
    path = tmp_path / "events" / "2026-10-15.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"seq": 1, "x": NaN}\n')
    report = log.verify()
    assert not report.ok and "line 2" in report.errors[0]


def test_verify_can_start_after_removed_old_days(log, clock, tmp_path):
    first = log.append("agent.action", {"n": 1})
    clock.advance(days=1)
    log.append("agent.action", {"n": 2})
    (tmp_path / "events" / "2026-10-15.jsonl").unlink()  # retention removed the oldest day

    assert not log.verify().ok
    assert log.verify(start=(first["seq"] + 1, first["hash"])).ok


def test_a_cursor_does_not_skip_events_after_a_failing_one(log):
    for n in range(3):
        log.append("agent.action", {"n": n})
    cursor = log.cursor()
    seen: list[object] = []
    with pytest.raises(RuntimeError):
        for event in cursor.read_new():
            if event["payload"]["n"] == 1 and not seen.count("failed"):
                seen.append("failed")
                raise RuntimeError("handler crashed")
            seen.append(event["payload"]["n"])
    seen.extend(event["payload"]["n"] for event in cursor.read_new())
    assert seen == [0, "failed", 1, 2]


def test_events_written_with_schema_1_1_still_verify(log, tmp_path):
    """Schema 1.2 only adds types; logs from before the change must stay valid."""
    old = {
        "id": "00000000-0000-4000-8000-000000000001",
        "seq": 0,
        "ts": "2026-10-15T11:00:00.000Z",
        "source": "test",
        "type": "agent.action",
        "schema": "event/1.1",
        "payload": {},
        "prev": GENESIS,
    }
    old["hash"] = event_hash(old)
    directory = tmp_path / "events"
    directory.mkdir(exist_ok=True)
    (directory / "2026-10-15.jsonl").write_text(json.dumps(old) + "\n", encoding="utf-8")

    new = log.append("character.mood", {"faktor": "lob"})

    assert new["schema"] == "event/1.2"
    assert new["prev"] == old["hash"]
    assert log.verify().ok
