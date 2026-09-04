# ResolveDesk — five-minute window-capture demo script

This is a truthful recording outline, not a claim that an external action was
performed. Keep the recording under five minutes. Use only the synthetic orders
shipped with the repository unless an authorised staging WooCommerce scan has
been separately validated and recorded.

## Capture rule

Treat every period below as one capture segment. Capture **only the named
window and resource type** for that period; stop or switch the recorder's
window source at the boundary. Do not tile terminal, browser, code, or
credentials together. Keep tokens, environment files, and browser autofill out
of every recording.

The public ResolveDesk dashboard establishes the visual identity first. The
technical diagram is a separate, supporting visual: do not record
[`docs/Architecture.md`](Architecture.md) until its diagram is embedded in the
document rather than the current `[ima]` placeholder.

## Period 1 — 0:00–0:25 · Browser · ResolveDesk live dashboard

**Capture this window:** a browser at
[`https://oec.connect-the-dots.biz`](https://oec.connect-the-dots.biz), with
the ResolveDesk header and “Local demo · no external actions” badge visible.

“Independent ecommerce operators lose time discovering delivery failures,
checking carrier evidence, and writing customer updates. ResolveDesk — Order
Exception Captain is a Professional Agent for that narrow post-purchase
workflow. It turns a delivery exception into an explainable draft, but a human
stays in control of every consequence.”

## Period 2 — 0:25–0:45 · Diagram viewer · architecture and boundaries

**Capture this window:** the final, embedded architecture diagram in a browser
or image viewer. Keep the diagram large enough to read; do not show the
dashboard, terminal, or editor in this segment.

Point to the deterministic policy, the three bounded specialist steps, and the
human approval boundary. Say that the model cannot select routes, approve a
draft, or trigger a side effect.

## Period 3 — 0:45–1:20 · Browser · Policy Builder

**Capture this window:** the ResolveDesk dashboard’s **Policy Builder**.

Show the active version-one rules. Change the stalled-tracking threshold in a
draft and use **Test draft with synthetic order**. Explain that the test does
not publish the change or call an external service. Publish only if you want
the next synthetic scan to use the revised policy, then point to the immutable
version number. Emphasise that administrators can configure bounded business
rules, but cannot add code, prompts, webhooks, or automated action authority.

## Period 4 — 1:20–1:45 · Browser · connector documentation

**Capture this window:** the rendered WooCommerce connector configuration or
documentation, with no credentials displayed.

State clearly that it is a read-only HTTPS GET connector with server-side Read
credentials and explicit tracking-metadata mapping. If an authorised staging
integration was not run, leave it unconfigured and say so; the control remains
unavailable and the synthetic queue is the truthful demo input.

## Period 5 — 1:45–2:00 · Terminal · local demo startup

**Capture this window:** a terminal showing only the fresh local-demo command;
hide environment variables and do not show any token value.

```powershell
uv sync --extra dev
uv run order-exception-captain-api --database data/video-demo.sqlite3
```

Say that the API is starting against a fresh local SQLite database containing
no customer data.

## Period 6 — 2:00–2:25 · Browser · synthetic queue

**Capture this window:** the locally running ResolveDesk dashboard, starting
empty and then showing **Load demo queue**.

Say that the queue contains only reserved-domain synthetic data and that the
screen shows the latest aggregate scan result.

## Period 7 — 2:25–3:10 · Browser · deterministic incident review

**Capture this window:** incident `order-1042` in the ResolveDesk workbench.

Show the policy trigger, evidence, selected carrier-escalation draft, and
customer-message draft. Explain that the coordinator—not the language
model—selected this route because tracking is stalled after the promised date.

## Period 8 — 3:10–3:45 · Browser · human approval and dry run

**Capture this window:** the same incident’s approval dialog and audit trail.

Approve the draft with a demo operator name. Show the new audit event, then
choose **Prepare dry-run handoff**. Point to `external_request_sent=false` and
the audit message stating that no request was sent. This is the safety claim:
the application is useful before it has permission to act externally.

## Period 9 — 3:45–4:10 · Browser · human rejection

**Capture this window:** incident `order-1044` in the ResolveDesk workbench.

Choose **Reject draft**, enter a concise reason, and show that the approval
path is closed and the rejection is recorded. This makes the human decision
visible rather than a vague promise.

## Period 10 — 4:10–4:30 · Terminal · backup and access safeguards

**Capture this window:** a terminal showing the backup command and its
non-secret result.

```powershell
uv run order-exception-captain-backup --database data/video-demo.sqlite3 --output-directory backups/video
```

Mention that non-local binding requires an operator token, the dashboard holds
it only in memory, and the deployed demo’s operator/admin tokens were generated
on the VPS rather than supplied by AWS or WooCommerce. Do not show or say their
values. The deployment guide requires TLS and an identity-aware proxy before
real data.

## Period 11 — 4:30–5:00 · Code editor · Strands and Bedrock proof

**Capture this window:** `strands_runtime.py` and the non-secret preflight
record or recorded synthetic Bedrock trace. Do not show an AWS credential
profile, environment file, or console with secrets.

Show the bounded evidence, resolution, and communications roles. If that
evidence is unavailable, or you elect to make a fresh paid call, obtain explicit
approval before running the live smoke test. Do not represent the offline
template runner as a live model invocation or imply that Bedrock selected a
resolution.

Close with: “ResolveDesk narrows an ambiguous delivery problem into a
repeatable, reviewable decision—without allowing an agent to silently send,
refund, replace, or purchase anything.”
