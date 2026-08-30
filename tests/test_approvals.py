import pytest

from order_exception_captain.approvals import ApprovalService
from order_exception_captain.domain import CarrierStatus, IncidentStatus, Order, OrderLine
from order_exception_captain.workflow import DeterministicCoordinator, TemplateSpecialistRunner


def make_lost_order(order_id: str) -> Order:
    return Order(
        id=order_id,
        customer_name="Test Customer",
        customer_email="test@example.com",
        carrier="Test Carrier",
        carrier_status=CarrierStatus.LOST,
        hours_without_tracking_update=0,
        promised_delivery_date="2026-08-01T00:00:00Z",
        total_amount=1000,
        currency="PLN",
        lines=[OrderLine(sku="SKU-1", title="Test item", quantity=1)],
    )


def test_approval_records_the_human_and_leaves_auditable_state() -> None:
    incident = DeterministicCoordinator(TemplateSpecialistRunner()).triage(make_lost_order("order-approval"))
    assert incident is not None

    approved = ApprovalService().approve(incident, "A. Operator")

    assert approved.status is IncidentStatus.APPROVED
    assert approved.drafts[0].approved_by == "A. Operator"
    assert approved.drafts[0].approved_at is not None


def test_approval_requires_a_named_operator() -> None:
    incident = DeterministicCoordinator(TemplateSpecialistRunner()).triage(make_lost_order("order-approval-empty"))
    assert incident is not None

    with pytest.raises(ValueError, match="approving operator"):
        ApprovalService().approve(incident, "  ")
