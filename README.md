# Agent

Standalone bounded autonomous-agent execution framework for Control and multiple current/future projects.

The repository is intentionally **not** a project database, Control replacement, scheduler, queue, or project-specific extension.

## Current target model — v0.3 Evidence-First Hermes

Hermes is the selected agent runtime. There is no Pydantic AI bake-off or fallback in this phase.

The first proof deliberately starts smaller than the eventual swarm architecture:

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
one direct approved free provider
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

Only measured limitations earn the next layers:

```text
single-worker proof
    -> evidence verifier
    -> two-worker diversity experiment
    -> FreeLLMAPI if quota/failover/diversity need is measured
    -> Modal Sandbox when shell/generated-code capability is required
    -> task profiles when a second capability class exists
    -> Control/project integration
    -> mobile interactive Hermes
```

Core principles:

- **Hermes is the chosen runtime.**
- **GitHub is current truth; Modal is runtime.**
- **Evidence before infrastructure.**
- **No production credentials in workers.**
- **Public does not automatically mean non-personal.**
- **Model calls, tool calls, retries, wall time and concurrency are bounded.**
- **Independent verification is separate from generation.**
- **`RESULT_READY` is not business `DONE`.**
- **No DB, queue, generic scheduler, publisher or recursive swarm before measured need.**

Canonical architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)  
Canonical implementation sequence: [`docs/ROADMAP.md`](docs/ROADMAP.md)  
Historical/adversarial design rationale: [`docs/DESIGN_REVIEW_10_ITERATIONS.md`](docs/DESIGN_REVIEW_10_ITERATIONS.md)
