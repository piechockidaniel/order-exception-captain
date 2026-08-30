"""The controlled scan use case, kept independent from HTTP and scheduling."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .domain import Order
from .persistence import IncidentRepository
from .workflow import DeterministicCoordinator


class ScanResult(BaseModel):
    scanned_orders: int = Field(ge=0)
    new_incident_ids: list[str]
    existing_incident_ids: list[str]


class IncidentScanService:
    """Makes repeat scans safe by relying on deterministic incident IDs and SQLite uniqueness."""

    def __init__(self, coordinator: DeterministicCoordinator, repository: IncidentRepository) -> None:
        self._coordinator = coordinator
        self._repository = repository

    def scan(self, orders: list[Order], now: datetime | None = None) -> ScanResult:
        new_incident_ids: list[str] = []
        existing_incident_ids: list[str] = []
        for order in orders:
            incident = self._coordinator.triage(order, now)
            if incident is None:
                continue
            if self._repository.save_if_new(incident):
                new_incident_ids.append(incident.id)
            else:
                existing_incident_ids.append(incident.id)
        return ScanResult(
            scanned_orders=len(orders),
            new_incident_ids=new_incident_ids,
            existing_incident_ids=existing_incident_ids,
        )
