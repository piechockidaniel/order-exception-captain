import json

import pytest

from order_exception_captain.order_source import JsonOrderFileSource, OrderSourceError
from order_exception_captain.persistence import SqliteIncidentRepository
from order_exception_captain.scheduled_scan import ReadOnlyScheduledScan
from order_exception_captain.scanning import IncidentScanService
from order_exception_captain.workflow import DeterministicCoordinator, TemplateSpecialistRunner


def write_orders(path) -> None:
    path.write_text(
        json.dumps(
            {
                "orders": [
                    {
                        "id": "scheduled-test",
                        "customer_name": "Scheduled Test Customer",
                        "customer_email": "scheduled-test@example.com",
                        "carrier": "Test Carrier",
                        "carrier_status": "stalled",
                        "hours_without_tracking_update": 52,
                        "promised_delivery_date": "2020-01-01T00:00:00Z",
                        "total_amount": 12900,
                        "currency": "PLN",
                        "lines": [{"sku": "SCHEDULED-01", "title": "Test item", "quantity": 1}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_read_only_scheduled_scan_loads_a_file_snapshot_and_is_idempotent(tmp_path) -> None:
    source_path = tmp_path / "orders.json"
    write_orders(source_path)
    source = JsonOrderFileSource(source_path)
    repository = SqliteIncidentRepository(tmp_path / "incidents.sqlite3")
    scanner = IncidentScanService(
        DeterministicCoordinator(TemplateSpecialistRunner()),
        repository,
    )
    job = ReadOnlyScheduledScan(source, scanner, repository)

    first = job.run_once()
    second = job.run_once()

    assert first.mode == "read_only_scheduled_scan"
    assert first.scan.new_incident_ids == ["delivery-scheduled-test-stalled"]
    assert second.scan.existing_incident_ids == ["delivery-scheduled-test-stalled"]
    assert source_path.read_text(encoding="utf-8").startswith("{")
    activity = repository.list_scan_activity()
    assert [record.status for record in activity] == ["succeeded", "succeeded"]
    assert activity[0].scanned_orders == 1
    assert activity[0].existing_incident_count == 1


def test_failed_scheduled_scan_records_a_safe_failure(tmp_path) -> None:
    repository = SqliteIncidentRepository(tmp_path / "incidents.sqlite3")
    scanner = IncidentScanService(DeterministicCoordinator(TemplateSpecialistRunner()), repository)
    job = ReadOnlyScheduledScan(JsonOrderFileSource(tmp_path / "missing.json"), scanner, repository)

    with pytest.raises(OrderSourceError, match="does not exist"):
        job.run_once()

    activity = repository.list_scan_activity()
    assert len(activity) == 1
    assert activity[0].status == "failed"
    assert activity[0].scanned_orders is None
    assert "missing.json" not in activity[0].detail


@pytest.mark.parametrize(
    "payload, message",
    [
        ("not json", "not valid JSON"),
        (json.dumps({"not_orders": []}), "orders list"),
    ],
)
def test_json_order_source_reports_safe_validation_failures(tmp_path, payload: str, message: str) -> None:
    source_path = tmp_path / "bad-orders.json"
    source_path.write_text(payload, encoding="utf-8")

    with pytest.raises(OrderSourceError, match=message):
        JsonOrderFileSource(source_path).load_orders()
