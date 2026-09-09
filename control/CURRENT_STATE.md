# Agent Framework — Current Project Facts

**Observed date:** 2026-09-09  
**Repository:** `market-predictions/agent`  
**Status type:** project-local implementation snapshot only  
**Control runtime/status authority:** **no**

> This file summarizes bounded project facts. Live GitHub/Modal facts override it. It is not the Control runtime queue and never grants lifecycle authority.

## Current implementation state

```text
architecture_version=v0.4
implementation_state=DEPLOYABLE_PHASE1_CARRIER_CANDIDATE
github_source_of_truth=true
modal_runtime_code_present=true
modal_live_deployment_proven=false
hermes_runtime_pinned=true
freellmapi_runtime_pinned=true
local_real_hermes_freellm_ci=IN_VALIDATION
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

## Implemented Phase-1 carrier

PR #1 now contains the actual minimal runtime implementation rather than only a bootstrap plan:

```text
Modal Hermes Function
  -> pinned Hermes 0.21.1 / exact commit
  -> one-shot
  -> Hermes web toolset only
  -> protected FreeLLMAPI /v1

Modal FreeLLMAPI service
  -> pinned v0.9.8 image digest
  -> Modal proxy auth
  -> stable unified bearer
  -> keyless Kilo + OVH default bootstrap pool
  -> optional complete FREEAPI_CONFIG_JSON provider config
```

Current candidate output state is `CANDIDATE`. `RESULT_READY` remains unavailable until the separate trusted verifier is implemented in Phase 2.

## Current security/capability facts

- Hermes receives no upstream provider API keys.
- Hermes receives no target-project production write credentials.
- The generic inference lane is `PUBLIC_NON_PERSONAL` only.
- FreeLLMAPI and Hermes are capped at one active Modal container each in Phase 1 and scale to zero.
- There is no direct-provider bypass, second agent runtime, framework DB, queue, publisher, fan-out, persistent Hermes memory, Modal Sandbox, or hidden paid fallback.
- FreeLLMAPI's default model bootstrap needs no provider key because current upstream Kilo and OVH adapters are keyless.

## Verification facts

Repository CI now covers two classes:

1. deterministic carrier/config/topology tests;
2. actual pinned upstream integration: exact Hermes install, exact FreeLLM image start/authentication, live `model=auto` call and a real local Hermes -> FreeLLMAPI -> web-tool candidate run.

The exact current head/run result must be read from PR #1. Do not copy a historical run number here as current authority.

## Live deployment boundary

The repository contains a complete Modal deployment path (`modal_app.py` and `.github/workflows/deploy-modal.yml`). A live cloud deployment cannot be claimed until the user's external Modal account credentials and named Modal Secrets exist and a remote smoke run passes.

Required secrets are documented in `docs/OPERATIONS.md`. Secret absence is not permission to commit credentials.

## Control governance state

`AGENT_FRAMEWORK` is canonically onboarded under Control V4:

```text
control_adoption_pr=252
control_adoption_merge=a6f627944d1e96d8f1a3111e62ccb8ef5cd36635
mission=control/missions/AGENT_FRAMEWORK.mission.json
mission_revision=2026-09-09-r1
repository_authority=control/repository-authority/market-predictions__agent.json
```

Control is deliberately frozen during this Agent implementation. The known candidate-less BUILD / existing-candidate-binding limitation is not an Agent runtime blocker and is not worked around with a second Agent-side scheduler, queue, poller or semantic actor.

## First governed gap

Canonical `AGENT-R1-GAP-01` remains broader than merely getting the first runtime online. Full acceptance also requires the 20-run qualification/quality evidence, exact-head validation and required external review.

The current objective is the smaller operational milestone:

```text
working Hermes
  -> working protected FreeLLMAPI
  -> actual free model
  -> Hermes web lookup
  -> structured CANDIDATE
  -> live on Modal
```

## Known open evidence

- live Modal deployment/readback;
- remote Modal end-to-end smoke;
- exact tool-call counter enforcement if it remains required and stable upstream telemetry does not expose it;
- 20-run qualification and initial usefulness gate;
- Phase-2 trusted verifier;
- external exact-candidate review for full GAP-01 acceptance.

## Cleanup rule

Every change must leave one coherent current truth. Superseded code/config/docs are deleted rather than retained as parallel alternatives unless an active requirement explicitly needs them.
