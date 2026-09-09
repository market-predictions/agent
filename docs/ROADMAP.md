# Agent Framework Roadmap

**Repository:** `market-predictions/agent`  
**Architecture:** v0.3 — Evidence-First Hermes  
**Status:** canonical implementation sequence  
**Date:** 2026-09-09

This roadmap implements `docs/ARCHITECTURE.md` in the smallest evidence-driven sequence.

Hermes is the selected runtime. There is no Pydantic AI bake-off or fallback in this phase.

---

## Roadmap principle

Do not build the next layer because it is technically attractive.

Build it only when the previous phase has produced evidence that the next layer solves a real limitation.

```text
uncertainty
   ↓
smallest experiment
   ↓
measured evidence
   ↓
next smallest justified capability
```

The hard pilot constraint is zero/near-zero external cost. Paid inference is not a hidden fallback.

---

# Phase 1 — Prove Hermes + one direct free provider

## Objective

Prove the actual high-risk hypothesis:

> Can Hermes complete a short multi-step research task reliably enough on one approved zero-cost/free model/provider route?

## Build only

- one Modal Function;
- pinned Hermes one-shot/headless execution;
- one direct approved free provider via Modal Secret;
- two fixed safe tools:
  - `search`;
  - `web_fetch`;
- one bounded PUBLIC_NON_PERSONAL background-research task;
- one simple structured result format;
- hard counters for model calls, tool calls, retries and wall time;
- usage/provenance logging.

## Do not build

- FreeLLMAPI;
- Sandbox;
- fan-out;
- task-profile resolver;
- database/queue;
- mobile service;
- project integration.

## Test

Run the same task 20 times.

Measure:

- structured result success rate;
- tool-loop completion rate;
- supported/evidenced claim rate;
- hallucination/unsupported claim rate;
- model calls/run;
- tool calls/run;
- retries/run;
- 429/5xx rate;
- wall time;
- human usefulness against a manually checked baseline.

## Gate

Proceed only if:

- useful output is consistently produced;
- initial target is approximately >=70% human-usable runs;
- usage stays inside hard request/time budgets;
- no data/secrets boundary is violated;
- failures are explicit rather than disguised as success.

If not green:

1. simplify task;
2. improve Hermes instruction/tool design;
3. try another approved free provider/model;
4. repeat measurement.

Do **not** add infrastructure to compensate for weak model/task fit.

---

# Phase 2 — Trusted evidence verifier

## Objective

Make worker output independently checkable.

## Build

One separate trusted Modal Function that:

- accepts strict structured result data only;
- validates required fields;
- validates URL schemes/hosts;
- rejects loopback/private/link-local/metadata targets;
- revalidates every redirect;
- fetches evidence with strict time/byte limits;
- normalizes fetched text;
- verifies evidence excerpt/claim support where deterministically possible.

## Security gate

Explicit tests for:

- localhost;
- `127.0.0.1` / `::1`;
- RFC1918/private ranges;
- link-local/metadata ranges;
- DNS rebinding/redirect to private range;
- oversized response;
- timeout;
- malformed structured input.

The verifier never executes worker-provided code, files or commands.

## Outcome

Introduce `RESULT_READY` only after this verifier passes.

---

# Phase 3 — Prove whether parallelism adds value

## Objective

Do not assume two agents are better than one.

Run two independent Hermes workers on the **same research objective**.

Prefer different approved free model routes if available; otherwise keep the experiment independent via separate runs while holding the task constant.

Measure:

- agreement;
- unique valid findings;
- verified evidence coverage;
- false positives;
- human usefulness;
- model/tool call increase;
- compute increase;
- useful output per unit of compute/inference.

## Gate

Only introduce standard worker fan-out if the second worker creates a material quality/coverage improvement.

If adopted, Modal owns fan-out.

Hermes internal delegation remains disabled until hierarchical reasoning itself is separately proven useful.

---

# Phase 4 — FreeLLMAPI only on measured trigger

## Trigger

At least one must be observed:

- direct provider quotas materially block useful work;
- provider outages materially reduce completion rate;
- model diversity materially improves result quality;
- multiple services/workers make centralized provider-key isolation materially valuable.

## Build

- one protected FreeLLMAPI Modal service;
- one unified/revocable worker credential;
- upstream provider keys only in the gateway service;
- fixed `ENCRYPTION_KEY` from Modal Secret;
- declarative provider configuration on cold start;
- max active writer/replica = 1 initially;
- actual route/model provenance logging.

## Do not build yet

- persistent DB Volume unless loss of quota/cooldown history is measured as material;
- Redis;
- Postgres;
- horizontal router cluster.

## Gate

Compare direct-provider baseline with FreeLLMAPI on:

- completion rate;
- route switches;
- tool-loop continuity;
- verified output quality;
- request consumption;
- operational complexity.

Keep FreeLLMAPI only if the measured value exceeds the added complexity.

---

# Phase 5 — Capability-specific isolation and profiles

These are two independent triggers.

## 5A — Modal Sandbox trigger

Move a task class from Modal Function to Modal Sandbox only when it requires:

- generated code execution;
- autonomous shell;
- broad filesystem operations;
- repository mutation;
- untrusted executable artifacts.

Do not move fixed safe-tool research workers into Sandboxes merely for architectural symmetry.

## 5B — Task profile trigger

Introduce Git-backed task profiles only when there are at least two materially different capability/data classes.

Example:

```text
public non-personal research
vs.
code review with repository access
```

Until then, least privilege is hardcoded in the one worker configuration.

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

Do not use the generic free lane for person-linked prospect data by default.

First integration is result-only with no production DB write authority and an explicit data/inference policy.

## Scrub

Initial integrations use synthetic/public non-sensitive material only.

Unredacted sensitive care/legal data stays outside the generic free lane.

## Publishers

A project-specific publisher is added only after repeated handoff demonstrates value.

It must be narrow, separate from worker execution and accept only independently verified result structures.

---

# Phase 7 — Mobile / interactive Hermes

## Product intent

After the bounded worker carrier is proven, allow the user to control a dedicated Hermes instance from mobile.

This is a reason Hermes remains the selected runtime now.

## Target topology

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
approved provider lane / protected FreeLLMAPI
```

## Must be designed separately

- authentication;
- session persistence;
- Hermes state/home persistence;
- one-user concurrency;
- cold-start behavior;
- memory scope;
- mobile approval UX;
- how interactive Hermes may request bounded framework tasks without becoming project/Control authority.

The interactive Hermes service is not the framework database and does not own project truth.

---

# Continuous requirements

At every phase:

- GitHub remains source of truth;
- pin important runtime dependencies;
- record actual provider/model provenance where observable;
- bound model calls, tool calls, retries, wall time and concurrency;
- zero/near-zero pilot budget fails closed when exhausted;
- deterministic work stays deterministic;
- remove superseded code/config/docs;
- update architecture and roadmap when actual behavior changes.

---

# Definition of Done

A phase is Done only when:

- its business/technical objective is achieved;
- relevant behavior is tested;
- failures and security boundaries are exercised;
- metrics/evidence are recorded;
- no unnecessary parallel implementation remains;
- stale code/config/docs are removed;
- README, architecture, roadmap and deployed behavior agree;
- no known material inconsistency is knowingly left behind.
