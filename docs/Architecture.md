# Architecture

```text
sample-store event / carrier feed
             |
             v
  deterministic delivery policy
             |
             +-- normal order -> no incident
             |
             v
      fixed three-step sequence
  evidence -> resolution explanation -> customer-message draft
             |
             v
      approval-gated action draft
             |
             v
       named human operator
```

The coordinator owns branching, ordering, idempotency, and approval gates. It
uses explicit carrier states and thresholds, rather than asking a language model
to decide what work should happen. Strands specialists add bounded value where
language is useful: evidence explanation and customer-facing draft wording.

No agent is allowed to send a message, alter an order, issue a refund, or create
a replacement. Those are future integration adapters that must require a named
operator approval and produce an audit record.

## Strands use

`strands_runtime.py` contains three role-specific Strands agents and an
evidence tool. The live runner is deliberately separate from the demo runner,
so the deterministic policy can be tested without a model credential. The
production wiring will call the roles serially in the coordinator's prescribed
order and retain their drafts with the incident record.
