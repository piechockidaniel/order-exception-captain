"""Optional live Strands specialists.

This module is intentionally separate from the deterministic coordinator. It
lets the demo switch from fixture drafts to real Strands agents without giving
an LLM authority over routing or approvals.
"""

from __future__ import annotations

from collections.abc import Callable

from strands import Agent, tool

from .live_configuration import (
    BedrockProviderConfiguration,
    LiveProviderConfiguration,
    OpenAIProviderConfiguration,
    build_live_model,
)


@tool
def describe_delivery_evidence(order_id: str, carrier_status: str, hours_without_update: int) -> str:
    """Return the exact delivery facts supplied by the deterministic coordinator."""
    return (
        f"Order {order_id}; carrier status={carrier_status}; "
        f"hours without tracking update={hours_without_update}."
    )


class StrandsSpecialistRunner:
    """Executes fixed-role Strands agents one at a time when model access is configured."""

    def __init__(self, model_factory: Callable[[], object]) -> None:
        self._agents = {
            "evidence": Agent(
                name="delivery_evidence_specialist",
                description="Extracts factual delivery evidence without prescribing outcomes.",
                system_prompt="Return only factual evidence. Never recommend refunds, replacements, or external actions.",
                tools=[describe_delivery_evidence],
                model=model_factory(),
            ),
            "resolution": Agent(
                name="delivery_resolution_explainer",
                description="Explains a preselected delivery policy result without changing it.",
                system_prompt="Explain only the supplied resolution. You may not change, extend, or approve it.",
                model=model_factory(),
            ),
            "communications": Agent(
                name="customer_message_drafter",
                description="Drafts empathetic customer updates for operator review.",
                system_prompt="Draft a concise customer update. Do not promise compensation, replacement, or a delivery date.",
                model=model_factory(),
            ),
        }

    @classmethod
    def from_openai_configuration(
        cls, configuration: OpenAIProviderConfiguration
    ) -> "StrandsSpecialistRunner":
        return cls.from_live_configuration(configuration)

    @classmethod
    def from_bedrock_configuration(
        cls, configuration: BedrockProviderConfiguration
    ) -> "StrandsSpecialistRunner":
        return cls.from_live_configuration(configuration)

    @classmethod
    def from_live_configuration(
        cls, configuration: LiveProviderConfiguration
    ) -> "StrandsSpecialistRunner":
        return cls(lambda: build_live_model(configuration))

    def run(self, role: str, prompt: str) -> str:
        try:
            agent = self._agents[role]
        except KeyError as exc:
            raise ValueError(f"Unknown specialist role: {role}") from exc
        return str(agent(prompt))
