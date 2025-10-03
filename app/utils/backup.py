"""Utilities for creating safe SQLite backups."""
from __future__ import annotations

import datetime as _dt
import sqlite3
from pathlib import Path

from database import DB_FILE


def vacuum_into(destination: str | Path, prefix: str = "app-backup") -> Path:
    """Run VACUUM INTO to create a consistent snapshot of the SQLite database."""

    target_dir = Path(destination)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    backup_path = target_dir / f"{prefix}-{timestamp}.db"

    with sqlite3.connect(DB_FILE) as connection:
        escaped = str(backup_path).replace("'", "''")
        connection.execute("VACUUM INTO '" + escaped + "'")

    return backup_path
