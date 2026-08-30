"""Explicit, secret-free configuration for the optional live Strands demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from os import environ
from typing import Mapping


class LiveConfigurationError(ValueError):
    """Raised before a live model call when its declared boundary is incomplete."""


@dataclass(frozen=True)
class OpenAIProviderConfiguration:
    """Runtime-only settings for a bounded OpenAI-backed Strands invocation."""

    model_id: str
    api_key: str = field(repr=False, compare=False)
    max_tokens: int = 300
    cost_boundary: str = ""

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "OpenAIProviderConfiguration":
        source = environ if environment is None else environment
        provider = source.get("OEC_MODEL_PROVIDER", "").strip().lower()
        if provider != "openai":
            raise LiveConfigurationError(
                "Set OEC_MODEL_PROVIDER=openai to explicitly select the live provider."
            )

        model_id = source.get("OEC_MODEL_ID", "").strip()
        api_key = source.get("OPENAI_API_KEY", "").strip()
        cost_boundary = source.get("OEC_COST_BOUNDARY", "").strip()
        if not model_id:
            raise LiveConfigurationError("Set OEC_MODEL_ID to the approved model identifier.")
        if not api_key:
            raise LiveConfigurationError(
                "Set OPENAI_API_KEY in the local environment; never store it in this repository."
            )
        if not cost_boundary:
            raise LiveConfigurationError(
                "Set OEC_COST_BOUNDARY to a human-approved spend boundary before a live call."
            )

        raw_max_tokens = source.get("OEC_MAX_TOKENS", "300").strip()
        try:
            max_tokens = int(raw_max_tokens)
        except ValueError as exc:
            raise LiveConfigurationError("OEC_MAX_TOKENS must be a whole number.") from exc
        if not 1 <= max_tokens <= 4096:
            raise LiveConfigurationError("OEC_MAX_TOKENS must be between 1 and 4096.")

        return cls(
            model_id=model_id,
            api_key=api_key,
            max_tokens=max_tokens,
            cost_boundary=cost_boundary,
        )

    def safe_summary(self) -> dict[str, str | int]:
        """Return audit-safe metadata without exposing the API key."""
        return {
            "provider": "openai",
            "model_id": self.model_id,
            "max_tokens_per_specialist": self.max_tokens,
            "specialist_count": 3,
            "cost_boundary": self.cost_boundary,
        }


def build_openai_model(configuration: OpenAIProviderConfiguration):
    """Build a Strands model only after explicit runtime configuration succeeds."""
    from strands.models.openai import OpenAIModel

    return OpenAIModel(
        client_args={"api_key": configuration.api_key},
        model_id=configuration.model_id,
        params={"max_tokens": configuration.max_tokens, "temperature": 0},
    )
