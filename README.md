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
be tested without cloud credentials. `strands_runtime.py` holds the live
Strands specialists for the next delivery slice.

## Guardrails

- The language model cannot choose the workflow route or action type.
- All actions are drafts and require a named human approval.
- The first demo uses synthetic, reserved-domain example customers only.
- No refund, replacement, cancellation or customer message is sent by the
  current code.

## Architecture and delivery plan

- [Living project plan](PLAN.md)
- [Architecture](docs/Architecture.md)
- [Delivery plan](docs/DeliveryPlan.md)

## Provenance

This is a new project. It is conceptually informed by lessons from prior agent
experiments, but contains no copied Agent Squad or Restock Room source code.

## License

[MIT](LICENSE)
