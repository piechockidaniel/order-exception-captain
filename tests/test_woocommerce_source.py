import base64
import json
from datetime import datetime, timezone

import pytest

from order_exception_captain.order_source import WooCommerceOrderSource, WooCommerceSourceConfiguration


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def order_payload(order_id: int, status: str = "stalled") -> dict:
    return {
        "id": order_id,
        "currency": "PLN",
        "total": "129.00",
        "shipping_lines": [{"method_title": "DPD"}],
        "line_items": [{"sku": "WOOD-01", "name": "Wooden train", "quantity": 2}],
        "billing": {"first_name": "Never", "email": "persisted@example.com"},
        "meta_data": [
            {"key": "_tracking_carrier", "value": "DPD"},
            {"key": "_tracking_status", "value": status},
            {"key": "_tracking_updated_at", "value": "2026-08-28T10:00:00Z"},
            {"key": "_promised_delivery_date", "value": "2026-08-30T10:00:00Z"},
        ],
    }


def configuration() -> WooCommerceSourceConfiguration:
    return WooCommerceSourceConfiguration(
        base_url="https://shop.example.test",
        consumer_key="ck_not_in_url",
        consumer_secret="cs_never_persisted",
        per_page=2,
    )


def test_woocommerce_source_reads_paginated_orders_with_basic_auth_and_minimises_customer_data() -> None:
    calls: list[tuple[str, dict[str, str]]] = []
    pages = [
        json.dumps([order_payload(101), {"id": 102, "meta_data": []}]).encode(),
        json.dumps([order_payload(103, status="lost")]).encode(),
    ]

    def http_get(url: str, headers: dict[str, str], timeout: float):
        calls.append((url, headers))
        return pages[len(calls) - 1], {"X-WP-TotalPages": "2"}

    source = WooCommerceOrderSource(configuration(), http_get=http_get, now=lambda: NOW)
    orders = source.load_orders()

    assert [order.id for order in orders] == ["woo-101", "woo-103"]
    assert orders[0].customer_name == "WooCommerce customer woo-101"
    assert str(orders[0].customer_email) == "woo-101@example.com"
    assert orders[0].hours_without_tracking_update == 86
    assert orders[0].total_amount == 12900
    assert orders[0].lines[0].sku == "WOOD-01"
    assert len(calls) == 2
    assert all("consumer" not in url and "ck_not_in_url" not in url and "cs_never_persisted" not in url for url, _ in calls)
    assert base64.b64decode(calls[0][1]["Authorization"].removeprefix("Basic ")).decode() == "ck_not_in_url:cs_never_persisted"
    assert "cs_never_persisted" not in source.safe_summary


def test_woocommerce_source_requires_https_and_complete_environment_configuration() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        WooCommerceSourceConfiguration("http://shop.example.test", "ck", "cs")
    with pytest.raises(ValueError, match="must not include"):
        WooCommerceSourceConfiguration("https://ck:cs@shop.example.test", "ck", "cs")
    assert not WooCommerceSourceConfiguration.is_environment_configured({"OEC_WOO_BASE_URL": "https://shop.example.test"})
    assert WooCommerceSourceConfiguration.is_environment_configured(
        {
            "OEC_WOO_BASE_URL": "https://shop.example.test",
            "OEC_WOO_CONSUMER_KEY": "ck",
            "OEC_WOO_CONSUMER_SECRET": "cs",
        }
    )


def test_woocommerce_source_skips_records_without_usable_tracking_metadata() -> None:
    response = json.dumps([order_payload(101, status="unsupported"), {"id": 102, "meta_data": []}]).encode()
    source = WooCommerceOrderSource(configuration(), http_get=lambda *_: (response, {}), now=lambda: NOW)

    assert source.load_orders() == []


def test_default_woocommerce_transport_uses_get_without_putting_credentials_in_the_url(monkeypatch) -> None:
    observed: dict[str, object] = {}

    class Response:
        headers = {"X-WP-TotalPages": "1"}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self) -> bytes:
            return json.dumps([order_payload(104)]).encode()

    def fake_urlopen(request, timeout: float):
        observed["method"] = request.get_method()
        observed["url"] = request.full_url
        observed["authorization"] = request.get_header("Authorization")
        observed["timeout"] = timeout
        return Response()

    monkeypatch.setattr("order_exception_captain.order_source.urlopen", fake_urlopen)
    source = WooCommerceOrderSource(configuration(), now=lambda: NOW)

    assert [order.id for order in source.load_orders()] == ["woo-104"]
    assert observed["method"] == "GET"
    assert "ck_not_in_url" not in str(observed["url"])
    assert "cs_never_persisted" not in str(observed["url"])
    assert str(observed["authorization"]).startswith("Basic ")
