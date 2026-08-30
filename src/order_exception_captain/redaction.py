"""Small, deterministic safeguards for operator-visible text.

The workflow deliberately does not persist the source Order. These filters add
a second guard when a future model response or an operator note contains a
common direct identifier.
"""

from __future__ import annotations

import re

from .domain import AuditEvent, DraftAction, Incident

_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_PHONE = re.compile(r"(?<![\w-])(?:\+?\d[\d\s().-]{6,}\d)(?![\w-])")


def redact_text(value: str) -> str:
    """Replace common direct identifiers without relying on model judgment."""
    return _PHONE.sub("[redacted phone]", _EMAIL.sub("[redacted email]", value))


def redact_incident_for_operator(incident: Incident) -> Incident:
    """Return a safe presentation copy; persistence retains no source Order."""
    visible = incident.model_copy(deep=True)
    visible.evidence_summary = redact_text(visible.evidence_summary)
    visible.policy_summary = redact_text(visible.policy_summary)
    visible.customer_message_draft = redact_text(visible.customer_message_draft)
    visible.drafts = [_redact_draft(draft) for draft in visible.drafts]
    return visible


def redact_event_for_operator(event: AuditEvent) -> AuditEvent:
    visible = event.model_copy(deep=True)
    visible.detail = redact_text(visible.detail)
    return visible


def _redact_draft(draft: DraftAction) -> DraftAction:
    visible = draft.model_copy(deep=True)
    visible.summary = redact_text(visible.summary)
    if visible.rejection_reason:
        visible.rejection_reason = redact_text(visible.rejection_reason)
    return visible
