# Agent Framework — Current Project Facts

**Observed at:** 2026-09-09 21:27 Europe/Amsterdam  
**Repository:** `market-predictions/agent`  
**Status type:** project-local implementation snapshot only  
**Control runtime/status authority:** **no**

> This file summarizes bounded project facts for operators and governed work. It is not the Control runtime queue, does not establish global Control status, and must never override current Mission/repository authority or live GitHub facts.

## Current implementation state

```text
architecture_version=v0.4
implementation_state=PRE_IMPLEMENTATION_WITH_BOOTSTRAP_CANDIDATE
github_source_of_truth=true
modal_runtime_deployed=false
hermes_runtime_deployed=false
freellmapi_deployed=false
trusted_verifier_deployed=false
worker_fanout_deployed=false
mobile_interactive_hermes_deployed=false
framework_database_present=false
framework_queue_present=false
production_project_write_authority=false
control_management_status=CONTROL_MANAGED
bootstrap_candidate_pr=1
bootstrap_handoff_status=CANDIDATE_BINDING_BLOCKED
```

## Current product decisions

- Hermes is the selected agent runtime.
- FreeLLMAPI is the canonical inference gateway from the first proof.
- Phase 1 uses all providers for which FreeLLMAPI has valid configuration/credentials; there is no temporary direct-provider path or hand-maintained one-provider pilot.
- Modal is the planned cloud runtime.
- The first generic inference lane is `PUBLIC_NON_PERSONAL` only.
- The first worker is one bounded fixed-safe-tool Hermes one-shot.
- Independent evidence verification is a separate trusted function.
- Worker fan-out is introduced only after a measured diversity/value experiment.
- Modal Sandbox is introduced only for task classes that actually need shell/generated-code/broad executable tooling.
- Mobile/interactive Hermes is a planned later capability and remains separate from bounded-worker business authority.

## Control governance state

`AGENT_FRAMEWORK` is canonically onboarded under Control V4.

```text
control_adoption_pr=252
control_adoption_merge=a6f627944d1e96d8f1a3111e62ccb8ef5cd36635
mission=control/missions/AGENT_FRAMEWORK.mission.json
mission_revision=2026-09-09-r1
repository_authority=control/repository-authority/market-predictions__agent.json
```

Post-adoption readback confirmed both authority files on `market-predictions/control-plane@main`. PR #250 is closed as superseded; PR #252 is historical adoption evidence, not a state plane.

Current Control lifecycle/status must be read from Control's canonical V4 runtime sources, not inferred from this file.

## Bootstrap candidate

Agent PR #1 (`bootstrap/agent-r1-gap-01`) is the intentionally small implementation candidate for `AGENT-R1-GAP-01`.

It establishes only:

```text
Hermes selected runtime
  -> FreeLLMAPI-only inference boundary
  -> model auto through custom Hermes alias
  -> PUBLIC_NON_PERSONAL
  -> read-only Hermes web toolset
  -> one-task budget envelope
  -> local boundary tests
```

The candidate code has been independently verified with six passing stdlib unit tests and successful dry-run plan generation. It does **not** claim that Hermes, FreeLLMAPI or Modal are deployed or that GAP-01 acceptance is satisfied.

## Current bootstrap handoff blocker

The intended handoff is not yet executable end-to-end with current Control V4.

Current deterministic V4 materialization creates a newly eligible root task with:

```text
candidate=null
phase=BUILD
```

The currently bound Runner has the explicit rule:

```text
BUILD: candidate-less BUILD always YIELDs
```

Current carrier V1 does not automatically discover or bind the already-open Agent PR #1 to that task. Therefore the project is Control-managed and the bootstrap candidate exists, but Control cannot yet enter autonomous REPAIR/REVIEW on that candidate.

The smallest missing capability is **existing-candidate binding**: validate a pre-existing governed target PR and bind it through existing `CANDIDATE_READY` semantics. This should not create code/branches/PRs, a second queue/state plane, or generic candidate-less BUILD.

Until that binding is governed and available, do not claim that Control has taken over GAP-01 implementation.

## First governed gap

The canonical Mission's first OPEN root is `AGENT-R1-GAP-01`: the Phase-1 carrier proof.

```text
Hermes
  -> protected FreeLLMAPI
  -> all configured free providers eligible
  -> bounded PUBLIC_NON_PERSONAL research task
  -> structured result + provenance
```

Canonical acceptance requires exact-head implementation/test evidence, bounded non-production Modal execution, hard model/tool/retry/time budgets, provider-key isolation, route/failure observability, at least 20 repeated quality runs with an initial approximately 70% human-usable quality gate, documentation alignment and fresh external exact-candidate review.

Task materialization/lifecycle status belongs to Control's canonical runtime queue and must not be mirrored here.

## Known prerequisites / likely blockers

The project currently has no committed runtime credentials or deployment secrets. This is intentional.

A real Modal/FreeLLMAPI proof will require externally configured credentials/secrets that are not stored in GitHub. Absence of those credentials is an operational prerequisite, not permission to embed them in repository code or documentation.

## Cleanup rule

Every governed change must leave one coherent current truth. Superseded direct-provider experiments, obsolete runtime paths, stale docs and conflicting configuration must be deleted rather than left as parallel alternatives unless an active governed requirement explicitly needs them.
