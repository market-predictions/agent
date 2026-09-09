# Agent Framework Roadmap

**Repository:** `market-predictions/agent`  
**Architecture:** v0.4 — Hermes + FreeLLMAPI on Modal  
**Status:** canonical implementation sequence  
**Date:** 2026-09-09

Hermes is the selected runtime. FreeLLMAPI is the canonical inference gateway from the first operational carrier. There is no Pydantic AI path or temporary direct-provider integration.

---

## Roadmap principle

Build only the next capability that current evidence requires.

```text
working smallest carrier
        ↓
measured evidence
        ↓
next smallest justified capability
```

Control remains frozen during current Agent implementation.

---

# Phase 1 — First operational Hermes + FreeLLMAPI carrier

## Status

**IMPLEMENTED AS DEPLOYABLE CANDIDATE; live Modal deployment/smoke evidence pending.**

## Implemented

### Hermes

- exact Hermes `0.21.1` / exact Git commit;
- one headless one-shot worker;
- Modal Function, one active container maximum, scale-to-zero;
- Hermes `web` toolset only (`web_search` / `web_extract` and upstream keyless fallbacks);
- no shell, browser automation, project writes, delegation, messaging, persistent memory, gateway or Cron;
- strict task instruction and strict JSON candidate output;
- wall-time / turns / model-call / concurrency bounds.

### FreeLLMAPI

- exact FreeLLMAPI `0.9.8` image digest;
- one protected Modal web service;
- Modal proxy authentication + unified FreeLLMAPI bearer;
- deterministic stable unified-key bootstrap through FreeLLMAPI's exported DB API;
- default zero-provider-key declarative pool: keyless Kilo + keyless OVH;
- optional `FREEAPI_CONFIG_JSON` in Modal Secret for the full desired provider set;
- upstream provider credentials stay outside Hermes;
- one active service container maximum, scale-to-zero;
- no persistent Volume yet.

### Verification

CI is required to prove:

- deterministic tests/compilation;
- exact Hermes installation;
- exact FreeLLMAPI image startup;
- FreeLLM unified-key authentication;
- real `model=auto` free-model inference with route header;
- real local Hermes -> FreeLLMAPI -> model -> Hermes web-tool candidate execution.

### Deployment

- `modal_app.py` is the single Modal topology;
- `.github/workflows/deploy-modal.yml` is the GitHub deployment route;
- `docs/OPERATIONS.md` is the operator runbook.

## Remaining before calling the carrier operational

1. configure the two named Modal Secrets and Modal account deployment token outside Git;
2. deploy `modal_app.py` to the user's Modal workspace;
3. run `modal run modal_app.py::smoke` successfully;
4. read back the deployed behavior and align docs if reality differs.

## Remaining before full `AGENT-R1-GAP-01` acceptance

A first operational carrier is not the whole Mission gap. After live deployment:

- resolve exact `max_tool_calls` enforcement if still required and not exposed by stable Hermes usage metadata;
- run at least 20 measured `PUBLIC_NON_PERSONAL` qualification runs;
- measure structured success, tool-loop success, supported claims, failures, calls/retries/wall time and route provenance;
- meet the initial approximately 70% human-usefulness gate or simplify/tune and repeat;
- exact-head validation;
- fresh required external review;
- cleanup and documentation alignment.

Do not add fan-out to mask weak single-worker quality.

---

# Phase 2 — Trusted evidence verifier

Build one separate trusted Modal Function that accepts only strict structured candidate data and independently re-fetches evidence.

Security requirements:

- HTTP(S) only;
- reject localhost/private/loopback/link-local/cloud-metadata destinations;
- re-resolve/revalidate redirects;
- byte/time limits;
- no worker-provided code/scripts/files executed.

Only after this verifier passes does `RESULT_READY` exist. Phase-1 success remains `CANDIDATE`.

---

# Phase 3 — Prove whether parallelism adds value

Compare one Hermes worker with two independent Hermes workers on the same bounded objective.

Measure verified quality/coverage uplift versus extra compute/inference. Modal fan-out is adopted only if it materially improves useful output. Hermes recursive delegation remains disabled unless separately justified.

---

# Phase 4 — Persist FreeLLMAPI state only if measured need exists

Trigger only if cold-start loss of quota/cooldown/analytics state materially harms useful capacity or diagnostics.

Candidate change: one Modal Volume, one FreeLLMAPI writer.

Do not add Redis, Postgres, horizontal router replicas, or multi-writer SQLite.

---

# Phase 5 — Capability-triggered isolation and profiles

Use Modal Sandbox only when a task class truly requires autonomous shell, generated code, broad filesystem access, repository mutation, or untrusted executable artifacts.

Introduce Git-backed task profiles only when at least two materially different capability/data classes exist. Until then least privilege stays hardcoded in the one worker.

---

# Phase 6 — Caller/project integration

Integrate the proven carrier result-only with a bounded real caller.

- no second Control state/queue/scheduler;
- no target-project business-state duplication;
- no production write credential in Hermes;
- `RESULT_READY` remains separate from caller/business `DONE`.

SolidDesign person-linked prospect data is not eligible for the generic free lane without a new data/inference policy. Scrub initially uses synthetic/public non-sensitive data only.

---

# Phase 7 — Mobile / interactive Hermes

After the bounded carrier is proven, build a separate authenticated interactive Hermes service reachable from a phone/mobile client.

Target:

```text
phone/mobile client
  -> authenticated cloud endpoint
  -> dedicated interactive Hermes
  -> protected FreeLLMAPI
  -> configured provider pool
```

Design session/memory persistence, single-user concurrency, cold starts, authentication and approval UX separately. Interactive state must not become Control state, framework task state or target-project business truth.

---

# Continuous requirements

At every phase:

- GitHub is code/config/docs truth; Modal is runtime;
- fresh-read the Execution & Engineering Constitution for consequential work;
- pin correctness-relevant software;
- preserve FreeLLMAPI as the sole inference boundary;
- keep provider credentials outside Hermes;
- generic free lane stays `PUBLIC_NON_PERSONAL`;
- bound model calls/turns, wall time, retries and concurrency;
- fail closed instead of silently using paid capacity;
- deterministic work remains deterministic;
- delete superseded code/config/docs;
- keep README, architecture, roadmap, operations and actual behavior aligned.

---

# Definition of Done

A phase is Done only when its actual outcome works, relevant failure/security boundaries are exercised, evidence exists, obsolete implementation is removed, and all current documentation agrees with reality.
