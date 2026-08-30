# Graph Report - .  (2026-08-30)

## Corpus Check
- Corpus is ~2,919 words - fits in a single context window. You may not need a graph.

## Summary
- 94 nodes · 206 edges · 12 communities (7 shown, 5 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Domain Models
- Approval and CLI
- Workflow Guardrails
- Product and Evidence
- Deterministic Orchestration
- Strands Runtime
- Tests and Demo
- Coordinator Boundaries
- Safe Human Action
- Persistence Roadmap
- Packaging
- API Continuity

## God Nodes (most connected - your core abstractions)
1. `DeterministicCoordinator` - 22 edges
2. `Order` - 19 edges
3. `TemplateSpecialistRunner` - 17 edges
4. `Incident` - 13 edges
5. `Route` - 12 edges
6. `IncidentStatus` - 11 edges
7. `CarrierStatus` - 10 edges
8. `DraftAction` - 10 edges
9. `SpecialistRunner` - 10 edges
10. `DeliveryExceptionPolicy` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Restock Room` --semantically_similar_to--> `Post-Purchase Delivery-Exception Assistant`  [INFERRED] [semantically similar]
  docs/DeliveryPlan.md → PLAN.md
- `make_order()` --references--> `CarrierStatus`  [EXTRACTED]
  tests/test_workflow.py → src/order_exception_captain/domain.py
- `make_order()` --calls--> `OrderLine`  [EXTRACTED]
  tests/test_workflow.py → src/order_exception_captain/domain.py
- `make_lost_order()` --references--> `Order`  [EXTRACTED]
  tests/test_approvals.py → src/order_exception_captain/domain.py
- `make_order()` --references--> `Order`  [EXTRACTED]
  tests/test_workflow.py → src/order_exception_captain/domain.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Delivery Exception Approval Flow** — docs_architecture_deterministic_delivery_policy, docs_architecture_fixed_three_step_sequence, docs_architecture_approval_gated_action_draft, docs_architecture_named_human_operator [EXTRACTED 1.00]
- **Live Strands Proof Milestone** — plan_deterministic_coordinator, plan_strands_specialists, docs_architecture_strands_runtime [INFERRED 0.85]
- **Safe External Action Gate** — plan_named_human_approval, plan_dry_run_write_adapter, plan_sqlite_incident_audit_storage [INFERRED 0.85]

## Communities (12 total, 5 thin omitted)

### Community 0 - "Domain Models"
Cohesion: 0.20
Nodes (15): BaseModel, Protocol, CarrierStatus, DraftAction, Incident, IncidentStatus, Small, explicit domain model for the delivery-exception workflow., ResolutionKind (+7 more)

### Community 1 - "Approval and CLI"
Cohesion: 0.22
Nodes (11): datetime, main(), A small command-line walkthrough for the first vertical slice., ApprovalService, Approval gate: drafts stay inert until a named operator approves them., OrderLine, demo_orders(), Demo-only store data. It contains no real customer or order information. (+3 more)

### Community 2 - "Workflow Guardrails"
Cohesion: 0.17
Nodes (12): Approval-Gated Action Draft, Audit Record, Customer-Message Draft, Demo Runner, Deterministic Delivery Policy, Evidence Explanation, Future Integration Adapter, Fixed Three-Step Sequence (+4 more)

### Community 3 - "Product and Evidence"
Cohesion: 0.22
Nodes (10): Architecture, Delivery Plan, Restock Room, Submission Evidence, Post-Purchase Delivery-Exception Assistant, Order Exception Captain Living Plan, Carrier-Escalation Draft, Delivery Incident (+2 more)

### Community 4 - "Deterministic Orchestration"
Cohesion: 0.53
Nodes (4): Order, DeterministicCoordinator, Runs a fixed evidence → policy → communication sequence for an incident., Route

### Community 5 - "Strands Runtime"
Cohesion: 0.25
Nodes (6): describe_delivery_evidence(), Optional live Strands specialists.  This module is intentionally separate from t, Return the exact delivery facts supplied by the deterministic coordinator., Executes fixed-role Strands agents one at a time when model access is configured, StrandsSpecialistRunner, tool

### Community 6 - "Tests and Demo"
Cohesion: 0.43
Nodes (6): Deterministic demo runner used in tests and without cloud credentials., TemplateSpecialistRunner, make_order(), test_lost_order_selects_replacement_before_any_specialist_runs(), test_normal_in_transit_order_does_not_become_an_incident(), test_stalled_late_order_runs_all_fixed_specialists_and_creates_approval_gated_draft()

## Knowledge Gaps
- **17 isolated node(s):** `order-exception-captain`, `Deterministic Coordinator`, `Bounded Strands Specialists`, `Named Human Approval`, `Service and Persistence Milestone` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DeterministicCoordinator` connect `Deterministic Orchestration` to `Domain Models`, `Approval and CLI`, `Tests and Demo`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `Order` connect `Deterministic Orchestration` to `Domain Models`, `Approval and CLI`, `Tests and Demo`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `TemplateSpecialistRunner` connect `Tests and Demo` to `Domain Models`, `Approval and CLI`, `Deterministic Orchestration`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `DeterministicCoordinator` (e.g. with `CarrierStatus` and `DraftAction`) actually correct?**
  _`DeterministicCoordinator` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Order` (e.g. with `DeliveryExceptionPolicy` and `DeterministicCoordinator`) actually correct?**
  _`Order` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `TemplateSpecialistRunner` (e.g. with `CarrierStatus` and `DraftAction`) actually correct?**
  _`TemplateSpecialistRunner` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Incident` (e.g. with `ApprovalService` and `DeliveryExceptionPolicy`) actually correct?**
  _`Incident` has 6 INFERRED edges - model-reasoned connections that need verification._