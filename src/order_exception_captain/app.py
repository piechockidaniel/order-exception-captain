"""A small command-line walkthrough for the first vertical slice."""

from __future__ import annotations

import argparse

from .approvals import ApprovalService
from .sample_data import demo_orders
from .workflow import DeterministicCoordinator, TemplateSpecialistRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Triage sample ecommerce delivery exceptions.")
    parser.add_argument("--approve", action="store_true", help="Approve the first generated draft as Demo Operator.")
    args = parser.parse_args()

    coordinator = DeterministicCoordinator(TemplateSpecialistRunner())
    incidents = [incident for order in demo_orders() if (incident := coordinator.triage(order)) is not None]
    for incident in incidents:
        print(f"{incident.id}: {incident.status}")
        print(incident.reason)
        print(incident.customer_message_draft)
        for draft in incident.drafts:
            print(f"  - {draft.id}: {draft.summary}")

    if args.approve and incidents:
        approved = ApprovalService().approve(incidents[0], "Demo Operator")
        print(f"Approved {approved.id} as {approved.drafts[0].approved_by}.")


if __name__ == "__main__":
    main()
