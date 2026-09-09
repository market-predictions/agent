# Agent Framework Roadmap

**Repository:** `market-predictions/agent`  
**Architecture:** v0.4 — Hermes + FreeLLMAPI bounded carrier  
**Status:** canonical implementation sequence  
**Date:** 2026-09-10

Hermes is the selected runtime. FreeLLMAPI is the sole inference gateway. There is no Pydantic AI path or direct-provider bypass.

---

## Roadmap principle

```text
smallest working carrier
        ↓
measured evidence
        ↓
next smallest justified capability
```

Control remains frozen during current Agent implementation.

---

# Phase 1A — Working Hermes + FreeLLMAPI carrier

## Status: PROVEN

The core chain is operational on a clean GitHub-hosted runner:

```text
pinned Hermes
  -> named FreeLLMAPI provider
  -> pinned FreeLLMAPI
  -> keyless free model pool
  -> real routed model
  -> Hermes live web tool
  -> strict CANDIDATE
```

Implemented and verified:

- Hermes `0.21.1`, exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- upstream-supported exact source/editable installation;
- top-level Hermes script one-shot (`-z`);
- named Hermes provider `freellmapi`, model `auto`;
- Hermes `web` toolset only;
- strict `PUBLIC_NON_PERSONAL` instruction and JSON candidate contract;
- wall/turn/model-call/concurrency bounds;
- FreeLLMAPI `0.9.8` exact image digest;
- stable unified-key bootstrap through FreeLLMAPI's own DB API;
- keyless Kilo + OVH declarative bootstrap;
- authenticated `/v1/models`;
- direct real `model=auto` inference with `X-Routed-Via`;
- real Hermes -> FreeLLMAPI -> model -> live web-tool execution;
- provider credentials kept outside Hermes;
- full-SHA GitHub Actions and no persisted checkout credential.

The expensive live proof runs once per pull-request candidate and once after merge to `main`.

Phase-1 output is `CANDIDATE`, not `RESULT_READY`.

---

# Phase 1B — Modal cloud deployment

## Status: PROVEN

Implemented and verified:

- `modal_app.py` as the single cloud topology;
- one protected FreeLLMAPI web service, max one active container, scale-to-zero;
- one Hermes Function, max one active container, scale-to-zero;
- exact upstream pins and same carrier code as the proven GitHub runner;
- Modal proxy auth + FreeLLM unified bearer;
- named Secrets `agent-hermes` and `agent-freellmapi`;
- GitHub repository authentication through `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`;
- idempotent first-deploy runtime bootstrap in `scripts/bootstrap_modal_runtime.py`;
- `.github/workflows/deploy-modal.yml` as the only deployment workflow;
- `docs/OPERATIONS.md` as the operator runbook;
- successful `modal deploy modal_app.py`;
- successful remote `modal run modal_app.py::smoke` returning `CANDIDATE`.

The runtime bootstrap generates credentials in-process, never prints them, preserves an already complete Secret pair, and fails closed on partial state. The deployment workflow is explicit-dispatch only; ordinary pushes do not deploy or consume Modal compute.

---

# Phase 1C — Qualification / AGENT-R1-GAP-01 evidence

## Status: NEXT

The first working cloud carrier is not full Mission acceptance.

Required next evidence:

- at least 20 repeated `PUBLIC_NON_PERSONAL` runs;
- structured-output success rate;
- web-tool completion rate;
- supported/unsupported claim rate;
- model calls, failures/retries and wall time;
- actual provider/model route where observable;
- initial approximately 70% human-usefulness gate;
- exact-head validation and required external review.

`max_tool_calls=20` remains a declared target, not an independently enforced counter, until Hermes exposes stable exact tool-call telemetry or a minimal verified wrapper earns its place.

Do not add fan-out to hide weak single-worker quality.

---

# Phase 2 — Trusted evidence verifier

Add one separate trusted verifier that accepts only strict candidate data and independently re-fetches cited evidence.

Security boundary:

- HTTP(S) only;
- reject localhost/private/loopback/link-local/cloud-metadata destinations;
- re-resolve and revalidate redirects;
- byte/time limits;
- never execute worker-provided code/scripts/files.

Only this phase introduces `RESULT_READY`.

---

# Phase 3 — Test whether parallelism adds value

Compare one worker with two independent workers on the same bounded objective. Adopt fan-out only when verified quality/coverage improves enough to justify extra inference/compute. Keep Hermes recursive delegation disabled unless separately justified.

---

# Phase 4 — Persist FreeLLMAPI state only if measured need exists

Only if cold-start loss of quota/cooldown/analytics state materially harms useful capacity or diagnostics, add one Modal Volume with one writer. Do not add Redis, Postgres, horizontal router replicas, or multi-writer SQLite.

---

# Phase 5 — Capability-triggered isolation and profiles

Use Modal Sandbox only for a task class requiring autonomous shell, generated code, broad filesystem access, repository mutation, or untrusted executable artifacts. Add Git-backed task profiles only when at least two materially different capability/data classes exist.

---

# Phase 6 — Caller/project integration

Integrate verified results with bounded callers without duplicating Control/project state. No production write credential belongs in Hermes. Person-linked SolidDesign prospecting and sensitive Scrub data remain outside the generic free lane unless a new explicit data/inference policy is approved.

---

# Phase 7 — Mobile / interactive Hermes

Only after bounded carrier qualification, design a separate authenticated interactive Hermes service. Its session/memory state must not become Control state or project business truth.

---

## Continuous requirements

At every phase:

- GitHub remains code/config/docs truth;
- fresh-read the Execution & Engineering Constitution for consequential work;
- exact-pin correctness-relevant software;
- FreeLLMAPI remains the sole inference boundary;
- provider credentials remain outside Hermes;
- generic free lane remains `PUBLIC_NON_PERSONAL`;
- fail closed instead of silently switching to paid capacity;
- deterministic work stays deterministic;
- remove superseded code/config/docs;
- keep README, architecture, roadmap, operations and observed behavior aligned.
