# Agent Framework — Historical Design Review and Decision Record

**Repository:** `market-predictions/agent`  
**Status:** historical / non-canonical rationale  
**Current architecture:** `docs/ARCHITECTURE.md` v0.4  
**Current roadmap:** `docs/ROADMAP.md`  
**Date:** 2026-09-09

> This file preserves why the design changed. It does **not** define current architecture. If any statement here conflicts with `docs/ARCHITECTURE.md`, the canonical architecture wins.

---

## 1. Original ten-iteration review of v0.2

The original Modal/Hermes/FreeLLMAPI proposal was attacked from first principles.

The durable conclusions that survived are:

1. bounded project execution and persistent/mobile Hermes are separate services;
2. Modal owns framework-level fan-out when fan-out is introduced;
3. when broad executable capability is needed, run the whole Hermes worker inside a Modal Sandbox rather than keeping Hermes elsewhere with only a remote terminal backend;
4. provider keys belong outside Hermes workers;
5. do not add persistent FreeLLMAPI state before measured need;
6. prompt prose is not a security boundary;
7. no framework DB, queue or business scheduler without a concrete need;
8. generation and verification remain separate;
9. mobile Hermes is a later dedicated service;
10. runtime software is pinned and dynamic inference is handled through provenance rather than false reproducibility claims.

---

## 2. External Opus review of v0.2

The external review identified a fundamental sequencing problem: the earlier design over-specified the carrier before testing the uncertain model/tool-loop quality.

Important findings adopted into current architecture:

- evidence-first build sequence;
- `PUBLIC_NON_PERSONAL` first data lane rather than assuming public data is non-personal;
- Modal Function for fixed-safe-tool workers, Sandbox only when executable capabilities require it;
- evidence verifier re-fetches evidence and is SSRF-hardened;
- hard budgets cover model calls and tool calls as well as wall time;
- parallelism must prove quality/diversity value rather than merely throughput;
- task-profile machinery waits until a second capability class exists;
- inference is provenance-accountable rather than claimed deterministic;
- `PARTIAL` requires worker/coverage identity.

The review also recommended Pydantic AI and initially recommended postponing FreeLLMAPI.

Those two recommendations were not retained as current product decisions.

---

## 3. Product-owner decisions after external review

### 3.1 Hermes remains fixed

The product owner explicitly chose Hermes as the runtime and rejected a Pydantic AI bake-off, fallback or parallel runtime.

Reason:

- Hermes is the intended long-term agent environment;
- mobile control of Hermes is a planned later phase;
- a second runtime would create fragmentation without serving the current objective.

Current truth:

```text
Hermes = selected runtime
Pydantic AI = not part of current architecture or roadmap
```

### 3.2 FreeLLMAPI is foundational from Phase 1

A temporary direct-provider path was also rejected.

Reason:

- the actual target system is Hermes -> FreeLLMAPI;
- direct-provider setup would create throwaway code/configuration;
- routing/failover/provider switching are part of the real path and should be measured immediately;
- upstream provider keys should live in the gateway rather than the Hermes worker.

Current truth:

```text
Hermes
  -> protected FreeLLMAPI
  -> configured free-provider pool
```

### 3.3 All configured providers are eligible from the start

The product owner explicitly chose not to begin with a hand-curated one-provider subset.

Phase 1 therefore allows every FreeLLMAPI provider for which valid credentials/configuration are present to participate according to the router's configured behavior.

This does not widen the data policy. The generic provider pool is limited to `PUBLIC_NON_PERSONAL` input. Person-linked, private or sensitive data remains outside that lane.

### 3.4 FreeLLMAPI remains simple despite being foundational

The external review correctly identified that provider keys live in SQLite and that cold starts need a real bootstrap strategy.

Current correction:

- stable `ENCRYPTION_KEY` from Modal Secrets;
- declarative `FREEAPI_CONFIG_JSON` / `FREEAPI_CONFIG_PATH` on every boot;
- max active writer/replica = 1 initially;
- no persistent Volume in the first proof;
- no Redis/Postgres/horizontal router cluster.

Persistence becomes a later evidence-triggered optimization only if lost quota/cooldown/analytics state materially harms operation.

---

## 4. Current v0.4 sequence

```text
Phase 1
one Hermes worker
+ protected FreeLLMAPI
+ all configured providers eligible
+ fixed safe tools
        ↓
Phase 2
trusted evidence verifier
        ↓
Phase 3
two-worker diversity/value experiment
        ↓
Phase 4
FreeLLMAPI persistence only if measured need
        ↓
Phase 5
Sandbox and/or task profiles only on capability triggers
        ↓
Phase 6
Control/project integrations
        ↓
Phase 7
mobile interactive Hermes
```

The current canonical implementation sequence is `docs/ROADMAP.md`.

---

## 5. Current non-goals

Do not add without a concrete trigger:

- Pydantic AI or any second runtime;
- harness bake-off;
- direct-provider bypass around FreeLLMAPI;
- framework database;
- queue/broker;
- generic business scheduler;
- persistent worker memory;
- recursive swarm;
- generic project adapter/plugin system;
- publisher/admin proxy;
- persistent FreeLLMAPI DB/Volume before measured need;
- Redis/Postgres for FreeLLMAPI;
- Sandbox for fixed safe-tool research;
- task-profile machinery while only one capability class exists.

---

## 6. Cleanup rule

Git history is the archive.

Current truth lives in:

- `docs/ARCHITECTURE.md` — canonical target architecture;
- `docs/ROADMAP.md` — canonical implementation sequence;
- `README.md` — concise aligned entry point.

This document is rationale only.

Definition of Done requires current docs and actual implementation behavior to remain aligned, with stale/conflicting current code/config/documentation removed rather than maintained in parallel.
