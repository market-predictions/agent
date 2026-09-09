# Agent

Standalone bounded autonomous-agent execution framework for Control and multiple current/future projects.

The repository is intentionally **not** a project database, Control replacement, scheduler, queue, or project-specific extension.

## Mandatory engineering doctrine

Consequential project work must fresh-read and apply the canonical Google Drive **Execution & Engineering Constitution**:

https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit

The Google Drive document remains canonical; do not substitute a remembered summary or local copy. It governs engineering method while Control Mission/repository/runtime authority governs what work is authorized. See [`control/PROJECT_GOVERNANCE.md`](control/PROJECT_GOVERNANCE.md) for the mandatory read order.

## Current implementation — v0.4 Hermes + FreeLLMAPI on Modal

PR #1 contains the first deployable bounded carrier:

```text
bounded PUBLIC_NON_PERSONAL task
        |
        v
Modal Function
  pinned Hermes v0.21.1 / exact commit
  one one-shot worker
  Hermes web toolset only
  hard wall/model-turn/concurrency bounds
        |
        v
protected FreeLLMAPI Modal service
  pinned v0.9.8 image digest
  stable unified gateway key
  default zero-key Kilo + OVH bootstrap pool
  optional FREEAPI_CONFIG_JSON adds/replaces configured providers
        |
        v
free-provider model inference
        |
        v
strict structured CANDIDATE
```

`CANDIDATE` is deliberately **not** `RESULT_READY`. Phase 2 adds a separate trusted evidence verifier; only verified output may become `RESULT_READY`.

### Runtime pins

- Modal Python SDK: `1.5.5`
- Hermes: release `0.21.1`, tag `v2026.9.7`, commit `2237be355906fbe6065ce1815711eee52b2d646e`
- FreeLLMAPI: `0.9.8`, exact GHCR image digest in [`runtime_versions.py`](runtime_versions.py)

### Current runtime boundaries

- Hermes is the only agent runtime; no Pydantic AI path exists.
- FreeLLMAPI is the only inference gateway; no direct-provider bypass exists.
- Upstream provider keys never enter the Hermes Function.
- The first lane is `PUBLIC_NON_PERSONAL` only.
- FreeLLMAPI is protected by both its unified bearer and Modal proxy authentication.
- FreeLLMAPI and Hermes scale to zero and each allow at most one active container in Phase 1.
- No framework DB, queue, publisher, persistent Hermes memory, fan-out, Sandbox, or project-write capability exists.
- Control remains a frozen governance baseline during Agent implementation; Agent creates no second Control actor/state/transport path.

## Run and deploy

Deterministic local verification:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python agent_carrier.py \
  --task-id dry-run \
  --objective "Research a public technical standard." \
  --freellmapi-base-url https://example.invalid/v1
```

Modal deployment and secret setup are documented in [`docs/OPERATIONS.md`](docs/OPERATIONS.md). The deployment workflow is `.github/workflows/deploy-modal.yml`.

## Current verification

CI checks:

- deterministic unit/boundary tests;
- Python compilation;
- Modal app import/topology;
- exact Hermes install from the pinned commit;
- exact FreeLLMAPI image pull;
- FreeLLMAPI cold-start bootstrap and unified-key authentication;
- live free-model call through the keyless FreeLLMAPI pool;
- a real local Hermes -> FreeLLMAPI -> model -> Hermes web-tool candidate run.

Exact live CI state must be read from PR #1 rather than inferred from this README.

## Control V4 governance

`AGENT_FRAMEWORK` is canonically Control-managed. Control remains frozen while this Agent carrier is implemented project-locally.

- Project governance: [`control/PROJECT_GOVERNANCE.md`](control/PROJECT_GOVERNANCE.md)
- Bounded project fact snapshot: [`control/CURRENT_STATE.md`](control/CURRENT_STATE.md)
- Canonical Control Mission: `market-predictions/control-plane:control/missions/AGENT_FRAMEWORK.mission.json`
- Canonical repository authority: `market-predictions/control-plane:control/repository-authority/market-predictions__agent.json`

The existing Control candidate-binding limitation is not an Agent implementation blocker and is not worked around inside this repository.

Canonical architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)  
Canonical implementation sequence: [`docs/ROADMAP.md`](docs/ROADMAP.md)  
Operations: [`docs/OPERATIONS.md`](docs/OPERATIONS.md)  
Implementation record: [`docs/IMPLEMENTATION_LOG.md`](docs/IMPLEMENTATION_LOG.md)  
Historical/adversarial design rationale: [`docs/DESIGN_REVIEW_10_ITERATIONS.md`](docs/DESIGN_REVIEW_10_ITERATIONS.md)
