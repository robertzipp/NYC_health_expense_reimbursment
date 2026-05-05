from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def connect(database_url: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(database_url)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = path.stem
        applied = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
        ).fetchone()
        if applied:
            continue
        conn.executescript(path.read_text())
        conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
    conn.commit()


def seed_minimal_reference_data(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO agencies (id, agency_code, name, status) VALUES (?, ?, ?, ?)",
        ("agency-nyc", "NYC", "City of New York", "active"),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO employees
            (id, agency_id, external_employee_number, first_name, last_name, employment_status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("employee-1", "agency-nyc", "EMP-1", "Ava", "Lee", "active"),
    )
    conn.commit()
