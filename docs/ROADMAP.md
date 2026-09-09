# Agent Framework Roadmap

**Repository:** `market-predictions/agent`  
**Architecture:** v0.4 — Evidence-First Hermes + FreeLLMAPI  
**Status:** canonical implementation sequence  
**Date:** 2026-09-09

Hermes is the selected runtime. FreeLLMAPI is the canonical inference gateway from Phase 1. There is no Pydantic AI bake-off, fallback runtime or temporary direct-provider integration.

---

## Roadmap principle

Build the real target path early, but keep every other dimension as small as possible.

```text
real Hermes -> FreeLLMAPI path
        +
smallest bounded task
        ↓
measured evidence
        ↓
next smallest justified capability
```

The pilot budget is zero/near-zero. Paid inference is not a hidden fallback.

---

# Phase 1 — Prove Hermes + FreeLLMAPI

## Objective

Prove the actual high-risk hypothesis:

> Can Hermes complete a short multi-step research task reliably enough when its inference is routed through the real FreeLLMAPI multi-provider free pool?

## Build

### Hermes worker

- one Modal Function;
- pinned Hermes one-shot/headless execution;
- fixed safe tools only:
  - `search`;
  - `web_fetch`;
- one bounded `PUBLIC_NON_PERSONAL` background-research task;
- simple structured result;
- hard model/tool/retry/wall-time counters.

### FreeLLMAPI

- one protected FreeLLMAPI Modal service;
- pinned FreeLLMAPI build/image;
- fixed `ENCRYPTION_KEY` in Modal Secrets;
- provider credentials/config in Modal Secrets;
- declarative `FREEAPI_CONFIG_JSON` or `FREEAPI_CONFIG_PATH` applied on every cold start;
- **all providers for which valid configuration/credentials are present are eligible**;
- no hand-maintained Phase-1 provider subset;
- max active FreeLLMAPI replica/writer: 1;
- provider/model/route provenance captured where exposed.

### Security boundary

Hermes receives only FreeLLMAPI endpoint/client auth. Upstream provider credentials remain in the FreeLLMAPI service.

## Do not build

- direct provider integration;
- persistent FreeLLMAPI Volume;
- Sandbox;
- worker fan-out;
- task-profile resolver;
- framework DB/queue;
- mobile service;
- project publisher/integration.

## Test

Run the same task 20 times through:

```text
Hermes -> FreeLLMAPI -> configured provider pool
```

Measure:

- structured-result success rate;
- tool-loop completion rate;
- evidence-supported claim rate;
- hallucination/unsupported claim rate;
- model calls/run;
- tool calls/run;
- retries/run;
- FreeLLMAPI route/fallback switches;
- actual provider/model where observable;
- provider 429/5xx failures;
- wall time;
- human usefulness against manually checked baseline.

## Gate

Proceed only if:

- approximately >=70% of runs are human-usable as an initial target;
- failures/routing degradation are explicit;
- resource/request budgets hold;
- no provider key reaches Hermes;
- no disallowed data enters the generic free pool.

If not green:

1. simplify the task;
2. improve Hermes instruction/tool design;
3. tune the FreeLLMAPI routing/configuration;
4. verify protocol/tool-call compatibility;
5. repeat measurement.

Do not add fan-out merely to compensate for weak single-worker quality.

---

# Phase 2 — Trusted evidence verifier

## Objective

Make worker claims independently checkable.

Build one separate trusted Modal Function that:

- accepts strict structured data only;
- validates required fields;
- validates HTTP(S) URL schemes;
- resolves hosts and rejects loopback/private/link-local/metadata ranges;
- revalidates redirects;
- fetches evidence under strict time/byte limits;
- normalizes text;
- verifies evidence excerpt/support deterministically where possible.

## Security gate

Test at minimum:

- localhost;
- `127.0.0.1` / `::1`;
- RFC1918/private ranges;
- link-local/cloud metadata ranges;
- redirect to private range;
- DNS/re-resolution cases;
- oversized response;
- timeout;
- malformed structured input.

The verifier never executes worker-provided code, scripts, commands or arbitrary files.

`RESULT_READY` is introduced only after this verifier passes.

---

# Phase 3 — Prove whether parallelism adds value

Run two independent Hermes workers on the same objective through FreeLLMAPI.

Purpose: quality/diversity, not just splitting a list.

Measure:

- agreement;
- unique verified findings;
- evidence coverage;
- false positives;
- provider/model diversity actually obtained;
- human usefulness;
- model/tool call increase;
- compute increase;
- useful output per unit of compute/inference.

Only standardize fan-out if the second worker materially improves accepted output.

If adopted, Modal owns framework fan-out. Hermes internal delegation remains disabled until hierarchical reasoning itself is independently justified.

---

# Phase 4 — Improve FreeLLMAPI persistence only if measured

FreeLLMAPI is already part of the architecture. This phase is only about durable router state.

## Trigger

At least one must be material:

- lost quota/cooldown history after cold starts wastes useful free capacity;
- loss of router analytics prevents useful diagnostics;
- cold-start reconfiguration creates measurable operational pain.

## Candidate change

Add exactly one Modal Volume for FreeLLMAPI SQLite state while keeping one active writer/replica.

Do not add:

- Redis;
- Postgres;
- horizontal router cluster;
- multi-writer SQLite.

Keep persistence only if its measured value exceeds the additional lifecycle complexity.

---

# Phase 5 — Capability-specific isolation and profiles

## 5A — Sandbox trigger

Move a task class from Modal Function to Modal Sandbox only when Hermes must perform:

- generated code execution;
- autonomous shell;
- broad filesystem operations;
- repository mutation;
- untrusted executable artifacts.

When Sandbox is required, run the whole Hermes process inside it.

## 5B — Task-profile trigger

Introduce Git-backed task profiles only when at least two materially different capability/data classes exist, for example:

```text
public non-personal research
vs.
repository code work
```

Until then least privilege is hardcoded in the one worker configuration.

---

# Phase 6 — Caller/project integration

Only after the carrier is measured and verified.

## Control

```text
Control
  -> bounded task
  -> Agent carrier
  -> RESULT_READY
  -> Control acceptance/successor
```

No second Control state machine, queue or scheduler.

## SolidDesign

Person-linked prospect data is not sent through the generic free pool by default. First integration requires an explicit data/inference policy and starts result-only with no production DB writes.

## Scrub

Initial integrations use synthetic/public non-sensitive data. Unredacted sensitive care/legal data remains outside the generic free pool.

## Publisher

Add one narrow project-specific publisher only after repeated handoff proves value. It remains separate from Hermes and accepts only independently verified results.

---

# Phase 7 — Mobile / interactive Hermes

## Product intent

After the bounded worker carrier is proven, make a dedicated Hermes instance controllable from a phone/mobile client.

FreeLLMAPI remains the shared inference boundary.

```text
phone / mobile client
        |
        v
authenticated Modal endpoint
        |
        v
dedicated interactive Hermes service
        |
        +--> persistent session/memory state
        |
        v
protected FreeLLMAPI
        |
        v
configured provider pool
```

Design separately:

- authentication;
- Hermes state/home persistence;
- one-user concurrency;
- cold starts;
- memory scope;
- mobile approval UX;
- how interactive Hermes can request bounded framework tasks without becoming Control/project authority.

---

# Continuous requirements

At every phase:

- GitHub remains source of truth;
- pin Hermes, FreeLLMAPI, Modal SDK and important dependencies;
- record provider/model/route provenance where observable;
- bound model calls, tool calls, retries, wall time and concurrency;
- budget exhaustion fails closed;
- provider secrets stay outside Hermes;
- only approved data classes enter the generic free-provider pool;
- deterministic work stays deterministic;
- remove superseded code/config/docs;
- keep README, architecture, roadmap and deployed behavior aligned.

---

# Definition of Done

A phase is Done only when:

- its objective is achieved;
- relevant behavior is verified;
- failure/security boundaries are exercised;
- evidence and usage metrics are captured;
- unnecessary parallel implementation is absent/removed;
- stale code/config/docs are removed;
- README, architecture, roadmap and actual behavior agree;
- no known material inconsistency is knowingly left behind.
