# Agent Framework — Current Project Facts

**Observed date:** 2026-09-09  
**Repository:** `market-predictions/agent`  
**Status type:** project-local implementation snapshot only  
**Control runtime/status authority:** **no**

> Live GitHub/Modal facts override this snapshot. This file is not the Control runtime queue and never grants lifecycle authority.

## Current implementation state

```text
architecture_version=v0.4
implementation_state=OPERATIONAL_PHASE1_CARRIER_PROVEN_IN_GITHUB_ACTIONS
github_source_of_truth=true
real_hermes_freellm_model_web_chain_proven=true
modal_runtime_code_present=true
modal_live_deployment_proven=false
modal_deployment_blocker=EXTERNAL_ACCOUNT_CREDENTIALS_ABSENT
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

## Proven Phase-1 carrier

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

The current output authority is `CANDIDATE`. `RESULT_READY` does not exist until the separate trusted verifier is implemented.

## Security/capability facts

- Hermes receives no upstream provider API keys.
- Hermes receives no target-project production write credentials.
- The generic inference lane is `PUBLIC_NON_PERSONAL` only.
- No direct-provider bypass or second agent runtime exists.
- No framework DB, queue, publisher, fan-out, persistent Hermes memory, Sandbox, or paid fallback exists.
- The zero-key model bootstrap uses current upstream keyless Kilo and OVH adapters.
- Modal topology caps FreeLLMAPI and Hermes at one active container each and scales them to zero.

## Modal deployment boundary

The repository contains the complete selected Modal topology and deployment workflow. A live cloud deployment is **not** current fact.

Observed deployment prerequisite failure: GitHub does not currently contain the account-owned `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`, so deployment stops before `modal deploy`. The repository and connected tools cannot create or recover the user's Modal account token. Named runtime Secrets are documented in `docs/OPERATIONS.md` and must remain outside Git.

The deployment workflow now runs from `main` or explicit dispatch only; candidate commits no longer create repeated credential-failure jobs.

## Verification facts

Candidate CI has two layers:

1. deterministic compile/tests/topology/contract checks;
2. exact upstream integration with a real free model and real Hermes web-tool execution.

The live provider proof runs once per pull-request candidate and once after merge to `main` to avoid duplicate free-provider quota use.

Exact current head/check status must always be read from PR #1 rather than copied here as authority.

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

## Scope after first operational carrier

Full `AGENT-R1-GAP-01` acceptance is broader than the proven carrier and still requires qualification/review evidence such as repeated runs and the Mission's quality gate.

Later roadmap phases add independent evidence verification, optional parallelism only if measured useful, persistence only if measured necessary, caller/project integration, and finally interactive/mobile Hermes.

## Cleanup rule

Every consequential change must leave one coherent current truth. Superseded code/config/docs are deleted instead of kept as parallel alternatives unless an active requirement explicitly needs them.
