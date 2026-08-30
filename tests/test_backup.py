import sqlite3
from datetime import datetime, timezone

import pytest

from order_exception_captain.backup import BackupError, create_verified_backup
from order_exception_captain.domain import ScanActivity, ScanActivityStatus
from order_exception_captain.persistence import SqliteIncidentRepository


def test_backup_copies_and_verifies_an_existing_database(tmp_path) -> None:
    database = tmp_path / "incidents.sqlite3"
    repository = SqliteIncidentRepository(database)
    repository.record_scan_activity(
        ScanActivity(
            occurred_at=datetime.now(timezone.utc),
            mode="backup-test",
            status=ScanActivityStatus.SUCCEEDED,
            scanned_orders=1,
            new_incident_count=0,
            existing_incident_count=1,
            detail="Synthetic test activity.",
        )
    )

    record = create_verified_backup(database, tmp_path / "backups")

    assert record.destination.is_file()
    with sqlite3.connect(record.destination) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT COUNT(*) FROM scan_activity").fetchone()[0] == 1


def test_backup_never_creates_an_empty_source_or_overwrites_a_known_target(tmp_path, monkeypatch) -> None:
    with pytest.raises(BackupError, match="does not exist"):
        create_verified_backup(tmp_path / "missing.sqlite3", tmp_path / "backups")

    database = tmp_path / "incidents.sqlite3"
    SqliteIncidentRepository(database)
    fixed_now = datetime(2026, 8, 30, tzinfo=timezone.utc)

    class FixedDateTime:
        @classmethod
        def now(cls, timezone):
            return fixed_now

    monkeypatch.setattr("order_exception_captain.backup.datetime", FixedDateTime)
    create_verified_backup(database, tmp_path / "backups")
    with pytest.raises(BackupError, match="already exists"):
        create_verified_backup(database, tmp_path / "backups")
