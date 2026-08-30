"""Deliberately opt-in live Strands smoke runner for synthetic demo data."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .live_configuration import OpenAIProviderConfiguration
from .sample_data import demo_orders
from .strands_runtime import StrandsSpecialistRunner
from .workflow import DeterministicCoordinator


def _write_preflight_record(
    configuration: OpenAIProviderConfiguration, output_directory: Path
) -> Path:
    """Write non-secret run metadata before the process can invoke a paid model."""
    sample_order = demo_orders()[0]
    timestamp = datetime.now(timezone.utc)
    record = {
        "run_id": str(uuid4()),
        "recorded_at": timestamp.isoformat(),
        "mode": "live_strands_smoke",
        "configuration": configuration.safe_summary(),
        "input": {
            "source": "synthetic demo data",
            "order_id": sample_order.id,
            "carrier_status": sample_order.carrier_status,
        },
        "expected_trace": ["evidence", "resolution", "communications"],
        "external_write_adapter": "absent",
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    record_path = output_directory / f"preflight-{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an explicitly authorised live Strands smoke test on synthetic delivery data."
    )
    parser.add_argument(
        "--allow-live-model-call",
        action="store_true",
        help="Invoke the configured provider after recording the preflight metadata.",
    )
    parser.add_argument(
        "--record-directory",
        type=Path,
        default=Path("data/live-runs"),
        help="Local directory for non-secret live-run metadata.",
    )
    args = parser.parse_args()

    configuration = OpenAIProviderConfiguration.from_environment()
    print(json.dumps({"configuration": configuration.safe_summary()}, indent=2))
    if not args.allow_live_model_call:
        print("No model call was made. Re-run with --allow-live-model-call after reviewing the boundary above.")
        return

    preflight_path = _write_preflight_record(configuration, args.record_directory)
    coordinator = DeterministicCoordinator(
        StrandsSpecialistRunner.from_openai_configuration(configuration)
    )
    incident = coordinator.triage(demo_orders()[0])
    print(
        json.dumps(
            {
                "preflight_record": str(preflight_path),
                "incident_id": incident.id if incident else None,
                "trace": ["evidence", "resolution", "communications"],
                "external_action": "none",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
