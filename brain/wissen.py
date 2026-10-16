"""Knowledge packs and their life cycle (Bauplan Lakehouse 1.2 and 1.3, Design Lakehouse 7).

A knowledge pack is one topic ("Kühlung", "Projekt Gehäuse", one of Marvin's interests): name,
summary, sections with their source, status and the marker "running project". The sections
are entries of the memory core (kind "abschnitt", tagged with the pack), so they share its
search, provenance, `pii` and deletion rules.

Life cycle (Marvin, 16.10.2026: fast by need, not by age):
- A pack becomes active when it is used. At most `max_aktiv` packs are active; the one unused
  longest goes back to rest. Running projects are never pushed out.
- After `ruhe_tage` days without use an active pack goes to long-term memory (status "ruhend")
  and gets a fresh summary from `kurzfassen`, if given. It stays searchable; nothing is deleted.
- A running project ends after `ruhe_tage` days without work on it.

Everything is an appended event; the current state of a pack is computed from its events.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from brain._sqlite import nur_anhaengen, oeffnen, version_pruefen
from brain.eventlog import format_ts, parse_ts

DB_VERSION = 1
MAX_AKTIV = 5  # Design Lakehouse 15 (assumption approved 16.10.2026)
RUHE_TAGE = 30
MAX_NAME = 80
ARTEN = ("aktiv", "ruhend", "genutzt", "projekt_an", "projekt_aus", "kurzfassung", "pii")
TAG_PREFIX = "paket:"

_SCHEMA = (
    """
CREATE TABLE IF NOT EXISTS pakete (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid TEXT NOT NULL UNIQUE,
    ts TEXT NOT NULL,
    name TEXT NOT NULL,
    pii INTEGER NOT NULL CHECK (pii IN (0, 1)),
    teilbar INTEGER NOT NULL CHECK (teilbar IN (0, 1)),
    herkunft TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS ereignisse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid TEXT NOT NULL REFERENCES pakete (pid),
    ts TEXT NOT NULL,
    art TEXT NOT NULL CHECK (art IN ('aktiv', 'ruhend', 'genutzt', 'projekt_an', 'projekt_aus', 'kurzfassung', 'pii')),
    wert TEXT,
    grund TEXT
) STRICT;
CREATE INDEX IF NOT EXISTS ereignisse_pid ON ereignisse (pid, art, id);
CREATE TABLE IF NOT EXISTS abschnitte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid TEXT NOT NULL REFERENCES pakete (pid),
    uid TEXT NOT NULL UNIQUE,
    ts TEXT NOT NULL
) STRICT;
CREATE INDEX IF NOT EXISTS abschnitte_pid ON abschnitte (pid, id);
"""
    + nur_anhaengen("pakete")
    + nur_anhaengen("ereignisse")
    + nur_anhaengen("abschnitte")
)


class WissenError(Exception):
    """A knowledge pack operation was rejected."""


@dataclass(frozen=True)
class Paket:
    pid: str
    name: str
    kurzfassung: str
    status: str  # "aktiv" or "ruhend"
    projekt: bool
    letzte_nutzung: str | None
    pii: bool
    teilbar: bool
    herkunft: str
    angelegt: str


@dataclass(frozen=True)
class Treffer:
    paket: Paket
    text: str
    quelle: str
    pii: bool
    uid: str
    score: float


def _utc_now():
    return datetime.now(UTC)


def _name(name):
    clean = (name or "").strip()
    if not clean or len(clean) > MAX_NAME or "\n" in clean or "\r" in clean:
        raise WissenError(f"Name muss einzeilig sein, 1 bis {MAX_NAME} Zeichen")
    return clean


class Wissen:
    def __init__(
        self,
        path,
        memory,
        log=None,
        clock=_utc_now,
        wait_s=5.0,
        *,
        max_aktiv=MAX_AKTIV,
        ruhe_tage=RUHE_TAGE,
        kurzfassen=None,
    ):
        self._memory = memory
        self._log = log
        self._clock = clock
        self._max_aktiv = max_aktiv
        self._ruhe = timedelta(days=ruhe_tage)
        self._kurzfassen = kurzfassen
        self._conn = oeffnen(path, wait_s)
        version = version_pruefen(self._conn, DB_VERSION, WissenError)
        self._conn.executescript(_SCHEMA)
        if version == 0:
            self._conn.execute(f"PRAGMA user_version = {DB_VERSION}")

    def close(self):
        self._conn.close()

    # --- helpers ---------------------------------------------------------------------

    def _now(self):
        return format_ts(self._clock())

    def _event(self, op, pid, pii, **extra):
        if self._log is not None:
            self._log.append("memory.write", {"paket": pid, **extra}, intent=f"wissen.{op}", pii=bool(pii))

    def _add(self, pid, art, wert=None, grund=None):
        self._conn.execute(
            "INSERT INTO ereignisse (pid, ts, art, wert, grund) VALUES (?, ?, ?, ?, ?)",
            (pid, self._now(), art, wert, grund),
        )

    def _row(self, pid):
        row = self._conn.execute("SELECT * FROM pakete WHERE pid = ?", (pid,)).fetchone()
        if row is None:
            raise WissenError(f"Paket {pid} unbekannt")
        return row

    def _last(self, pid, arten):
        placeholders = ",".join("?" * len(arten))
        return self._conn.execute(
            f"SELECT * FROM ereignisse WHERE pid = ? AND art IN ({placeholders}) ORDER BY id DESC LIMIT 1",
            (pid, *arten),
        ).fetchone()

    def _paket(self, row):
        pid = row["pid"]
        status = self._last(pid, ("aktiv", "ruhend"))
        projekt = self._last(pid, ("projekt_an", "projekt_aus"))
        kurz = self._last(pid, ("kurzfassung",))
        genutzt = self._last(pid, ("genutzt",))
        pii = bool(row["pii"]) or self._last(pid, ("pii",)) is not None
        return Paket(
            pid=pid,
            name=row["name"],
            kurzfassung=kurz["wert"] if kurz else "",
            status=status["art"] if status else "ruhend",
            projekt=projekt is not None and projekt["art"] == "projekt_an",
            letzte_nutzung=genutzt["ts"] if genutzt else None,
            pii=pii,
            teilbar=bool(row["teilbar"]),
            herkunft=row["herkunft"],
            angelegt=row["ts"],
        )

    def _alle(self):
        return [self._paket(row) for row in self._conn.execute("SELECT * FROM pakete ORDER BY id")]

    # --- packs and sections (1.2) -------------------------------------------------------

    def anlegen(self, name, *, kurzfassung="", pii=False, teilbar=False, herkunft="gehirn"):
        """New pack; it rests until it is used."""
        name = _name(name)
        pid = f"p-{uuid.uuid4().hex[:12]}"
        with self._conn:
            self._conn.execute(
                "INSERT INTO pakete (pid, ts, name, pii, teilbar, herkunft) VALUES (?, ?, ?, ?, ?, ?)",
                (pid, self._now(), name, int(bool(pii)), int(bool(teilbar)), herkunft),
            )
            if kurzfassung:
                self._add(pid, "kurzfassung", kurzfassung)
        self._event("anlegen", pid, pii)
        return pid

    def abschnitt(self, pid, text, *, quelle, pii=False, teilbar=False, tags=()):
        """Add a section to a pack; it is stored in the memory core and found by `suche`."""
        row = self._row(pid)
        uid = self._memory.remember(
            text,
            kind="abschnitt",
            source=quelle,
            tags=[f"{TAG_PREFIX}{pid}", *tags],
            pii=pii,
            shareable=teilbar,
        )
        with self._conn:
            self._conn.execute("INSERT INTO abschnitte (pid, uid, ts) VALUES (?, ?, ?)", (pid, uid, self._now()))
            if pii and not row["pii"] and self._last(pid, ("pii",)) is None:
                self._add(pid, "pii", grund="Abschnitt mit persönlichen Daten")
        return uid

    def abschnitte(self, pid, tag=None):
        """Texts of the visible sections of a pack, oldest first, optionally only those with `tag`.

        Found by the pack's tag in the memory core, so corrections (new entries with the same
        tags) take the place of the corrected text.
        """
        self._row(pid)
        hits = self._memory.mit_tag(f"{TAG_PREFIX}{pid}")
        return [hit.content for hit in hits if tag is None or tag in hit.tags]

    def paket(self, pid):
        return self._paket(self._row(pid))

    def aktive(self):
        """Active packs, most recently used first; only packs whose last status is "aktiv" are read."""
        rows = self._conn.execute(
            "SELECT p.* FROM pakete p WHERE (SELECT e.art FROM ereignisse e WHERE e.pid = p.pid"
            " AND e.art IN ('aktiv', 'ruhend') ORDER BY e.id DESC LIMIT 1) = 'aktiv'"
        ).fetchall()
        aktiv = [self._paket(row) for row in rows]
        return sorted(aktiv, key=lambda paket: paket.letzte_nutzung or "", reverse=True)

    def suche(self, text, limit=5, scope="marvin"):
        """Sections matching `text` from all packs, active or resting.

        Scope "guest" sees only sections of shareable packs without personal data.
        """
        hits = self._memory.recall(text, limit=limit * 3, scope=scope, kind="abschnitt")
        treffer = []
        for hit in hits:
            pid = next((tag[len(TAG_PREFIX) :] for tag in hit.tags if tag.startswith(TAG_PREFIX)), None)
            if pid is None:
                continue
            try:
                paket = self.paket(pid)
            except WissenError:
                continue
            if scope == "guest" and (paket.pii or not paket.teilbar):
                continue
            treffer.append(Treffer(paket, hit.content, hit.source, hit.pii, hit.uid, hit.score))
            if len(treffer) == limit:
                break
        return treffer

    # --- life cycle (1.3) ------------------------------------------------------------------

    def nutzen(self, pid, grund=None):
        """Mark a pack as used and active. Returns the packs pushed back to rest."""
        paket = self.paket(pid)
        with self._conn:
            self._add(pid, "genutzt", grund=grund)
            if paket.status != "aktiv":
                self._add(pid, "aktiv", grund=grund)
        if paket.status != "aktiv":
            self._event("aktiv", pid, paket.pii)
        return self._begrenzen(keep=pid)

    def _begrenzen(self, keep):
        verdraengt: list[str] = []
        aktiv = self.aktive()
        frei = [paket for paket in reversed(aktiv) if not paket.projekt and paket.pid != keep]
        while len(aktiv) - len(verdraengt) > self._max_aktiv and frei:
            paket = frei.pop(0)
            with self._conn:
                self._add(paket.pid, "ruhend", grund="verdrängt")
            self._event("ruhend", paket.pid, paket.pii, grund="verdrängt")
            verdraengt.append(paket.pid)
        return verdraengt

    def projekt(self, pid, an, *, grund):
        """Set or end the marker "running project". A running project is active and used."""
        paket = self.paket(pid)
        if paket.projekt == bool(an):
            return
        with self._conn:
            self._add(pid, "projekt_an" if an else "projekt_aus", grund=grund)
        self._event("projekt_an" if an else "projekt_aus", pid, paket.pii, grund=grund)
        if an:
            self.nutzen(pid, grund=grund)

    def pflege(self):
        """Daily care: end idle projects, send idle packs to rest. Returns the packs sent to rest."""
        grenze = self._clock() - self._ruhe
        ruhend = []
        for paket in self._alle():
            zuletzt = parse_ts(paket.letzte_nutzung) if paket.letzte_nutzung else parse_ts(paket.angelegt)
            if zuletzt > grenze:
                continue
            if paket.projekt:
                self.projekt(paket.pid, False, grund=f"{self._ruhe.days} Tage ohne Arbeit")
            if paket.status == "aktiv":
                self._ruhen(paket)
                ruhend.append(paket.pid)
        return ruhend

    def _ruhen(self, paket):
        neu = None
        if self._kurzfassen is not None:
            try:
                neu = self._kurzfassen(paket, self.abschnitte(paket.pid))
            except Exception as error:  # the model may fail; the pack rests anyway with its old summary
                self._event("kurzfassung_fehler", paket.pid, paket.pii, fehler=type(error).__name__)
        with self._conn:
            self._add(paket.pid, "ruhend", grund=f"{self._ruhe.days} Tage nicht genutzt")
            if neu and neu != paket.kurzfassung:
                self._add(paket.pid, "kurzfassung", neu)
        self._event("ruhend", paket.pid, paket.pii, grund="lange nicht genutzt")
