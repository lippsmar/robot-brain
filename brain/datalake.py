"""Data lake (L5) on the brain (Bauplan Daten, Phase 7, with 2.2, 6.1 and 8.2).

The cube sends a batch of readings every minute with a running number. The data lake

- stores readings as time series (time, device, channel, value, unit, quality) and sound
  classes (time, class, confidence, speech yes or no, number of voices), never sound or speech,
- ignores a batch it already has, so buffered batches can be sent again safely, and finds
  missing numbers,
- marks failed sensors as "fehler" without a value and implausible values as "unplausibel",
  instead of storing wrong values as good ones,
- knows places only from WLANs that Marvin names ("Das ist das Büro"), otherwise "unterwegs";
  there is no GPS,
- keeps Marvin's labels for sound classes next to the original class, with a note,
- keeps everything forever: rows can only be added (Design Daten: Aufbewahrung für immer),
- lists counts, time span and personal data per channel in a manifest.

Readings at a named place and sounds with speech count as personal data (`pii`), because they
describe Marvin's day.
"""

import math
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from brain.eventlog import format_ts

DB_VERSION = 1
UNTERWEGS = "unterwegs"
# channel -> (unit, plausible minimum, plausible maximum)
CHANNELS = {
    "zuluft_temp": ("°C", -20.0, 85.0),
    "abluft_temp": ("°C", -20.0, 85.0),
    "abluft_feuchte": ("%", 0.0, 100.0),
    "abluft_druck": ("hPa", 300.0, 1100.0),
    "licht": ("lx", 0.0, 120000.0),
    "chip_temp": ("°C", -20.0, 110.0),
    "chip_drosselung": ("an/aus", 0.0, 1.0),
    "modem_temp": ("°C", -40.0, 110.0),
    "akku": ("%", 0.0, 100.0),
    "wlan_signal": ("dBm", -110.0, 0.0),
    "lte_signal": ("dBm", -140.0, -40.0),
    "lautstaerke": ("dB", 0.0, 130.0),
}
_DEVICE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
_TABLES = ("readings", "sounds", "labels", "place_names")
_SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device TEXT NOT NULL,
    seq INTEGER NOT NULL,
    ts TEXT NOT NULL,
    channel TEXT NOT NULL,
    value REAL,
    unit TEXT NOT NULL,
    quality TEXT NOT NULL CHECK (quality IN ('ok', 'fehler', 'unplausibel')),
    place TEXT NOT NULL,
    pii INTEGER NOT NULL CHECK (pii IN (0, 1)),
    UNIQUE (device, seq, channel)
) STRICT;
CREATE INDEX IF NOT EXISTS readings_by_channel ON readings (channel, ts);
CREATE TABLE IF NOT EXISTS sounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device TEXT NOT NULL,
    seq INTEGER NOT NULL,
    ts TEXT NOT NULL,
    klasse TEXT NOT NULL,
    sicherheit REAL NOT NULL CHECK (sicherheit BETWEEN 0 AND 1),
    sprache INTEGER NOT NULL CHECK (sprache IN (0, 1)),
    stimmen INTEGER NOT NULL CHECK (stimmen >= 0),
    place TEXT NOT NULL,
    pii INTEGER NOT NULL CHECK (pii IN (0, 1)),
    UNIQUE (device, seq, klasse)
) STRICT;
CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sound_id INTEGER NOT NULL REFERENCES sounds (id),
    klasse TEXT NOT NULL,
    vermerk TEXT NOT NULL,
    ts TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS place_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wlan TEXT NOT NULL,
    name TEXT NOT NULL,
    ts TEXT NOT NULL
) STRICT;
"""


class LakeError(Exception):
    """A batch, sound, label or place was rejected, or the database does not fit."""


@dataclass(frozen=True)
class IngestResult:
    new: bool
    warnings: tuple


@dataclass(frozen=True)
class Reading:
    ts: str
    device: str
    seq: int
    channel: str
    value: float | None
    unit: str
    quality: str
    place: str
    pii: bool


@dataclass(frozen=True)
class Sound:
    id: int
    ts: str
    device: str
    klasse: str
    original: str
    vermerk: str
    sicherheit: float
    sprache: bool
    stimmen: int
    place: str
    pii: bool


@dataclass(frozen=True)
class HourStats:
    hour: str
    minimum: float
    maximum: float
    mean: float
    std: float
    count: int


@dataclass(frozen=True)
class ManifestEntry:
    name: str
    count: int
    pii_count: int
    first: str | None
    last: str | None


def _utc_now():
    return datetime.now(UTC)


def _is_number(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def _check_text(value, label, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise LakeError(f"{label} muss ein Text mit 1 bis {limit} Zeichen sein")


def _check_sound(sound):
    if not isinstance(sound, dict) or not {"klasse", "sicherheit", "sprache", "stimmen"} <= set(sound):
        raise LakeError("Geräusch braucht klasse, sicherheit, sprache und stimmen")
    _check_text(sound["klasse"], "Geräuschklasse", 40)
    if isinstance(sound["sicherheit"], bool) or not _is_number(sound["sicherheit"]):
        raise LakeError("Geräusch: sicherheit muss eine Zahl sein")
    if not 0 <= sound["sicherheit"] <= 1:
        raise LakeError("Geräusch: sicherheit muss zwischen 0 und 1 liegen")
    if not isinstance(sound["sprache"], bool):
        raise LakeError("Geräusch: sprache muss ja oder nein sein")
    if isinstance(sound["stimmen"], bool) or not isinstance(sound["stimmen"], int) or sound["stimmen"] < 0:
        raise LakeError("Geräusch: stimmen muss eine ganze Zahl ab 0 sein")


class DataLake:
    def __init__(self, path, log=None, clock=_utc_now):
        self._path = Path(path)
        if not self._path.exists():
            os.close(os.open(self._path, os.O_CREAT | os.O_RDWR, 0o600))  # only Schlaubi's account
        self._log = log
        self._clock = clock
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._conn.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
        for pragma in ("journal_mode = WAL", "synchronous = FULL", "foreign_keys = ON", "trusted_schema = OFF"):
            self._conn.execute(f"PRAGMA {pragma}")
        version = self._conn.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, DB_VERSION):
            self._conn.close()
            raise LakeError(f"Datenbank-Version {version}, der Code erwartet {DB_VERSION}: Umstellung nötig")
        triggers = "".join(
            f"CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END;"
            f"CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END;"
            for table in _TABLES
        )
        self._conn.executescript(_SCHEMA + triggers)
        if version == 0:
            self._conn.execute(f"PRAGMA user_version = {DB_VERSION}")

    def close(self):
        self._conn.close()

    def _event(self, type, payload, intent, pii=False):
        if self._log is not None:
            self._log.append(type, payload, intent=intent, pii=pii)

    # --- places (Bauplan Daten 6.1) ------------------------------------------------------

    def name_place(self, wlan, name):
        """Marvin names the place of a WLAN; later batches from this WLAN get this name."""
        _check_text(wlan, "WLAN", 64)
        _check_text(name, "Ort", 40)
        if name == UNTERWEGS:
            raise LakeError(f"„{UNTERWEGS}“ ist kein Ortsname, sondern gilt ohne bekanntes WLAN")
        with self._conn:
            self._conn.execute(
                "INSERT INTO place_names (wlan, name, ts) VALUES (?, ?, ?)", (wlan, name, format_ts(self._clock()))
            )
        self._event("agent.action", {"ort": name}, "datalake.place_named", pii=True)

    def place_for(self, wlan):
        if wlan is None:
            return UNTERWEGS
        row = self._conn.execute(
            "SELECT name FROM place_names WHERE wlan = ? ORDER BY id DESC LIMIT 1", (wlan,)
        ).fetchone()
        return row["name"] if row else UNTERWEGS

    # --- ingest (Bauplan Daten 2.2 and 7.1) ----------------------------------------------

    def ingest(self, device, seq, ts, values, *, wlan=None, sounds=()):
        """Store one batch. Returns whether it was new and warnings for failed or unknown channels."""
        if not isinstance(device, str) or not _DEVICE.match(device):
            raise LakeError("Gerät: nur Kleinbuchstaben, Ziffern und Bindestrich, höchstens 40 Zeichen")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
            raise LakeError("laufende Nummer muss eine ganze Zahl ab 0 sein")
        if not isinstance(ts, datetime) or ts.tzinfo is None:
            raise LakeError("Messzeit ohne Zeitzone")
        rows, warnings, sensor_errors, unknown = [], [], [], []
        for channel, value in values.items():
            if channel not in CHANNELS:
                unknown.append(channel)
                warnings.append(f"Kanal {channel!r} unbekannt, nicht gespeichert")
                continue
            unit, low, high = CHANNELS[channel]
            if value is None:
                quality = "fehler"
                sensor_errors.append(channel)
                warnings.append(f"Sensor {channel!r} meldet einen Fehler")
            elif not _is_number(value):
                raise LakeError(f"Kanal {channel!r}: Wert ist keine Zahl")
            else:
                value = float(value)
                quality = "ok" if low <= value <= high else "unplausibel"
            rows.append((channel, value, unit, quality))
        for sound in sounds:
            _check_sound(sound)
        place = self.place_for(wlan)
        stamp = format_ts(ts)
        at_named_place = int(place != UNTERWEGS)
        inserted = 0
        with self._conn:
            for channel, value, unit, quality in rows:
                cursor = self._conn.execute(
                    "INSERT OR IGNORE INTO readings (device, seq, ts, channel, value, unit, quality, place, pii)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (device, seq, stamp, channel, value, unit, quality, place, at_named_place),
                )
                inserted += cursor.rowcount
            for sound in sounds:
                cursor = self._conn.execute(
                    "INSERT OR IGNORE INTO sounds"
                    " (device, seq, ts, klasse, sicherheit, sprache, stimmen, place, pii)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        device,
                        seq,
                        stamp,
                        sound["klasse"],
                        float(sound["sicherheit"]),
                        int(sound["sprache"]),
                        sound["stimmen"],
                        place,
                        int(at_named_place or sound["sprache"]),
                    ),
                )
                inserted += cursor.rowcount
        if inserted:
            for channel in sensor_errors:
                self._event("error", {"geraet": device, "nummer": seq, "kanal": channel}, "datalake.sensor_error")
            if unknown:
                self._event("error", {"geraet": device, "nummer": seq, "kanaele": unknown}, "datalake.unknown_channel")
        return IngestResult(bool(inserted), tuple(warnings))

    def missing(self, device, first, last):
        """Running numbers between first and last (inclusive) without any data."""
        seen = {
            row[0]
            for row in self._conn.execute(
                "SELECT seq FROM readings WHERE device = ? AND seq BETWEEN ? AND ?"
                " UNION SELECT seq FROM sounds WHERE device = ? AND seq BETWEEN ? AND ?",
                (device, first, last, device, first, last),
            )
        }
        return [number for number in range(first, last + 1) if number not in seen]

    # --- queries (Bauplan Daten 7.1, 9) -------------------------------------------------

    def readings(self, channel, start, end, *, place=None, quality="ok"):
        """Readings of one channel in [start, end), optionally only at one place; good values by default."""
        sql = "SELECT * FROM readings WHERE channel = ? AND ts >= ? AND ts < ?"
        params: list = [channel, format_ts(start), format_ts(end)]
        if place is not None:
            sql += " AND place = ?"
            params.append(place)
        if quality is not None:
            sql += " AND quality = ?"
            params.append(quality)
        return [self._reading(row) for row in self._conn.execute(sql + " ORDER BY ts, id", params)]

    def all_readings(self, start, end):
        rows = self._conn.execute(
            "SELECT * FROM readings WHERE ts >= ? AND ts < ? ORDER BY ts, id", (format_ts(start), format_ts(end))
        )
        return [self._reading(row) for row in rows]

    @staticmethod
    def _reading(row):
        return Reading(
            row["ts"],
            row["device"],
            row["seq"],
            row["channel"],
            row["value"],
            row["unit"],
            row["quality"],
            row["place"],
            bool(row["pii"]),
        )

    def hourly(self, channel, start, end, *, place=None):
        """Minimum, maximum, mean, standard deviation and count per hour (UTC), good values only."""
        sql = (
            "SELECT substr(ts, 1, 13) AS hour, MIN(value) AS lo, MAX(value) AS hi, AVG(value) AS mean,"
            " AVG(value * value) AS square, COUNT(value) AS n FROM readings"
            " WHERE channel = ? AND quality = 'ok' AND ts >= ? AND ts < ?"
        )
        params: list = [channel, format_ts(start), format_ts(end)]
        if place is not None:
            sql += " AND place = ?"
            params.append(place)
        result = []
        for row in self._conn.execute(sql + " GROUP BY hour ORDER BY hour", params):
            variance = max(0.0, row["square"] - row["mean"] ** 2)
            result.append(HourStats(row["hour"], row["lo"], row["hi"], row["mean"], math.sqrt(variance), row["n"]))
        return result

    # --- sounds and labels (Bauplan Daten 4.1, 8.2) -----------------------------------

    def sounds(self, start, end, *, place=None):
        """Sound classes in [start, end); Marvin's latest label replaces the class, the original stays visible."""
        sql = (
            "SELECT s.*, l.klasse AS label, l.vermerk AS vermerk FROM sounds s"
            " LEFT JOIN labels l ON l.id = (SELECT MAX(id) FROM labels WHERE sound_id = s.id)"
            " WHERE s.ts >= ? AND s.ts < ?"
        )
        params: list = [format_ts(start), format_ts(end)]
        if place is not None:
            sql += " AND s.place = ?"
            params.append(place)
        return [
            Sound(
                row["id"],
                row["ts"],
                row["device"],
                row["label"] or row["klasse"],
                row["klasse"],
                row["vermerk"] or "",
                row["sicherheit"],
                bool(row["sprache"]),
                row["stimmen"],
                row["place"],
                bool(row["pii"]),
            )
            for row in self._conn.execute(sql + " ORDER BY s.ts, s.id", params)
        ]

    def label_sound(self, sound_id, klasse, *, vermerk):
        """Marvin corrects a sound class, e.g. "Das war Regen"; kept with a note for later models."""
        _check_text(klasse, "Geräuschklasse", 40)
        _check_text(vermerk, "Vermerk", 120)
        if self._conn.execute("SELECT 1 FROM sounds WHERE id = ?", (sound_id,)).fetchone() is None:
            raise LakeError(f"Geräusch {sound_id} unbekannt")
        with self._conn:
            self._conn.execute(
                "INSERT INTO labels (sound_id, klasse, vermerk, ts) VALUES (?, ?, ?, ?)",
                (sound_id, klasse, vermerk, format_ts(self._clock())),
            )
        self._event("agent.action", {"geraeusch": sound_id, "klasse": klasse}, "datalake.label")

    # --- manifest (Bauplan Daten 7.2) ---------------------------------------------------

    def manifest(self):
        """Count, personal data and time span per channel, for sounds and for labels."""
        entries = [
            ManifestEntry(f"readings:{row[0]}", row[1], row[2], row[3], row[4])
            for row in self._conn.execute(
                "SELECT channel, COUNT(*), SUM(pii), MIN(ts), MAX(ts) FROM readings GROUP BY channel ORDER BY channel"
            )
        ]
        count, pii, first, last = self._conn.execute(
            "SELECT COUNT(*), SUM(pii), MIN(ts), MAX(ts) FROM sounds"
        ).fetchone()
        entries.append(ManifestEntry("sounds", count, pii or 0, first, last))
        count, first, last = self._conn.execute("SELECT COUNT(*), MIN(ts), MAX(ts) FROM labels").fetchone()
        entries.append(ManifestEntry("labels", count, 0, first, last))
        return entries
