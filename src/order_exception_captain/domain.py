"""Small, explicit domain model for the delivery-exception workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class CarrierStatus(StrEnum):
    IN_TRANSIT = "in_transit"
    STALLED = "stalled"
    LOST = "lost"
    DELIVERY_ATTEMPT_FAILED = "delivery_attempt_failed"
    DELIVERED = "delivered"


class IncidentStatus(StrEnum):
    DETECTED = "detected"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    ACTIONED = "actioned"


class AuditEventType(StrEnum):
    INCIDENT_DETECTED = "incident_detected"
    INCIDENT_APPROVED = "incident_approved"


class ResolutionKind(StrEnum):
    CARRIER_ESCALATION = "carrier_escalation"
    REPLACEMENT = "replacement"
    REFUND = "refund"
    ADDRESS_CONFIRMATION = "address_confirmation"


class OrderLine(BaseModel):
    sku: str
    title: str
    quantity: int = Field(gt=0)


class Order(BaseModel):
    id: str
    customer_name: str
    customer_email: EmailStr
    carrier: str
    carrier_status: CarrierStatus
    hours_without_tracking_update: int = Field(ge=0)
    promised_delivery_date: datetime
    total_amount: int = Field(ge=0, description="Amount in minor currency units.")
    currency: str = Field(min_length=3, max_length=3)
    lines: list[OrderLine]


class DraftAction(BaseModel):
    id: str
    kind: ResolutionKind
    summary: str
    requires_human_approval: bool = True
    approved_by: str | None = None
    approved_at: datetime | None = None

    @property
    def is_approved(self) -> bool:
        return self.approved_by is not None


class Incident(BaseModel):
    id: str
    order_id: str
    reason: str
    status: IncidentStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_summary: str = ""
    policy_summary: str = ""
    customer_message_draft: str = ""
    drafts: list[DraftAction] = Field(default_factory=list)


class AuditEvent(BaseModel):
    id: int | None = None
    incident_id: str
    event_type: AuditEventType
    occurred_at: datetime
    actor: str | None = None
    detail: str
