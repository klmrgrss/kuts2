"""Minimal SQLite migration runner."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def run_pending_migrations(db_path: str) -> None:
    """Execute SQL migrations in order based on their numeric prefix."""

    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    migrations = sorted(_iter_migration_files())
    if not migrations:
        return

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=OFF;")
        connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        current = connection.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        if current is None:
            connection.execute("INSERT INTO schema_version(version) VALUES (0)")
            version = 0
        else:
            version = int(current["version"])

        for migration in migrations:
            number = int(migration.stem.split("_", 1)[0])
            if number <= version:
                continue

            sql = migration.read_text()
            print(f"--- Applying migration {migration.name} ---")
            connection.executescript(sql)
            connection.execute("UPDATE schema_version SET version = ?", (number,))
        connection.commit()
        connection.execute("PRAGMA foreign_keys=ON;")


def _iter_migration_files() -> Iterable[Path]:
    for path in MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        yield path
