# Five-minute demo script

This is a truthful recording outline, not a claim that an external action was
performed. Keep the recording under five minutes. Use only the synthetic orders
shipped with the repository unless an authorised staging WooCommerce scan has
been separately validated and recorded.

## 0:00–0:30 — problem and audience

“Independent ecommerce operators lose time discovering delivery failures,
checking carrier evidence, and writing customer updates. Order Exception
Captain is a Professional Agent for that narrow post-purchase workflow. It
turns a delivery exception into an explainable draft, but a human stays in
control of every consequence.”

Show the architecture diagram. Point to the deterministic policy and the
approval boundary.

## 0:30–1:15 — configure the deterministic policy

Open **Policy Builder** and show the active version-one rules. Change the
stalled tracking threshold in a draft, use **Test draft with synthetic order**,
and explain that the test does not publish the change or call any external
service. Publish only if you want the next synthetic scan to use the revised
policy, then point to the immutable version number. Emphasise that administrators
can configure bounded business rules, but cannot add code, prompts, webhooks,
or automated action authority.

## 1:15–1:45 — show the connector boundary

Show the documented WooCommerce configuration. State clearly that it is a
read-only HTTPS GET connector with server-side Read credentials and explicit
tracking metadata mapping. If an authorised staging integration was not run,
leave it unconfigured and say so; the control remains unavailable and the
synthetic queue is the truthful demo input.

## 1:45–2:25 — start and show the product

Start the local API with a fresh database, then open the dashboard:

```powershell
uv sync --extra dev
uv run order-exception-captain-api --database data/video-demo.sqlite3
```

Show the empty dashboard, then select **Load demo queue**. Say that the queue
contains only reserved-domain synthetic data and that the screen shows the
latest aggregate scan result.

## 2:25–3:10 — explain one deterministic incident

Open `order-1042`. Show the policy trigger, evidence, selected carrier
escalation draft, and customer-message draft. Explain that the coordinator—not
the language model—selected this route because tracking is stalled after the
promised date.

## 3:10–3:45 — human approval and auditable dry run

Approve the draft with a demo operator name. Show the new audit event, then
choose **Prepare dry-run handoff**. Point to `external_request_sent=false` and
the audit message stating that no request was sent. This is the safety claim:
the application is useful before it has permission to act externally.

## 3:45–4:10 — show human rejection

Open `order-1044`, choose **Reject draft**, enter a concise reason, and show
that the approval path is closed and the rejection is recorded. This makes the
human decision visible rather than a vague promise.

## 4:10–4:35 — show operational safeguards

Briefly show the scan activity, then run a verified backup:

```powershell
uv run order-exception-captain-backup --database data/video-demo.sqlite3 --output-directory backups/video
```

Mention that non-local binding requires an operator token, that the dashboard
holds it only in memory, and that the deployed demo's operator/admin tokens
were generated on the VPS rather than supplied by AWS or WooCommerce. Do not
show or say their values. The deployment guide requires TLS and an
identity-aware proxy before real data.

## 4:35–5:00 — Strands, Bedrock, and honest close

Show `strands_runtime.py` and the bounded evidence, resolution, and
communications roles. Show the preflight record configured for Amazon Bedrock,
then run the separately authorised synthetic live smoke test and include its
visible trace in this segment. Do not represent the offline template runner as
a live model invocation or imply that Bedrock selected a resolution.

Close with: “Order Exception Captain narrows an ambiguous delivery problem into
a repeatable, reviewable decision—without allowing an agent to silently send,
refund, replace, or purchase anything.”
