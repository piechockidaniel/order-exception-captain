"""Versioned, declarative delivery policy rules.

The policy deliberately describes only deterministic conditions and proposed
resolutions.  It cannot contain prompts, executable code, webhooks, or any
outbound action.  Human approval remains required after a rule matches.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

from .domain import CarrierStatus, ResolutionKind


class DeliveryPolicyRule(BaseModel):
    """One ordered, declarative rule in the delivery policy pack."""

    id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*$")
    label: str = Field(min_length=3, max_length=120)
    priority: int = Field(ge=1, le=1_000)
    carrier_status: CarrierStatus
    resolution: ResolutionKind
    reason: str = Field(min_length=8, max_length=300)
    minimum_hours_without_tracking_update: int | None = Field(default=None, ge=0, le=8_760)
    requires_promised_delivery_date_past: bool = False

    @field_validator("label", "reason")
    @classmethod
    def require_meaningful_text(cls, value: str) -> str:
        normalised = value.strip()
        if not normalised:
            raise ValueError("A policy rule needs meaningful text.")
        return normalised


class DeliveryPolicyDraft(BaseModel):
    """Administrator-supplied policy data before a server assigns its version."""

    name: str = Field(min_length=3, max_length=120)
    rules: list[DeliveryPolicyRule] = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def require_meaningful_name(cls, value: str) -> str:
        normalised = value.strip()
        if not normalised:
            raise ValueError("A policy needs a name.")
        return normalised

    @model_validator(mode="after")
    def require_unambiguous_rule_order(self) -> "DeliveryPolicyDraft":
        rule_ids = [rule.id for rule in self.rules]
        priorities = [rule.priority for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("Every policy rule must have a unique identifier.")
        if len(priorities) != len(set(priorities)):
            raise ValueError("Every policy rule must have a unique priority.")
        return self

    def versioned(self, version: int, published_by: str, published_at: datetime | None = None) -> "DeliveryPolicyDocument":
        return DeliveryPolicyDocument(
            version=version,
            name=self.name,
            rules=self.rules,
            published_by=published_by.strip(),
            published_at=published_at or datetime.now(timezone.utc),
        )


class DeliveryPolicyDocument(DeliveryPolicyDraft):
    """An immutable policy version stored with its publication metadata."""

    version: int = Field(ge=1)
    published_by: str = Field(min_length=1, max_length=120)
    published_at: datetime


def default_delivery_policy() -> DeliveryPolicyDocument:
    """Return the historical fixed rules as policy version one."""
    return DeliveryPolicyDraft(
        name="Default delivery exception policy",
        rules=[
            DeliveryPolicyRule(
                id="lost-parcel",
                label="Lost parcel",
                priority=10,
                carrier_status=CarrierStatus.LOST,
                resolution=ResolutionKind.REPLACEMENT,
                reason="carrier marked the parcel as lost",
            ),
            DeliveryPolicyRule(
                id="delivery-address-confirmation",
                label="Delivery attempt failed",
                priority=20,
                carrier_status=CarrierStatus.DELIVERY_ATTEMPT_FAILED,
                resolution=ResolutionKind.ADDRESS_CONFIRMATION,
                reason="carrier needs a confirmed delivery address",
            ),
            DeliveryPolicyRule(
                id="stalled-after-promise-date",
                label="Stalled after promised date",
                priority=30,
                carrier_status=CarrierStatus.STALLED,
                resolution=ResolutionKind.CARRIER_ESCALATION,
                reason="tracking has been stalled for at least 48 hours after the promise date",
                minimum_hours_without_tracking_update=48,
                requires_promised_delivery_date_past=True,
            ),
        ],
    ).versioned(version=1, published_by="system")
