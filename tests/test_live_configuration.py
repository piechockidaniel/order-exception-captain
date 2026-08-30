import pytest

from order_exception_captain.live_configuration import (
    LiveConfigurationError,
    OpenAIProviderConfiguration,
)
from order_exception_captain.strands_runtime import StrandsSpecialistRunner


def live_environment(**overrides: str) -> dict[str, str]:
    values = {
        "OEC_MODEL_PROVIDER": "openai",
        "OEC_MODEL_ID": "approved-test-model",
        "OPENAI_API_KEY": "test-key-not-a-secret",
        "OEC_COST_BOUNDARY": "Synthetic smoke test only; operator-approved limit.",
        "OEC_MAX_TOKENS": "120",
    }
    values.update(overrides)
    return values


def test_live_configuration_is_explicit_and_never_exposes_the_api_key() -> None:
    configuration = OpenAIProviderConfiguration.from_environment(live_environment())

    assert configuration.safe_summary() == {
        "provider": "openai",
        "model_id": "approved-test-model",
        "max_tokens_per_specialist": 120,
        "specialist_count": 3,
        "cost_boundary": "Synthetic smoke test only; operator-approved limit.",
    }
    assert "test-key-not-a-secret" not in repr(configuration)


def test_live_runner_configures_exactly_the_three_bounded_specialists() -> None:
    runner = StrandsSpecialistRunner.from_openai_configuration(
        OpenAIProviderConfiguration.from_environment(live_environment())
    )

    assert set(runner._agents) == {"evidence", "resolution", "communications"}


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"OEC_MODEL_PROVIDER": ""}, "OEC_MODEL_PROVIDER"),
        ({"OEC_MODEL_ID": ""}, "OEC_MODEL_ID"),
        ({"OPENAI_API_KEY": ""}, "OPENAI_API_KEY"),
        ({"OEC_COST_BOUNDARY": ""}, "OEC_COST_BOUNDARY"),
        ({"OEC_MAX_TOKENS": "0"}, "OEC_MAX_TOKENS"),
    ],
)
def test_live_configuration_rejects_missing_or_invalid_boundaries(
    overrides: dict[str, str], message: str
) -> None:
    with pytest.raises(LiveConfigurationError, match=message):
        OpenAIProviderConfiguration.from_environment(live_environment(**overrides))
