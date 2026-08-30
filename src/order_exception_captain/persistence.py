"""SQLite persistence for incidents and their human-visible audit trail."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .approvals import ApprovalService
from .domain import AuditEvent, AuditEventType, Incident, IncidentStatus, ScanActivity


class IncidentRepository(Protocol):
    def save_if_new(self, incident: Incident) -> bool:
        """Persist an incident once. Return true only for the first scan result."""

    def list_incidents(self) -> list[Incident]:
        """Return every incident, newest first."""

    def get_incident(self, incident_id: str) -> Incident:
        """Return one incident or raise KeyError."""

    def approve(self, incident_id: str, operator: str) -> Incident:
        """Approve a draft and record the operator in the audit trail."""

    def reject(self, incident_id: str, operator: str, reason: str) -> Incident:
        """Reject a draft and record why without triggering an external action."""

    def record_dry_run(self, incident_id: str, operator: str) -> bool:
        """Record one prepared dry run for an approved incident. Return true if newly recorded."""

    def record_scan_activity(self, activity: ScanActivity) -> None:
        """Persist a privacy-safe operational record for a scan attempt."""

    def list_scan_activity(self, limit: int = 20) -> list[ScanActivity]:
        """Return recent scan records, newest first."""

    def check_storage_health(self) -> None:
        """Raise the underlying SQLite error if the configured storage is unavailable."""

    def list_events(self, incident_id: str) -> list[AuditEvent]:
        """Return the ordered audit events for one incident."""


class SqliteIncidentRepository:
    """A small repository with database-enforced idempotency on incident ID."""

    def __init__(self, database_path: str | Path) -> None:
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise_schema()

    def save_if_new(self, incident: Incident) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO incidents (id, order_id, status, created_at, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    incident.id,
                    incident.order_id,
                    incident.status.value,
                    incident.created_at.isoformat(),
                    incident.model_dump_json(),
                ),
            )
            if cursor.rowcount == 0:
                return False
            self._append_event(
                connection,
                AuditEvent(
                    incident_id=incident.id,
                    event_type=AuditEventType.INCIDENT_DETECTED,
                    occurred_at=incident.created_at,
                    detail="Deterministic delivery policy created an approval-gated draft.",
                ),
            )
            return True

    def list_incidents(self) -> list[Incident]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM incidents ORDER BY created_at DESC, id DESC").fetchall()
        return [Incident.model_validate_json(row["payload"]) for row in rows]

    def get_incident(self, incident_id: str) -> Incident:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        if row is None:
            raise KeyError(incident_id)
        return Incident.model_validate_json(row["payload"])

    def approve(self, incident_id: str, operator: str) -> Incident:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT payload FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if row is None:
                raise KeyError(incident_id)
            incident = Incident.model_validate_json(row["payload"])
            approved = ApprovalService().approve(incident, operator)
            connection.execute(
                "UPDATE incidents SET status = ?, payload = ? WHERE id = ?",
                (approved.status.value, approved.model_dump_json(), incident_id),
            )
            self._append_event(
                connection,
                AuditEvent(
                    incident_id=incident_id,
                    event_type=AuditEventType.INCIDENT_APPROVED,
                    occurred_at=approved.drafts[0].approved_at,
                    actor=operator,
                    detail="Named operator approved the draft; no external action was sent.",
                ),
            )
            return approved

    def reject(self, incident_id: str, operator: str, reason: str) -> Incident:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT payload FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if row is None:
                raise KeyError(incident_id)
            incident = Incident.model_validate_json(row["payload"])
            rejected = ApprovalService().reject(incident, operator, reason)
            connection.execute(
                "UPDATE incidents SET status = ?, payload = ? WHERE id = ?",
                (rejected.status.value, rejected.model_dump_json(), incident_id),
            )
            self._append_event(
                connection,
                AuditEvent(
                    incident_id=incident_id,
                    event_type=AuditEventType.INCIDENT_REJECTED,
                    occurred_at=rejected.drafts[0].rejected_at,
                    actor=operator,
                    detail=f"Named operator rejected the draft: {rejected.drafts[0].rejection_reason}",
                ),
            )
            return rejected

    def record_dry_run(self, incident_id: str, operator: str) -> bool:
        if not operator.strip():
            raise ValueError("An operator is required to prepare a dry run.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT payload FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if row is None:
                raise KeyError(incident_id)
            incident = Incident.model_validate_json(row["payload"])
            if incident.status is not IncidentStatus.APPROVED:
                raise ValueError(f"Incident {incident.id} must be approved before a dry run can be prepared.")
            exists = connection.execute(
                "SELECT 1 FROM audit_events WHERE incident_id = ? AND event_type = ?",
                (incident_id, AuditEventType.DRY_RUN_PREPARED.value),
            ).fetchone()
            if exists is not None:
                return False
            self._append_event(
                connection,
                AuditEvent(
                    incident_id=incident_id,
                    event_type=AuditEventType.DRY_RUN_PREPARED,
                    occurred_at=datetime.now(timezone.utc),
                    actor=operator.strip(),
                    detail="Approved operator prepared a dry-run outbound handoff; no request was sent.",
                ),
            )
            return True

    def record_scan_activity(self, activity: ScanActivity) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scan_activity (
                    occurred_at, mode, status, scanned_orders,
                    new_incident_count, existing_incident_count, detail
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    activity.occurred_at.isoformat(),
                    activity.mode,
                    activity.status.value,
                    activity.scanned_orders,
                    activity.new_incident_count,
                    activity.existing_incident_count,
                    activity.detail,
                ),
            )

    def list_scan_activity(self, limit: int = 20) -> list[ScanActivity]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, occurred_at, mode, status, scanned_orders,
                       new_incident_count, existing_incident_count, detail
                FROM scan_activity
                ORDER BY occurred_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            ScanActivity(
                id=row["id"],
                occurred_at=row["occurred_at"],
                mode=row["mode"],
                status=row["status"],
                scanned_orders=row["scanned_orders"],
                new_incident_count=row["new_incident_count"],
                existing_incident_count=row["existing_incident_count"],
                detail=row["detail"],
            )
            for row in rows
        ]

    def check_storage_health(self) -> None:
        with self._connect() as connection:
            connection.execute("SELECT 1").fetchone()

    def list_events(self, incident_id: str) -> list[AuditEvent]:
        self.get_incident(incident_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, incident_id, event_type, occurred_at, actor, detail
                FROM audit_events
                WHERE incident_id = ?
                ORDER BY occurred_at, id
                """,
                (incident_id,),
            ).fetchall()
        return [
            AuditEvent(
                id=row["id"],
                incident_id=row["incident_id"],
                event_type=row["event_type"],
                occurred_at=row["occurred_at"],
                actor=row["actor"],
                detail=row["detail"],
            )
            for row in rows
        ]

    def _initialise_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL REFERENCES incidents(id),
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    actor TEXT NULL,
                    detail TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_audit_events_incident ON audit_events(incident_id, id);
                CREATE TABLE IF NOT EXISTS scan_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    scanned_orders INTEGER NULL,
                    new_incident_count INTEGER NULL,
                    existing_incident_count INTEGER NULL,
                    detail TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_scan_activity_occurred_at ON scan_activity(occurred_at DESC, id DESC);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _append_event(connection: sqlite3.Connection, event: AuditEvent) -> None:
        connection.execute(
            """
            INSERT INTO audit_events (incident_id, event_type, occurred_at, actor, detail)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event.incident_id,
                event.event_type.value,
                event.occurred_at.isoformat(),
                event.actor,
                event.detail,
            ),
        )
