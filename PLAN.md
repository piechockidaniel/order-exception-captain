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
| 3. Live Strands proof | complete | A native Bedrock Haiku 4.5 proof ran on 2026-08-30 UTC in `eu-north-1` after a non-secret preflight record. The synthetic stalled-order workflow completed evidence → resolution → communications with a 128-token limit per specialist and no external action. |
| 4. Operator workflow | complete | Local dashboard passed a real browser approve/reject walkthrough, has PII minimisation/redaction, and includes a repeatable operator guide. |
| 5. Safe integration | in progress | Browser-verified, approval-gated dry-run adapter generates one auditable handoff preview with no external write. The optional WooCommerce connector is separately bounded to HTTPS GET with server-side Read credentials and remains unconfigured in the demo. The Policy Builder stores immutable rule versions and requires a separate admin token. A real staging-store validation remains an explicit decision gate. |
| 6. Production readiness | in progress | The synthetic demo is live at `https://oec.connect-the-dots.biz` behind HTTPS, a token-protected operator/admin boundary, OpenLiteSpeed, and a verified SQLite backup. 49 tests pass. Telemetry, retention owner, restore cadence, and a user-authorised staging validation still need operating decisions. |
| 7. Submission evidence | in progress | The GitHub repository is publicly readable and visibly MIT-licensed, but public `main` remains at `89db9f8`. Local commit `9dc6520` adds the live-demo, deployment, and operator material and needs explicit confirmation before it is pushed. The architecture diagram, five-minute script, Devpost description, live demo, and authorised live Strands proof are ready. The required external steps are the confirmed push, public video, Builder ID, and Devpost form. |

## Active slice — safe integration

### Deliverables

- [x] Keep an outbound action behind explicit, named approval.
- [x] Add an outbound-shaped adapter with no HTTP client, credentials, or external endpoint.
- [x] Prepare a deterministic, auditable dry-run handoff exactly once per approved incident.
- [x] Run an end-to-end browser review of the dry-run handoff.
- [x] Fix the approval-dialog field-visibility regression and recheck it in a browser.
- [x] Build a distributable wheel and verify it includes the operator dashboard assets.
- [ ] Validate the WooCommerce source against one user-authorised staging store and a Read-only key; do not use production credentials without a new approval.
- [x] Add a read-only scheduled ingestion path with a manual scan fallback; do not let it trigger external writes.
- [x] Add a versioned, declarative Policy Builder whose rule edits remain bounded, auditable, and separate from approval authority.
- [x] Add a WooCommerce `wc/v3/orders` HTTPS GET source with environment-only Read credentials, explicit tracking metadata mapping, pagination, and customer-data minimisation.
- [x] Record privacy-safe scan successes and failures; show the latest result in the local dashboard and API.
- [x] Require a token for non-local operator access and keep it only in dashboard memory.
- [x] Add health checks, verified SQLite backup, and documented recovery procedure.
- [x] Select and deploy demo hosting: `https://oec.connect-the-dots.biz` runs the synthetic dashboard behind HTTPS, with server-generated operator/admin tokens and a verified SQLite backup.
- [ ] Select telemetry destination, retention owner, and restore-test cadence before connecting non-synthetic data.

### Deferred live Bedrock decision

- [x] Add a native Amazon Bedrock Strands provider using the ambient AWS credential chain.
- [x] Select an AWS region, Bedrock model enabled for that account, and a spend boundary; then explicitly authorise the first paid smoke invocation. The 2026-08-30 UTC synthetic proof used Haiku 4.5 in `eu-north-1`, a 128-token per-specialist ceiling, and no external adapter.

### Active submission-evidence tasks

- [x] Produce a repository-native architecture diagram and five-minute demo script.
- [x] Track every required submission item and distinguish finished evidence from external gates.
- [x] Authorise and capture one live synthetic Strands-on-Bedrock trace with a selected model, region, and spend boundary. A non-secret preflight record and successful three-role trace were captured locally on 2026-08-30 UTC.
- [x] Re-verify the current official rules, public GitHub visibility and MIT license, current local test suite, wheel assets, scheduled-scan/backup path, and public live-demo access on 2026-09-03.
- [ ] Obtain explicit action-time confirmation, then push the local submission/deployment documentation commits to public GitHub `main`.
- [ ] Record and publish a public video that demonstrates the live dashboard and its synthetic workflow.
- [ ] Register the final project with AWS Builder ID and submit before 2026-09-14 17:00 PDT.

### Optional after the core submission

- Decide whether an AgentCore deployment dry-run is justified as a technical-score upgrade; do not deploy without explicit approval.
- Validate the WooCommerce source only against a user-authorised staging store with a Read-only key.
- Select telemetry destination, retention owner, and restore-test cadence before connecting non-synthetic data.

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
| A live Bedrock trace exceeds the intended spend. | Require a recorded human approval and a per-specialist output limit. This is not a hard dollar cap; configure an AWS budget or billing alert and keep the first run synthetic. |
| AgentCore deployment expands the scope and AWS footprint. | First secure a successful local Bedrock trace. Treat AgentCore as a separately approved, optional score-strengthening deployment. |
| A real-store integration creates customer or financial risk. | Start with a dry-run adapter and retain explicit approval as a hard gate. |
| Scope overlaps Restock Room. | Do not add stock replenishment, supplier ordering, or purchasing. |
| The public repository does not yet contain final submission material. | Anonymous lookup confirms `piechockidaniel/order-exception-captain` is public with a visible MIT license and README. Its public `main` is `89db9f8`; obtain action-time confirmation before pushing local commit `9dc6520` and this verification update. |

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
