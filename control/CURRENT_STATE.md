# Agent Framework — Current Project Facts

**Observed date:** 2026-09-11  
**Repository:** `market-predictions/agent`  
**Status type:** project-local implementation snapshot only  
**Control runtime/status authority:** **no**

> Live GitHub/Modal facts override this snapshot. This file is not the Control runtime queue and never grants lifecycle authority.

## Current implementation state

```text
architecture_version=v0.5
bounded_carrier_state=PHASE1_QUALIFIED_EXTERNAL_REVIEW_PENDING
interactive_dashboard_state=DEPLOYED_AUTHENTICATED_BROWSER_CHAT_PROVEN
interactive_dashboard_persistence_restart_proven=false
interactive_dashboard_websocket_browser_proven=true
interactive_dashboard_web_only_authority_pinned=true
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
native_mobile_client_deployed=false
framework_database_present=false
framework_queue_present=false
production_project_write_authority=false
control_management_status=CONTROL_MANAGED
control_baseline=FROZEN
```

## Proven bounded Phase-1 carrier

The bounded runtime executes:

```text
pinned Hermes 0.21.1 / exact commit
  -> named Hermes provider freellmapi
  -> pinned FreeLLMAPI 0.9.8 / exact image digest
  -> keyless Kilo + OVH bootstrap
  -> real routed free model
  -> Hermes live web tool
  -> strict CANDIDATE
```

A clean GitHub-hosted proof installs exact source, pulls/starts exact FreeLLMAPI, verifies gateway auth, performs direct real `model=auto` inference with `X-Routed-Via`, then completes the actual Hermes web-tool carrier.

The fixed 20-run qualification produced 18 strict source-bearing candidates. Manual source readback confirmed all 18 candidate claims, yielding 90% human-usable output against the initial approximately 70% gate. Both non-candidate runs remained fail-closed.

The bounded output authority remains `CANDIDATE`. Qualification does not create `RESULT_READY`.

## Interactive dashboard facts

PR #2 adds a separate native Hermes Web Dashboard/TUI without widening bounded-worker authority.

Verified live facts:

- public Modal dashboard endpoint deployed;
- native Nous Portal OAuth completes in a real browser;
- anonymous session API access fails closed;
- browser-facing WebSocket/chat remains connected after the dashboard-only compression compatibility fix;
- a real interactive prompt completed Hermes web search and returned an answer;
- dashboard runtime is hard-pinned with `HERMES_TUI_TOOLSETS=web`;
- dashboard startup fails closed if that operator pin or the FreeLLMAPI provider boundary is missing;
- terminal, file mutation, browser automation, code execution and delegation are not part of the intended interactive model authority;
- one persistent Modal Volume is present for interactive profiles/sessions/state only;
- restart/scale-down persistence has not yet been intentionally proven.

The dashboard uses one active container maximum. Modal accepts multiple simultaneous HTTP/WebSocket inputs so the native UI transport can function, while Hermes itself remains limited to one concurrent interactive session.

The dashboard's exact Hermes checkout gets one narrow source-anchor-checked Uvicorn setting change (`ws_per_message_deflate=False`) because real production evidence showed protocol close code `1002` through the Modal intermediary. The bounded worker remains unpatched exact upstream Hermes.

## Security/capability facts

- Hermes receives no upstream provider API keys.
- Hermes receives no target-project production write credentials.
- The generic bounded inference lane is `PUBLIC_NON_PERSONAL` only.
- No direct-provider bypass or second agent runtime exists.
- Bounded worker tool authority is only `web_search` / `web_extract`.
- Interactive dashboard model tool authority is hard-pinned to the same web-only set through Hermes' native TUI operator override.
- Hard model-call, tool-call, retry, wall-time and concurrency limits are enforced fail-closed in the bounded worker.
- No framework DB, queue, publisher, fan-out, Sandbox or paid fallback exists.
- GitHub holds only the Modal deployment token pair as encrypted Actions Secrets; generated runtime credentials remain in Modal Secrets.
- Control remains frozen; no second Agent-side scheduler, queue, poller or semantic Control actor has been introduced.

## Modal deployment boundary

The canonical deployment path is `.github/workflows/deploy-modal.yml` and is explicit-dispatch only in steady state.

Current deployed topology:

```text
GitHub Actions repository Secrets
  -> Modal authentication
  -> idempotent runtime credential bootstrap
  -> modal deploy modal_app.py
       -> protected FreeLLMAPI web service
       -> bounded Hermes Function
       -> authenticated Hermes dashboard web function
  -> dashboard auth smoke
  -> optional bounded smoke / qualification
```

Temporary path-limited triggers used only for a deliberate promotion are removed immediately after use. There is no second deployment workflow.

## Verification facts

Candidate CI has two layers:

1. deterministic compile/tests/topology/contract checks;
2. exact upstream integration with a real free model and real Hermes web-tool execution.

The fixed qualification evidence remains historically bound to its measured runtime candidate; later interactive-dashboard work does not rewrite that evidence or relax the bounded worker.

Remaining bounded `AGENT-R1-GAP-01` gate: required fresh external exact-candidate review.

Remaining interactive-dashboard proof: intentional restart/scale-down persistence check, followed by fresh exact-candidate external review once the branch is final.

## Control governance state

`AGENT_FRAMEWORK` remains canonically onboarded under Control V4. This snapshot does not override the canonical Mission or live Control status.

Control remains deliberately frozen. The known candidate-less BUILD / existing-candidate binding limitation is not worked around with another scheduler, queue, poller or semantic actor.

## Cleanup rule

Every consequential change must leave one coherent current truth. Superseded code/config/docs are deleted instead of kept as parallel alternatives unless an active requirement explicitly needs them.