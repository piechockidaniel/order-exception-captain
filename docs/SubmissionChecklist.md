# Agents for Humans submission checklist

Track: **Professional Agents**. Current official deadline: **September 14,
2026, 5:00pm PDT**. Verify the rules again immediately before submitting.

| Requirement | Status | Evidence or next action |
|---|---|---|
| New project created during submission period | complete | New repository; provenance is documented in the README. |
| Strands Agents SDK and Amazon Bedrock incorporated | complete | The bounded Bedrock Haiku 4.5 trace completed on synthetic data in `eu-north-1` after a non-secret preflight. The fixed evidence → resolution → communications sequence produced no external action. |
| Works consistently as depicted | complete for the synthetic demo | Verified on 2026-09-03: the 49-case automated suite exited successfully, `uv build` succeeded with all dashboard assets, a fresh scheduled scan created one incident, and its backup passed SQLite integrity. Release `3a24f88` is live on the VPS: the public shell and health endpoint return `200`, while anonymous incident access returns `401`. |
| Public repository with visible MIT/Apache license and README | complete | Anonymous GitHub lookup confirms the repository is public and visibly MIT-licensed with a README. Public `main` was pushed and verified at `3a24f88` on 2026-09-03. |
| Architecture diagram | complete | Mermaid diagram in `docs/Architecture.md`. |
| English text description and testing instructions | complete | Copy-ready [Devpost submission text](DevpostSubmission.md), README, and demo script are in English. |
| Public video, maximum five minutes | ready to record | `docs/DemoScript.md`; upload to public YouTube or Vimeo. Show the non-secret recorded Bedrock trace if available; a new paid invocation is only needed if you choose to make one and explicitly approve it. |
| AWS Builder ID | not started | Add it on the Devpost submission form. |
| Devpost form | not started | Complete the required English fields and submit before the deadline. |
| Optional live demo link | complete | [`https://oec.connect-the-dots.biz`](https://oec.connect-the-dots.biz) serves the synthetic dashboard over HTTPS. Its operator/admin tokens are generated and held only on the VPS; do not publish them. |
| Optional AWS Builder blog post | not started | Can cover the product journey after the submission is stable. |

## Before submitting

1. Record the video using the script; keep it under five minutes and publish it.
2. Complete Devpost fields in English, including the code URL, diagram, video,
   Builder ID, and testing instructions.

The live Bedrock trace has already been captured on synthetic data. Re-run the
authorised smoke invocation only if its configuration or code changes, if its
recorded evidence is unavailable for the video, or if you explicitly decide to
create a fresh paid trace. AgentCore, staging-store validation, and the AWS
Builder blog post are optional score or product follow-ons, not core submission
blockers.

The official rules require a new Strands project that does real work for real
people, a public licensed repository, an architecture diagram, a public video,
and AWS Builder ID. They say a live demo and/or Amazon Bedrock AgentCore may
strengthen technical implementation, but AgentCore is not mandatory. Source:
[Agents for Humans official rules](https://agentsforhumans.devpost.com/rules).
