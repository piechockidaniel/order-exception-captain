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
| 3. Live Strands proof | in progress | Explicit OpenAI provider configuration, three bounded specialists, a preflight record, and an opt-in smoke command; awaiting a user-selected model and cost boundary for the first paid invocation. |
| 4. Operator workflow | not started | Dashboard lets an operator inspect evidence, approve/reject a draft, and see an immutable audit record. |
| 5. Safe integration | not started | One external adapter starts in dry-run; an approved action is required before any actual side effect. |
| 6. Submission evidence | not started | Public repository, README, architecture diagram, deployed demo, and a <=5-minute video showing the end-to-end flow. |

## Active slice — live Strands proof

### Deliverables

- [x] Define an incident repository interface and a SQLite implementation.
- [x] Persist incidents, specialist drafts, approvals, and audit events.
- [x] Add a `POST /scans` endpoint for controlled demo triggering.
- [x] Add `GET /incidents` and `POST /incidents/{id}/approve` endpoints.
- [x] Make repeated scans idempotent by deterministic incident ID.
- [x] Cover normal, stalled, lost, failed-delivery, duplicate-scan, and approval paths with API tests.

### Live Strands deliverables

- [x] Add explicit, validated provider configuration; no credentials in files.
- [x] Keep the deterministic coordinator as the only caller deciding role order.
- [x] Make the selected provider available to all three bounded specialists.
- [x] Add a credential-free configuration test and a separately invoked live smoke command.
- [x] Record the model/provider, input, trace, and cost boundary before a paid invocation.
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
