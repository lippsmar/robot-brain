"""Catalog of all data sets in the lakehouse (Bauplan Lakehouse 1.1, Design Lakehouse 10).

One row per version of a data set: where it lies, format, schema version, time span, count,
checksum, personal data (`pii`) and retention. Rows are only added; the newest row of a data
set is its current state, so the history of every data set stays visible. The data lake
manifest is the first source of entries; documents and knowledge packs follow.
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from brain._sqlite import nur_anhaengen, oeffnen, version_pruefen
from brain.eventlog import format_ts

DB_VERSION = 1
_FRIST = re.compile(r"immer|\d{1,4} (Tage|Monate|Jahre)")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS eintraege (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    datensatz TEXT NOT NULL CHECK (length(datensatz) > 0),
    ort TEXT NOT NULL,
    format TEXT NOT NULL CHECK (length(format) > 0),
    schema_version TEXT,
    von TEXT,
    bis TEXT,
    anzahl INTEGER NOT NULL CHECK (anzahl >= 0),
    pruefsumme TEXT,
    pii INTEGER NOT NULL CHECK (pii IN (0, 1)),
    frist TEXT NOT NULL
) STRICT;
CREATE INDEX IF NOT EXISTS eintraege_datensatz ON eintraege (datensatz, id);
""" + nur_anhaengen("eintraege")


class KatalogError(Exception):
    """A catalog entry or query was rejected."""


@dataclass(frozen=True)
class Eintrag:
    datensatz: str
    ort: str
    format: str
    schema_version: str | None
    von: str | None
    bis: str | None
    anzahl: int
    pruefsumme: str | None
    pii: bool
    frist: str
    ts: str


def pruefsumme_datei(path, chunk=1024 * 1024):
    """SHA-256 of a file, read in pieces so large files need little memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as datei:
        while block := datei.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def _utc_now():
    return datetime.now(UTC)


class Katalog:
    def __init__(self, path, log=None, clock=_utc_now, wait_s=5.0):
        self._log = log
        self._clock = clock
        self._conn = oeffnen(path, wait_s)
        version = version_pruefen(self._conn, DB_VERSION, KatalogError)
        self._conn.executescript(_SCHEMA)
        if version == 0:
            self._conn.execute(f"PRAGMA user_version = {DB_VERSION}")

    def close(self):
        self._conn.close()

    def eintragen(
        self,
        datensatz,
        *,
        ort,
        format,
        anzahl,
        pruefsumme=None,
        pii=False,
        frist="immer",
        schema_version=None,
        von=None,
        bis=None,
    ):
        """Add a new version of a data set."""
        for feld in (datensatz, ort, format):
            if not feld or "\n" in feld or "\r" in feld:
                raise KatalogError("Datensatz, Ort und Format müssen einzeilig und nicht leer sein")
        if isinstance(anzahl, bool) or not isinstance(anzahl, int) or anzahl < 0:
            raise KatalogError(f"Anzahl {anzahl!r} ist keine Zahl ab 0")
        if not _FRIST.fullmatch(frist):
            raise KatalogError(f"Frist {frist!r}: erlaubt sind 'immer' oder z. B. '90 Tage'")
        ts = format_ts(self._clock())
        with self._conn:
            self._conn.execute(
                "INSERT INTO eintraege (ts, datensatz, ort, format, schema_version, von, bis, anzahl,"
                " pruefsumme, pii, frist) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ts, datensatz, ort, format, schema_version, von, bis, anzahl, pruefsumme, int(bool(pii)), frist),
            )
        if self._log is not None:
            self._log.append(
                "memory.write",
                {"datensatz": datensatz, "anzahl": anzahl},
                intent="katalog.eintragen",
                pii=bool(pii),
            )

    @staticmethod
    def _eintrag(row):
        return Eintrag(
            datensatz=row["datensatz"],
            ort=row["ort"],
            format=row["format"],
            schema_version=row["schema_version"],
            von=row["von"],
            bis=row["bis"],
            anzahl=row["anzahl"],
            pruefsumme=row["pruefsumme"],
            pii=bool(row["pii"]),
            frist=row["frist"],
            ts=row["ts"],
        )

    def aktuell(self, datensatz):
        row = self._conn.execute(
            "SELECT * FROM eintraege WHERE datensatz = ? ORDER BY id DESC LIMIT 1", (datensatz,)
        ).fetchone()
        return None if row is None else self._eintrag(row)

    def alle(self):
        """The current version of every data set, sorted by name."""
        rows = self._conn.execute(
            "SELECT * FROM eintraege WHERE id IN (SELECT MAX(id) FROM eintraege GROUP BY datensatz) ORDER BY datensatz"
        ).fetchall()
        return [self._eintrag(row) for row in rows]

    def pruefen(self, datensatz, pruefsumme):
        """True if the stored checksum of the current version matches.

        A data set stored without checksum, or a missing checksum to compare, cannot be checked:
        that is an error, never a silent "ok".
        """
        eintrag = self.aktuell(datensatz)
        if eintrag is None:
            raise KatalogError(f"Datensatz {datensatz!r} ist nicht im Katalog")
        if eintrag.pruefsumme is None or pruefsumme is None:
            raise KatalogError(f"Datensatz {datensatz!r}: keine Prüfsumme zum Vergleichen")
        return eintrag.pruefsumme == pruefsumme

    def datalake_eintragen(self, lake, *, ort):
        """One entry per data lake channel, from its manifest (Design Lakehouse 10).

        A channel that has not changed since its last entry gets no new version.
        """
        for teil in lake.manifest():
            alt = self.aktuell(f"datalake:{teil.name}")
            if alt is not None and (alt.ort, alt.anzahl, alt.pii, alt.von, alt.bis) == (
                ort,
                teil.count,
                teil.pii_count > 0,
                teil.first,
                teil.last,
            ):
                continue
            self.eintragen(
                f"datalake:{teil.name}",
                ort=ort,
                format="sqlite",
                anzahl=teil.count,
                pii=teil.pii_count > 0,
                von=teil.first,
                bis=teil.last,
            )
