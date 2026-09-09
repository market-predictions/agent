# Agent

Standalone bounded autonomous-agent execution framework for Control and multiple current/future projects.

The repository is intentionally **not** a project database, Control replacement, scheduler, queue, or project-specific extension.

## Mandatory engineering doctrine

Consequential project work must fresh-read and apply the canonical Google Drive **Execution & Engineering Constitution**:

https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit

The Google Drive document remains canonical; do not substitute a remembered summary or local copy. It governs engineering method while Control Mission/repository/runtime authority governs what work is authorized. See [`control/PROJECT_GOVERNANCE.md`](control/PROJECT_GOVERNANCE.md) for the mandatory read order.

## Current target model — v0.4 Evidence-First Hermes + FreeLLMAPI

Hermes is the selected agent runtime and FreeLLMAPI is part of the inference path from the first proof. There is no Pydantic AI bake-off or temporary direct-provider integration.

```text
human / caller
     |
     | bounded PUBLIC_NON_PERSONAL research task
     v
Modal Function
     |
     | pinned Hermes one-shot
     | fixed safe tools
     | hard model/tool/time budgets
     v
protected FreeLLMAPI service
     |
     | all configured providers eligible
     | routing/failover observed
     v
free provider pool
     |
     v
structured candidate result
     |
     v
separate trusted evidence verifier
     |
     v
RESULT_READY
     |
     v
caller / project authority
```

Phase 1 deliberately keeps everything else small: one Hermes worker, no fan-out, no Sandbox, no project writes, no framework DB/queue, no persistent Hermes memory and no task-profile framework yet.

Core principles:

- **Hermes is the chosen runtime.**
- **FreeLLMAPI is the canonical inference gateway from Phase 1.**
- **All configured FreeLLMAPI providers are eligible; no hand-maintained Phase-1 provider subset.**
- **GitHub is current truth; Modal is runtime.**
- **Evidence before further infrastructure.**
- **No production credentials in workers.** Provider credentials live in the FreeLLMAPI service.
- **Public does not automatically mean non-personal.**
- **Model calls, tool calls, retries, wall time and concurrency are bounded.**
- **Provider/model routing and route switches are recorded where observable.**
- **Independent verification is separate from generation.**
- **`RESULT_READY` is not business `DONE`.**
- **No DB, queue, generic scheduler, publisher or recursive swarm before measured need.**

## Control V4 governance

This project is **Control-managed** under the canonical Control V4 Mission and repository-authority committed on `market-predictions/control-plane@main`.

- Project governance: [`control/PROJECT_GOVERNANCE.md`](control/PROJECT_GOVERNANCE.md)
- Bounded project fact snapshot: [`control/CURRENT_STATE.md`](control/CURRENT_STATE.md)
- Canonical Control Mission: `market-predictions/control-plane:control/missions/AGENT_FRAMEWORK.mission.json`
- Canonical repository authority: `market-predictions/control-plane:control/repository-authority/market-predictions__agent.json`
- First bootstrap implementation candidate: Agent PR #1 (`bootstrap/agent-r1-gap-01`)

Only the adopted Mission may materialize governed gaps. The roadmap explains implementation sequence but does not create Control work by itself.

**Current handoff blocker:** current Control V4 materializes a new root with no candidate and its bound Runner always YIELDs candidate-less BUILD. It does not automatically bind an already-open bootstrap PR. Therefore Agent is onboarded and PR #1 exists, but autonomous REPAIR/REVIEW takeover cannot start until a governed existing-candidate binding is available. Do not solve this by silently adding candidate-less BUILD.

Canonical architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)  
Canonical implementation sequence: [`docs/ROADMAP.md`](docs/ROADMAP.md)  
Historical/adversarial design rationale: [`docs/DESIGN_REVIEW_10_ITERATIONS.md`](docs/DESIGN_REVIEW_10_ITERATIONS.md)
