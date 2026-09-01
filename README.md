# Order Exception Captain

Order Exception Captain is a new, focused **Professional Agent** project for
independent ecommerce operators. It watches delivery status, detects a specific
post-purchase exception, and creates an evidence-backed action draft for human
approval.

It does not try to be a generic agent platform. The coordinator is deliberately
deterministic: carrier states and explicit thresholds decide which fixed pieces
of work run and in which order. Strands specialists are used for bounded
analysis and customer-facing language, never for approval or side-effect
decisions.

## First demo scenario

When carrier tracking has been stalled for 48+ hours after the promised delivery
date, the application:

1. creates a delivery incident;
2. calls the evidence, resolution and communications specialists in sequence;
3. creates a carrier-escalation draft; and
4. waits for a named operator before anything external can happen.

Lost parcels and failed delivery attempts follow different explicit routes.

## Policy Builder and read-only WooCommerce source

The dashboard now exposes the active rule pack to every operator and, in local
mode, lets an administrator publish a new immutable policy version. A rule can
only express a priority, carrier status, optional tracking-age threshold,
optional promise-date condition, operator-visible reason, and proposed
resolution. It cannot contain executable code, a prompt, a webhook, or an
external action. Each incident retains the policy version and matching rule ID
that created it.

On a protected service, configure a distinct 16+-character `OEC_ADMIN_TOKEN`.
An operator token alone cannot test or publish policy. The page holds both
tokens only in memory.

For the deployed demo, both tokens were generated once on the VPS during
provisioning with the operating system's cryptographic random generator. They
are not AWS, Bedrock, WooCommerce, or GitHub credentials, are never committed
to this repository, and are stored only in the root-owned server file described
in the [deployment guide](docs/Deployment.md#token-origin-and-handling).

The optional WooCommerce source calls only `GET /wp-json/wc/v3/orders` over
HTTPS and paginates using WooCommerce's response headers. Create a WooCommerce
REST API key with **Read** access, keep its values in the host secret store,
and configure these server-side environment variables:

```powershell
$env:OEC_WOO_BASE_URL = "https://staging-shop.example"
$env:OEC_WOO_CONSUMER_KEY = "<read-only-consumer-key>"
$env:OEC_WOO_CONSUMER_SECRET = "<read-only-consumer-secret>"
```

Tracking is not a standard WooCommerce field, so the source requires three
configured metadata fields: carrier status, tracking update time, and promised
delivery date. The defaults are `_tracking_status`, `_tracking_updated_at`, and
`_promised_delivery_date`; set the matching `OEC_WOO_*_METADATA_KEY`
environment variables if a chosen tracking plugin uses different names. Orders
without all three fields are skipped rather than guessed. Customer identity is
replaced with a synthetic placeholder before deterministic triage and is never
persisted or sent to a specialist.

After server-side configuration, an administrator can choose **Read
WooCommerce orders** in the dashboard, or run one explicit read-only scan:

```powershell
uv run order-exception-captain-scan-woocommerce --database data/woocommerce-demo.sqlite3 --once
```

The connector has no POST, PUT, PATCH, or DELETE operation. Start against a
user-authorised staging store and a read-only key; do not use a production
store without a separate privacy and operational review. See WooCommerce's
[REST API guide](https://developer.woocommerce.com/docs/apis/rest-api/) and
[authentication guide](https://developer.woocommerce.com/docs/apis/rest-api/authentication)
for key creation and permissions.

## Quick start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```powershell
uv sync --extra dev
uv run pytest
uv run order-exception-captain --approve
```

The initial command-line flow uses deterministic fixture specialists so it can
be tested without cloud credentials. `strands_runtime.py` holds the bounded
live Strands specialists; the coordinator still determines their fixed order.

## Local API demo

```powershell
uv run order-exception-captain-api --database data/demo.sqlite3
```

`POST /scans` accepts synthetic order data, `GET /incidents` shows persisted
drafts, and `POST /incidents/{id}/approve` records a named operator approval.
Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the local operator
dashboard. It can load a synthetic queue, show evidence and audit history, and
record a named approval or rejection. The API is local by default and has no
external write adapter.

For a repeatable presenter walkthrough, see the [operator guide](docs/OperatorGuide.md).
The demo queue contains a stalled delivery and a lost parcel. An approved draft
can prepare a visible, idempotent dry-run handoff; that adapter has no network
client or external credentials and always records `external_request_sent=false`.

## Read-only scheduled scan

The local scheduler reads an order snapshot, invokes the same deterministic
triage, and writes only approval-gated incidents to SQLite. It never writes to
the source, a store, carrier, customer, or payment system. The existing
`POST /scans` endpoint remains the manual fallback.

```powershell
uv run order-exception-captain-scan --orders examples/synthetic-orders.json --database data/scheduled-demo.sqlite3 --once
```

Omit `--once` to scan the source every five minutes. The command emits one
structured activity record per run and a redacted failure record if the input
is unavailable or invalid.

Customer names and emails are excluded from specialist prompts and original
orders are not stored with incidents. The service also redacts common email and
phone-number patterns before persisting specialist drafts or rejection reasons,
and before returning operator-facing records. This is a data-minimization
guardrail, not a substitute for a real-store privacy review.

## Operator access outside localhost

The default loopback demo is intentionally open for a presenter. To bind the
service to any non-local host, set a 16+-character `OEC_OPERATOR_TOKEN` in the
host environment. Startup refuses a non-local host without it. The dashboard
will request the token and retains it only for the open page; API clients send
it as `Authorization: Bearer <token>`.

This is a minimal access boundary, not user identity: the named operator in an
approval remains an auditable declaration. A real deployment should terminate
TLS and place this service behind company SSO or an identity-aware proxy.

## Deployment and recovery

A loopback-only Docker Compose template, a live OpenLiteSpeed VPS deployment,
SQLite health check, verified backup command, retention guidance, and rollback
procedure are in the [deployment guide](docs/Deployment.md). The live demo
does not configure WooCommerce credentials or make an external business action.

## Final Bedrock Strands proof

The final proof path uses Amazon Bedrock through Strands. It runs only against
synthetic demo data and has no external write adapter. Configure AWS credentials
through your local AWS profile, role, or other standard credential chain—never
in source control—then set the provider, an enabled model ID, region, and a
human-approved cost boundary in your local shell:

```powershell
$env:OEC_MODEL_PROVIDER = "bedrock"
$env:OEC_MODEL_ID = "<Bedrock-model-enabled-for-this-account>"
$env:AWS_REGION = "<enabled-model-region>"
$env:OEC_MAX_TOKENS = "300"
$env:OEC_COST_BOUNDARY = "Synthetic three-specialist smoke test; approved spend limit: <amount>"
uv run order-exception-captain-live
```

The command above validates the configuration and makes **no** model call. To
run the three bounded specialists, review the printed boundary and invoke:

```powershell
uv run order-exception-captain-live --allow-live-model-call
```

Before that invocation, the command writes a non-secret preflight record under
`data/live-runs/` with the selected provider/model, region, synthetic input,
fixed trace, and cost boundary. That folder is ignored by Git. The OpenAI
provider remains available as an explicit alternative for non-final testing, but
the final hackathon trace and video should use Bedrock.

`OEC_COST_BOUNDARY` records a specific human approval; it is **not** an
AWS-enforced dollar stop. The runner fixes the three specialist roles and caps
generated output per specialist, but final charges also depend on input tokens
and any tool follow-up. Set an AWS billing alert or budget separately, start
with a small synthetic invocation, and review the preflight before using
`--allow-live-model-call`.

The [Bedrock proof runbook](docs/BedrockProofRunbook.md) gives the exact
safe-preflight, recording, and optional AgentCore-upgrade sequence for the
final video.

## Guardrails

- The language model cannot choose the workflow route or action type.
- All actions are drafts and require a named human approval.
- The first demo uses synthetic, reserved-domain example customers only.
- No refund, replacement, cancellation or customer message is sent by the
  current code.
- A non-local API binding cannot start without an operator access token.
- Policy publication needs a separate administrator token when the operator
  desk is protected; an operator token never grants policy-editing authority.
- The WooCommerce connector is read-only and needs explicit server-side
  configuration; it is not enabled by the synthetic demo.

## Architecture and delivery plan

- [Living project plan](PLAN.md)
- [Architecture](docs/Architecture.md)
- [Delivery plan](docs/DeliveryPlan.md)
- [Five-minute demo script](docs/DemoScript.md)
- [Submission checklist](docs/SubmissionChecklist.md)
- [Copy-ready Devpost submission text](docs/DevpostSubmission.md)

## Provenance

This is a new project. It is conceptually informed by lessons from prior agent
experiments, but contains no copied Agent Squad or Restock Room source code.

## License

[MIT](LICENSE)
