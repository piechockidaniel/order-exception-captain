import boto3
import pytest

from order_exception_captain.live_configuration import (
    BedrockProviderConfiguration,
    LiveConfigurationError,
    OpenAIProviderConfiguration,
    build_live_model,
    load_live_configuration,
)
from order_exception_captain.strands_runtime import StrandsSpecialistRunner


def live_environment(**overrides: str) -> dict[str, str]:
    values = {
        "OEC_MODEL_PROVIDER": "openai",
        "OEC_MODEL_ID": "approved-test-model",
        "OPENAI_API_KEY": "test-key-not-a-secret",
        "OEC_COST_BOUNDARY": "Synthetic smoke test only; operator-approved limit.",
        "OEC_MAX_TOKENS": "128",
    }
    values.update(overrides)
    return values


def bedrock_environment(**overrides: str) -> dict[str, str]:
    values = {
        "OEC_MODEL_PROVIDER": "bedrock",
        "OEC_MODEL_ID": "amazon.nova-lite-v1:0",
        "AWS_REGION": "us-east-1",
        "OEC_COST_BOUNDARY": "Synthetic three-specialist smoke test; approved spend limit.",
        "OEC_MAX_TOKENS": "128",
    }
    values.update(overrides)
    return values


def test_live_configuration_is_explicit_and_never_exposes_the_api_key() -> None:
    configuration = OpenAIProviderConfiguration.from_environment(live_environment())

    assert configuration.safe_summary() == {
        "provider": "openai",
        "model_id": "approved-test-model",
        "max_tokens_per_specialist": 128,
        "specialist_count": 3,
        "cost_boundary": "Synthetic smoke test only; operator-approved limit.",
    }
    assert "test-key-not-a-secret" not in repr(configuration)


def test_live_runner_configures_exactly_the_three_bounded_specialists() -> None:
    runner = StrandsSpecialistRunner.from_openai_configuration(
        OpenAIProviderConfiguration.from_environment(live_environment())
    )

    assert set(runner._agents) == {"evidence", "resolution", "communications"}


def test_bedrock_configuration_builds_with_an_explicit_non_networked_session() -> None:
    configuration = BedrockProviderConfiguration.from_environment(bedrock_environment())
    session = boto3.Session(
        aws_access_key_id="test-access-key",
        aws_secret_access_key="test-secret-key",
        region_name=configuration.region_name,
    )
    model = build_live_model(configuration, boto_session=session)
    runner = StrandsSpecialistRunner(
        lambda: build_live_model(configuration, boto_session=session)
    )

    assert configuration.safe_summary() == {
        "provider": "bedrock",
        "model_id": "amazon.nova-lite-v1:0",
        "aws_region": "us-east-1",
        "max_tokens_per_specialist": 128,
        "specialist_count": 3,
        "cost_boundary": "Synthetic three-specialist smoke test; approved spend limit.",
    }
    assert model.config["model_id"] == "amazon.nova-lite-v1:0"
    assert model.client.meta.region_name == "us-east-1"
    assert set(runner._agents) == {"evidence", "resolution", "communications"}


def test_live_configuration_selects_only_an_explicit_provider() -> None:
    assert isinstance(load_live_configuration(live_environment()), OpenAIProviderConfiguration)
    assert isinstance(load_live_configuration(bedrock_environment()), BedrockProviderConfiguration)

    with pytest.raises(LiveConfigurationError, match="either bedrock or openai"):
        load_live_configuration({"OEC_MODEL_PROVIDER": "other"})


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"OEC_MODEL_PROVIDER": ""}, "OEC_MODEL_PROVIDER"),
        ({"OEC_MODEL_ID": ""}, "OEC_MODEL_ID"),
        ({"OPENAI_API_KEY": ""}, "OPENAI_API_KEY"),
        ({"OEC_COST_BOUNDARY": ""}, "OEC_COST_BOUNDARY"),
        ({"OEC_MAX_TOKENS": "127"}, "OEC_MAX_TOKENS"),
    ],
)
def test_live_configuration_rejects_missing_or_invalid_boundaries(
    overrides: dict[str, str], message: str
) -> None:
    with pytest.raises(LiveConfigurationError, match=message):
        OpenAIProviderConfiguration.from_environment(live_environment(**overrides))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"OEC_MODEL_ID": ""}, "OEC_MODEL_ID"),
        ({"AWS_REGION": ""}, "AWS_REGION"),
        ({"OEC_COST_BOUNDARY": ""}, "OEC_COST_BOUNDARY"),
        ({"OEC_MAX_TOKENS": "127"}, "OEC_MAX_TOKENS"),
        ({"OEC_MAX_TOKENS": "5000"}, "OEC_MAX_TOKENS"),
    ],
)
def test_bedrock_configuration_rejects_missing_or_invalid_boundaries(
    overrides: dict[str, str], message: str
) -> None:
    with pytest.raises(LiveConfigurationError, match=message):
        BedrockProviderConfiguration.from_environment(bedrock_environment(**overrides))
