# Agent

Standalone bounded autonomous-agent execution framework for Control and multiple current/future projects.

The repository is intentionally **not** a project database, Control replacement, scheduler, queue, or project-specific extension.

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

This project is being onboarded for Control V4 management. Project-local governance is explicit and does not duplicate Control runtime state.

- Project governance bootstrap: [`control/PROJECT_GOVERNANCE.md`](control/PROJECT_GOVERNANCE.md)
- Bounded project fact snapshot: [`control/CURRENT_STATE.md`](control/CURRENT_STATE.md)
- Canonical Control Mission path after governed adoption: `market-predictions/control-plane:control/missions/AGENT_FRAMEWORK.mission.json`
- Canonical repository-authority path after governed adoption: `market-predictions/control-plane:control/repository-authority/market-predictions__agent.json`

Until those Control authority artifacts are adopted through the governed Control V4 authority-change path, the project status is **PENDING_AUTHORITY_ADOPTION**. The roadmap does not create Control work by itself; only the adopted Mission can materialize governed gaps.

Canonical architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)  
Canonical implementation sequence: [`docs/ROADMAP.md`](docs/ROADMAP.md)  
Historical/adversarial design rationale: [`docs/DESIGN_REVIEW_10_ITERATIONS.md`](docs/DESIGN_REVIEW_10_ITERATIONS.md)
