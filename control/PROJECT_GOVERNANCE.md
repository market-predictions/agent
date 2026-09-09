# Agent Framework — Project Governance

```text
project_id=AGENT_FRAMEWORK
project_repository=market-predictions/agent
source_of_truth=GITHUB
control_protocol=CONTROL_V4
control_management_status=CONTROL_MANAGED
bootstrap_handoff_status=DEFERRED_ON_FROZEN_CONTROL_BASELINE
project_risk_class=AGENT_EXECUTION_INFRASTRUCTURE
production_project_mutation=NOT_AUTHORIZED
paid_inference_fallback=NOT_AUTHORIZED
personal_or_sensitive_generic_free_lane=NOT_AUTHORIZED
principal_manual_relay_target=0
```

## Purpose

This file is the project-local governance contract for `market-predictions/agent` under Control V4.

It does **not** duplicate Control authority and it is **not** Control runtime state. Control authority exists through the current canonical Control V4 runtime authority, Mission Contract, repository-authority record and canonical runtime queue in `market-predictions/control-plane` / `control-runtime-state`.

The project-local purpose is to make the repository self-describing enough that a Control task can be executed without relying on chat memory or narrative handover.

## Mandatory cross-project engineering doctrine

All consequential architecture, engineering, implementation, refactoring, debugging, documentation and roadmap work in this repository must fresh-read and apply the canonical Google Drive document:

**Execution & Engineering Constitution**  
https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit

This document is the mandatory cross-project operating doctrine. It is not a second Control semantic authority source: Control Mission/repository/runtime authority determines **what work is authorized**, while the Constitution governs **how engineering work is approached and executed**. Project-local architecture and implementation may narrow the doctrine for this project but may not silently contradict it.

If the Constitution cannot be read when consequential project work requires it, do not substitute chat memory or a local paraphrase as if it were current canonical doctrine; report the missing dependency and limit work to actions that do not depend on that doctrine.

## Canonical authority

```text
Control architecture:
market-predictions/control-plane:control/CONTROL_AUTONOMY_ARCHITECTURE_V4.md

Control system index:
market-predictions/control-plane:control/SYSTEM_INDEX.md

Canonical Mission:
market-predictions/control-plane:control/missions/AGENT_FRAMEWORK.mission.json

Canonical repository authority:
market-predictions/control-plane:control/repository-authority/market-predictions__agent.json

Mandatory cross-project engineering doctrine:
Google Drive — Execution & Engineering Constitution
https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit

Project-local architecture:
docs/ARCHITECTURE.md

Project-local implementation sequence:
docs/ROADMAP.md

Project-local factual snapshot:
control/CURRENT_STATE.md
```

`AGENT_FRAMEWORK` is an active Control-managed Mission. Current mutable lifecycle/status must be read from Control's canonical V4 runtime sources rather than inferred from this file.

## Authority model

Control governs **which declared Mission gap is eligible and how its BUILD / REVIEW / REPAIR / integration lifecycle proceeds**.

The target repository remains authoritative for:

- commits and exact candidate/base identity;
- branches and pull requests;
- CI/check results;
- review evidence;
- merge state;
- actual implementation facts.

The Mission owns governed intent, success criteria, gap dependencies and per-gap review/integration policy.

The project roadmap explains implementation sequencing but does **not** create Control work by itself.

Project-local `CURRENT_STATE.md` is a bounded implementation-fact snapshot only. It is never global Control runtime/status authority.

## Bootstrap handoff rule and frozen-baseline boundary

The intended minimal handoff is:

1. `AGENT_FRAMEWORK` and its repository-authority record are adopted in canonical Control authority — **DONE**;
2. one small implementation candidate exists for the first eligible gap, `AGENT-R1-GAP-01` — Agent PR #1 on `bootstrap/agent-r1-gap-01` — **DONE**;
3. Control binds that existing candidate and owns convergence through governed REPAIR / REVIEW / PASS — **DEFERRED while the working Control baseline remains frozen**.

Current V4 materializes a new root task with `candidate=null` and `phase=BUILD`. The currently bound Runner explicitly YIELDs candidate-less BUILD and has no automatic existing-PR binding rule. Repository-local metadata cannot populate the private canonical task candidate by itself.

Agent therefore must **not** compensate by creating a second scheduler, semantic worker, polling bridge, synthetic Control event producer, queue/state plane or other mechanism that impersonates the canonical Runner. That would solve onboarding convenience by violating the architecture.

No Control runtime/trust change is requested by this project while the current Control baseline is intentionally stabilizing. Agent PR #1 remains the bounded project-side candidate. A future Control-side handoff capability may be considered only after the baseline stabilization period and only if it remains a concrete cross-project requirement rather than an Agent-specific convenience.

Do not implement generic candidate-less BUILD merely to solve this bootstrap handoff.

## Project product decisions

Current product decisions are:

1. **Hermes is the selected agent runtime.** No Pydantic AI bake-off or fallback is in scope.
2. **FreeLLMAPI is the canonical inference gateway from Phase 1.** There is no temporary direct-provider path.
3. **All correctly configured FreeLLMAPI providers are eligible from the first proof.** The first generic lane is therefore restricted to `PUBLIC_NON_PERSONAL` data.
4. **Modal is runtime; GitHub is current truth.**
5. **One fixed-safe-tool Hermes worker is proven before fan-out.**
6. **Independent evidence verification is separate from generation.**
7. **Modal Sandbox is capability-triggered** when autonomous shell/generated-code/broad executable tooling is actually required.
8. **Mobile/interactive Hermes is a planned later capability**, separated from bounded-worker business authority.

## Hard authority boundaries

Project-local implementation must preserve these boundaries; the canonical Mission may narrow them further:

- no target-project production write credential in a Hermes worker;
- no upstream provider API keys in a Hermes worker; provider credentials belong to the protected FreeLLMAPI service;
- no secrets or client data in GitHub;
- no personal, sensitive, confidential or regulated data through the generic free-provider pool;
- no hidden paid inference or compute fallback;
- no production/customer-environment mutation authority inferred from repository access;
- no framework database, queue or business scheduler unless a later governed requirement explicitly justifies one;
- no duplicate Control lifecycle/state plane;
- no autonomous business acceptance: `RESULT_READY` is not business `DONE`;
- no recursive/hierarchical swarm authority unless a later governed Mission revision explicitly introduces it.

A bounded non-production Modal proof using `PUBLIC_NON_PERSONAL` data is within the intended project scope only after the required credentials are configured outside GitHub and hard zero/near-zero budget limits are active.

## Required read order for consequential project work

Before consequential work on a Control-governed gap, fresh-read the smallest sufficient current evidence in this order:

1. current Control V4 mandatory authority sources from `control/SYSTEM_INDEX.md`;
2. the current Google Drive **Execution & Engineering Constitution**;
3. current `AGENT_FRAMEWORK` Mission Contract;
4. current `market-predictions__agent` repository-authority record;
5. canonical Control runtime queue when lifecycle state is relevant;
6. this `control/PROJECT_GOVERNANCE.md`;
7. `control/CURRENT_STATE.md` for project-local implementation facts only;
8. `docs/ARCHITECTURE.md`;
9. `docs/ROADMAP.md`;
10. only the code, tests, PR, CI, review and external evidence required for the selected gap.

The Constitution read is mandatory; a remembered summary or copied excerpt does not substitute for the current Google Drive source.

Do not route work from chat history, handovers, README prose or roadmap ordering when they conflict with current Mission/repository authority.

## Review and integration

Per-gap `review_policy` and `integration_policy` come only from the current Mission.

- `INTERNAL` means Control's governed critical engineering review is sufficient for that gap.
- `EXTERNAL` requires fresh external review bound to the complete exact candidate/base identity.
- `AUTO_AFTER_PASS` permits governed repository integration only when current Control integration authority actually enables it and every exact candidate/base/CI/review gate is satisfied.
- `HOLD_AFTER_PASS` remains READY after PASS and must not be silently integrated.

Current Control carrier V1 has integration disabled; Mission policy does not override that global restriction.

No review policy creates production deployment, customer-data, paid-provider or business-final-decision authority.

## Documentation hierarchy

Current truth per concern:

```text
Cross-project engineering doctrine -> Google Drive Execution & Engineering Constitution
Control governed intent             -> canonical Mission Contract
Control repository restrictions     -> repository-authority record
Control lifecycle                   -> canonical Control V4 runtime queue
Project architecture                -> docs/ARCHITECTURE.md
Project implementation sequence     -> docs/ROADMAP.md
Project implementation facts        -> live repository + control/CURRENT_STATE.md as bounded summary
Historical design rationale         -> docs/DESIGN_REVIEW_10_ITERATIONS.md
Git history                         -> archive/audit history
```

Do not create a local copy of the Constitution as a competing canonical doctrine, a second Mission mirror or a local runtime queue in this repository.

## Definition of Done

A governed gap is not Done merely because code exists.

Done requires the exact current Mission acceptance to be satisfied by authoritative evidence, the required review policy to pass, integration/convergence requirements to be satisfied, and the repository to be coherent afterward.

At project level, cleanup is part of Done:

- remove superseded code/configuration;
- remove stale or conflicting current documentation;
- keep README, architecture, roadmap and actual behavior aligned;
- preserve the live reference/read obligation to the canonical Execution & Engineering Constitution;
- do not preserve obsolete execution state as a second current state plane;
- do not knowingly leave a material inconsistency behind.
