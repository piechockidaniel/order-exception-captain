"""Explicit, secret-free configuration for the optional live Strands demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from os import environ
from typing import Mapping, TypeAlias

MINIMUM_LIVE_MAX_TOKENS = 128
MAXIMUM_LIVE_MAX_TOKENS = 4096


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
        if not MINIMUM_LIVE_MAX_TOKENS <= max_tokens <= MAXIMUM_LIVE_MAX_TOKENS:
            raise LiveConfigurationError(
                "OEC_MAX_TOKENS must be between 128 and 4096 so a specialist can "
                "complete a bounded tool-assisted response."
            )

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


@dataclass(frozen=True)
class BedrockProviderConfiguration:
    """Runtime-only settings for a bounded Amazon Bedrock Strands invocation."""

    model_id: str
    region_name: str
    max_tokens: int = 300
    cost_boundary: str = ""

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "BedrockProviderConfiguration":
        source = environ if environment is None else environment
        provider = source.get("OEC_MODEL_PROVIDER", "").strip().lower()
        if provider != "bedrock":
            raise LiveConfigurationError(
                "Set OEC_MODEL_PROVIDER=bedrock to explicitly select the live provider."
            )

        model_id = source.get("OEC_MODEL_ID", "").strip()
        region_name = source.get("AWS_REGION", "").strip()
        cost_boundary = source.get("OEC_COST_BOUNDARY", "").strip()
        if not model_id:
            raise LiveConfigurationError("Set OEC_MODEL_ID to a Bedrock model enabled for this account.")
        if not region_name:
            raise LiveConfigurationError("Set AWS_REGION for the enabled Bedrock model.")
        if not cost_boundary:
            raise LiveConfigurationError(
                "Set OEC_COST_BOUNDARY to a human-approved spend boundary before a live call."
            )

        raw_max_tokens = source.get("OEC_MAX_TOKENS", "300").strip()
        try:
            max_tokens = int(raw_max_tokens)
        except ValueError as exc:
            raise LiveConfigurationError("OEC_MAX_TOKENS must be a whole number.") from exc
        if not MINIMUM_LIVE_MAX_TOKENS <= max_tokens <= MAXIMUM_LIVE_MAX_TOKENS:
            raise LiveConfigurationError(
                "OEC_MAX_TOKENS must be between 128 and 4096 so a specialist can "
                "complete a bounded tool-assisted response."
            )

        return cls(
            model_id=model_id,
            region_name=region_name,
            max_tokens=max_tokens,
            cost_boundary=cost_boundary,
        )

    def safe_summary(self) -> dict[str, str | int]:
        """Return run metadata without resolving or exposing AWS credentials."""
        return {
            "provider": "bedrock",
            "model_id": self.model_id,
            "aws_region": self.region_name,
            "max_tokens_per_specialist": self.max_tokens,
            "specialist_count": 3,
            "cost_boundary": self.cost_boundary,
        }


LiveProviderConfiguration: TypeAlias = OpenAIProviderConfiguration | BedrockProviderConfiguration


def load_live_configuration(
    environment: Mapping[str, str] | None = None,
) -> LiveProviderConfiguration:
    """Load only the provider explicitly named in the local environment."""
    source = environ if environment is None else environment
    provider = source.get("OEC_MODEL_PROVIDER", "").strip().lower()
    if provider == "openai":
        return OpenAIProviderConfiguration.from_environment(source)
    if provider == "bedrock":
        return BedrockProviderConfiguration.from_environment(source)
    raise LiveConfigurationError("Set OEC_MODEL_PROVIDER to either bedrock or openai before a live call.")


def build_live_model(
    configuration: LiveProviderConfiguration, *, boto_session: object | None = None
):
    """Build the selected Strands model after non-secret configuration validation.

    ``boto_session`` is intentionally optional. Production uses the ambient AWS
    credential chain; tests can supply a static, non-networked session so their
    result does not depend on a developer's active AWS profile.
    """
    if isinstance(configuration, OpenAIProviderConfiguration):
        return build_openai_model(configuration)

    from botocore.exceptions import MissingDependencyException
    from strands.models import BedrockModel

    try:
        if boto_session is not None:
            return BedrockModel(
                boto_session=boto_session,
                model_id=configuration.model_id,
                max_tokens=configuration.max_tokens,
                temperature=0,
            )

        return BedrockModel(
            model_id=configuration.model_id,
            region_name=configuration.region_name,
            max_tokens=configuration.max_tokens,
            temperature=0,
        )
    except MissingDependencyException as exc:
        raise LiveConfigurationError(
            "The configured AWS login profile requires CRT support. Run `uv sync` "
            "to install this project's botocore[crt] dependency, then retry."
        ) from exc
