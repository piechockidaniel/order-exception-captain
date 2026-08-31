# Bedrock proof runbook

Use this runbook only for the final, synthetic Strands-on-Bedrock proof. It is
not a production deployment guide and it must never be used with real customer,
order, carrier, or payment data.

## What the recording must prove

The video should visibly establish all of these facts:

1. The deterministic coordinator routes the synthetic delivery exception before
   calling any specialist.
2. Three Strands specialists run in the fixed evidence, resolution, then
   communications order.
3. The model is invoked through Amazon Bedrock with an explicitly selected
   region and model, never with credentials stored in the repository.
4. The result remains an approval-gated draft; no carrier, store, customer, or
   financial action can occur.

## Before authorising the run

1. Choose an Amazon Bedrock model available to the AWS account in the target
   region. Confirm any model-access and Marketplace prerequisites in the AWS
   console. [AWS model access guidance](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
2. Make standard AWS credentials available through a local profile or role. Do
   not paste credentials into a shell transcript, source file, video, or chat.
3. Set an AWS billing alert or budget. `OEC_COST_BOUNDARY` records an approval,
   but it cannot enforce a dollar ceiling.
4. Agree a small, specific first-run boundary, such as one synthetic invocation
   with a 128-token output limit for each specialist. The runner rejects smaller
   limits before a model call because they cannot reliably finish its bounded
   tool-assisted response.

## Safe preflight

In a local PowerShell session, set only non-secret run settings:

```powershell
$env:OEC_MODEL_PROVIDER = "bedrock"
$env:OEC_MODEL_ID = "<model-enabled-for-this-account>"
$env:AWS_REGION = "<enabled-model-region>"
$env:OEC_MAX_TOKENS = "128"
$env:OEC_COST_BOUNDARY = "One synthetic proof run; operator-approved boundary: <amount>"
uv run order-exception-captain-live
```

Review the printed configuration and the new non-secret file in
`data/live-runs/`. The command exits without an inference request at this
stage. Do not continue if the selected model, region, synthetic input, or
boundary are wrong.

## Authorised live proof

After that review, use the same shell to run:

```powershell
uv run order-exception-captain-live --allow-live-model-call
```

Record the terminal and local dashboard for the video. State precisely that
Bedrock produces bounded drafts, while the deterministic policy selects the
route and a named human remains responsible for approval. Keep the generated
preflight record out of the public repository unless it has been reviewed for
safe publication.

## Optional AgentCore upgrade

The contest rules say an Amazon Bedrock AgentCore deployment can strengthen the
Technical Implementation score, but it is not required. Treat it as a separate
decision after the local Bedrock trace is successful: first run the AgentCore
deployment tooling in dry-run mode, review the resources and cost impact, then
seek explicit approval before deployment. [AgentCore CLI guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-cli.html)
