# Agent Framework — Current Project Facts

**Observed date:** 2026-09-10  
**Repository:** `market-predictions/agent`  
**Status type:** project-local implementation snapshot only  
**Control runtime/status authority:** **no**

> Live GitHub/Modal facts override this snapshot. This file is not the Control runtime queue and never grants lifecycle authority.

## Current implementation state

```text
architecture_version=v0.4
implementation_state=PHASE1_CARRIER_QUALIFIED_EXTERNAL_REVIEW_PENDING
github_source_of_truth=true
real_hermes_freellm_model_web_chain_proven=true
modal_runtime_code_present=true
modal_live_deployment_proven=true
modal_remote_smoke_proven=true
modal_deployment_blocker=NONE
modal_runtime_secret_bootstrap_proven=true
phase1_qualification_runs=20
phase1_structured_candidate_rate=0.90
phase1_human_usable_rate=0.90
phase1_supported_candidate_claim_rate=1.00
phase1_external_review_passed=false
hermes_runtime_pinned=true
freellmapi_runtime_pinned=true
trusted_verifier_deployed=false
worker_fanout_deployed=false
mobile_interactive_hermes_deployed=false
framework_database_present=false
framework_queue_present=false
production_project_write_authority=false
control_management_status=CONTROL_MANAGED
bootstrap_candidate_pr=1
control_baseline=FROZEN
```

## Proven and qualified Phase-1 carrier

PR #1 contains and has executed the actual bounded runtime chain:

```text
pinned Hermes 0.21.1 / exact commit
  -> named Hermes provider freellmapi
  -> pinned FreeLLMAPI 0.9.8 / exact image digest
  -> keyless Kilo + OVH bootstrap
  -> real routed free model
  -> Hermes live web tool
  -> strict CANDIDATE
```

A clean GitHub-hosted proof installs Hermes from the exact source commit, pulls/starts the exact FreeLLMAPI image, verifies gateway authentication, performs a direct real `model=auto` inference with `X-Routed-Via`, and then completes the actual Hermes web-tool carrier.

The same pinned carrier is deployed on Modal. The live promotion authenticated from GitHub Actions, created the required runtime credential boundary, deployed the protected FreeLLMAPI service plus bounded Hermes Function, and completed the remote smoke with `CANDIDATE`.

The fixed Phase-1 qualification then executed 20 sequential `PUBLIC_NON_PERSONAL` research tasks through the live Modal carrier. Eighteen returned strict source-bearing candidates. Manual source readback confirmed all 18 candidate claims, producing a 90% human-usable run rate against the Mission's initial approximately 70% gate. Both non-candidate runs were strict-schema failures and remained fail-closed. Detailed evidence identity and review are in `qualification/PHASE1_QUALIFICATION_REVIEW.md`.

The current output authority remains `CANDIDATE`. Qualification does not create `RESULT_READY`; that requires the separate trusted verifier.

## Security/capability facts

- Hermes receives no upstream provider API keys.
- Hermes receives no target-project production write credentials.
- The generic inference lane is `PUBLIC_NON_PERSONAL` only.
- No direct-provider bypass or second agent runtime exists.
- Hermes exposes only the `web` toolset in the bounded worker.
- Hard model-call, tool-call, retry, wall-time and concurrency limits are enforced fail-closed.
- No framework DB, queue, publisher, fan-out, persistent Hermes memory, Sandbox, or paid fallback exists in PR #1.
- The zero-key model bootstrap uses current upstream keyless Kilo and OVH adapters.
- Modal topology caps FreeLLMAPI and Hermes at one active container each and scales them to zero.
- GitHub holds only the Modal deployment token pair as encrypted Actions Secrets; generated runtime credentials remain in Modal Secrets.
- The runtime bootstrap is idempotent and fails closed on partial named-Secret state.

## Modal deployment boundary

The canonical deployment path is `.github/workflows/deploy-modal.yml` and is explicit-dispatch only.

Current verified chain:

```text
GitHub Actions repository Secrets
  -> Modal account authentication
  -> idempotent runtime credential bootstrap
  -> modal deploy modal_app.py
  -> protected FreeLLMAPI web service
  -> bounded Hermes Function
  -> optional remote smoke / qualification
  -> CANDIDATE evidence
```

The one-time qualification trigger and temporary second deployment workflow were removed after the first evidence run. The qualification harness remains reusable only as an explicit option on the canonical deployment workflow. Ordinary source pushes therefore do not automatically deploy or spend Modal compute.

## Verification facts

Candidate CI has two layers:

1. deterministic compile/tests/topology/contract checks;
2. exact upstream integration with a real free model and real Hermes web-tool execution.

The live provider proof runs once per pull-request candidate and once per merge to `main` to avoid duplicate free-provider quota use. Modal promotion is separately explicit.

The 20-run qualification evidence is bound to runtime candidate `a74871525458e47f69fa2c01ba6d0bdfc4a01202`; later PR #1 cleanup changes only evidence/documentation/workflow surfaces and does not relax or replace the measured worker runtime. Exact current PR head/check status must always be read live from PR #1.

The remaining `AGENT-R1-GAP-01` acceptance gate is a fresh external exact-candidate review after final exact-head CI.

## Control governance state

`AGENT_FRAMEWORK` is canonically onboarded under Control V4:

```text
control_adoption_pr=252
control_adoption_merge=a6f627944d1e96d8f1a3111e62ccb8ef5cd36635
mission=control/missions/AGENT_FRAMEWORK.mission.json
mission_revision=2026-09-09-r1
repository_authority=control/repository-authority/market-predictions__agent.json
```

Control remains deliberately frozen. The known candidate-less BUILD / existing-candidate binding limitation is not an Agent runtime blocker and is not worked around with another scheduler, queue, poller, or semantic actor.

A separate proposed Mission revision may change later gap sequencing; until merged into Control main it is not canonical authority and is intentionally not reflected here as current Control state.

## Scope after Phase-1 acceptance

The first carrier is qualified but not yet externally accepted. Later governed work may add interactive Hermes, independent evidence verification, optional parallelism only if measured useful, and bounded caller/project integration. Their exact sequence comes from the current canonical Mission, not from this snapshot.

## Cleanup rule

Every consequential change must leave one coherent current truth. Superseded code/config/docs are deleted instead of kept as parallel alternatives unless an active requirement explicitly needs them.
