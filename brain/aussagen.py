"""Statements with evidence, trust, validity and status (Bauplan Wissen 1.1 and 1.2, Design Wissen S2).

A statement is subject, relation and object ("BMP280 – misst – Luftdruck"). The same statement
from ten sources is one statement with ten pieces of evidence. Each piece of evidence names its
source (a memory entry or a document) and its rating A to D (Bauplan Gehirn 10.4); trust grows
with independent evidence and better ratings.

Status: unbestätigt, bestätigt (by Marvin or a trusted module), umstritten (contradiction on a
single-valued relation with overlapping validity) or ersetzt (a newer statement took its place).
"umstritten" is computed on reading: it ends by itself when the other value is replaced or loses
its evidence, and Marvin's confirmation wins over it.
Validity: "gültig seit" and "gültig bis" as dates; nothing is deleted because it is out of date.

Removing a source (only after Marvin's approval elsewhere) drops its evidence so far; a statement
without evidence is no longer found. Evidence the source gives later counts again.
Everything is appended; the state is computed from events.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from brain._sqlite import nur_anhaengen, oeffnen, version_pruefen
from brain.eventlog import format_ts
from brain.memory import normalize_german

DB_VERSION = 1
STUFEN = {"A": 0.9, "B": 0.75, "C": 0.5, "D": 0.25}  # weight of one piece of evidence per rating
MAX_TEIL = 200
_SPACE = re.compile(r"\s+")
_STATUS = {"bestaetigt": "bestätigt", "ersetzt": "ersetzt"}

_SCHEMA = (
    """
CREATE TABLE IF NOT EXISTS aussagen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aid TEXT NOT NULL UNIQUE,
    ts TEXT NOT NULL,
    subjekt TEXT NOT NULL,
    beziehung TEXT NOT NULL,
    objekt TEXT NOT NULL,
    schluessel TEXT NOT NULL,
    n_subjekt TEXT NOT NULL,
    n_beziehung TEXT NOT NULL,
    n_objekt TEXT NOT NULL,
    text TEXT NOT NULL,
    gueltig_ab TEXT,
    gueltig_bis TEXT,
    eindeutig INTEGER NOT NULL CHECK (eindeutig IN (0, 1))
) STRICT;
CREATE INDEX IF NOT EXISTS aussagen_schluessel ON aussagen (schluessel);
CREATE INDEX IF NOT EXISTS aussagen_subjekt ON aussagen (n_subjekt, n_beziehung);
CREATE INDEX IF NOT EXISTS aussagen_objekt ON aussagen (n_objekt);
CREATE TABLE IF NOT EXISTS belege (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aid TEXT NOT NULL REFERENCES aussagen (aid),
    ts TEXT NOT NULL,
    quelle TEXT NOT NULL,
    stufe TEXT NOT NULL CHECK (stufe IN ('A', 'B', 'C', 'D')),
    pii INTEGER NOT NULL CHECK (pii IN (0, 1))
) STRICT;
CREATE INDEX IF NOT EXISTS belege_aid ON belege (aid);
CREATE INDEX IF NOT EXISTS belege_quelle ON belege (quelle);
CREATE TABLE IF NOT EXISTS ereignisse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aid TEXT NOT NULL REFERENCES aussagen (aid),
    ts TEXT NOT NULL,
    art TEXT NOT NULL CHECK (art IN ('bestaetigt', 'ersetzt', 'beleg_weg')),
    wert TEXT,
    grund TEXT NOT NULL
) STRICT;
CREATE INDEX IF NOT EXISTS ereignisse_aid ON ereignisse (aid, art);
"""
    + nur_anhaengen("aussagen")
    + nur_anhaengen("belege")
    + nur_anhaengen("ereignisse")
)


class AussagenError(Exception):
    """A statement or operation was rejected."""


@dataclass(frozen=True)
class Beleg:
    quelle: str
    stufe: str
    pii: bool
    ts: str


@dataclass(frozen=True)
class Aussage:
    aid: str
    subjekt: str
    beziehung: str
    objekt: str
    text: str
    status: str
    vertrauen: float
    belege: tuple
    pii: bool
    gueltig_ab: str | None
    gueltig_bis: str | None
    erfasst: str


def _utc_now():
    return datetime.now(UTC)


def _teil(name, value):
    clean = _SPACE.sub(" ", value or "").strip()
    if not clean or "\n" in (value or "") or "\r" in (value or "") or len(clean) > MAX_TEIL:
        raise AussagenError(f"{name} muss einzeilig sein, 1 bis {MAX_TEIL} Zeichen")
    return clean


def _datum(name, value):
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as error:
        raise AussagenError(f"{name} {value!r} ist kein Datum der Form JJJJ-MM-TT") from error


def _schluessel(*teile):
    return "|".join(_norm(teil) for teil in teile)


def _norm(teil):
    return normalize_german(teil)


def _ueberlappen(a_ab, a_bis, b_ab, b_bis):
    return (a_bis is None or b_ab is None or b_ab <= a_bis) and (b_bis is None or a_ab is None or a_ab <= b_bis)


class Aussagen:
    def __init__(self, path, log=None, clock=_utc_now, wait_s=5.0):
        self._log = log
        self._clock = clock
        self._conn = oeffnen(path, wait_s)
        version = version_pruefen(self._conn, DB_VERSION, AussagenError)
        self._conn.executescript(_SCHEMA)
        if version == 0:
            self._conn.execute(f"PRAGMA user_version = {DB_VERSION}")

    def close(self):
        self._conn.close()

    # --- helpers ---------------------------------------------------------------------

    def _now(self):
        return format_ts(self._clock())

    def _event(self, op, aid, pii, **extra):
        if self._log is not None:
            self._log.append("memory.write", {"aussage": aid, **extra}, intent=f"aussagen.{op}", pii=bool(pii))

    def _row(self, aid):
        row = self._conn.execute("SELECT * FROM aussagen WHERE aid = ?", (aid,)).fetchone()
        if row is None:
            raise AussagenError(f"Aussage {aid} unbekannt")
        return row

    def _beleg_zeilen(self, aid):
        """Evidence rows that were not removed (removal names the row, so later evidence counts)."""
        weg = {
            row["wert"]
            for row in self._conn.execute("SELECT wert FROM ereignisse WHERE aid = ? AND art = 'beleg_weg'", (aid,))
        }
        rows = self._conn.execute("SELECT * FROM belege WHERE aid = ? ORDER BY id", (aid,)).fetchall()
        return [r for r in rows if str(r["id"]) not in weg]

    def _belege(self, aid):
        return tuple(Beleg(r["quelle"], r["stufe"], bool(r["pii"]), r["ts"]) for r in self._beleg_zeilen(aid))

    def _entschieden(self, aid):
        """Last decision on a statement: "bestaetigt", "ersetzt" or None."""
        row = self._conn.execute(
            "SELECT art FROM ereignisse WHERE aid = ? AND art IN ('bestaetigt', 'ersetzt') ORDER BY id DESC LIMIT 1",
            (aid,),
        ).fetchone()
        return row["art"] if row else None

    def _umstritten(self, row):
        """Another value on a single-valued relation, with evidence and overlapping validity."""
        for other in self._conn.execute(
            "SELECT * FROM aussagen WHERE n_subjekt = ? AND n_beziehung = ? AND schluessel != ?",
            (row["n_subjekt"], row["n_beziehung"], row["schluessel"]),
        ).fetchall():
            if not (row["eindeutig"] or other["eindeutig"]) or self._entschieden(other["aid"]) == "ersetzt":
                continue
            if not self._beleg_zeilen(other["aid"]):
                continue
            if _ueberlappen(row["gueltig_ab"], row["gueltig_bis"], other["gueltig_ab"], other["gueltig_bis"]):
                return True
        return False

    def _status(self, row):
        entschieden = self._entschieden(row["aid"])
        if entschieden is not None:
            return _STATUS[entschieden]
        return "umstritten" if self._umstritten(row) else "unbestätigt"

    @staticmethod
    def _vertrauen(belege):
        """1 - product of (1 - weight) over independent sources; each source counts once, its best rating."""
        best: dict[str, float] = {}
        for beleg in belege:
            best[beleg.quelle] = max(best.get(beleg.quelle, 0.0), STUFEN[beleg.stufe])
        rest = 1.0
        for weight in best.values():
            rest *= 1.0 - weight
        return round(min(1.0 - rest, 0.99), 4)

    def _aussage(self, row):
        belege = self._belege(row["aid"])
        return Aussage(
            aid=row["aid"],
            subjekt=row["subjekt"],
            beziehung=row["beziehung"],
            objekt=row["objekt"],
            text=row["text"],
            status=self._status(row),
            vertrauen=self._vertrauen(belege),
            belege=belege,
            pii=any(beleg.pii for beleg in belege),
            gueltig_ab=row["gueltig_ab"],
            gueltig_bis=row["gueltig_bis"],
            erfasst=row["ts"],
        )

    def _mark(self, aid, art, grund, wert=None):
        self._conn.execute(
            "INSERT INTO ereignisse (aid, ts, art, wert, grund) VALUES (?, ?, ?, ?, ?)",
            (aid, self._now(), art, wert, grund),
        )

    # --- writing -------------------------------------------------------------------------

    def erfassen(
        self,
        subjekt,
        beziehung,
        objekt,
        *,
        quelle,
        stufe="C",
        text=None,
        pii=False,
        gueltig_ab=None,
        gueltig_bis=None,
        eindeutig=False,
    ):
        """Store a statement or add evidence to the same one. Returns its id."""
        subjekt, beziehung, objekt = _teil("Subjekt", subjekt), _teil("Beziehung", beziehung), _teil("Objekt", objekt)
        if not quelle or not str(quelle).strip():
            raise AussagenError("Quelle fehlt")
        if stufe not in STUFEN:
            raise AussagenError(f"Stufe {stufe!r}: erlaubt sind A, B, C, D")
        ab, bis = _datum("gültig seit", gueltig_ab), _datum("gültig bis", gueltig_bis)
        if ab and bis and bis < ab:
            raise AussagenError("„gültig bis“ liegt vor „gültig seit“")
        key = _schluessel(subjekt, beziehung, objekt)
        with self._conn:
            row = self._conn.execute(
                "SELECT * FROM aussagen WHERE schluessel = ? AND coalesce(gueltig_ab, '') = ?"
                " AND coalesce(gueltig_bis, '') = ? ORDER BY id DESC LIMIT 1",
                (key, ab or "", bis or ""),
            ).fetchone()
            if row is not None and self._entschieden(row["aid"]) != "ersetzt":
                aid = row["aid"]
            else:
                aid = f"a-{uuid.uuid4().hex[:12]}"
                self._conn.execute(
                    "INSERT INTO aussagen (aid, ts, subjekt, beziehung, objekt, schluessel, n_subjekt, n_beziehung,"
                    " n_objekt, text, gueltig_ab, gueltig_bis, eindeutig)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        aid,
                        self._now(),
                        subjekt,
                        beziehung,
                        objekt,
                        key,
                        _norm(subjekt),
                        _norm(beziehung),
                        _norm(objekt),
                        text or f"{subjekt} {beziehung} {objekt}",
                        ab,
                        bis,
                        int(bool(eindeutig)),
                    ),
                )
            best = max((STUFEN[b.stufe] for b in self._belege(aid) if b.quelle == quelle), default=None)
            if best is None or STUFEN[stufe] > best:  # new source, or a better rating from a known one
                self._conn.execute(
                    "INSERT INTO belege (aid, ts, quelle, stufe, pii) VALUES (?, ?, ?, ?, ?)",
                    (aid, self._now(), quelle, stufe, int(bool(pii))),
                )
        self._event("erfassen", aid, pii or self.aussage(aid).pii)
        return aid

    def bestaetigen(self, aid, *, grund):
        """Marvin (or a module marked as trusted) confirms the statement."""
        self._row(aid)
        with self._conn:
            self._mark(aid, "bestaetigt", grund)
        self._event("bestaetigen", aid, self.aussage(aid).pii)

    def ersetzen(self, alt, neu, *, grund):
        """A newer statement takes the place of an older one; the old one stays for the record."""
        self._row(alt)
        self._row(neu)
        if alt == neu:
            raise AussagenError("Eine Aussage kann sich nicht selbst ersetzen")
        with self._conn:
            self._mark(alt, "ersetzt", grund, wert=neu)
        self._event("ersetzen", alt, self.aussage(alt).pii, neu=neu)

    def quelle_entfernen(self, quelle, *, grund):
        """Drop all evidence of one source (after Marvin's approval). Returns the statements touched."""
        aids = [row["aid"] for row in self._conn.execute("SELECT DISTINCT aid FROM belege WHERE quelle = ?", (quelle,))]
        betroffen: dict[str, bool] = {}
        with self._conn:
            for aid in aids:
                for r in self._beleg_zeilen(aid):
                    if r["quelle"] == quelle:
                        self._mark(aid, "beleg_weg", grund, wert=str(r["id"]))
                        betroffen[aid] = betroffen.get(aid, False) or bool(r["pii"])
        for aid, pii in betroffen.items():
            self._event("quelle_entfernen", aid, pii)
        return list(betroffen)

    # --- reading ---------------------------------------------------------------------------

    def aussage(self, aid):
        return self._aussage(self._row(aid))

    def finden(self, *, subjekt=None, beziehung=None, objekt=None, am=None, mit_ersetzten=False):
        """Statements with evidence, filtered by parts (spelling-tolerant: case, umlauts, ß) and a date."""
        stichtag = _datum("Stichtag", am)
        where, params = [], []
        for name, value in (("subjekt", subjekt), ("beziehung", beziehung), ("objekt", objekt)):
            if value is not None:
                where.append(f"n_{name} = ?")
                params.append(_norm(_SPACE.sub(" ", value).strip()))
        sql = "SELECT * FROM aussagen" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY id"
        result = []
        for row in self._conn.execute(sql, params).fetchall():
            a = self._aussage(row)
            if not a.belege or (a.status == "ersetzt" and not mit_ersetzten):
                continue
            if stichtag and not (a.gueltig_ab or stichtag) <= stichtag <= (a.gueltig_bis or stichtag):
                continue
            result.append(a)
        return result
