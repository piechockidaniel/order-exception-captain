# Operator guide

Order Exception Captain is a local review desk. It does not send customer
messages, update an order, issue a replacement, or contact a carrier.

## Start a clean, repeatable demo

Use a new local database filename for each demo run. This avoids deleting past
records and makes the walkthrough repeatable:

```powershell
uv run order-exception-captain-api --database data/demo-20260830.sqlite3
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and select **Load demo
queue**. The queue includes two synthetic exceptions:

1. `order-1042`: tracking stalled after the promised date, with a proposed
   carrier escalation.
2. `order-1044`: carrier marked a parcel as lost, with a proposed replacement.

## Review a case

1. Select an incident and inspect the policy trigger, evidence, resolution
   explanation, and customer-message draft.
2. Choose **Approve draft** only when the proposed action is appropriate. Enter
   your name; approval is added to the audit trail.
3. Choose **Reject draft** to stop the proposal. A short reason is required and
   becomes part of the audit trail.
4. For an approved case, choose **Prepare dry-run handoff**. This produces an
   auditable preview only; it does not make a network request or an external
   change.

## Recommended two-minute demonstration

1. Load the demo queue and open `order-1042`.
2. Explain that policy, not the model, selected carrier escalation.
3. Approve it as `Demo Operator`; point out the new audit event.
4. Prepare the dry-run handoff; point out that the audit text says no request
   was sent.
5. Open `order-1044`, reject it with a reason, and show the second audit trail.

All data in this walkthrough is synthetic. Before connecting a real store, use
the data-minimisation controls documented in the architecture and obtain
explicit authorisation for the selected integration.
