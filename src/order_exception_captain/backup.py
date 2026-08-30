"""Safe, explicit SQLite backup command for the local operator service."""

from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class BackupError(RuntimeError):
    """Raised when a backup cannot be made without risking an existing file."""


@dataclass(frozen=True)
class BackupRecord:
    source: Path
    destination: Path
    created_at: datetime

    def safe_summary(self) -> dict[str, str]:
        return {
            "source": str(self.source),
            "destination": str(self.destination),
            "created_at": self.created_at.isoformat(),
            "integrity": "ok",
        }


def create_verified_backup(source: str | Path, destination_directory: str | Path) -> BackupRecord:
    """Copy one SQLite database using SQLite's online backup API and verify it."""
    source_path = Path(source)
    output_directory = Path(destination_directory)
    if not source_path.is_file():
        raise BackupError("The source database does not exist.")
    output_directory.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc)
    timestamp = created_at.strftime("%Y%m%dT%H%M%SZ")
    destination = output_directory / f"{source_path.stem}-{timestamp}.sqlite3"
    temporary_destination = destination.with_suffix(".sqlite3.partial")
    if destination.exists() or temporary_destination.exists():
        raise BackupError("The generated backup filename already exists; no file was overwritten.")

    try:
        with closing(sqlite3.connect(source_path)) as source_connection, closing(
            sqlite3.connect(temporary_destination)
        ) as destination_connection:
            source_connection.backup(destination_connection)
        with closing(sqlite3.connect(temporary_destination)) as check_connection:
            integrity = check_connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise BackupError("SQLite could not verify the backup integrity; the partial file was retained for investigation.")
        temporary_destination.replace(destination)
    except sqlite3.Error as error:
        raise BackupError("SQLite could not create a backup; no existing backup was overwritten.") from error

    return BackupRecord(source=source_path, destination=destination, created_at=created_at)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and verify a non-destructive SQLite backup.")
    parser.add_argument("--database", type=Path, default=Path("data/order-exception-captain.sqlite3"))
    parser.add_argument("--output-directory", type=Path, default=Path("backups"))
    args = parser.parse_args()
    try:
        record = create_verified_backup(args.database, args.output_directory)
    except BackupError as error:
        parser.error(str(error))
    print(json.dumps(record.safe_summary()))
