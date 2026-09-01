# Agents for Humans submission checklist

Track: **Professional Agents**. Current official deadline: **September 14,
2026, 5:00pm PDT**. Verify the rules again immediately before submitting.

| Requirement | Status | Evidence or next action |
|---|---|---|
| New project created during submission period | complete | New repository; provenance is documented in the README. |
| Strands Agents SDK and Amazon Bedrock incorporated | complete | The bounded Bedrock Haiku 4.5 trace completed on synthetic data in `eu-north-1` after a non-secret preflight. The fixed evidence → resolution → communications sequence produced no external action. |
| Works consistently as depicted | complete for the synthetic demo | 49 automated tests pass, and the live VPS demo has verified HTTPS, health, token-gated routes, administrator access, and a SQLite integrity-checked backup. Record the final video against this source revision. |
| Public repository with visible MIT/Apache license and README | complete | Anonymous GitHub lookup confirms the public repository, visible MIT license, and README. |
| Architecture diagram | complete | Mermaid diagram in `docs/Architecture.md`. |
| English text description and testing instructions | complete | Copy-ready [Devpost submission text](DevpostSubmission.md), README, and demo script are in English. |
| Public video, maximum five minutes | ready to record | `docs/DemoScript.md`; upload to public YouTube or Vimeo after final live-proof run. |
| AWS Builder ID | not started | Add it on the Devpost submission form. |
| Optional live demo link | complete | [`https://oec.connect-the-dots.biz`](https://oec.connect-the-dots.biz) serves the synthetic dashboard over HTTPS. Its operator/admin tokens are generated and held only on the VPS; do not publish them. |
| Optional AWS Builder blog post | not started | Can cover the product journey after the submission is stable. |

## Before submitting

1. Re-run `uv run pytest` and capture the result.
2. Re-run the authorised, synthetic Strands-on-Bedrock smoke invocation and save
   its non-secret preflight/trace evidence if the model, region, prompts, or source revision changed.
3. Optionally run an AgentCore deployment dry-run, then seek explicit approval
   before deploying it as a technical-score upgrade.
4. Record the video using the script; keep it under five minutes and publish it.
5. Verify anonymous access to the public README and MIT license after the final push.
6. Complete Devpost fields in English, including the code URL, diagram, video,
   Builder ID, and testing instructions.

The official rules require a new Strands project that does real work for real
people, a public licensed repository, an architecture diagram, a public video,
and AWS Builder ID. They say a live demo and/or Amazon Bedrock AgentCore may
strengthen technical implementation, but AgentCore is not mandatory. Source:
[Agents for Humans official rules](https://agentsforhumans.devpost.com/rules).
