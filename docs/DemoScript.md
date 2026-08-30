# Five-minute demo script

This is a truthful recording outline, not a claim that an external action was
performed. Keep the recording under five minutes and use only the synthetic
orders shipped with the repository.

## 0:00–0:30 — problem and audience

“Independent ecommerce operators lose time discovering delivery failures,
checking carrier evidence, and writing customer updates. Order Exception
Captain is a Professional Agent for that narrow post-purchase workflow. It
turns a delivery exception into an explainable draft, but a human stays in
control of every consequence.”

Show the architecture diagram. Point to the deterministic policy and the
approval boundary.

## 0:30–1:15 — start and show the product

Start the local API with a fresh database, then open the dashboard:

```powershell
uv sync --extra dev
uv run order-exception-captain-api --database data/video-demo.sqlite3
```

Show the empty dashboard, then select **Load demo queue**. Say that the queue
contains only reserved-domain synthetic data and that the screen shows the
latest aggregate scan result.

## 1:15–2:15 — explain one deterministic incident

Open `order-1042`. Show the policy trigger, evidence, selected carrier
escalation draft, and customer-message draft. Explain that the coordinator—not
the language model—selected this route because tracking is stalled after the
promised date.

## 2:15–3:00 — human approval and auditable dry run

Approve the draft with a demo operator name. Show the new audit event, then
choose **Prepare dry-run handoff**. Point to `external_request_sent=false` and
the audit message stating that no request was sent. This is the safety claim:
the application is useful before it has permission to act externally.

## 3:00–3:35 — show human rejection

Open `order-1044`, choose **Reject draft**, enter a concise reason, and show
that the approval path is closed and the rejection is recorded. This makes the
human decision visible rather than a vague promise.

## 3:35–4:25 — show operational safeguards

Briefly show the scan activity, then run a verified backup:

```powershell
uv run order-exception-captain-backup --database data/video-demo.sqlite3 --output-directory backups/video
```

Mention that non-local binding requires an operator token, that the dashboard
holds it only in memory, and that the deployment guide requires TLS and an
identity-aware proxy before real data.

## 4:25–5:00 — Strands and honest close

Show `strands_runtime.py` and the bounded evidence, resolution, and
communications roles. For the final submission, run the separately authorised
synthetic live smoke test and include its visible trace in this segment. Do not
represent the offline template runner as a live model invocation.

Close with: “Order Exception Captain narrows an ambiguous delivery problem into
a repeatable, reviewable decision—without allowing an agent to silently send,
refund, replace, or purchase anything.”
