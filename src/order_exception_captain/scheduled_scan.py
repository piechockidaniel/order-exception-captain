"""Read-only scheduled scan use case and its local command-line runner."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from .domain import ScanActivity, ScanActivityStatus
from .order_source import JsonOrderFileSource, OrderSource, OrderSourceError
from .persistence import SqliteIncidentRepository
from .scanning import IncidentScanService, ScanResult
from .workflow import DeterministicCoordinator, TemplateSpecialistRunner


class ScheduledScanRecord(BaseModel):
    """Safe activity record emitted after a scan; source order details stay out of logs."""

    occurred_at: datetime
    mode: str = "read_only_scheduled_scan"
    scan: ScanResult


class ReadOnlyScheduledScan:
    """Loads an order snapshot and creates only approval-gated local incidents."""

    def __init__(
        self, source: OrderSource, scanner: IncidentScanService, activity_repository: SqliteIncidentRepository
    ) -> None:
        self._source = source
        self._scanner = scanner
        self._activity_repository = activity_repository

    def run_once(self) -> ScheduledScanRecord:
        occurred_at = datetime.now(timezone.utc)
        try:
            orders = self._source.load_orders()
            scan = self._scanner.scan(orders)
        except OrderSourceError as error:
            self._activity_repository.record_scan_activity(
                ScanActivity(
                    occurred_at=occurred_at,
                    mode="read_only_scheduled_scan",
                    status=ScanActivityStatus.FAILED,
                    detail=str(error),
                )
            )
            raise

        self._activity_repository.record_scan_activity(
            ScanActivity(
                occurred_at=occurred_at,
                mode="read_only_scheduled_scan",
                status=ScanActivityStatus.SUCCEEDED,
                scanned_orders=scan.scanned_orders,
                new_incident_count=len(scan.new_incident_ids),
                existing_incident_count=len(scan.existing_incident_ids),
                detail="Read-only source scan completed; no external action was attempted.",
            )
        )
        return ScheduledScanRecord(occurred_at=occurred_at, scan=scan)


def _build_job(order_path: Path, database_path: Path) -> ReadOnlyScheduledScan:
    source = JsonOrderFileSource(order_path)
    repository = SqliteIncidentRepository(database_path)
    scanner = IncidentScanService(DeterministicCoordinator(TemplateSpecialistRunner()), repository)
    return ReadOnlyScheduledScan(source, scanner, repository)


def _emit(record: ScheduledScanRecord) -> None:
    print(record.model_dump_json())


def _emit_failure(error: OrderSourceError) -> None:
    print(
        json.dumps(
            {
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "mode": "read_only_scheduled_scan",
                "status": "failed",
                "detail": str(error),
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read a local order JSON snapshot on a schedule and create local approval-gated incidents."
    )
    parser.add_argument("--orders", type=Path, required=True, help="Path to a read-only JSON order snapshot.")
    parser.add_argument("--database", type=Path, default=Path("data/order-exception-captain.sqlite3"))
    parser.add_argument("--interval-seconds", type=int, default=300, help="Seconds between scans; minimum 30.")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit.")
    args = parser.parse_args()
    if args.interval_seconds < 30:
        parser.error("--interval-seconds must be at least 30.")

    job = _build_job(args.orders, args.database)
    while True:
        try:
            _emit(job.run_once())
        except OrderSourceError as error:
            _emit_failure(error)
            if args.once:
                raise SystemExit(1) from error
        if args.once:
            return
        time.sleep(args.interval_seconds)
