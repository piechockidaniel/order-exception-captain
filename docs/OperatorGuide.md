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

## Configure delivery rules safely

Open **Policy Builder** to see the active, versioned rules. In the open local
demo you can add, remove, or change a rule, test the draft against a synthetic
stalled order, and publish it as a new immutable version. The change affects
future scans only; it does not alter existing incidents or remove the approval
gate.

For a non-local desk, set a separate administrator token in the host secret
store before starting the API:

```powershell
$env:OEC_OPERATOR_TOKEN = "<operator-secret-held-outside-the-repository>"
$env:OEC_ADMIN_TOKEN = "<different-admin-secret-held-outside-the-repository>"
```

Unlock the operator desk first, then unlock the policy builder with the admin
token. The two credentials have different authority: an operator can review,
approve, or reject drafts but cannot publish policy.

## Connect an authorised WooCommerce staging store

Create a WooCommerce REST API key with **Read** permission for a service user;
do not reuse an owner credential and do not put the key in the browser. Configure
the server environment, using the metadata names from the tracking plugin on
that staging store:

```powershell
$env:OEC_WOO_BASE_URL = "https://staging-shop.example"
$env:OEC_WOO_CONSUMER_KEY = "<read-only-key>"
$env:OEC_WOO_CONSUMER_SECRET = "<read-only-secret>"
$env:OEC_WOO_TRACKING_STATUS_METADATA_KEY = "_tracking_status"
$env:OEC_WOO_TRACKING_UPDATED_AT_METADATA_KEY = "_tracking_updated_at"
$env:OEC_WOO_PROMISED_DELIVERY_DATE_METADATA_KEY = "_promised_delivery_date"
```

Restart the API, unlock the policy builder, and choose **Read WooCommerce
orders**. The source makes HTTPS `GET` requests only and skips records without
the three required tracking fields. It creates local approval-gated incidents;
it never changes WooCommerce, the carrier, a customer, or a payment record.
For a terminal preflight, use:

```powershell
uv run order-exception-captain-scan-woocommerce --database data/woocommerce-staging.sqlite3 --once
```

Use a staging store first and obtain a new explicit approval before any
production-store validation.

## Run a read-only scheduled demo scan

In a second local terminal, run the example snapshot once:

```powershell
uv run order-exception-captain-scan --orders examples/synthetic-orders.json --database data/demo-20260830.sqlite3 --once
```

Refresh the dashboard to review any detected incident. The scheduler reads the
snapshot only; it never changes the file or takes an external action. Omit
`--once` to repeat the scan every five minutes.

## Run on a non-local host

Only do this behind HTTPS and a controlled network boundary. Configure an
operator token in the host environment through your secret manager, then start
the service. Do not put the value in a `.env` file that might be committed, the
browser URL, or this guide.

```powershell
$env:OEC_OPERATOR_TOKEN = "<secret-held-outside-the-repository>"
uv run order-exception-captain-api --host 0.0.0.0 --database data/operator.sqlite3
```

The dashboard opens with an **Unlock operator desk** control. Enter the same
token after reaching the site; it is held only while that page remains open.
The token protects access, while the name entered during approval remains the
human-readable audit record. Use SSO or an identity-aware reverse proxy before
using a real store connection.
