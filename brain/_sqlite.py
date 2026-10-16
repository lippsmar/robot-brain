"""Shared SQLite setup for the lakehouse stores (Katalog, Wissen).

Same rules as the memory core and the data lake: file only readable by Schlaubi's account,
WAL with synchronous FULL, defensive mode, no untrusted schema, and rows that can only be added
(triggers per table, see `nur_anhaengen`).
"""

import os
import sqlite3
from pathlib import Path


def oeffnen(path, wait_s=5.0):
    path = Path(path)
    if not path.exists():
        os.close(os.open(path, os.O_CREAT | os.O_RDWR, 0o600))  # only Schlaubi's account
    conn = sqlite3.connect(path, timeout=wait_s)
    conn.row_factory = sqlite3.Row
    conn.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
    for pragma in (
        "journal_mode = WAL",
        "synchronous = FULL",
        "foreign_keys = ON",
        "secure_delete = ON",
        "recursive_triggers = ON",
        "trusted_schema = OFF",
    ):
        conn.execute(f"PRAGMA {pragma}")
    return conn


def nur_anhaengen(table):
    """Triggers that reject UPDATE, DELETE and INSERT OR REPLACE on `table`."""
    return f"""
CREATE TRIGGER IF NOT EXISTS {table}_no_replace BEFORE INSERT ON {table}
WHEN EXISTS (SELECT 1 FROM {table} WHERE id = new.id)
BEGIN SELECT RAISE(ABORT, '{table} is append-only, no replace'); END;
CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table}
BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END;
CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table}
BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END;
"""


def version_pruefen(conn, expected, error):
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version not in (0, expected):
        raise error(f"database version {version}, code expects {expected}: a migration is needed")
    return version
