"""Deterministic routing around bounded Strands specialists.

The coordinator decides *which* work happens and *in what order*. A language
model may help specialists explain evidence or draft human-facing language, but
it never decides whether the system refunds, replaces, or contacts a customer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .delivery_policy import DeliveryPolicyDocument, default_delivery_policy
from .domain import DraftAction, Incident, IncidentStatus, Order, ResolutionKind
from .redaction import redact_text


class SpecialistRunner(Protocol):
    def run(self, role: str, prompt: str) -> str:
        """Run one named specialist and return only its draft/evidence text."""


@dataclass(frozen=True)
class Route:
    reason: str
    resolution: ResolutionKind
    policy_version: int
    policy_rule_id: str


class DeliveryExceptionPolicy:
    """Pure, testable policy. No model output influences this decision."""

    def __init__(self, document: DeliveryPolicyDocument | None = None) -> None:
        self._document = document or default_delivery_policy()

    @property
    def document(self) -> DeliveryPolicyDocument:
        return self._document

    def route(self, order: Order, now: datetime) -> Route | None:
        for rule in sorted(self._document.rules, key=lambda item: item.priority):
            if order.carrier_status != rule.carrier_status:
                continue
            if (
                rule.minimum_hours_without_tracking_update is not None
                and order.hours_without_tracking_update < rule.minimum_hours_without_tracking_update
            ):
                continue
            if rule.requires_promised_delivery_date_past and order.promised_delivery_date > now:
                continue
            return Route(
                reason=rule.reason,
                resolution=rule.resolution,
                policy_version=self._document.version,
                policy_rule_id=rule.id,
            )
        return None


class DeterministicCoordinator:
    """Runs a fixed evidence → policy → communication sequence for an incident."""

    def __init__(self, runner: SpecialistRunner, policy: DeliveryExceptionPolicy | None = None) -> None:
        self._runner = runner
        self._policy = policy or DeliveryExceptionPolicy()

    def triage(self, order: Order, now: datetime | None = None) -> Incident | None:
        now = now or datetime.now(timezone.utc)
        route = self._policy.route(order, now)
        if route is None:
            return None

        incident_id = f"delivery-{order.id}-{order.carrier_status}"
        evidence = redact_text(self._runner.run("evidence", self._evidence_prompt(order, route)))
        policy_summary = redact_text(self._runner.run("resolution", self._policy_prompt(order, route, evidence)))
        customer_message = redact_text(
            self._runner.run("communications", self._message_prompt(order, route, policy_summary))
        )

        draft = DraftAction(
            id=f"draft-{incident_id}",
            kind=route.resolution,
            summary=self._draft_summary(order, route),
        )
        return Incident(
            id=incident_id,
            order_id=order.id,
            reason=route.reason,
            status=IncidentStatus.AWAITING_APPROVAL,
            evidence_summary=evidence,
            policy_summary=policy_summary,
            customer_message_draft=customer_message,
            drafts=[draft],
            policy_version=route.policy_version,
            policy_rule_id=route.policy_rule_id,
        )

    @staticmethod
    def _evidence_prompt(order: Order, route: Route) -> str:
        return (
            "Summarise the delivery evidence in three factual bullets. Do not recommend an action. "
            f"Order={order.id}; carrier={order.carrier}; status={order.carrier_status}; "
            f"hours_without_update={order.hours_without_tracking_update}; trigger={route.reason}."
        )

    @staticmethod
    def _policy_prompt(order: Order, route: Route, evidence: str) -> str:
        return (
            "Explain the preselected resolution in two concise bullets. Do not change it and do not invent policy. "
            f"Order={order.id}; resolution={route.resolution}; evidence={evidence}"
        )

    @staticmethod
    def _message_prompt(order: Order, route: Route, policy_summary: str) -> str:
        return (
            "Draft a warm, plain-language customer update under 80 words. State that the operator will review "
            "the next step; do not promise a refund, replacement, or delivery date. "
            f"Customer=customer; order={order.id}; resolution_under_review={route.resolution}; "
            f"context={policy_summary}"
        )

    @staticmethod
    def _draft_summary(order: Order, route: Route) -> str:
        return f"{route.resolution.replace('_', ' ').title()} draft for {order.id}; approval required before any external action."


class TemplateSpecialistRunner:
    """Deterministic demo runner used in tests and without cloud credentials."""

    def run(self, role: str, prompt: str) -> str:
        if role == "evidence":
            return "• Carrier status and tracking inactivity crossed the configured incident threshold.\n• The order is past its promised date.\n• No external system was changed."
        if role == "resolution":
            return "• The proposed resolution was selected by the delivery policy.\n• An operator must approve any customer-facing or carrier action."
        if role == "communications":
            return "We are reviewing a delay affecting your order and will update you shortly. Thank you for your patience."
        raise ValueError(f"Unknown specialist role: {role}")
