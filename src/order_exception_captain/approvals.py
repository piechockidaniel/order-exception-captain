"""Approval gate: drafts stay inert until a named operator approves them."""

from __future__ import annotations

from datetime import datetime, timezone

from .domain import Incident, IncidentStatus


class ApprovalService:
    def approve(self, incident: Incident, operator: str) -> Incident:
        if incident.status is not IncidentStatus.AWAITING_APPROVAL:
            raise ValueError(f"Incident {incident.id} is not awaiting approval.")
        if not operator.strip():
            raise ValueError("An approving operator is required.")

        now = datetime.now(timezone.utc)
        for draft in incident.drafts:
            draft.approved_by = operator
            draft.approved_at = now
        incident.status = IncidentStatus.APPROVED
        return incident
