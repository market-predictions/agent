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
- hard wall/turn/model-call/tool-call/retry/concurrency bounds;
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

## Status: QUALIFIED — EXTERNAL REVIEW REMAINS

The fixed 20-run `PUBLIC_NON_PERSONAL` qualification completed against runtime candidate `a74871525458e47f69fa2c01ba6d0bdfc4a01202`.

Measured evidence:

- attempted runs: **20**;
- strict structured candidates: **18/20 = 90%**;
- human-usable runs after source readback: **18/20 = 90%**;
- completed web-tool loops: **20/20 = 100%**;
- manually supported candidate claims: **18/18 = 100%**;
- model calls: **66**;
- tool calls: **47**;
- retries: **0**;
- provider errors: **0**;
- aggregate carrier wall time: **580.178 seconds**;
- multiple free route/model identities observed.

The two rejected runs are preserved as failures: one invalid JSON response and one result that violated the exact `summary` + `claims` schema after consuming the bounded model-call budget. The carrier remained fail-closed; the parser was not weakened to improve the score.

The initial approximately 70% human-usefulness gate is therefore satisfied at **90%**. See [`qualification/PHASE1_QUALIFICATION_REVIEW.md`](../qualification/PHASE1_QUALIFICATION_REVIEW.md) for the evidence identity, per-run review and source-support assessment.

The fixed qualification harness remains reusable through the single canonical `.github/workflows/deploy-modal.yml` workflow via its explicit `run_qualification` input. The temporary second deployment workflow and one-shot trigger artifact were removed after the first evidence run.

`max_tool_calls=20` is enforced by the native Hermes policy plugin at `pre_tool_call`; it is no longer merely a declared target.

Remaining GAP-01 gate: final exact-head validation plus the required fresh external exact-candidate review.

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
