"""Read-only order sources kept separate from triage and outbound actions."""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from pydantic import ValidationError

from .domain import CarrierStatus, Order


class OrderSourceError(RuntimeError):
    """Raised when an input source cannot provide valid order records."""


class OrderSource(Protocol):
    """A source provides order snapshots; it has no write operations."""

    def load_orders(self) -> list[Order]:
        """Return the current read-only snapshot of orders."""


class JsonOrderFileSource:
    """Load a locally controlled JSON order snapshot without changing the source file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load_orders(self) -> list[Order]:
        try:
            raw_payload = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise OrderSourceError("The configured order snapshot does not exist.") from error
        except json.JSONDecodeError as error:
            raise OrderSourceError("The configured order snapshot is not valid JSON.") from error

        raw_orders = self._extract_orders(raw_payload)
        try:
            return [Order.model_validate(raw_order) for raw_order in raw_orders]
        except ValidationError as error:
            raise OrderSourceError("The configured order snapshot contains an invalid order.") from error

    @staticmethod
    def _extract_orders(payload: object) -> list[object]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, Mapping) and isinstance(payload.get("orders"), list):
            return payload["orders"]
        raise OrderSourceError("The configured order snapshot must be a JSON list or an object with an orders list.")


HttpGet = Callable[[str, Mapping[str, str], float], tuple[bytes, Mapping[str, str]]]


@dataclass(frozen=True)
class WooCommerceSourceConfiguration:
    """Non-secret settings plus read-only credentials for a WooCommerce source."""

    base_url: str
    consumer_key: str = field(repr=False)
    consumer_secret: str = field(repr=False)
    order_status: str = "completed"
    per_page: int = 100
    carrier_metadata_key: str = "_tracking_carrier"
    tracking_status_metadata_key: str = "_tracking_status"
    tracking_updated_at_metadata_key: str = "_tracking_updated_at"
    promised_delivery_date_metadata_key: str = "_promised_delivery_date"
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url.strip())
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("The WooCommerce source requires an HTTPS store URL.")
        if parsed.username or parsed.password or parsed.params or parsed.query or parsed.fragment:
            raise ValueError("The WooCommerce store URL must not include parameters, a query, or a fragment.")
        if not self.consumer_key.strip() or not self.consumer_secret.strip():
            raise ValueError("The WooCommerce source requires a consumer key and consumer secret.")
        if not self.order_status.strip():
            raise ValueError("The WooCommerce order status is required.")
        if not 1 <= self.per_page <= 100:
            raise ValueError("WooCommerce per-page must be between 1 and 100.")
        if not 1 <= self.timeout_seconds <= 30:
            raise ValueError("WooCommerce timeout must be between 1 and 30 seconds.")
        if not all(
            value.strip()
            for value in (
                self.carrier_metadata_key,
                self.tracking_status_metadata_key,
                self.tracking_updated_at_metadata_key,
                self.promised_delivery_date_metadata_key,
            )
        ):
            raise ValueError("WooCommerce tracking metadata keys must not be empty.")

    @property
    def orders_endpoint(self) -> str:
        return f"{self.base_url.strip().rstrip('/')}/wp-json/wc/v3/orders"

    @classmethod
    def is_environment_configured(cls, environment: Mapping[str, str] | None = None) -> bool:
        values = os.environ if environment is None else environment
        return all((values.get(name) or "").strip() for name in ("OEC_WOO_BASE_URL", "OEC_WOO_CONSUMER_KEY", "OEC_WOO_CONSUMER_SECRET"))

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "WooCommerceSourceConfiguration":
        values = os.environ if environment is None else environment
        required = ("OEC_WOO_BASE_URL", "OEC_WOO_CONSUMER_KEY", "OEC_WOO_CONSUMER_SECRET")
        if not all((values.get(name) or "").strip() for name in required):
            raise OrderSourceError(
                "WooCommerce is not configured. Set OEC_WOO_BASE_URL, OEC_WOO_CONSUMER_KEY, and OEC_WOO_CONSUMER_SECRET."
            )
        try:
            return cls(
                base_url=values["OEC_WOO_BASE_URL"],
                consumer_key=values["OEC_WOO_CONSUMER_KEY"],
                consumer_secret=values["OEC_WOO_CONSUMER_SECRET"],
                order_status=values.get("OEC_WOO_ORDER_STATUS", "completed"),
                per_page=int(values.get("OEC_WOO_PER_PAGE", "100")),
                carrier_metadata_key=values.get("OEC_WOO_CARRIER_METADATA_KEY", "_tracking_carrier"),
                tracking_status_metadata_key=values.get("OEC_WOO_TRACKING_STATUS_METADATA_KEY", "_tracking_status"),
                tracking_updated_at_metadata_key=values.get(
                    "OEC_WOO_TRACKING_UPDATED_AT_METADATA_KEY", "_tracking_updated_at"
                ),
                promised_delivery_date_metadata_key=values.get(
                    "OEC_WOO_PROMISED_DELIVERY_DATE_METADATA_KEY", "_promised_delivery_date"
                ),
                timeout_seconds=float(values.get("OEC_WOO_TIMEOUT_SECONDS", "10")),
            )
        except (TypeError, ValueError) as error:
            raise OrderSourceError("WooCommerce connector configuration is invalid.") from error


class WooCommerceOrderSource:
    """Read WooCommerce orders through GET requests and minimise customer data immediately.

    Tracking metadata is intentionally explicit because WooCommerce does not define
    a universal tracking schema.  Records without the configured status, tracking
    timestamp, and promised-delivery fields are skipped rather than guessed.
    """

    def __init__(
        self,
        configuration: WooCommerceSourceConfiguration,
        http_get: HttpGet | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._configuration = configuration
        self._http_get = http_get or self._default_http_get
        self._now = now or (lambda: datetime.now(timezone.utc))

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "WooCommerceOrderSource":
        return cls(WooCommerceSourceConfiguration.from_environment(environment))

    @property
    def safe_summary(self) -> str:
        parsed = urlparse(self._configuration.base_url)
        return (
            f"Read-only WooCommerce order source for {parsed.netloc}; status={self._configuration.order_status}; "
            "credentials are environment-only."
        )

    def load_orders(self) -> list[Order]:
        orders: list[Order] = []
        page = 1
        while True:
            response, headers = self._http_get(self._url_for_page(page), self._headers(), self._configuration.timeout_seconds)
            try:
                raw_orders = json.loads(response.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise OrderSourceError("WooCommerce returned an invalid order response.") from error
            if not isinstance(raw_orders, list):
                raise OrderSourceError("WooCommerce returned an unexpected order response.")

            now = self._normalise_datetime(self._now())
            for raw_order in raw_orders:
                if isinstance(raw_order, Mapping):
                    order = self._to_order(raw_order, now)
                    if order is not None:
                        orders.append(order)

            total_pages = self._total_pages(headers, default=page)
            if page >= total_pages or not raw_orders:
                return orders
            page += 1

    def _url_for_page(self, page: int) -> str:
        query = urlencode(
            {
                "status": self._configuration.order_status.strip(),
                "per_page": self._configuration.per_page,
                "page": page,
                "orderby": "modified",
                "order": "asc",
            }
        )
        return f"{self._configuration.orders_endpoint}?{query}"

    def _headers(self) -> dict[str, str]:
        credentials = f"{self._configuration.consumer_key}:{self._configuration.consumer_secret}".encode("utf-8")
        return {
            "Accept": "application/json",
            "Authorization": f"Basic {base64.b64encode(credentials).decode('ascii')}",
        }

    @staticmethod
    def _default_http_get(url: str, headers: Mapping[str, str], timeout_seconds: float) -> tuple[bytes, Mapping[str, str]]:
        request = Request(url, headers=dict(headers), method="GET")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - URL is validated as HTTPS configuration.
                return response.read(), dict(response.headers.items())
        except HTTPError as error:
            raise OrderSourceError(f"WooCommerce request failed with status {error.code}.") from error
        except URLError as error:
            raise OrderSourceError("WooCommerce request could not be completed.") from error

    @staticmethod
    def _total_pages(headers: Mapping[str, str], default: int) -> int:
        value = next((value for name, value in headers.items() if name.lower() == "x-wp-totalpages"), None)
        try:
            return max(default, int(value)) if value is not None else default
        except (TypeError, ValueError):
            return default

    def _to_order(self, raw_order: Mapping[str, object], now: datetime) -> Order | None:
        metadata = self._metadata(raw_order.get("meta_data"))
        status = self._carrier_status(metadata.get(self._configuration.tracking_status_metadata_key))
        tracking_updated_at = self._parse_datetime(metadata.get(self._configuration.tracking_updated_at_metadata_key))
        promised_delivery_date = self._parse_datetime(metadata.get(self._configuration.promised_delivery_date_metadata_key))
        raw_id = raw_order.get("id")
        if status is None or tracking_updated_at is None or promised_delivery_date is None or raw_id is None:
            return None

        try:
            order_id = f"woo-{str(raw_id).strip()}"
            if order_id == "woo-":
                return None
            return Order(
                id=order_id,
                customer_name=f"WooCommerce customer {order_id}",
                customer_email=f"{order_id}@example.com",
                carrier=self._carrier(raw_order, metadata),
                carrier_status=status,
                hours_without_tracking_update=max(0, int((now - tracking_updated_at).total_seconds() // 3_600)),
                promised_delivery_date=promised_delivery_date,
                total_amount=self._minor_amount(raw_order.get("total")),
                currency=str(raw_order.get("currency", "XXX")).upper(),
                lines=self._lines(raw_order.get("line_items")),
            )
        except (TypeError, ValueError, InvalidOperation, ValidationError):
            return None

    def _carrier(self, raw_order: Mapping[str, object], metadata: Mapping[str, object]) -> str:
        configured_carrier = metadata.get(self._configuration.carrier_metadata_key)
        if isinstance(configured_carrier, (str, int, float)) and str(configured_carrier).strip():
            return str(configured_carrier).strip()
        shipping_lines = raw_order.get("shipping_lines")
        if isinstance(shipping_lines, list):
            for line in shipping_lines:
                if isinstance(line, Mapping) and str(line.get("method_title", "")).strip():
                    return str(line["method_title"]).strip()
        return "WooCommerce carrier"

    @staticmethod
    def _metadata(raw_metadata: object) -> dict[str, object]:
        if not isinstance(raw_metadata, list):
            return {}
        return {
            str(item["key"]): item.get("value")
            for item in raw_metadata
            if isinstance(item, Mapping) and item.get("key") is not None
        }

    @staticmethod
    def _carrier_status(value: object) -> CarrierStatus | None:
        if not isinstance(value, str):
            return None
        normalised = value.strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "in_transit": "in_transit",
            "stalled": "stalled",
            "lost": "lost",
            "delivery_attempt_failed": "delivery_attempt_failed",
            "delivered": "delivered",
        }
        try:
            return CarrierStatus(aliases[normalised])
        except (KeyError, ValueError):
            return None

    @staticmethod
    def _normalise_datetime(value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

    @classmethod
    def _parse_datetime(cls, value: object) -> datetime | None:
        if isinstance(value, datetime):
            return cls._normalise_datetime(value)
        if not isinstance(value, str):
            return None
        try:
            return cls._normalise_datetime(datetime.fromisoformat(value.strip().replace("Z", "+00:00")))
        except ValueError:
            return None

    @staticmethod
    def _minor_amount(value: object) -> int:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return int(amount * 100)

    @staticmethod
    def _lines(raw_lines: object) -> list[dict[str, object]]:
        if not isinstance(raw_lines, list):
            return []
        lines: list[dict[str, object]] = []
        for item in raw_lines:
            if not isinstance(item, Mapping):
                continue
            try:
                quantity = int(item.get("quantity", 0))
            except (TypeError, ValueError):
                continue
            if quantity <= 0:
                continue
            lines.append(
                {
                    "sku": str(item.get("sku") or item.get("product_id") or "woo-item"),
                    "title": str(item.get("name") or "WooCommerce item"),
                    "quantity": quantity,
                }
            )
        return lines
