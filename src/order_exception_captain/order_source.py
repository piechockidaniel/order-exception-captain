"""Read-only order sources kept separate from triage and outbound actions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from .domain import Order


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
