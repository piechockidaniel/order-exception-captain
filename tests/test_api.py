from fastapi.testclient import TestClient

from order_exception_captain.api import create_app


def make_client(tmp_path) -> TestClient:
    return TestClient(create_app(tmp_path / "incidents.sqlite3"))


def delivery_exception_order(order_id: str = "order-api") -> dict:
    return {
        "id": order_id,
        "customer_name": "API Customer",
        "customer_email": "customer@example.com",
        "carrier": "Demo Carrier",
        "carrier_status": "stalled",
        "hours_without_tracking_update": 72,
        "promised_delivery_date": "2020-01-01T00:00:00Z",
        "total_amount": 12900,
        "currency": "PLN",
        "lines": [{"sku": "API-01", "title": "Demo item", "quantity": 1}],
    }


def normal_order() -> dict:
    order = delivery_exception_order("order-normal")
    order.update(
        carrier_status="in_transit",
        hours_without_tracking_update=2,
        promised_delivery_date="2099-01-01T00:00:00Z",
    )
    return order


def test_scan_creates_only_the_exception_and_repeat_scan_is_idempotent(tmp_path) -> None:
    client = make_client(tmp_path)
    body = {"orders": [delivery_exception_order(), normal_order()]}

    first = client.post("/scans", json=body)
    second = client.post("/scans", json=body)

    assert first.status_code == 200
    assert first.json() == {
        "scanned_orders": 2,
        "new_incident_ids": ["delivery-order-api-stalled"],
        "existing_incident_ids": [],
    }
    assert second.status_code == 200
    assert second.json()["new_incident_ids"] == []
    assert second.json()["existing_incident_ids"] == ["delivery-order-api-stalled"]
    incidents = client.get("/incidents").json()
    assert len(incidents) == 1
    assert incidents[0]["status"] == "awaiting_approval"


def test_approval_updates_the_draft_and_creates_an_audit_event(tmp_path) -> None:
    client = make_client(tmp_path)
    incident_id = "delivery-order-api-stalled"
    client.post("/scans", json={"orders": [delivery_exception_order()]})

    approved = client.post(f"/incidents/{incident_id}/approve", json={"operator": "Demo Operator"})
    events = client.get(f"/incidents/{incident_id}/events")

    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["drafts"][0]["approved_by"] == "Demo Operator"
    assert [event["event_type"] for event in events.json()] == ["incident_detected", "incident_approved"]
    assert events.json()[1]["actor"] == "Demo Operator"


def test_unknown_incident_returns_not_found(tmp_path) -> None:
    client = make_client(tmp_path)

    response = client.post("/incidents/missing/approve", json={"operator": "Demo Operator"})

    assert response.status_code == 404


def test_lost_and_failed_delivery_follow_their_own_deterministic_routes(tmp_path) -> None:
    client = make_client(tmp_path)
    lost = delivery_exception_order("order-lost")
    lost["carrier_status"] = "lost"
    failed_delivery = delivery_exception_order("order-address")
    failed_delivery["carrier_status"] = "delivery_attempt_failed"

    response = client.post("/scans", json={"orders": [lost, failed_delivery]})
    incidents = {incident["order_id"]: incident for incident in client.get("/incidents").json()}

    assert response.status_code == 200
    assert incidents["order-lost"]["drafts"][0]["kind"] == "replacement"
    assert incidents["order-address"]["drafts"][0]["kind"] == "address_confirmation"
