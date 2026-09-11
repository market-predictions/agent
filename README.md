# Agent

Standalone bounded autonomous-agent execution framework for Control and multiple current/future projects, with a separate human-facing Hermes Web Dashboard.

The repository is intentionally **not** a project database, Control replacement, scheduler, queue, or project-specific extension.

## Mandatory engineering doctrine

Consequential project work must fresh-read and apply the canonical Google Drive **Execution & Engineering Constitution**:

https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit

The Drive document remains canonical. See [`control/PROJECT_GOVERNANCE.md`](control/PROJECT_GOVERNANCE.md) for the required governance read order.

## Current implementation

### Qualified bounded Phase-1 carrier

The bounded core is proven end-to-end both on a clean GitHub-hosted runner and as a live Modal deployment:

```text
PUBLIC_NON_PERSONAL task
        |
        v
Hermes 0.21.1 / exact commit
script one-shot, web toolset only
        |
        v
named provider: freellmapi / model=auto
        |
        v
FreeLLMAPI 0.9.8 / exact image digest
stable unified bearer
keyless Kilo + OVH bootstrap
        |
        v
real free routed model
        |
        v
Hermes live web lookup
        |
        v
strict structured CANDIDATE
```

A fixed 20-run Phase-1 qualification produced 18 strict source-bearing candidates. Manual source readback supported all 18 candidate claims, giving a **90% human-usable run rate** against the Mission's initial approximately 70% gate. Both rejected runs remained fail-closed on the strict output contract. See [`qualification/PHASE1_QUALIFICATION_REVIEW.md`](qualification/PHASE1_QUALIFICATION_REVIEW.md).

`CANDIDATE` is deliberately **not** `RESULT_READY`; independent evidence verification is a later governed capability. `AGENT-R1-GAP-01` still requires its fresh external exact-candidate review before acceptance.

### Isolated interactive Hermes dashboard

A separate native Hermes Web Dashboard/TUI is now deployed on Modal at:

`https://market-predictions--agent-carrier-dashboard.modal.run`

It reuses the same pinned Hermes and FreeLLMAPI-only inference boundary but is not the bounded worker and has no Control/project business authority. It has one persistent Modal Volume for interactive profiles/sessions/state, authenticates through native Nous Portal OAuth, and is hard-pinned with Hermes' own `HERMES_TUI_TOOLSETS=web` operator override. Terminal, file mutation, browser automation, code execution and delegation are therefore outside the interactive model tool surface.

A real authenticated browser session has completed a live Hermes web search and response while remaining connected. The Modal ingress WebSocket protocol issue was isolated to `permessage-deflate`; the dashboard image applies one narrow fail-closed compatibility patch to the exact pinned Hermes source that sets Uvicorn `ws_per_message_deflate=False`. The bounded worker remains unpatched exact upstream Hermes.

Persistence across an intentional dashboard restart/scale-down is still a separate verification item; it is not claimed as proven here.

### Exact runtime pins

- Modal SDK: `1.5.5`
- Hermes: `0.21.1`, tag `v2026.9.7`, commit `2237be355906fbe6065ce1815711eee52b2d646e`
- FreeLLMAPI: `0.9.8`, exact GHCR image digest in [`runtime_versions.py`](runtime_versions.py)

### Boundaries

- Hermes is the only agent runtime.
- FreeLLMAPI is the only inference gateway.
- Upstream provider keys never enter Hermes.
- Generic bounded inference is `PUBLIC_NON_PERSONAL` only.
- The bounded worker gets only `web`; no shell, project writes, browser automation, delegation, messaging, gateway/Cron/Kanban, or persistent Hermes memory.
- The interactive dashboard is separately hard-pinned to the `web` toolset and owns no Control/project write credentials.
- Hard model-call, tool-call, retry, wall-time and concurrency limits fail closed in the bounded worker.
- No framework DB, queue, publisher, fan-out, Sandbox, or paid fallback exists in the Phase-1 carrier.
- Control remains frozen; Agent introduces no second Control actor/state/transport path.

## Cloud deployment

`modal_app.py` is the single cloud topology and currently defines three isolated runtime surfaces:

1. protected FreeLLMAPI web service;
2. bounded Hermes task Function;
3. authenticated native Hermes interactive dashboard.

Each is capped at one active container. The dashboard permits enough request-level concurrency for Hermes' normal HTTP/WebSocket multiplexing while Hermes itself remains limited to one concurrent interactive session.

GitHub Actions authenticates with repository secrets `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`. The canonical workflow [`deploy-modal.yml`](.github/workflows/deploy-modal.yml) is the only deployment route and is explicit-dispatch only in steady state. It idempotently bootstraps the required Modal runtime Secrets through [`scripts/bootstrap_modal_runtime.py`](scripts/bootstrap_modal_runtime.py), deploys the pinned runtime, verifies the dashboard auth boundary and can run the bounded worker smoke or qualification harness.

## Verification

`.github/workflows/ci.yml` runs deterministic compilation/tests/config/topology checks plus exact Hermes/FreeLLMAPI integration with a real free model and real Hermes web-tool execution.

The live bounded-provider proof runs once per pull-request candidate and once after merge to `main`, avoiding duplicate free-provider quota consumption. Modal deployment remains a separate explicit promotion action rather than an automatic source-push side effect.

## Current docs

- Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md)
- Operations: [`docs/OPERATIONS.md`](docs/OPERATIONS.md)
- Implementation record: [`docs/IMPLEMENTATION_LOG.md`](docs/IMPLEMENTATION_LOG.md)
- Qualification review: [`qualification/PHASE1_QUALIFICATION_REVIEW.md`](qualification/PHASE1_QUALIFICATION_REVIEW.md)
- Project-local facts: [`control/CURRENT_STATE.md`](control/CURRENT_STATE.md)
- Historical/adversarial design rationale: [`docs/DESIGN_REVIEW_10_ITERATIONS.md`](docs/DESIGN_REVIEW_10_ITERATIONS.md)

## Control V4 governance

`AGENT_FRAMEWORK` remains canonically Control-managed. The working Control runtime is treated as a frozen baseline during this implementation; the existing candidate-binding limitation is neither changed nor bypassed inside Agent.