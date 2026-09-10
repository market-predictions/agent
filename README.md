# Agent

Standalone bounded autonomous-agent execution framework for Control and multiple current/future projects.

The repository is intentionally **not** a project database, Control replacement, scheduler, queue, or project-specific extension.

## Mandatory engineering doctrine

Consequential project work must fresh-read and apply the canonical Google Drive **Execution & Engineering Constitution**:

https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit

The Drive document remains canonical. See [`control/PROJECT_GOVERNANCE.md`](control/PROJECT_GOVERNANCE.md) for the required governance read order.

## Current implementation — qualified Phase-1 carrier

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

The GitHub integration proof performs both a direct real FreeLLMAPI `model=auto` call with `X-Routed-Via` and the actual Hermes -> FreeLLMAPI -> model -> web chain. The Modal promotion additionally deploys the same pinned carrier and requires a remote smoke to return `CANDIDATE`.

A fixed 20-run Phase-1 qualification produced 18 strict source-bearing candidates. Manual source readback supported all 18 candidate claims, giving a **90% human-usable run rate** against the Mission's initial approximately 70% gate. Both rejected runs remained fail-closed on the strict output contract. See [`qualification/PHASE1_QUALIFICATION_REVIEW.md`](qualification/PHASE1_QUALIFICATION_REVIEW.md).

`CANDIDATE` is deliberately **not** `RESULT_READY`; independent evidence verification is a later governed capability. `AGENT-R1-GAP-01` still requires its fresh external exact-candidate review before acceptance.

### Exact runtime pins

- Modal SDK: `1.5.5`
- Hermes: `0.21.1`, tag `v2026.9.7`, commit `2237be355906fbe6065ce1815711eee52b2d646e`
- FreeLLMAPI: `0.9.8`, exact GHCR image digest in [`runtime_versions.py`](runtime_versions.py)

### Boundaries

- Hermes is the only agent runtime.
- FreeLLMAPI is the only inference gateway.
- Upstream provider keys never enter Hermes.
- Generic inference is `PUBLIC_NON_PERSONAL` only.
- Hermes gets only the `web` toolset; no shell, project writes, browser automation, delegation, messaging, gateway/Cron/Kanban, or persistent memory in the bounded worker.
- Hard model-call, tool-call, retry, wall-time and concurrency limits fail closed.
- No framework DB, queue, publisher, fan-out, Sandbox, or paid fallback exists in the Phase-1 carrier.
- Control remains frozen; Agent introduces no second Control actor/state/transport path.

## Cloud deployment

`modal_app.py` is the proven cloud topology: one bounded Hermes Function and one protected FreeLLMAPI web service, both scale-to-zero and capped at one active container in Phase 1.

GitHub Actions authenticates with repository secrets `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`. The canonical workflow [`deploy-modal.yml`](.github/workflows/deploy-modal.yml) is the only deployment route and is explicit-dispatch only. On first promotion it idempotently creates the two named Modal runtime Secrets plus one Modal proxy token through [`scripts/bootstrap_modal_runtime.py`](scripts/bootstrap_modal_runtime.py); later promotions preserve them.

The same workflow can optionally run the reusable fixed 20-task qualification after deployment. The temporary qualification-specific deployment workflow used for the first evidence run was removed, preserving one deployment path.

A live deployment and remote Hermes -> FreeLLMAPI smoke have succeeded. Exact operating and recovery semantics are in [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

## Verification

`.github/workflows/ci.yml` runs:

- deterministic compilation/tests/config/topology checks;
- exact Hermes source installation;
- exact FreeLLMAPI image pull/start/authentication;
- real free routed model inference;
- real Hermes web-tool candidate execution.

The live provider proof runs once per pull-request candidate and once after merge to `main`, avoiding duplicate free-provider quota consumption. Modal deployment remains a separate explicit promotion action rather than an automatic push side effect.

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
