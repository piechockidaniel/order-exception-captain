        # Order Exception Captain — editable delivery plan

**Status legend:** `complete` · `in progress` · `next` · `blocked` · `not started`

This is the living plan for the project. Update the status, evidence, and next
action when a milestone materially changes. Keep the scope narrow: this is a
post-purchase delivery-exception assistant, not a generic agent platform and
not a replenishment system.

## Outcome

An independent ecommerce operator gets a quiet, approval-gated assistant that
detects a late, stalled, lost, or failed delivery; produces evidence and a
customer-message draft; and waits for a named human before any external action.

## Current checkpoint

| Milestone | Status | Evidence / exit condition |
|---|---|---|
| 1. Foundation | complete | Clean Python repository, MIT license, deterministic policy, demo data, approval gate, and five passing tests. |
| 2. Service and persistence | complete | HTTP API, SQLite incident/audit storage, idempotent scan, nine passing tests, and a local server smoke test. |
| 3. Live Strands proof | in progress | Explicit OpenAI provider configuration, three bounded specialists, a preflight record, an opt-in smoke command, and sixteen passing offline tests; awaiting a user-selected model and cost boundary for the first paid invocation. |
| 4. Operator workflow | complete | Local dashboard passed a real browser approve/reject walkthrough, has PII minimisation/redaction, and includes a repeatable operator guide. |
| 5. Safe integration | in progress | Browser-verified, approval-gated dry-run adapter generates one auditable handoff preview with no network client, credentials, or external side effect; the distributable wheel includes the operator dashboard. A real provider selection remains an explicit decision gate. |
| 6. Production readiness | in progress | Read-only file-snapshot ingestion, scheduled scan command, a privacy-safe activity feed, token-gated non-local access, verified SQLite backups, and a loopback-only container template preserve the manual API fallback. 30 tests, wheel build, Compose validation, and a disposable container health check pass. The hosting, telemetry, retention owner, and restore cadence still need an operating decision. |
| 7. Submission evidence | not started | Public repository, README, architecture diagram, deployed demo, and a <=5-minute video showing the end-to-end flow. |

## Active slice — safe integration

### Deliverables

- [x] Keep an outbound action behind explicit, named approval.
- [x] Add an outbound-shaped adapter with no HTTP client, credentials, or external endpoint.
- [x] Prepare a deterministic, auditable dry-run handoff exactly once per approved incident.
- [x] Run an end-to-end browser review of the dry-run handoff.
- [x] Fix the approval-dialog field-visibility regression and recheck it in a browser.
- [x] Build a distributable wheel and verify it includes the operator dashboard assets.
- [ ] Choose one real carrier or ecommerce adapter and obtain explicit authorisation before any non-dry-run implementation.
- [x] Add a read-only scheduled ingestion path with a manual scan fallback; do not let it trigger external writes.
- [x] Record privacy-safe scan successes and failures; show the latest result in the local dashboard and API.
- [x] Require a token for non-local operator access and keep it only in dashboard memory.
- [x] Add health checks, verified SQLite backup, and documented recovery procedure.
- [ ] Select hosting, telemetry destination, retention owner, and restore-test cadence before connecting non-synthetic data.

### Deferred live Strands decision

- [ ] Select a model and a spend boundary, then explicitly authorise the first paid smoke invocation.

### Acceptance criteria

- A repeat scan never creates a second active incident for the same order and carrier state.
- An approval records operator identity and timestamp.
- The API never performs an external action; it stores drafts only.
- The offline test suite stays independent of cloud model credentials.
- A live smoke test runs only after the selected provider and cost boundary are recorded.

## Architectural decisions that must remain true

- The coordinator decides routing and ordering with explicit code and policy.
- Strands specialists only create bounded evidence, explanation, or language drafts.
- A language model cannot choose an action type, approve an action, or bypass policy.
- Every future write adapter defaults to dry-run and requires a named approval.
- Fixture data remains synthetic and contains no customer data.

## Risks and decision gates

| Risk | Gate / response |
|---|---|
| The entry looks like a generic multi-agent platform. | Keep one delivery-exception workflow and demo it from trigger to approval. |
| Live model behavior changes the deterministic route. | Test all routing before invoking specialists; persist model output as non-authoritative drafts. |
| AWS/Bedrock setup delays the demo. | Preserve the deterministic local demo; add live Strands proof as an isolated milestone. |
| A real-store integration creates customer or financial risk. | Start with a dry-run adapter and retain explicit approval as a hard gate. |
| Scope overlaps Restock Room. | Do not add stock replenishment, supplier ordering, or purchasing. |
| Submission repository is not publicly verifiable. | A GitHub remote exists, but anonymous lookup cannot verify its visibility. Confirm the intended repository and permission to publish before pushing this work or changing visibility. |

## API-funded development continuity

- This repository does **not** require an OpenAI API key for the current offline
  demo or test suite.
- If you elect to use API-funded OpenAI tooling after a product usage limit,
  configure the key only in your local user environment as `OPENAI_API_KEY`.
  Do not add it to source, commit it, paste it into chat, or expose it in a
  browser client.
- An API key is for API requests; this plan makes no assumption that setting it
  changes the billing or quota of the current Codex/ChatGPT session.
- Before any code path starts consuming an API credential, record the provider,
  expected cost boundary, and a testable fallback in this plan.

## Update protocol

1. On every material delivery, change the milestone status and add the evidence.
2. Before starting the next milestone, move it to `in progress` and copy its
   concrete tasks into **Active slice**.
3. Record any scope change or external side effect under **Risks and decision
   gates** before implementing it.
4. Keep secrets out of this file and all repository files.
