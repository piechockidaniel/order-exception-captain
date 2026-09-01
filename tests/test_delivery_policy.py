from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from order_exception_captain.delivery_policy import DeliveryPolicyDraft, DeliveryPolicyRule, default_delivery_policy
from order_exception_captain.domain import CarrierStatus, Order, ResolutionKind
from order_exception_captain.workflow import DeliveryExceptionPolicy


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def make_order(**changes) -> Order:
    values = {
        "id": "policy-order",
        "customer_name": "Policy Customer",
        "customer_email": "policy@example.com",
        "carrier": "Demo Carrier",
        "carrier_status": CarrierStatus.STALLED,
        "hours_without_tracking_update": 48,
        "promised_delivery_date": datetime(2026, 8, 31, tzinfo=timezone.utc),
        "total_amount": 12900,
        "currency": "PLN",
        "lines": [],
    }
    values.update(changes)
    return Order(**values)


def test_default_policy_preserves_the_original_delivery_routes() -> None:
    policy = DeliveryExceptionPolicy(default_delivery_policy())

    stalled = policy.route(make_order(), NOW)
    lost = policy.route(make_order(carrier_status=CarrierStatus.LOST, hours_without_tracking_update=0), NOW)
    failed = policy.route(
        make_order(carrier_status=CarrierStatus.DELIVERY_ATTEMPT_FAILED, hours_without_tracking_update=0), NOW
    )
    not_late = policy.route(make_order(promised_delivery_date=datetime(2026, 9, 2, tzinfo=timezone.utc)), NOW)

    assert (stalled.reason, stalled.resolution, stalled.policy_version, stalled.policy_rule_id) == (
        "tracking has been stalled for at least 48 hours after the promise date",
        ResolutionKind.CARRIER_ESCALATION,
        1,
        "stalled-after-promise-date",
    )
    assert lost.resolution is ResolutionKind.REPLACEMENT
    assert failed.resolution is ResolutionKind.ADDRESS_CONFIRMATION
    assert not_late is None


def test_administrator_policy_uses_priority_and_declared_conditions() -> None:
    document = DeliveryPolicyDraft(
        name="Expedited stalled-delivery review",
        rules=[
            DeliveryPolicyRule(
                id="stalled-24-hours",
                label="Stalled for a day",
                priority=20,
                carrier_status="stalled",
                resolution="carrier_escalation",
                reason="tracking has been stalled for at least 24 hours",
                minimum_hours_without_tracking_update=24,
            ),
            DeliveryPolicyRule(
                id="lost-first",
                label="Lost parcel",
                priority=10,
                carrier_status="lost",
                resolution="replacement",
                reason="carrier marked the parcel as lost",
            ),
        ],
    ).versioned(version=7, published_by="Policy Admin", published_at=NOW)

    route = DeliveryExceptionPolicy(document).route(make_order(hours_without_tracking_update=24), NOW)

    assert route is not None
    assert route.policy_version == 7
    assert route.policy_rule_id == "stalled-24-hours"
    assert route.resolution is ResolutionKind.CARRIER_ESCALATION


def test_policy_rejects_ambiguous_rule_order_and_duplicate_identifiers() -> None:
    first = DeliveryPolicyRule(
        id="first-rule",
        label="First rule",
        priority=10,
        carrier_status="lost",
        resolution="replacement",
        reason="carrier marked the parcel as lost",
    )
    second = first.model_copy(update={"id": "second-rule"})

    with pytest.raises(ValidationError, match="unique priority"):
        DeliveryPolicyDraft(name="Ambiguous policy", rules=[first, second])
    with pytest.raises(ValidationError, match="unique identifier"):
        DeliveryPolicyDraft(name="Duplicate identifiers", rules=[first, first.model_copy(update={"priority": 20})])
