# Delivery plan

The editable, current execution plan is maintained in [`PLAN.md`](../PLAN.md).
This document records the initial delivery strategy and submission definition.

## Goal

Build a new Professional Agents submission for independent ecommerce operators:
an autonomous, approval-gated assistant that identifies delivery exceptions and
turns them into evidence-backed action drafts.

## Definition of a successful demo

1. A scheduled sample-store scan finds a late, stalled or lost delivery.
2. The deterministic coordinator assigns evidence, resolution and communication
   work in a visible fixed order.
3. Strands specialists produce bounded evidence and a customer-message draft.
4. The system saves a draft action and shows that nothing external happens until
   a named operator approves it.
5. The operator approves one action; the audit trail records who and when.

## Milestones

1. **Foundation — complete in this slice.** Clean repository, MIT license,
   bounded domain, deterministic policy, demo fixture, approval model and tests.
2. **Runnable service.** Add a small HTTP API, persistent SQLite incident store,
   scheduled scan and an operator dashboard.
3. **Live Strands proof.** Configure an AWS Bedrock-backed Strands runner,
   preserve the fixed routing sequence, and record actual tool/agent traces.
4. **Operator experience.** Add the explicit approve/reject flow, a redacted
   event history, versioned policy builder, and a read-only WooCommerce source;
   keep every write-shaped adapter in dry-run first.
5. **Submission evidence.** Deploy a testable demo, create the architecture
   diagram, record a <=5 minute public video, and publish the repository,
   README and setup instructions. An AgentCore deployment is an optional
   technical-score upgrade, not a prerequisite for the VPS demo.

## Non-goals

- Replenishment, supplier ordering, or purchasing workflows (Restock Room owns
  that problem space).
- A generic multi-agent platform or configurable agent marketplace.
- Autonomous refunds, replacements, cancellations, or customer contact.
