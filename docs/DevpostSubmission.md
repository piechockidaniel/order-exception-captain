# Order Exception Captain — Devpost submission text

## Tagline

An approval-gated Strands agent that turns delivery exceptions into safe,
evidence-backed operator drafts.

## What it does

Independent ecommerce operators often discover a stalled, lost, or failed
delivery only after a customer has already had a poor experience. Order
Exception Captain turns that repetitive exception-handling work into one clear,
reviewable workflow.

It reads a delivery-status snapshot, applies deterministic policy to identify a
specific exception, then runs three bounded Strands specialists in a fixed
order: evidence, resolution explanation, and customer-message drafting. The
result is an auditable draft for a named human operator. The agent cannot select
the route, approve an action, issue a refund, contact a carrier, or message a
customer.

## Who it is for and why it matters

The project is for small ecommerce operations teams that need to respond to
delivery problems quickly without turning customer communication or financial
decisions over to an LLM. It makes the important facts, policy result, and
proposed message visible before a human decides what happens next.

## How it is built

- Python, FastAPI, SQLite, and the Strands Agents SDK.
- Deterministic routing and idempotency are ordinary code, not model decisions.
- Three role-specific Strands agents create bounded drafts only.
- Amazon Bedrock provides the final live-proof path. A synthetic Amazon Bedrock
  Haiku 4.5 run completed in `eu-north-1` after a recorded cost boundary and
  produced the fixed evidence → resolution → communications trace.
- The local dashboard supports loading synthetic data, reviewing redacted
  drafts, named approve/reject decisions, and an auditable dry-run handoff.

## Safety and privacy

The demo uses synthetic, reserved-domain data. Customer names and emails are
excluded from specialist prompts; common email and phone patterns are redacted
before drafts are persisted or displayed. No network client or external write
adapter exists in the current demo. All outbound-shaped activity is a visible,
idempotent dry-run preview after named approval.

## Testing instructions

The offline demo is free to run and needs only Python 3.11+ and uv:

```powershell
uv sync --extra dev
uv run pytest
uv run order-exception-captain --approve
uv run order-exception-captain-api --database data/demo.sqlite3
```

Open `http://127.0.0.1:8000/` to load the synthetic queue and approve or reject
a draft. The optional Bedrock proof is documented in
[`BedrockProofRunbook.md`](BedrockProofRunbook.md); it uses only synthetic data
and requires the evaluator's own AWS credentials and selected cost boundary.

## Provenance and third-party tools

This is a new project created during the submission period. It uses standard
open-source libraries and AWS services. It is conceptually informed by prior
agent experiments but contains no copied source code from them.
