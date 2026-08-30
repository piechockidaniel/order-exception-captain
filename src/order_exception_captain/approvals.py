"""Human decision gate: drafts stay inert until a named operator decides."""

from __future__ import annotations

from datetime import datetime, timezone

from .domain import Incident, IncidentStatus
from .redaction import redact_text


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

    def reject(self, incident: Incident, operator: str, reason: str) -> Incident:
        if incident.status is not IncidentStatus.AWAITING_APPROVAL:
            raise ValueError(f"Incident {incident.id} is not awaiting approval.")
        if not operator.strip():
            raise ValueError("A rejecting operator is required.")
        if not reason.strip():
            raise ValueError("A rejection reason is required.")

        now = datetime.now(timezone.utc)
        for draft in incident.drafts:
            draft.rejected_by = operator
            draft.rejected_at = now
            draft.rejection_reason = redact_text(reason.strip())
        incident.status = IncidentStatus.REJECTED
        return incident
