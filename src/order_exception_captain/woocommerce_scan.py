"""Explicit command for polling a configured WooCommerce source with GET requests only."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .order_source import OrderSourceError, WooCommerceOrderSource
from .persistence import SqliteIncidentRepository
from .scheduled_scan import ReadOnlyScheduledScan, ScheduledScanRecord
from .scanning import IncidentScanService
from .workflow import DeliveryExceptionPolicy, DeterministicCoordinator, TemplateSpecialistRunner


def _build_job(database_path: Path) -> ReadOnlyScheduledScan:
    repository = SqliteIncidentRepository(database_path)
    scanner = IncidentScanService(
        lambda: DeterministicCoordinator(
            TemplateSpecialistRunner(),
            policy=DeliveryExceptionPolicy(repository.get_active_policy()),
        ),
        repository,
    )
    return ReadOnlyScheduledScan(
        WooCommerceOrderSource.from_environment(),
        scanner,
        repository,
        mode="woocommerce_read_only_scan",
    )


def _emit(record: ScheduledScanRecord) -> None:
    print(record.model_dump_json())


def _emit_failure(error: OrderSourceError) -> None:
    print(
        json.dumps(
            {
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "mode": "woocommerce_read_only_scan",
                "status": "failed",
                "detail": str(error),
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read configured WooCommerce orders on a schedule. This command makes GET requests only."
    )
    parser.add_argument("--database", type=Path, default=Path("data/order-exception-captain.sqlite3"))
    parser.add_argument("--interval-seconds", type=int, default=300, help="Seconds between scans; minimum 30.")
    parser.add_argument("--once", action="store_true", help="Run one read-only scan and exit.")
    args = parser.parse_args()
    if args.interval_seconds < 30:
        parser.error("--interval-seconds must be at least 30.")

    try:
        job = _build_job(args.database)
    except OrderSourceError as error:
        _emit_failure(error)
        raise SystemExit(1) from error
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
