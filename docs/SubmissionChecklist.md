# Agents for Humans submission checklist

Track: **Professional Agents**. Current official deadline: **September 14,
2026, 5:00pm PDT**. Verify the rules again immediately before submitting.

| Requirement | Status | Evidence or next action |
|---|---|---|
| New project created during submission period | complete | New repository; provenance is documented in the README. |
| Strands Agents SDK and Amazon Bedrock incorporated | complete, live proof pending | Dependency and bounded Bedrock runtime roles are in source. Record the authorised live synthetic run before the video. |
| Works consistently as depicted | in progress | 37 automated tests, wheel, browser checks, and a disposable container health check pass; record the final video against the tagged code. |
| Public repository with visible MIT/Apache license and README | blocked on publication approval | Remote exists with MIT license and README, but repository visibility has not been changed. |
| Architecture diagram | complete | Mermaid diagram in `docs/Architecture.md`. |
| Public video, maximum five minutes | ready to record | `docs/DemoScript.md`; upload to public YouTube or Vimeo after final live-proof run. |
| AWS Builder ID | not started | Add it on the Devpost submission form. |
| Optional live demo link | not started | Deploy only after hosting, telemetry, retention, and access decisions are authorised. |
| Optional AWS Builder blog post | not started | Can cover the product journey after the submission is stable. |

## Before submitting

1. Re-run `uv run pytest` and capture the result.
2. Run the authorised, synthetic Strands-on-Bedrock smoke invocation and save
   its non-secret preflight/trace evidence.
3. Record the video using the script; keep it under five minutes and publish it.
4. Confirm permission to make the repository public, then verify anonymous
   access to the README and MIT license.
5. Complete Devpost fields in English, including the code URL, diagram, video,
   Builder ID, and testing instructions.

The official rules require a new Strands project that does real work for real
people, a public licensed repository, an architecture diagram, a public video,
and AWS Builder ID. They say a live demo and/or Amazon Bedrock AgentCore may
strengthen technical implementation, but AgentCore is not mandatory. Source:
[Agents for Humans official rules](https://agentsforhumans.devpost.com/rules).
