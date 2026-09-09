# Agent Framework — Historical Design Review and Decision Record

**Repository:** `market-predictions/agent`  
**Status:** historical / non-canonical rationale  
**Current architecture:** `docs/ARCHITECTURE.md` v0.3  
**Current roadmap:** `docs/ROADMAP.md`  
**Date:** 2026-09-09

> This file preserves why the design changed. It does **not** define current architecture. If any statement here conflicts with `docs/ARCHITECTURE.md`, the canonical architecture wins.

---

## 1. Original ten-iteration review of v0.2

The original Modal/Hermes/FreeLLMAPI proposal was attacked ten times from first principles.

### Iteration 1 — scope

**Finding:** bounded project execution and a persistent mobile/personal Hermes are different products.

**Decision:** keep the bounded worker carrier as core; interactive/mobile Hermes becomes a later separate service.

**Current status:** retained in v0.3, but mobile Hermes is now an explicit roadmap phase because Hermes has been chosen as the long-term runtime.

### Iteration 2 — duplicate orchestration

**Finding:** Modal fan-out plus Hermes subagents creates two concurrency/failure authorities.

**Decision:** Modal owns framework-level fan-out when fan-out is introduced.

**Current status:** retained. V0.3 goes further: first prove one worker before adding fan-out at all.

### Iteration 3 — Hermes/Modal boundary

**Finding:** Hermes `terminal.backend: modal` leaves the Hermes process elsewhere and does not provide whole-agent headless cloud execution.

**Decision:** if a task needs a Sandbox, run the whole Hermes process inside it.

**Current status:** narrowed. V0.3 starts with a Modal Function because the first task exposes only fixed safe tools. Sandbox becomes capability-triggered when shell/generated-code/repository mutation is actually required.

### Iteration 4 — FreeLLMAPI placement

**Finding:** placing FreeLLMAPI and all provider keys inside every worker increases worker-compromise blast radius.

**Decision:** when FreeLLMAPI is introduced, run it as a separate protected service.

**Current status:** retained as the eventual design, but FreeLLMAPI itself is removed from the first proof until routing/failover/diversity need is measured.

### Iteration 5 — FreeLLMAPI persistence

**Finding:** persistent SQLite state can preserve quota/cooldown history, but persistence adds lifecycle/concurrency complexity.

**Decision:** do not add persistent DB/Volume before measured need.

**Current status:** retained. Later FreeLLMAPI cold start must use a fixed encryption key plus declarative provider configuration. Persistent SQLite remains optional and single-writer if eventually added.

### Iteration 6 — prompt constraints versus capability

**Finding:** natural-language statements such as `no production writes` are not security controls.

**Decision:** authority must eventually be machine-enforced outside Hermes.

**Current status:** principle retained, mechanism deferred. V0.3 hardcodes least privilege for the single first capability class. Git-backed task profiles are introduced only when a second materially different capability/data class exists.

### Iteration 7 — framework state

**Finding:** a generic agent framework naturally attracts a DB, queue, retry scheduler and status service even when callers already own lifecycle.

**Decision:** no framework DB, queue or business scheduler in v1.

**Current status:** retained unchanged.

### Iteration 8 — verification

**Finding:** a worker cannot be the final authority for its own output.

**Decision:** generation and trusted verification are separate.

**Current status:** strengthened in v0.3. The verifier now re-fetches evidence and must be SSRF-hardened rather than checking only schema/URL shape.

### Iteration 9 — mobile interaction

**Finding:** mobile interactive Hermes introduces persistent sessions, memory, auth and UX concerns that should not contaminate the bounded-worker core.

**Decision:** separate future service.

**Current status:** retained, but explicitly planned after carrier proof. This future mobile direction is one of the reasons Hermes remains the selected runtime.

### Iteration 10 — reproducibility and supply chain

**Finding:** floating Hermes/FreeLLMAPI/software versions undermine reproducibility.

**Decision:** pin runtime software and record provenance.

**Current status:** refined. Software/runtime is pinned; dynamic model/provider inference is treated as provenance-accountable rather than falsely claimed to be fully reproducible.

---

## 2. External Opus review of v0.2

An external review identified a more fundamental sequencing problem:

> the design was proving the carrier before proving the uncertain model/tool-loop quality.

The review also identified concrete issues around:

- ephemeral FreeLLMAPI provider configuration;
- dynamic routing/catalog behavior versus reproducibility claims;
- `public` data not necessarily being non-personal;
- weak evidence verification;
- missing cross-task/request budgets;
- Sandbox cost/necessity for fixed-tool workers;
- premature task profiles;
- two-worker partitioning proving throughput rather than quality diversity.

These findings materially changed the current architecture.

### Adopted from the external review

1. **Evidence-first build order.** Prove Hermes + one direct free provider before adding routing/fan-out infrastructure.
2. **First pilot uses PUBLIC_NON_PERSONAL data.** SolidDesign prospecting is not the first generic free-lane pilot.
3. **FreeLLMAPI moves to a measured optimization phase.**
4. **Modal Function first for fixed safe tools.** Sandbox is capability-triggered later.
5. **Independent verifier re-fetches evidence** and is explicitly SSRF-hardened.
6. **Budgets include model calls and tool calls**, not only wall time.
7. **Parallelism is tested for quality/diversity value**, not assumed.
8. **Task profiles are deferred** until there is more than one capability class.
9. **Inference is provenance-controlled, not falsely called deterministic/reproducible.**
10. **Coverage/worker identity is required** when `PARTIAL` becomes relevant.

### Not adopted as proposed

The external review recommended Pydantic AI for v1 and suggested a harness comparison.

The product owner explicitly chose **Hermes** as the runtime for this phase and rejected a Pydantic AI bake-off or fallback.

Reason:

- Hermes is already the intended long-term agent environment;
- the next planned product phase is mobile control of Hermes from a phone;
- a second runtime would create product/runtime fragmentation without serving the current goal.

Therefore current truth is:

```text
Hermes = selected runtime
Pydantic AI = not part of current architecture or roadmap
```

This is a deliberate product constraint, not an unresolved experiment.

---

## 3. Current architecture after review

The v0.3 sequence is now:

```text
Phase 1
Hermes + one direct free provider + fixed safe tools
        ↓
Phase 2
trusted evidence verifier
        ↓
Phase 3
two-worker independent diversity experiment
        ↓
Phase 4
FreeLLMAPI only if quota/failover/diversity trigger fires
        ↓
Phase 5
Sandbox and/or task profiles only when capability triggers fire
        ↓
Phase 6
Control/project integrations
        ↓
Phase 7
mobile interactive Hermes
```

This sequence is canonicalized in `docs/ROADMAP.md`.

---

## 4. Current non-goals inherited from the review process

Do not add without a measured trigger:

- a second agent runtime;
- Pydantic AI;
- harness bake-off;
- framework database;
- queue/broker;
- generic scheduler;
- persistent worker memory;
- recursive swarm;
- generic project adapter layer;
- publisher/admin proxy;
- persistent FreeLLMAPI DB;
- Sandbox for fixed safe-tool research;
- task-profile machinery while only one capability class exists.

---

## 5. Historical cleanup rule

Git history is the archive.

Current files must describe current truth, not preserve obsolete architecture as if still active.

Therefore this file records decisions and supersession explicitly, while:

- `docs/ARCHITECTURE.md` defines the current target design;
- `docs/ROADMAP.md` defines the current implementation sequence;
- `README.md` is only a concise aligned entry point.

Definition of Done requires these files and actual implementation behavior to remain aligned.
