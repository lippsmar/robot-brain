"""Document store of the lakehouse (Bauplan Lakehouse 1.5, Design Lakehouse 10).

Originals are kept unchanged under `<root>/dokumente/YYYY/MM/`, named after their checksum, with
a metadata file next to them (source, time, `pii`, licence or robots.txt status, checksum, size)
and an entry in the catalog. The same document is stored only once. Its text can go into a
knowledge pack as sections. Runtime data never lies in the code repository (CLAUDE.md §3).
"""

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from brain.eventlog import format_ts

REPO = Path(__file__).resolve().parents[1]
MAX_NAME = 80
MAX_ZEICHEN = 1000
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")
_SATZ = re.compile(r"(?<=[.!?])\s+")


class AblageError(Exception):
    """The document store was used in a way that is not allowed."""


@dataclass(frozen=True)
class Dokument:
    pfad: Path
    pruefsumme: str
    neu: bool


def _utc_now():
    return datetime.now(UTC)


def _sicherer_name(name):
    """Only letters, digits, dot, dash and underscore; never a path or a hidden file."""
    clean = _UNSAFE.sub("_", Path(name or "").name).strip("._")[:MAX_NAME]
    return clean or "dokument"


def _zerteilen(absatz, max_zeichen):
    """A paragraph longer than the limit: cut at sentence ends, a sentence too long: cut hard."""
    teile, aktuell = [], ""
    for satz in _SATZ.split(absatz):
        while len(satz) > max_zeichen:
            if aktuell:
                teile.append(aktuell)
                aktuell = ""
            teile.append(satz[:max_zeichen])
            satz = satz[max_zeichen:]
        if aktuell and len(aktuell) + 1 + len(satz) > max_zeichen:
            teile.append(aktuell)
            aktuell = satz
        else:
            aktuell = f"{aktuell} {satz}" if aktuell else satz
    if aktuell:
        teile.append(aktuell)
    return teile


def abschnitte(text, max_zeichen=MAX_ZEICHEN):
    """Sections of at most `max_zeichen` characters; short paragraphs are joined."""
    teile, aktuell = [], ""
    for absatz in (a.strip() for a in re.split(r"\n\s*\n", text or "")):
        if not absatz:
            continue
        for stueck in _zerteilen(absatz, max_zeichen):
            if aktuell and len(aktuell) + 2 + len(stueck) > max_zeichen:
                teile.append(aktuell)
                aktuell = stueck
            else:
                aktuell = f"{aktuell}\n\n{stueck}" if aktuell else stueck
    if aktuell:
        teile.append(aktuell)
    return teile


def _schreiben(pfad, daten):
    """Write privately (0600) and atomically: a crash leaves no half file under the final name."""
    tmp = pfad.with_name(f".{pfad.name}.tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as datei:
        datei.write(daten)
        datei.flush()
        os.fsync(datei.fileno())
    os.replace(tmp, pfad)


class Ablage:
    def __init__(self, root, katalog, *, wissen=None, log=None, clock=_utc_now):
        self._root = Path(root).resolve()
        if self._root.is_relative_to(REPO):
            raise AblageError("Die Ablage darf nicht im Code-Repository liegen (Laufzeitdaten nie im Repo)")
        self._katalog = katalog
        self._wissen = wissen
        self._log = log
        self._clock = clock

    def ablegen(self, daten, *, name, quelle, pii=False, lizenz=None, text=None, paket=None):
        """Store a document once; with `text` and `paket` its text becomes sections of the pack."""
        if text and paket is not None and self._wissen is None:
            raise AblageError("Für Text in einem Wissenspaket braucht die Ablage das Wissen")
        sha = hashlib.sha256(daten).hexdigest()
        datensatz = f"dokument:{sha}"
        bekannt = self._katalog.aktuell(datensatz)
        if bekannt is not None:
            self._abschnitte(sha, text, paket, quelle, name, pii)
            return Dokument(self._root / bekannt.ort, sha, False)
        now = self._clock()
        sicher = _sicherer_name(name)
        ordner = self._root / "dokumente" / f"{now:%Y}" / f"{now:%m}"
        ordner.mkdir(parents=True, exist_ok=True, mode=0o700)
        pfad = ordner / f"{sha[:16]}-{sicher}"
        meta = {
            "name": name,
            "quelle": quelle,
            "abrufzeit": format_ts(now),
            "pii": bool(pii),
            "lizenz": lizenz,
            "pruefsumme": sha,
            "groesse": len(daten),
        }
        _schreiben(pfad, daten)
        _schreiben(pfad.with_name(pfad.name + ".meta.json"), json.dumps(meta, ensure_ascii=False).encode("utf-8"))
        self._katalog.eintragen(
            datensatz,
            ort=pfad.relative_to(self._root).as_posix(),
            format=Path(sicher).suffix.lstrip(".").lower() or "bin",
            anzahl=1,
            pruefsumme=sha,
            pii=pii,
        )
        self._abschnitte(sha, text, paket, quelle, name, pii)
        if self._log is not None:
            self._log.append(
                "memory.write", {"dokument": sha[:16], "groesse": len(daten)}, intent="ablage.ablegen", pii=bool(pii)
            )
        return Dokument(pfad, sha, True)

    def _abschnitte(self, sha, text, paket, quelle, name, pii):
        """Sections of the text into the pack; those the pack already has from this document are skipped,
        so a second pack or a retry after an error adds exactly what is missing."""
        if not text or paket is None or self._wissen is None:
            return
        tag = f"dokument:{sha}"
        vorhanden = set(self._wissen.abschnitte(paket, tag=tag))
        for teil in abschnitte(text):
            if teil not in vorhanden:
                self._wissen.abschnitt(paket, teil, quelle=f"{quelle} ({name})", pii=pii, tags=[tag])
                vorhanden.add(teil)
