"""Memory core: append-only SQLite store with provenance and full-text search.

Rules from the Memory Core and Bauplan Gehirn 10.2/10.2a:
- Entries are never changed. Corrections are new entries that replace the old one.
- Status changes (keep, archived, disputed, confirmed, replaced) are appended as marks.
- `forget` archives. Physical deletion needs Marvin's approval and is recorded
  (without content) in `deletion_approvals`; protected entries need an explicit override.
- Every entry carries source, rating A-D, confidence, origin (device or host), pii,
  shareable, contributor and trust (prepared for sharing knowledge in version 2).
- Search uses two FTS5 indexes, whole words and word parts (trigrams, for German
  compound words), merged with reciprocal rank fusion. Vector search joins later.
- Entries from other hosts wait in an inbox until they are accepted or rejected.
"""

import json
import os
import re
import sqlite3
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from brain.eventlog import format_ts
from brain.secrets_guard import find_secret, find_secret_in_text

SCHEMA_VERSION = "entry/1.0"
DB_VERSION = 1
RRF_K = 60
STATUS_MARKS = ("archived", "disputed", "confirmed", "replaced", "active")
_STATUS_SQL = (
    "COALESCE((SELECT m.mark FROM marks m WHERE m.uid = e.uid AND m.mark IN"
    " ('archived', 'disputed', 'confirmed', 'replaced', 'active') ORDER BY m.id DESC LIMIT 1), 'active')"
)
VISIBLE = ("active", "confirmed", "disputed")
SCOPES = ("marvin", "guest")
APPROVERS = ("marvin",)
_INBOX_FIELDS = {
    "content",
    "kind",
    "source",
    "source_rating",
    "confidence",
    "tags",
    "pii",
    "shareable",
    "contributor",
    "trust",
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    source_rating TEXT CHECK (source_rating IN ('A', 'B', 'C', 'D')),
    confidence REAL CHECK (confidence BETWEEN 0 AND 1),
    origin TEXT NOT NULL,
    pii INTEGER NOT NULL DEFAULT 0 CHECK (pii IN (0, 1)),
    shareable INTEGER NOT NULL DEFAULT 0 CHECK (shareable IN (0, 1)),
    contributor TEXT,
    trust REAL CHECK (trust BETWEEN 0 AND 1),
    tags TEXT NOT NULL DEFAULT '[]',
    replaces TEXT,
    search_text TEXT NOT NULL,
    schema_version TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL,
    ts TEXT NOT NULL,
    mark TEXT NOT NULL CHECK (mark IN ('keep', 'archived', 'disputed', 'confirmed', 'replaced', 'active')),
    reason TEXT
) STRICT;
CREATE INDEX IF NOT EXISTS marks_uid ON marks (uid);
CREATE TABLE IF NOT EXISTS deletion_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL,
    ts TEXT NOT NULL,
    reason TEXT NOT NULL,
    approved_by TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    origin TEXT NOT NULL,
    payload TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS inbox_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inbox_id INTEGER NOT NULL UNIQUE,
    ts TEXT NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('accepted', 'rejected')),
    uid TEXT,
    reason TEXT
) STRICT;
CREATE VIRTUAL TABLE IF NOT EXISTS entries_words USING fts5(
    search_text, content='entries', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS entries_no_replace BEFORE INSERT ON entries
WHEN EXISTS (SELECT 1 FROM entries WHERE uid = new.uid OR id = new.id)
BEGIN SELECT RAISE(ABORT, 'entries are append-only, no replace'); END;
CREATE TRIGGER IF NOT EXISTS marks_no_replace BEFORE INSERT ON marks
WHEN EXISTS (SELECT 1 FROM marks WHERE id = new.id)
BEGIN SELECT RAISE(ABORT, 'marks are append-only, no replace'); END;
CREATE TRIGGER IF NOT EXISTS approvals_no_replace BEFORE INSERT ON deletion_approvals
WHEN EXISTS (SELECT 1 FROM deletion_approvals WHERE id = new.id)
BEGIN SELECT RAISE(ABORT, 'deletion_approvals are append-only, no replace'); END;
CREATE TRIGGER IF NOT EXISTS inbox_no_replace BEFORE INSERT ON inbox
WHEN EXISTS (SELECT 1 FROM inbox WHERE id = new.id)
BEGIN SELECT RAISE(ABORT, 'inbox is append-only, no replace'); END;
CREATE TRIGGER IF NOT EXISTS inbox_results_no_replace BEFORE INSERT ON inbox_results
WHEN EXISTS (SELECT 1 FROM inbox_results WHERE id = new.id OR inbox_id = new.inbox_id)
BEGIN SELECT RAISE(ABORT, 'inbox_results are append-only, no replace'); END;
CREATE TRIGGER IF NOT EXISTS entries_no_update BEFORE UPDATE ON entries
BEGIN SELECT RAISE(ABORT, 'entries are append-only'); END;
CREATE TRIGGER IF NOT EXISTS entries_guarded_delete BEFORE DELETE ON entries
WHEN NOT EXISTS (SELECT 1 FROM deletion_approvals WHERE uid = old.uid)
BEGIN SELECT RAISE(ABORT, 'entries are append-only, deleting needs an approval'); END;
CREATE TRIGGER IF NOT EXISTS marks_no_update BEFORE UPDATE ON marks
BEGIN SELECT RAISE(ABORT, 'marks are append-only'); END;
CREATE TRIGGER IF NOT EXISTS marks_guarded_delete BEFORE DELETE ON marks
WHEN NOT EXISTS (SELECT 1 FROM deletion_approvals WHERE uid = old.uid)
BEGIN SELECT RAISE(ABORT, 'marks are append-only, deleting needs an approval'); END;
CREATE TRIGGER IF NOT EXISTS approvals_no_update BEFORE UPDATE ON deletion_approvals
BEGIN SELECT RAISE(ABORT, 'deletion_approvals are append-only'); END;
CREATE TRIGGER IF NOT EXISTS approvals_no_delete BEFORE DELETE ON deletion_approvals
BEGIN SELECT RAISE(ABORT, 'deletion_approvals are append-only'); END;
CREATE TRIGGER IF NOT EXISTS inbox_no_update BEFORE UPDATE ON inbox
BEGIN SELECT RAISE(ABORT, 'inbox is append-only'); END;
CREATE TRIGGER IF NOT EXISTS inbox_guarded_delete BEFORE DELETE ON inbox
WHEN NOT EXISTS (SELECT 1 FROM inbox_results WHERE inbox_id = old.id)
BEGIN SELECT RAISE(ABORT, 'inbox is append-only until an item is processed'); END;
CREATE TRIGGER IF NOT EXISTS inbox_results_no_update BEFORE UPDATE ON inbox_results
BEGIN SELECT RAISE(ABORT, 'inbox_results are append-only'); END;
CREATE TRIGGER IF NOT EXISTS inbox_results_no_delete BEFORE DELETE ON inbox_results
BEGIN SELECT RAISE(ABORT, 'inbox_results are append-only'); END;

CREATE TRIGGER IF NOT EXISTS entries_index_words AFTER INSERT ON entries BEGIN
    INSERT INTO entries_words (rowid, search_text) VALUES (new.id, new.search_text);
END;
CREATE TRIGGER IF NOT EXISTS entries_unindex_words AFTER DELETE ON entries BEGIN
    INSERT INTO entries_words (entries_words, rowid, search_text) VALUES ('delete', old.id, old.search_text);
END;
"""

# Trigram tables need SQLite 3.34; remove_diacritics for trigrams needs 3.45 (Debian 13 has 3.46).
_PARTS_TOKENIZER: str | None
if sqlite3.sqlite_version_info >= (3, 45, 0):
    _PARTS_TOKENIZER = "trigram remove_diacritics 1"
elif sqlite3.sqlite_version_info >= (3, 34, 0):
    _PARTS_TOKENIZER = "trigram"
else:
    _PARTS_TOKENIZER = None
_PARTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS entries_index_parts AFTER INSERT ON entries BEGIN
    INSERT INTO entries_parts (rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS entries_unindex_parts AFTER DELETE ON entries BEGIN
    INSERT INTO entries_parts (entries_parts, rowid, content) VALUES ('delete', old.id, old.content);
END;
"""


def normalize_german(text):
    """Spelling-tolerant form for the word index: case folded, ß as ss, umlauts as ae/oe/ue.

    "Straße" and "Strasse", "Kühlung" and "Kuehlung" become the same word. The word-part
    index keeps the original text (with diacritics folded), so "Kuhlung" is found as well.
    """
    folded = unicodedata.normalize("NFC", text).casefold()  # NFC joins decomposed umlauts, casefold turns ß into ss
    return folded.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")


class MemoryStoreError(Exception):
    """An entry or operation was rejected."""


@dataclass(frozen=True)
class Hit:
    uid: str
    content: str
    kind: str
    source: str
    source_rating: str
    confidence: float
    origin: str
    pii: bool
    shareable: bool
    contributor: str
    trust: float
    tags: list
    replaces: str
    schema_version: str
    ts: str
    status: str
    keep: bool
    score: float | None = None


def _utc_now():
    return datetime.now(UTC)


class Memory:
    def __init__(self, path, log=None, origin="gehirn", clock=_utc_now, wait_s=5.0):
        self._path = Path(path)
        if not self._path.exists():
            os.close(os.open(self._path, os.O_CREAT | os.O_RDWR, 0o600))  # only Schlaubi's account
        self._log = log
        self._origin = origin
        self._clock = clock
        self._conn = sqlite3.connect(self._path, timeout=wait_s)  # how long to wait for other readers/writers
        self._conn.row_factory = sqlite3.Row
        self._conn.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
        for pragma in (
            "journal_mode = WAL",  # with synchronous FULL: committed data survives a power loss
            "synchronous = FULL",
            "foreign_keys = ON",
            "secure_delete = ON",  # deleted content is overwritten, not just unlinked
            "recursive_triggers = ON",  # delete triggers also fire for REPLACE conflicts
            "trusted_schema = OFF",
        ):
            self._conn.execute(f"PRAGMA {pragma}")
        self._create_schema()

    def close(self):
        self._conn.close()

    def _create_schema(self):
        version = self._conn.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, DB_VERSION):
            raise MemoryStoreError(f"database version {version}, code expects {DB_VERSION}: a migration is needed")
        if _PARTS_TOKENIZER is None:
            raise MemoryStoreError(f"SQLite {sqlite3.sqlite_version} has no FTS5 trigram tokenizer (needs 3.34)")
        self._conn.executescript(
            _SCHEMA
            + "CREATE VIRTUAL TABLE IF NOT EXISTS entries_parts USING fts5("
            + f"content, content='entries', content_rowid='id', tokenize='{_PARTS_TOKENIZER}');"
            + _PARTS_TRIGGERS
        )
        if version == 0:
            self._conn.execute(f"PRAGMA user_version = {DB_VERSION}")

    # --- helpers --------------------------------------------------------------------

    def _now(self):
        return format_ts(self._clock())

    def _event(self, op, uid, pii=False, **extra):
        if self._log is not None:
            self._log.append("memory.write", {"op": op, "uid": uid, **extra}, intent=f"memory.{op}", pii=bool(pii))

    def _require(self, uid):
        row = self._conn.execute("SELECT * FROM entries WHERE uid = ?", (uid,)).fetchone()
        if row is None:
            raise MemoryStoreError(f"no entry {uid}")
        return row

    def _status(self, uid):
        placeholders = ",".join("?" * len(STATUS_MARKS))
        row = self._conn.execute(
            f"SELECT mark FROM marks WHERE uid = ? AND mark IN ({placeholders}) ORDER BY id DESC LIMIT 1",
            (uid, *STATUS_MARKS),
        ).fetchone()
        return row["mark"] if row else "active"

    def _keep(self, uid):
        return self._conn.execute("SELECT 1 FROM marks WHERE uid = ? AND mark = 'keep'", (uid,)).fetchone() is not None

    def _hit(self, row, score=None):
        return Hit(
            uid=row["uid"],
            content=row["content"],
            kind=row["kind"],
            source=row["source"],
            source_rating=row["source_rating"],
            confidence=row["confidence"],
            origin=row["origin"],
            pii=bool(row["pii"]),
            shareable=bool(row["shareable"]),
            contributor=row["contributor"],
            trust=row["trust"],
            tags=json.loads(row["tags"]),
            replaces=row["replaces"],
            schema_version=row["schema_version"],
            ts=row["ts"],
            status=self._status(row["uid"]),
            keep=self._keep(row["uid"]),
            score=score,
        )

    def _mark(self, uid, mark, reason=None):
        self._conn.execute(
            "INSERT INTO marks (uid, ts, mark, reason) VALUES (?, ?, ?, ?)", (uid, self._now(), mark, reason)
        )

    @staticmethod
    def _validate(content, kind, source, source_rating, confidence, trust, tags):
        if not isinstance(content, str) or not content.strip():
            raise MemoryStoreError("content must not be empty")
        if not isinstance(kind, str) or not kind.strip():
            raise MemoryStoreError("kind must not be empty")
        if not isinstance(source, str) or not source.strip():
            raise MemoryStoreError("source must not be empty")
        if source_rating is not None and source_rating not in ("A", "B", "C", "D"):
            raise MemoryStoreError("source_rating must be A, B, C or D")
        for name, value in (("confidence", confidence), ("trust", trust)):
            if value is not None and not 0 <= value <= 1:
                raise MemoryStoreError(f"{name} must be between 0 and 1")
        secret = find_secret_in_text(content) or find_secret({"source": source, "tags": tags})
        if secret:
            raise MemoryStoreError(f"secret detected, entry not stored ({secret})")

    def _insert(
        self,
        content,
        kind,
        source,
        source_rating=None,
        confidence=None,
        tags=None,
        pii=False,
        shareable=False,
        contributor=None,
        trust=None,
        origin=None,
        replaces=None,
    ):
        tags = list(tags or [])
        self._validate(content, kind, source, source_rating, confidence, trust, tags)
        uid = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO entries (uid, ts, kind, content, source, source_rating, confidence, origin, pii,"
            " shareable, contributor, trust, tags, replaces, search_text, schema_version)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                uid,
                self._now(),
                kind.strip(),
                content.strip(),
                source.strip(),
                source_rating,
                confidence,
                origin or self._origin,
                int(bool(pii)),
                int(bool(shareable)),
                contributor,
                trust,
                json.dumps(tags, ensure_ascii=False),
                replaces,
                normalize_german(content) + "\n" + normalize_german(" ".join(map(str, tags))),
                SCHEMA_VERSION,
            ),
        )
        return uid

    # --- writing ----------------------------------------------------------------------

    def remember(
        self,
        content,
        *,
        kind,
        source,
        source_rating=None,
        confidence=None,
        tags=None,
        pii=False,
        shareable=False,
        contributor=None,
        trust=None,
        origin=None,
    ):
        """Store a new entry and return its uid."""
        with self._conn:
            uid = self._insert(
                content, kind, source, source_rating, confidence, tags, pii, shareable, contributor, trust, origin
            )
        self._event("remember", uid, pii, kind=kind)
        return uid

    def correct(self, uid, content, *, source, **changes):
        """Store a corrected version as a new entry; the old one is marked as replaced.

        Kind, tags, pii and shareable describe the topic and are taken over. Rating, confidence,
        contributor and trust describe the old source and are not: the correction has its own."""
        old = self._require(uid)
        fields = {
            "kind": old["kind"],
            "tags": json.loads(old["tags"]),
            "pii": bool(old["pii"]),
            "shareable": bool(old["shareable"]),
        }
        fields.update(changes)
        with self._conn:
            new_uid = self._insert(content, source=source, replaces=uid, **fields)
            self._mark(uid, "replaced", f"replaced by {new_uid}")
            if self._keep(uid):
                self._mark(new_uid, "keep", f"merken taken over from {uid}")
        self._event("correct", new_uid, fields["pii"], replaces=uid)
        return new_uid

    def keep(self, uid):
        """Marvin said "merken": protect the entry from deadlines and deletion."""
        row = self._require(uid)
        with self._conn:
            self._mark(uid, "keep")
        self._event("keep", uid, row["pii"])

    def forget(self, uid, reason):
        """Archive an entry. It stays stored and can be found with include_archived."""
        row = self._require(uid)
        with self._conn:
            self._mark(uid, "archived", reason)
        self._event("forget", uid, row["pii"])

    def restore(self, uid, reason):
        row = self._require(uid)
        with self._conn:
            self._mark(uid, "active", reason)
        self._event("restore", uid, row["pii"])

    def dispute(self, uid_a, uid_b, reason):
        """Two entries contradict each other: keep both, mark both as disputed."""
        rows = [self._require(uid_a), self._require(uid_b)]
        with self._conn:
            self._mark(uid_a, "disputed", f"{reason} ({uid_b})")
            self._mark(uid_b, "disputed", f"{reason} ({uid_a})")
        for row in rows:
            self._event("dispute", row["uid"], row["pii"])

    def confirm(self, uid, reason):
        row = self._require(uid)
        with self._conn:
            self._mark(uid, "confirmed", reason)
        self._event("confirm", uid, row["pii"])

    def delete(self, uid, *, reason, approved_by, override_keep=False):
        """Physically delete an entry. Only with Marvin's approval; protected entries need override_keep."""
        if approved_by not in APPROVERS:
            raise MemoryStoreError("deleting needs Marvin's approval (approved_by='marvin')")
        row = self._require(uid)
        if self._keep(uid) and not override_keep:
            raise MemoryStoreError("entry is marked keep; deleting it needs override_keep=True")
        with self._conn:
            self._conn.execute(
                "INSERT INTO deletion_approvals (uid, ts, reason, approved_by) VALUES (?, ?, ?, ?)",
                (uid, self._now(), reason, approved_by),
            )
            self._conn.execute("DELETE FROM marks WHERE uid = ?", (uid,))
            self._conn.execute("DELETE FROM entries WHERE uid = ?", (uid,))
        self._event("delete", uid, row["pii"], approved_by=approved_by)
        flushed = self._compact()
        self._event("compact", uid, row["pii"], wal_flushed=flushed)
        return {"wal_flushed": flushed}

    def _compact(self):
        """Merge index segments so deleted terms do not linger, then write the WAL into the database
        and empty it. Returns False if another reader kept old pages alive (try again later)."""
        try:
            for table in ("entries_words", "entries_parts"):
                with self._conn:
                    self._conn.execute(f"INSERT INTO {table} ({table}) VALUES ('optimize')")
            busy, _log_pages, _done = self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        except sqlite3.OperationalError:
            return False
        return busy == 0

    # --- inbox (entries from other hosts, version 2 prepared) ---------------------------------------

    def enqueue(self, payload, origin):
        if not isinstance(payload, dict):
            raise MemoryStoreError("payload must be an object")
        secret = find_secret(payload)
        if secret:
            raise MemoryStoreError(f"secret detected, item not stored ({secret})")
        with self._conn:
            cursor = self._conn.execute(
                "INSERT INTO inbox (ts, origin, payload) VALUES (?, ?, ?)",
                (self._now(), origin, json.dumps(payload, ensure_ascii=False)),
            )
        item = cursor.lastrowid
        self._event("enqueue", f"inbox:{item}", payload.get("pii", False), origin=origin)
        return item

    def pending(self):
        rows = self._conn.execute("SELECT id, ts, origin, payload FROM inbox ORDER BY id").fetchall()
        return [
            {"id": r["id"], "ts": r["ts"], "origin": r["origin"], "payload": json.loads(r["payload"])} for r in rows
        ]

    def _inbox_item(self, item):
        row = self._conn.execute("SELECT * FROM inbox WHERE id = ?", (item,)).fetchone()
        if row is None:
            raise MemoryStoreError(f"no pending inbox item {item}")
        return row

    def accept(self, item):
        row = self._inbox_item(item)
        payload = json.loads(row["payload"])
        unknown = set(payload) - _INBOX_FIELDS
        if unknown:
            raise MemoryStoreError(f"unknown fields {sorted(unknown)}")
        if "content" not in payload or "kind" not in payload or "source" not in payload:
            raise MemoryStoreError("content, kind and source are required")
        with self._conn:
            uid = self._insert(origin=row["origin"], **payload)
            self._conn.execute(
                "INSERT INTO inbox_results (inbox_id, ts, result, uid) VALUES (?, ?, 'accepted', ?)",
                (item, self._now(), uid),
            )
            self._conn.execute("DELETE FROM inbox WHERE id = ?", (item,))
        self._event("accept", uid, payload.get("pii", False), origin=row["origin"])
        return uid

    def reject(self, item, reason):
        row = self._inbox_item(item)
        with self._conn:
            self._conn.execute(
                "INSERT INTO inbox_results (inbox_id, ts, result, reason) VALUES (?, ?, 'rejected', ?)",
                (item, self._now(), reason),
            )
            self._conn.execute("DELETE FROM inbox WHERE id = ?", (item,))
        self._event("reject", f"inbox:{item}", False, origin=row["origin"])

    # --- reading ------------------------------------------------------------------------

    def get(self, uid):
        row = self._conn.execute("SELECT * FROM entries WHERE uid = ?", (uid,)).fetchone()
        return self._hit(row) if row else None

    def deletions(self):
        rows = self._conn.execute("SELECT uid, ts, reason, approved_by FROM deletion_approvals ORDER BY id")
        return [dict(row) for row in rows]

    def _ranked(self, table, query, limit, where, params):
        """Ids of matching entries, best first. Scope, kind and status are filtered inside the
        query, so hidden entries can never push visible ones out of the candidate list."""
        try:
            rows = self._conn.execute(
                f"SELECT e.id AS id FROM {table} JOIN entries e ON e.id = {table}.rowid"
                f" WHERE {table} MATCH ?{where} ORDER BY bm25({table}) LIMIT ?",
                (query, *params, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []  # a query the tokenizer reduces to nothing
        return [row["id"] for row in rows]

    def recall(self, query, limit=5, scope="marvin", include_archived=False, kind=None, exclude_kind=None):
        """Find entries for a free-text query. Scope "guest" sees only shareable entries without pii."""
        if scope not in SCOPES:
            raise MemoryStoreError(f"unknown scope {scope!r}")
        terms = re.findall(r"\w+", query or "")
        if not terms:
            return []
        candidates = max(50, limit * 10)
        where, params = "", []
        if scope == "guest":
            where += " AND e.pii = 0 AND e.shareable = 1"
        if kind:
            where += " AND e.kind = ?"
            params.append(kind)
        if exclude_kind:
            where += " AND e.kind != ?"
            params.append(exclude_kind)
        if not include_archived:
            visible = ", ".join(f"'{status}'" for status in VISIBLE)
            where += f" AND {_STATUS_SQL} IN ({visible})"
        word_terms = re.findall(r"\w+", normalize_german(query))
        word_query = " OR ".join(f'"{t}"*' if len(t) >= 4 else f'"{t}"' for t in word_terms)
        rankings = [self._ranked("entries_words", word_query, candidates, where, params)]
        part_terms = [t for t in terms if len(t) >= 3]
        if part_terms:
            part_query = " OR ".join(f'"{t}"' for t in part_terms)
            rankings.append(self._ranked("entries_parts", part_query, candidates, where, params))

        scores: dict[int, float] = {}
        for ranking in rankings:
            for position, rowid in enumerate(ranking, start=1):
                scores[rowid] = scores.get(rowid, 0.0) + 1.0 / (RRF_K + position)

        hits = []
        for rowid, score in sorted(scores.items(), key=lambda item: (-item[1], -item[0]))[:limit]:
            row = self._conn.execute("SELECT * FROM entries WHERE id = ?", (rowid,)).fetchone()
            hits.append(self._hit(row, score))
        return hits

    def mit_tag(self, tag, include_archived=False):
        """Entries carrying `tag`, oldest first; replaced and (by default) archived ones are left out."""
        statuses = VISIBLE + (("archived",) if include_archived else ())
        allowed = ", ".join(f"'{status}'" for status in statuses)
        rows = self._conn.execute(
            "SELECT e.* FROM entries e WHERE EXISTS (SELECT 1 FROM json_each(e.tags) WHERE value = ?)"
            f" AND {_STATUS_SQL} IN ({allowed}) ORDER BY e.id",
            (tag,),
        ).fetchall()
        return [self._hit(row) for row in rows]

    def merkliste(self, limit=50):
        """Visible entries Marvin asked to keep ("merken"), newest first (Design Lakehouse 5)."""
        visible = ", ".join(f"'{status}'" for status in VISIBLE)
        rows = self._conn.execute(
            "SELECT e.* FROM entries e WHERE EXISTS (SELECT 1 FROM marks m WHERE m.uid = e.uid AND m.mark = 'keep')"
            f" AND {_STATUS_SQL} IN ({visible}) ORDER BY e.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._hit(row) for row in rows]

    # --- maintenance --------------------------------------------------------------------

    def check(self):
        """Daily database check (Bauplan 14.1): SQLite integrity and both search indexes."""
        integrity = self._conn.execute("PRAGMA integrity_check").fetchone()[0]
        fts = "ok"
        for table in ("entries_words", "entries_parts"):
            try:
                with self._conn:  # the check is written as an INSERT; end its transaction again
                    self._conn.execute(f"INSERT INTO {table} ({table}, rank) VALUES ('integrity-check', 1)")
            except sqlite3.DatabaseError as error:
                fts = f"{table}: {error}"
        return {"integrity": integrity, "fts": fts}
