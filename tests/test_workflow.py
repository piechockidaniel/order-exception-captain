from datetime import datetime, timedelta, timezone

from order_exception_captain.domain import CarrierStatus, IncidentStatus, Order, OrderLine, ResolutionKind
from order_exception_captain.workflow import DeterministicCoordinator, TemplateSpecialistRunner


class CapturingSpecialistRunner:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def run(self, role: str, prompt: str) -> str:
        self.prompts.append(prompt)
        return "Please call +48 123 456 789 or contact person@example.com."


def make_order(*, status: CarrierStatus, hours: int, promised_delta_days: int) -> Order:
    return Order(
        id="order-test",
        customer_name="Test Customer",
        customer_email="test@example.com",
        carrier="Test Carrier",
        carrier_status=status,
        hours_without_tracking_update=hours,
        promised_delivery_date=datetime.now(timezone.utc) + timedelta(days=promised_delta_days),
        total_amount=1000,
        currency="PLN",
        lines=[OrderLine(sku="SKU-1", title="Test item", quantity=1)],
    )


def test_stalled_late_order_runs_all_fixed_specialists_and_creates_approval_gated_draft() -> None:
    incident = DeterministicCoordinator(TemplateSpecialistRunner()).triage(
        make_order(status=CarrierStatus.STALLED, hours=48, promised_delta_days=0)
    )

    assert incident is not None
    assert incident.status is IncidentStatus.AWAITING_APPROVAL
    assert incident.drafts[0].kind is ResolutionKind.CARRIER_ESCALATION
    assert incident.drafts[0].requires_human_approval
    assert "No external system was changed" in incident.evidence_summary


def test_normal_in_transit_order_does_not_become_an_incident() -> None:
    incident = DeterministicCoordinator(TemplateSpecialistRunner()).triage(
        make_order(status=CarrierStatus.IN_TRANSIT, hours=10, promised_delta_days=2)
    )

    assert incident is None


def test_lost_order_selects_replacement_before_any_specialist_runs() -> None:
    incident = DeterministicCoordinator(TemplateSpecialistRunner()).triage(
        make_order(status=CarrierStatus.LOST, hours=1, promised_delta_days=1)
    )

    assert incident is not None
    assert incident.drafts[0].kind is ResolutionKind.REPLACEMENT


def test_specialist_prompts_minimise_customer_data_and_outputs_are_redacted() -> None:
    runner = CapturingSpecialistRunner()
    order = make_order(status=CarrierStatus.LOST, hours=1, promised_delta_days=1)
    order.customer_name = "Ada Customer"
    order.customer_email = "ada.customer@example.com"

    incident = DeterministicCoordinator(runner).triage(order)

    assert incident is not None
    prompts = " ".join(runner.prompts)
    assert "Ada Customer" not in prompts
    assert "ada.customer@example.com" not in prompts
    assert "[redacted phone]" in incident.customer_message_draft
    assert "[redacted email]" in incident.customer_message_draft
