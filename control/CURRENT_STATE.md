# Agent Framework — Current Project Facts

**Observed at:** 2026-09-09 21:14 Europe/Amsterdam  
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
control_management_status=PENDING_AUTHORITY_ADOPTION
bootstrap_candidate_pr=1
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

## Current repository surfaces

Current canonical/project-local documentation:

- `README.md` — concise entry point;
- `docs/ARCHITECTURE.md` — canonical technical architecture;
- `docs/ROADMAP.md` — canonical implementation sequence;
- `docs/DESIGN_REVIEW_10_ITERATIONS.md` — historical/non-canonical design rationale;
- `control/PROJECT_GOVERNANCE.md` — Control V4 project-local governance bootstrap and bootstrap-handoff rule;
- `control/CURRENT_STATE.md` — this bounded snapshot.

`main` still contains no runtime implementation code. The first implementation code exists only in draft Agent PR #1 (`bootstrap/agent-r1-gap-01`) and is intentionally incomplete so Control can converge it after governed onboarding.

## Control onboarding state

The current Control V4 authority candidate is **draft PR #252** in `market-predictions/control-plane`.

```text
control_candidate_pr=252
control_candidate_base=c92cd78dabafafbb4ea1199db0ab1312483dc6f8
control_candidate_head=eec8ce44bb43c5e0a018032b397032e490dc4a71
mission_candidate=control/missions/AGENT_FRAMEWORK.mission.json
repository_authority_candidate=control/repository-authority/market-predictions__agent.json
```

The previous PR #250 is closed as superseded. PR #252 adds only the Mission Contract and matching repository-authority record. It is intentionally **not merged** and is not current Control authority until governed adoption completes.

Until those authority artifacts are reviewed and adopted through the current Control V4 authority-change discipline:

```text
Control may inspect this repository and candidate
but
AGENT_FRAMEWORK is not yet an active governed Mission
```

After adoption, current Control lifecycle/status must be read from Control's canonical V4 sources, not inferred from this file or PR metadata.

## Bootstrap candidate for the first governed gap

Draft Agent PR #1 is the intentionally small implementation candidate for `AGENT-R1-GAP-01`.

It currently establishes only:

```text
Hermes selected runtime
  -> FreeLLMAPI-only inference boundary
  -> model auto through custom Hermes alias
  -> PUBLIC_NON_PERSONAL
  -> read-only Hermes web toolset
  -> one-task budget envelope
  -> local boundary tests
```

The bootstrap candidate has been locally verified with six passing stdlib unit tests and successful dry-run plan generation. It does **not** claim that Hermes, FreeLLMAPI or Modal are deployed or that GAP-01 acceptance is satisfied.

After Mission adoption, Control should own further convergence of this candidate through the existing governed REPAIR / REVIEW / PASS / integration flow. The principal/bootstrap role should not manually complete multiple roadmap phases first.

## Expected first governed gap after adoption

The candidate Mission's first OPEN root is `AGENT-R1-GAP-01`: the Phase-1 carrier proof.

```text
Hermes
  -> protected FreeLLMAPI
  -> all configured free providers eligible
  -> bounded PUBLIC_NON_PERSONAL research task
  -> structured result + provenance
```

The candidate acceptance requires exact-head implementation/test evidence, bounded non-production Modal execution, hard model/tool/retry/time budgets, provider-key isolation, route/failure observability, at least 20 repeated quality runs with an initial approximately 70% human-usable quality gate, documentation alignment and fresh external exact-candidate review.

The canonical gap definition and acceptance criteria exist only after the Mission Contract is adopted on Control authority.

## Known prerequisites / likely blockers

The project currently has no committed runtime credentials or deployment secrets. This is intentional.

A real Modal/FreeLLMAPI proof will require externally configured credentials/secrets that are not stored in GitHub. Absence of those credentials is an operational prerequisite, not permission to embed them in repository code or documentation.

## Cleanup rule

Every governed change must leave one coherent current truth. Superseded direct-provider experiments, obsolete runtime paths, stale docs and conflicting configuration must be deleted rather than left as parallel alternatives unless an active governed requirement explicitly needs them.
