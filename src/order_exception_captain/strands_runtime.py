"""Optional live Strands specialists.

This module is intentionally separate from the deterministic coordinator. It
lets the demo switch from fixture drafts to real Strands agents without giving
an LLM authority over routing or approvals.
"""

from __future__ import annotations

from strands import Agent, tool


@tool
def describe_delivery_evidence(order_id: str, carrier_status: str, hours_without_update: int) -> str:
    """Return the exact delivery facts supplied by the deterministic coordinator."""
    return (
        f"Order {order_id}; carrier status={carrier_status}; "
        f"hours without tracking update={hours_without_update}."
    )


class StrandsSpecialistRunner:
    """Executes fixed-role Strands agents one at a time when model access is configured."""

    def __init__(self) -> None:
        self._agents = {
            "evidence": Agent(
                name="delivery_evidence_specialist",
                description="Extracts factual delivery evidence without prescribing outcomes.",
                system_prompt="Return only factual evidence. Never recommend refunds, replacements, or external actions.",
                tools=[describe_delivery_evidence],
            ),
            "resolution": Agent(
                name="delivery_resolution_explainer",
                description="Explains a preselected delivery policy result without changing it.",
                system_prompt="Explain only the supplied resolution. You may not change, extend, or approve it.",
            ),
            "communications": Agent(
                name="customer_message_drafter",
                description="Drafts empathetic customer updates for operator review.",
                system_prompt="Draft a concise customer update. Do not promise compensation, replacement, or a delivery date.",
            ),
        }

    def run(self, role: str, prompt: str) -> str:
        try:
            agent = self._agents[role]
        except KeyError as exc:
            raise ValueError(f"Unknown specialist role: {role}") from exc
        return str(agent(prompt))
