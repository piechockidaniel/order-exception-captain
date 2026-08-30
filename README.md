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

A loopback-only Docker Compose template, SQLite health check, verified backup
command, retention guidance, and rollback procedure are in the
[deployment guide](docs/Deployment.md). It does not provision infrastructure
or connect an external system.

## Optional live Strands smoke test

The live proof is an explicit, local-only opt-in. It uses the OpenAI provider
for Strands, runs only against synthetic demo data, and has no external write
adapter. Install dependencies first, then set these values in your local shell
(not in a repository file):

```powershell
$env:OEC_MODEL_PROVIDER = "openai"
$env:OEC_MODEL_ID = "<approved-model-id>"
$env:OPENAI_API_KEY = "<local-api-key>"
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
`data/live-runs/` with the selected provider/model, synthetic input, fixed
trace, and cost boundary. That folder is ignored by Git.

## Guardrails

- The language model cannot choose the workflow route or action type.
- All actions are drafts and require a named human approval.
- The first demo uses synthetic, reserved-domain example customers only.
- No refund, replacement, cancellation or customer message is sent by the
  current code.
- A non-local API binding cannot start without an operator access token.

## Architecture and delivery plan

- [Living project plan](PLAN.md)
- [Architecture](docs/Architecture.md)
- [Delivery plan](docs/DeliveryPlan.md)

## Provenance

This is a new project. It is conceptually informed by lessons from prior agent
experiments, but contains no copied Agent Squad or Restock Room source code.

## License

[MIT](LICENSE)
