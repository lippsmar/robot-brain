"""Knowledge modules: Markdown folders with a description (Bauplan Wissen 1.4, Design Wissen 7).

A module is a folder with `modul.yaml` and Markdown files. The description names the module,
its version, source, licence, language, trust setting ("gesichert" or "zu_pruefen", decided
per module; the default is chosen in the live test), personal data, shareability and the
SHA-256 of every file. Reading a module

- checks the description and every checksum; only plain `.md` files directly in the folder,
  no links, no hidden files, no paths,
- turns the module into a knowledge pack with sections (tagged with the module version),
- replaces an older version: its sections are archived, never deleted,
- treats the text as data: hidden instructions are marked in the result and the log, never followed.

A later NFC chip only carries the key `schlaubi-modul:<kennung>@<version>` (Design Wissen 7).
"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from brain._sqlite import nur_anhaengen, oeffnen, version_pruefen
from brain.ablage import abschnitte
from brain.character.safe_yaml import YamlError, load_yaml
from brain.eventlog import format_ts

DB_VERSION = 1
MAX_YAML = 64 * 1024
MAX_DATEI = 1024 * 1024
VERTRAUEN = ("gesichert", "zu_pruefen")
FELDER = ("kennung", "titel", "version", "quelle", "lizenz", "sprache", "vertrauen", "pii", "teilbar", "dateien")
_KENNUNG = re.compile(r"[a-z0-9][a-z0-9-]{2,60}")
_DATEINAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}\.md")
_SHA = re.compile(r"[0-9a-f]{64}")
# Phrases that try to give orders to the model; marked, never followed
_ANWEISUNG = re.compile(
    r"(ignorier\w*\s+(alle\s+)?(bisherigen\s+|vorherigen\s+)?(anweisungen|regeln)"
    r"|ignore\s+(all\s+)?(previous\s+|prior\s+)?(instructions|rules)"
    r"|vergiss\s+(alle\s+)?(deine\s+)?(anweisungen|regeln)"
    r"|du\s+bist\s+(ab\s+)?jetzt\s+|you\s+are\s+now\s+|system\s*prompt)",
    re.IGNORECASE,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS module (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kennung TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    pid TEXT NOT NULL,
    pruefsumme TEXT NOT NULL,
    vertrauen TEXT NOT NULL CHECK (vertrauen IN ('gesichert', 'zu_pruefen'))
) STRICT;
CREATE INDEX IF NOT EXISTS module_kennung ON module (kennung, id);
""" + nur_anhaengen("module")


class ModulError(Exception):
    """A module was rejected; the message says why, in German."""


@dataclass(frozen=True)
class Modulstand:
    kennung: str
    version: int
    pid: str
    pruefsumme: str
    vertrauen: str


@dataclass(frozen=True)
class Ergebnis:
    kennung: str
    version: int
    pid: str
    neu: bool
    abschnitte: int
    auffaellig: tuple


def _utc_now():
    return datetime.now(UTC)


def _beschreibung(ordner):
    datei = ordner / "modul.yaml"
    if datei.is_symlink() or not datei.is_file():
        raise ModulError("modul.yaml fehlt oder ist ein Link")
    try:
        daten = load_yaml(datei.read_text(encoding="utf-8"), max_bytes=MAX_YAML)
    except (YamlError, UnicodeDecodeError) as error:
        raise ModulError(f"modul.yaml: {error}") from error
    if not isinstance(daten, dict):
        raise ModulError("modul.yaml muss Schlüssel und Werte enthalten")
    fehlt = [feld for feld in FELDER if feld not in daten]
    if fehlt:
        raise ModulError(f"modul.yaml: es fehlen {', '.join(fehlt)}")
    if not isinstance(daten["kennung"], str) or not _KENNUNG.fullmatch(daten["kennung"]):
        raise ModulError("Kennung: nur Kleinbuchstaben, Ziffern und Bindestrich, 3 bis 61 Zeichen")
    if isinstance(daten["version"], bool) or not isinstance(daten["version"], int) or daten["version"] < 1:
        raise ModulError("Version muss eine ganze Zahl ab 1 sein")
    if daten["vertrauen"] not in VERTRAUEN:
        raise ModulError(f"Vertrauen: erlaubt sind {', '.join(VERTRAUEN)}")
    for feld in ("pii", "teilbar"):
        if not isinstance(daten[feld], bool):
            raise ModulError(f"{feld} muss true oder false sein")
    for feld in ("titel", "quelle", "lizenz", "sprache"):
        if not isinstance(daten[feld], str) or not daten[feld].strip() or "\n" in daten[feld]:
            raise ModulError(f"{feld} muss ein einzeiliger Text sein")
    dateien = daten["dateien"]
    if not isinstance(dateien, dict) or not dateien:
        raise ModulError("dateien: mindestens eine Markdown-Datei mit Prüfsumme")
    return daten


def _dateien(ordner, liste):
    """Read the listed files: plain .md directly in the folder, checksum must match."""
    texte = {}
    for name, summe in sorted(liste.items()):
        if not isinstance(name, str) or not _DATEINAME.fullmatch(name):
            raise ModulError(f"Datei {name!r}: nur .md-Dateien direkt im Modul-Ordner")
        if not isinstance(summe, str) or not _SHA.fullmatch(summe):
            raise ModulError(f"Datei {name}: Prüfsumme muss SHA-256 in Kleinbuchstaben sein")
        pfad = ordner / name
        if pfad.is_symlink():
            raise ModulError(f"Datei {name} ist ein Link, das ist nicht erlaubt")
        if not pfad.is_file():
            raise ModulError(f"Datei {name} fehlt")
        if pfad.stat().st_size > MAX_DATEI:
            raise ModulError(f"Datei {name} ist größer als {MAX_DATEI // 1024} KB")
        daten = pfad.read_bytes()
        if hashlib.sha256(daten).hexdigest() != summe:
            raise ModulError(f"Datei {name}: Prüfsumme stimmt nicht")
        try:
            texte[name] = daten.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ModulError(f"Datei {name} ist kein UTF-8-Text") from error
    return texte


def _auffaellig(texte):
    funde = []
    for name, text in texte.items():
        for match in _ANWEISUNG.finditer(text):
            satz = text[match.start() :].split("\n", 1)[0]
            satz = re.split(r"\s+und\s+|[.!?]", satz, maxsplit=1)[0].strip()
            funde.append(f"{name}: {satz[:80]}")
    return tuple(funde)


class Module:
    def __init__(self, path, wissen, memory, log=None, clock=_utc_now, wait_s=5.0):
        self._wissen = wissen
        self._memory = memory
        self._log = log
        self._clock = clock
        self._conn = oeffnen(path, wait_s)
        version = version_pruefen(self._conn, DB_VERSION, ModulError)
        self._conn.executescript(_SCHEMA)
        if version == 0:
            self._conn.execute(f"PRAGMA user_version = {DB_VERSION}")

    def close(self):
        self._conn.close()

    def stand(self, kennung):
        """Current version of a module, or None."""
        row = self._conn.execute(
            "SELECT * FROM module WHERE kennung = ? ORDER BY id DESC LIMIT 1", (kennung,)
        ).fetchone()
        if row is None:
            return None
        return Modulstand(row["kennung"], row["version"], row["pid"], row["pruefsumme"], row["vertrauen"])

    def einlesen(self, ordner):
        """Read a module folder into a knowledge pack (see module docstring)."""
        ordner = Path(ordner)
        daten = _beschreibung(ordner)
        texte = _dateien(ordner, daten["dateien"])
        kennung, version = daten["kennung"], daten["version"]
        # description and file checksums: a changed setting (pii, vertrauen, ...) also needs a new version
        gesamt = hashlib.sha256(json.dumps(daten, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        alt = self.stand(kennung)
        if alt is not None:
            if version < alt.version:
                raise ModulError(f"Version {version} ist älter als die eingelesene Version {alt.version}")
            if version == alt.version:
                if gesamt != alt.pruefsumme:
                    raise ModulError(f"Version {version} gibt es schon mit anderem Inhalt: bitte Version erhöhen")
                zahl = len(self._wissen.abschnitte(alt.pid, tag=f"modul:{kennung}@{version}"))
                funde = _auffaellig(texte)
                self._protokoll(kennung, version, zahl, funde, daten["pii"], neu=False)
                return Ergebnis(kennung, version, alt.pid, False, zahl, funde)
        tag = f"modul:{kennung}@{version}"
        if alt is None:
            # a pack left by an attempt that broke off is used again instead of a second one
            frueher = self._wissen.mit_herkunft(f"modul:{kennung}")
            pid = frueher[0].pid if frueher else None
        else:
            pid = alt.pid
            for hit in self._memory.mit_tag(f"modul:{kennung}@{alt.version}"):
                self._memory.forget(hit.uid, f"ersetzt durch Modul {kennung} Version {version}")
        if pid is None:
            pid = self._wissen.anlegen(
                daten["titel"], pii=daten["pii"], teilbar=daten["teilbar"], herkunft=f"modul:{kennung}"
            )
        for hit in self._memory.mit_tag(tag):  # sections of an attempt that broke off
            self._memory.forget(hit.uid, f"Modul {kennung} Version {version} wird neu eingelesen")
        zahl = 0
        for name, text in texte.items():
            for teil in abschnitte(text):
                self._wissen.abschnitt(
                    pid,
                    teil,
                    quelle=f"{tag}/{name}",
                    pii=daten["pii"],
                    teilbar=daten["teilbar"],
                    tags=[tag],
                )
                zahl += 1
        with self._conn:
            self._conn.execute(
                "INSERT INTO module (ts, kennung, version, pid, pruefsumme, vertrauen) VALUES (?, ?, ?, ?, ?, ?)",
                (format_ts(self._clock()), kennung, version, pid, gesamt, daten["vertrauen"]),
            )
        funde = _auffaellig(texte)
        self._protokoll(kennung, version, zahl, funde, daten["pii"], neu=True)
        return Ergebnis(kennung, version, pid, True, zahl, funde)

    def _protokoll(self, kennung, version, zahl, funde, pii, *, neu):
        if self._log is not None:
            self._log.append(
                "memory.write" if neu else "agent.action",
                {"modul": kennung, "version": version, "abschnitte": zahl, "auffaellig": len(funde), "neu": neu},
                intent="module.einlesen",
                pii=pii,
            )
