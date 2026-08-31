import json

from order_exception_captain.live_configuration import BedrockProviderConfiguration
from order_exception_captain.live_demo import _write_preflight_record


def test_preflight_record_is_written_before_any_live_invocation(tmp_path) -> None:
    configuration = BedrockProviderConfiguration.from_environment(
        {
            "OEC_MODEL_PROVIDER": "bedrock",
            "OEC_MODEL_ID": "amazon.nova-lite-v1:0",
            "AWS_REGION": "us-east-1",
            "OEC_COST_BOUNDARY": "Synthetic proof only; approved by the operator.",
            "OEC_MAX_TOKENS": "128",
        }
    )

    record_path = _write_preflight_record(configuration, tmp_path)
    record = json.loads(record_path.read_text(encoding="utf-8"))

    assert record_path.name.startswith("preflight-")
    assert record["configuration"] == configuration.safe_summary()
    assert record["input"]["source"] == "synthetic demo data"
    assert record["expected_trace"] == ["evidence", "resolution", "communications"]
    assert record["external_write_adapter"] == "absent"
