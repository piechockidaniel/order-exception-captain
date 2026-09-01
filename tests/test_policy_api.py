from fastapi.testclient import TestClient

from order_exception_captain.api import create_app
from order_exception_captain.domain import CarrierStatus, Order


OPERATOR_TOKEN = "test-operator-token-at-least-16-characters"
ADMIN_TOKEN = "test-admin-token-at-least-16-characters"


def stalled_order(order_id: str, hours: int = 24) -> dict:
    return {
        "id": order_id,
        "customer_name": "Policy API Customer",
        "customer_email": "policy-api@example.com",
        "carrier": "Demo Carrier",
        "carrier_status": "stalled",
        "hours_without_tracking_update": hours,
        "promised_delivery_date": "2020-01-01T00:00:00Z",
        "total_amount": 12900,
        "currency": "PLN",
        "lines": [],
    }


def custom_policy() -> dict:
    return {
        "name": "Faster stalled-delivery review",
        "administrator": "Policy Admin",
        "rules": [
            {
                "id": "stalled-24-hours",
                "label": "Stalled for 24 hours",
                "priority": 10,
                "carrier_status": "stalled",
                "resolution": "carrier_escalation",
                "reason": "tracking has been stalled for at least 24 hours",
                "minimum_hours_without_tracking_update": 24,
                "requires_promised_delivery_date_past": True,
            }
        ],
    }


def test_policy_is_visible_to_operators_but_only_a_separate_admin_token_can_publish(tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "incidents.sqlite3", operator_token=OPERATOR_TOKEN, admin_token=ADMIN_TOKEN))
    operator_headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    admin_headers = {**operator_headers, "X-OEC-Admin-Token": ADMIN_TOKEN}

    active = client.get("/policy")
    missing_admin = client.put("/admin/policy", headers=operator_headers, json=custom_policy())
    published = client.put("/admin/policy", headers=admin_headers, json=custom_policy())
    scanned = client.post("/scans", headers=operator_headers, json={"orders": [stalled_order("new-policy-order")]})
    incident = client.get("/incidents/delivery-new-policy-order-stalled", headers=operator_headers)

    assert active.status_code == 200
    assert active.json()["version"] == 1
    assert missing_admin.status_code == 403
    assert published.status_code == 200
    assert published.json()["version"] == 2
    assert published.json()["published_by"] == "Policy Admin"
    assert scanned.json()["new_incident_ids"] == ["delivery-new-policy-order-stalled"]
    assert incident.json()["policy_version"] == 2
    assert incident.json()["policy_rule_id"] == "stalled-24-hours"


def test_policy_simulation_is_non_network_and_does_not_publish_the_draft(tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "incidents.sqlite3", operator_token=OPERATOR_TOKEN, admin_token=ADMIN_TOKEN))
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}", "X-OEC-Admin-Token": ADMIN_TOKEN}
    request = {**custom_policy(), "order": stalled_order("simulated-order")}

    simulated = client.post("/admin/policy/simulate", headers=headers, json=request)
    active = client.get("/policy")

    assert simulated.status_code == 200
    assert simulated.json() == {
        "matched": True,
        "policy_version": 2,
        "rule_id": "stalled-24-hours",
        "reason": "tracking has been stalled for at least 24 hours",
        "resolution": "carrier_escalation",
        "external_action_attempted": False,
    }
    assert active.json()["version"] == 1


def test_woocommerce_scan_uses_admin_authority_and_only_injected_read_only_source(tmp_path) -> None:
    order = Order(
        id="woo-200",
        customer_name="WooCommerce customer woo-200",
        customer_email="woo-200@example.com",
        carrier="DPD",
        carrier_status=CarrierStatus.LOST,
        hours_without_tracking_update=0,
        promised_delivery_date="2020-01-01T00:00:00Z",
        total_amount=12900,
        currency="PLN",
        lines=[],
    )

    class Source:
        def load_orders(self) -> list[Order]:
            return [order]

    client = TestClient(
        create_app(
            tmp_path / "incidents.sqlite3",
            operator_token=OPERATOR_TOKEN,
            admin_token=ADMIN_TOKEN,
            woo_source_factory=Source,
        )
    )
    operator_headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    admin_headers = {**operator_headers, "X-OEC-Admin-Token": ADMIN_TOKEN}

    blocked = client.post("/admin/woocommerce/scan", headers=operator_headers)
    scanned = client.post("/admin/woocommerce/scan", headers=admin_headers)

    assert blocked.status_code == 403
    assert scanned.json()["new_incident_ids"] == ["delivery-woo-200-lost"]
    activity = client.get("/activity", headers=operator_headers).json()
    assert activity[0]["mode"] == "woocommerce_read_only_scan"
    assert "customer" not in activity[0]["detail"].lower()
