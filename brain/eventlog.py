"""Append-only event log: one JSONL file per UTC day, sequence numbers and a SHA-256 hash chain.

Every event carries the hash of the event before it (`prev`) and its own hash over all
other fields (`hash`). `verify()` walks the chain, so an edited, removed or inserted
line is detected. Damaged lines are never repaired or removed; they stay visible.
Several processes may write to the same directory; a file lock serialises appends.
"""

import fcntl
import hashlib
import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from brain.schema import load_schema, validate
from brain.secrets_guard import find_secret

SCHEMA_ID = "event/1.1"
GENESIS = "0" * 64
DEFAULT_SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "event.schema.json"
_OPTIONAL_FIELDS = ("device_id", "intent", "result", "latency_ms", "confidence", "pii")
_TAIL_CHUNK = 64 * 1024


class EventLogError(Exception):
    """An event was rejected (invalid, contains a secret) or the log cannot be written."""


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def event_hash(event_without_hash):
    return hashlib.sha256(canonical(event_without_hash)).hexdigest()


def format_ts(moment):
    moment = moment.astimezone(UTC)
    return f"{moment:%Y-%m-%dT%H:%M:%S}.{moment.microsecond // 1000:03d}Z"


def parse_ts(text):
    return datetime.fromisoformat(text)


def _utc_now():
    return datetime.now(UTC)


@dataclass
class VerifyReport:
    ok: bool
    count: int
    errors: list = field(default_factory=list)


class Cursor:
    """Reads events that were appended since the last call, across files and processes."""

    def __init__(self, directory, since_day=None):
        self._directory = Path(directory)
        self._since_day = since_day
        self._offsets = {}

    def read_new(self):
        for path in sorted(self._directory.glob("*.jsonl")):
            if self._since_day and path.stem < self._since_day:
                continue
            offset = self._offsets.get(path.name, 0)
            with path.open("rb") as handle:
                handle.seek(offset)
                data = handle.read()
            end = data.rfind(b"\n")
            if end < 0:
                continue
            self._offsets[path.name] = offset + end + 1
            for line in data[: end + 1].splitlines():
                event = _parse(line)
                if event is not None:
                    yield event


def _parse(line):
    try:
        event = json.loads(line)
    except (ValueError, UnicodeDecodeError):
        return None
    return event if isinstance(event, dict) else None


class EventLog:
    def __init__(self, directory, source, schema_path=DEFAULT_SCHEMA, clock=_utc_now):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.directory.chmod(0o700)  # events can contain personal data: only Schlaubi's account
        self.source = source
        self._schema = load_schema(schema_path)
        self._clock = clock
        self._thread_lock = threading.Lock()

    # --- writing ----------------------------------------------------------------------

    def append(self, type, payload=None, **fields):
        unknown = set(fields) - set(_OPTIONAL_FIELDS)
        if unknown:
            raise EventLogError(f"unknown fields {sorted(unknown)}")
        payload = {} if payload is None else payload
        secret = find_secret(
            {"payload": payload, "intent": fields.get("intent", ""), "result": fields.get("result", "")}
        )
        if secret:
            raise EventLogError(f"secret detected, event not written ({secret})")

        with self._thread_lock, self._file_lock():
            last_seq, last_hash = self._repair_tail_marker()
            event = self._build(type, payload, fields, last_seq + 1, last_hash)
            self._write(event)
        return event

    def _build(self, type, payload, fields, seq, prev):
        moment = self._clock()
        event = {
            "id": str(uuid.uuid4()),
            "seq": seq,
            "ts": format_ts(moment),
            "source": self.source,
            "type": type,
            "payload": payload,
            "schema": SCHEMA_ID,
            "prev": prev,
        }
        for name in _OPTIONAL_FIELDS:
            if fields.get(name) is not None:
                event[name] = fields[name]
        event["hash"] = event_hash(event)
        errors = validate(event, self._schema)
        if errors:
            raise EventLogError("; ".join(errors))
        return event

    def _write(self, event):
        path = self.directory / f"{event['ts'][:10]}.jsonl"
        line = canonical(event) + b"\n"
        with _open_private(path) as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

    def _file_lock(self):
        return _FileLock(self.directory / ".lock")

    def _repair_tail_marker(self):
        """Return (seq, hash) of the last valid event. A torn last line (crash during a
        write) is closed with a newline and reported with an `error` event; it is not removed."""
        files = sorted(self.directory.glob("*.jsonl"))
        last_seq, last_hash = -1, GENESIS
        for path in reversed(files):
            found = _last_valid_event(path)
            if found:
                last_seq, last_hash = found["seq"], found["hash"]
                break
        if files and _ends_torn(files[-1]):
            torn_file = files[-1]
            line_number = _count_lines(torn_file) + 1
            with torn_file.open("ab") as handle:
                handle.write(b"\n")
                handle.flush()
                os.fsync(handle.fileno())
            notice = self._build(
                "error",
                {"file": torn_file.name, "line": line_number},
                {"intent": "log.torn_line", "result": "line kept, logging continues"},
                last_seq + 1,
                last_hash,
            )
            self._write(notice)
            last_seq, last_hash = notice["seq"], notice["hash"]
        return last_seq, last_hash

    # --- reading ----------------------------------------------------------------------

    def cursor(self, since_day=None):
        """Incremental reader; `since_day` (YYYY-MM-DD) skips older files."""
        return Cursor(self.directory, since_day)

    def iter_events(self, types=None, start=None, end=None):
        """Yield valid events in file order, optionally filtered by type and time [start, end)."""
        first_day = start.astimezone(UTC).date().isoformat() if start else None
        last_day = end.astimezone(UTC).date().isoformat() if end else None
        for path in sorted(self.directory.glob("*.jsonl")):
            day = path.stem
            if (first_day and day < first_day) or (last_day and day > last_day):
                continue
            with path.open("rb") as handle:
                for line in handle:
                    event = _parse(line)
                    if event is None:
                        continue
                    if types and event.get("type") not in types:
                        continue
                    if start or end:
                        moment = parse_ts(event["ts"])
                        if (start and moment < start) or (end and moment >= end):
                            continue
                    yield event

    def events(self):
        return list(self.iter_events())

    def verify(self):
        """Check every line: valid JSON, schema, own hash, link to the previous event, sequence."""
        errors = []
        count = 0
        expected_seq, expected_prev = 0, GENESIS
        for path in sorted(self.directory.glob("*.jsonl")):
            with path.open("rb") as handle:
                for number, line in enumerate(handle, start=1):
                    where = f"{path.name} line {number}"
                    event = _parse(line)
                    if event is None:
                        errors.append(f"{where}: not a valid JSON event")
                        continue
                    count += 1
                    seq = event.get("seq")
                    problems = validate(event, self._schema)
                    if problems:
                        errors.append(f"{where} (seq {seq}): schema: {'; '.join(problems)}")
                    if event.get("hash") != event_hash({k: v for k, v in event.items() if k != "hash"}):
                        errors.append(f"{where} (seq {seq}): hash does not match the content")
                    if seq != expected_seq:
                        errors.append(f"{where}: seq {seq}, expected {expected_seq}")
                    if event.get("prev") != expected_prev:
                        errors.append(f"{where} (seq {seq}): chain broken, prev does not match")
                    if isinstance(seq, int):
                        expected_seq = seq + 1
                    expected_prev = event.get("hash", "")
        return VerifyReport(ok=not errors, count=count, errors=errors)


class _FileLock:
    """Exclusive lock across processes (flock on a lock file in the log directory)."""

    def __init__(self, path):
        self._path = path
        self._handle = None

    def __enter__(self):
        self._handle = _open_private(self._path)
        fcntl.flock(self._handle, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._handle, fcntl.LOCK_UN)
        self._handle.close()


def _open_private(path):
    """Open for appending; a new file is readable and writable only by the owner."""
    return os.fdopen(os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600), "ab")


def _ends_torn(path):
    size = path.stat().st_size
    if size == 0:
        return False
    with path.open("rb") as handle:
        handle.seek(size - 1)
        return handle.read(1) != b"\n"


def _count_lines(path):
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(_TAIL_CHUNK), b""))


def _last_valid_event(path):
    """Read the file backwards in chunks and return the last parseable event, or None."""
    size = path.stat().st_size
    with path.open("rb") as handle:
        position = size
        rest = b""
        while position > 0:
            step = min(_TAIL_CHUNK, position)
            position -= step
            handle.seek(position)
            data = handle.read(step) + rest
            lines = data.split(b"\n")
            # the first piece may be cut in the middle unless we reached the file start
            rest = lines[0] if position > 0 else b""
            candidates = lines[1:] if position > 0 else lines
            for line in reversed(candidates):
                event = _parse(line) if line.strip() else None
                if event is not None and "seq" in event and "hash" in event:
                    return event
    return None
