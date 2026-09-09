# Agent

Standalone bounded autonomous-agent execution framework for use by Control and multiple current/future projects.

The repository is intentionally **not** a project database, Control replacement, scheduler, or project-specific extension.

Current target execution model:

```text
caller / Control / project
        |
        | bounded task + task profile
        v
Modal orchestrator
        |
        +--> isolated Modal Sandbox / headless Hermes worker
        +--> isolated Modal Sandbox / headless Hermes worker
        |
        v
protected FreeLLMAPI inference service
        |
        v
approved provider pool

worker results
        |
        v
separate deterministic verifier
        |
        v
RESULT_READY
        |
        v
caller / project authority
```

Core boundary:

> **bounded task + machine-enforced profile -> isolated autonomous execution -> independent verification -> result back to caller authority**

GitHub is the framework source of truth. Modal is runtime. Target projects keep their own business state and irreversible authority.

Canonical current architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)  
Ten-iteration adversarial design rationale: [`docs/DESIGN_REVIEW_10_ITERATIONS.md`](docs/DESIGN_REVIEW_10_ITERATIONS.md)
