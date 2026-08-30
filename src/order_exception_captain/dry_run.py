"""Safe outbound boundary used before any real ecommerce/carrier integration."""

from __future__ import annotations

from .domain import DryRunPreview, Incident, IncidentStatus


class DryRunOutboundAdapter:
    """Creates deterministic previews only; it has no HTTP client or external credentials."""

    def prepare(self, incident: Incident) -> DryRunPreview:
        if incident.status is not IncidentStatus.APPROVED:
            raise ValueError(f"Incident {incident.id} must be approved before a dry run can be prepared.")
        if not incident.drafts:
            raise ValueError(f"Incident {incident.id} has no draft to prepare.")

        draft = incident.drafts[0]
        return DryRunPreview(
            incident_id=incident.id,
            draft_id=draft.id,
            action_kind=draft.kind,
            request_summary=(
                f"Dry run only: would prepare a {draft.kind.replace('_', ' ')} handoff "
                f"for {incident.order_id}. No customer, carrier, store, or payment request was sent."
            ),
        )
