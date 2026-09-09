# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Status:** Target architecture / pre-implementation  
**Version:** 0.3 — Evidence-First Hermes  
**Date:** 2026-09-09  
**Canonical:** yes — this document is the single current architecture truth.

Historical rationale is recorded in `docs/DESIGN_REVIEW_10_ITERATIONS.md`. The implementation sequence is canonicalized in `docs/ROADMAP.md`.

---

## 1. Objective

`agent` is a standalone execution framework for **bounded autonomous AI work across multiple projects**.

It exists to make tasks such as these cheap, reusable and independently verifiable:

- public non-personal web research and evidence collection;
- SolidDesign support once data-policy boundaries are satisfied;
- synthetic Scrub test generation and edge-case discovery;
- code, pull-request and architecture critique;
- documentation consistency checks;
- adversarial review;
- future project-specific bounded work.

Potential callers are:

- Control;
- a target project;
- a human operator;
- a future automation that already owns its lifecycle.

The governing contract is:

> **bounded task -> Hermes execution within machine limits -> independent evidence verification -> result back to caller authority**

`agent` is an **execution carrier**, not:

- a Control replacement;
- a project database;
- a generic scheduler;
- a queue/broker;
- a persistent multi-agent control plane;
- a production authority plane.

The target project owns its business truth and irreversible actions. When Control is the caller, Control owns mission lifecycle, scheduling, acceptance and successor decisions.

---

## 2. Governing engineering doctrine

Decision order:

1. business outcome;
2. simplest complete solution;
3. proven/native capability;
4. lowest maintenance/operational burden;
5. least new architecture;
6. easiest verification.

Hard principles:

- solid but simple;
- no overengineering;
- first-principles reasoning;
- do not reinvent the wheel;
- every dependency and state plane must earn its existence;
- one source of truth per concern;
- least privilege;
- untrusted model/web/repository input is hostile-capable;
- deterministic work stays deterministic;
- evidence before abstraction;
- implementation is not Done without verification and cleanup;
- stale/conflicting code, configuration and documentation are removed rather than kept as parallel current truth.

Canonical expanded doctrine:

`https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit`

---

## 3. Product decisions

### 3.1 Hermes is the selected agent runtime

There is **no runtime bake-off in this phase**.

Hermes is a deliberate product choice because:

- it provides a headless one-shot agent interface;
- it provides a mature tool/skill runtime;
- the same ecosystem can later support an interactive/mobile Hermes experience;
- using one agent runtime across bounded workers and a later interactive service reduces product fragmentation.

Pydantic AI is not a v0.3 alternative, fallback or parallel implementation.

This does **not** mean every Hermes feature is enabled. V1 uses only the minimum capabilities required for a short bounded worker.

### 3.2 Modal remains the cloud runtime

GitHub is the canonical source of truth. Modal provides headless cloud execution.

```text
GitHub = architecture/code/config/history
Modal  = runtime
```

No PC or VPS is required for runtime operation.

### 3.3 Evidence-first sequence replaces carrier-first sequence

The first uncertainty is not whether Modal can start a process. The first uncertainty is:

> **Can Hermes, using a zero-cost/free model lane and a very small fixed toolset, complete a short multi-step research loop with sufficiently reliable, evidence-backed output?**

Therefore v0.3 proves that path **before** adding FreeLLMAPI, worker fan-out, policy-profile machinery, persistent state or Sandbox-only features.

---

## 4. V0.3 first-proof architecture

```text
                   HUMAN / CALLER
                        |
                        | bounded public-non-personal task
                        v
                 +-------------------+
                 | Modal Function    |
                 |                   |
                 | Hermes one-shot   |
                 | fixed safe tools  |
                 | hard budgets      |
                 +---------+---------+
                           |
                           | direct inference
                           v
                 +-------------------+
                 | ONE approved free |
                 | model/provider    |
                 +---------+---------+
                           |
                    structured result
                           |
                           v
                 +-------------------+
                 | Trusted verifier  |
                 | separate Function |
                 | evidence re-fetch |
                 | SSRF protections  |
                 +---------+---------+
                           |
                      RESULT_READY
                           |
                           v
                    CALLER AUTHORITY
```

The first proof deliberately has:

- one Hermes worker;
- one approved direct free provider;
- one Modal Function for worker execution;
- a fixed, small toolset;
- no FreeLLMAPI;
- no worker fan-out;
- no task-profile resolver;
- no project mutation capability.

---

## 5. Why Modal Function first, Sandbox later

The first worker receives only framework-owned, fixed tools such as:

- `search(query)`;
- `web_fetch(url)`.

It does not execute arbitrary model-generated shell/code and does not mutate repositories.

For that capability class, a normal Modal Function is the smallest complete runtime.

A Modal Sandbox becomes mandatory when a task class requires any of the following:

- autonomous shell execution;
- generated code execution;
- broad filesystem tooling;
- repository mutation;
- untrusted executable artifacts.

Evolution rule:

```text
fixed safe tools only
    -> Modal Function

shell / generated code / broad executable tools
    -> Modal Sandbox
```

Do not pay the complexity/cost of Sandbox isolation before the capability requires it.

---

## 6. Hermes worker model

V1 worker behavior is deliberately narrow.

```text
1. receive bounded objective and structured inputs
2. run pinned Hermes in headless/one-shot mode
3. use only fixed registered tools
4. stop when result schema is complete or a hard budget is hit
5. emit structured candidate result + usage/provenance
6. terminate
```

Disabled/not used in the first proof:

- Hermes gateway;
- Hermes Cron;
- Hermes Kanban;
- long-term/canonical Hermes memory;
- persistent team profiles;
- internal recursive delegation;
- target-project write tools;
- shell/code execution.

Hermes remains the chosen runtime despite those disabled features because later mobile/interactive operation is an explicit product direction.

---

## 7. Hard execution budgets

Wall time alone is not sufficient for a free inference lane.

Every worker has machine-enforced limits for at least:

- `max_model_calls`;
- `max_tool_calls`;
- `max_wall_seconds`;
- maximum retries;
- maximum concurrent tasks at deployment/workspace level.

Initial proof target:

```text
max_model_calls: 12
max_tool_calls: 20
max_wall_minutes: 10
max_retries: 1
concurrent_tasks: 1
```

These values are pilot defaults and may change only from measured evidence.

Cost rule:

> **Credits/budget exhausted -> fail closed. Do not continue by silently increasing paid usage.**

---

## 8. Data classification

The previous `PUBLIC` category was too broad.

### FREE_PUBLIC_NON_PERSONAL — permitted by default

- public technical documentation;
- public product/vendor information not about natural persons;
- public standards/specifications;
- public repositories where no sensitive/private context is introduced;
- synthetic data;
- non-sensitive generated fixtures.

### Not in the generic free lane by default

- public information about identifiable natural persons;
- sole-trader/person-linked prospect data;
- proprietary source code;
- internal business data;
- personal data;
- client/customer content.

### Never through the generic free lane

- credentials or secrets;
- production database contents;
- unredacted sensitive legal/care documents;
- regulated/high-impact personal dossiers.

Public availability is not equivalent to non-personal data.

The first pilot therefore uses **technology/product/standard research without personal data**, not SolidDesign prospecting.

---

## 9. Result contract

The first implementation may use one current schema without building a generic schema registry.

A research result contains at minimum:

```json
{
  "task_id": "...",
  "status": "CANDIDATE",
  "claims": [
    {
      "claim": "...",
      "evidence_url": "https://...",
      "evidence_excerpt": "..."
    }
  ],
  "coverage": {
    "requested_items": 10,
    "returned_items": 8
  },
  "provenance": {
    "framework_sha": "...",
    "hermes_version": "...",
    "requested_model": "...",
    "provider": "..."
  },
  "usage": {
    "model_calls": 0,
    "tool_calls": 0,
    "wall_seconds": 0
  }
}
```

When multiple workers are introduced later, every result also records worker identity and coverage/partition identity so `PARTIAL` is meaningful.

Git history is the first schema version history. A separate schema-versioning subsystem is added only when compatibility between multiple live schema versions becomes a real requirement.

---

## 10. Independent evidence verification

A separate trusted Modal Function verifies candidate results.

It must not trust worker-provided URLs merely because they are syntactically valid.

For each evidence item it performs:

1. strict input-schema validation;
2. URL scheme validation (`https`/approved `http` only);
3. hostname resolution;
4. rejection of localhost, private, loopback, link-local and metadata-address ranges;
5. controlled fetch with byte/time limits;
6. redirect revalidation at every hop;
7. text normalization;
8. evidence-excerpt presence check or other explicit deterministic evidence check.

The verifier accepts **structured data only**. It does not execute worker-provided scripts, commands or arbitrary files.

The verifier may prove evidence presence. It must not pretend subjective business judgment is deterministic.

---

## 11. Authority model

Framework execution states:

```text
REJECTED
FAILED
PARTIAL
RESULT_READY
```

`RESULT_READY` means only:

- candidate execution completed sufficiently;
- required deterministic/evidence checks passed.

It does not mean:

- business accepted;
- merged;
- published;
- sent;
- mission complete;
- `DONE`.

Caller/project/Control remains acceptance authority.

V1 has no publisher and no target-project production mutation capability.

---

## 12. Phase-1 quality qualification

The first proof runs the **same non-personal background-research task 20 times with Hermes** using one selected free provider/model route.

This is not a harness comparison.

Measure:

- valid structured output rate;
- complete multi-step tool-loop rate;
- evidence verification pass rate;
- hallucination/unsupported-claim rate;
- model calls per run;
- tool calls per run;
- retries per run;
- provider 429/5xx failures;
- wall time;
- human usefulness against a small manually checked baseline.

Initial go/no-go target:

- target at least ~70% human-usable runs;
- no secret/data-boundary violation;
- unsupported claims must be observable rather than silently accepted.

If the model lane performs below threshold, do **not** add infrastructure. First simplify the task/prompt or select another approved free provider/model while keeping Hermes.

---

## 13. Parallelism is earned by a diversity experiment

After the single-worker path is useful, test two independent Hermes workers on the **same objective**.

The purpose is not merely to halve a list.

Measure whether independent execution improves:

- verified evidence coverage;
- agreement on important findings;
- unique valid findings;
- false-positive rate;
- human usefulness;
- useful output per model call/compute unit.

If two workers do not materially improve accepted output, keep one worker.

Modal owns fan-out when fan-out is adopted. Hermes internal delegation remains off until hierarchical reasoning itself is separately justified.

---

## 14. FreeLLMAPI is an optimization phase, not a prerequisite

FreeLLMAPI is introduced only when measurement shows at least one concrete need:

- provider quota exhaustion materially blocks useful work;
- availability/failover materially improves completion rate;
- deliberate model diversity improves result quality;
- central provider-key isolation becomes valuable across multiple workers/services.

Until then Hermes uses one direct approved provider credential scoped through Modal Secrets.

When FreeLLMAPI is introduced:

- deploy it as a separate protected Modal service;
- Hermes receives only the gateway credential;
- upstream provider keys stay outside worker execution;
- use a fixed `ENCRYPTION_KEY` from Modal Secrets;
- bootstrap provider configuration declaratively on cold start;
- maximum active FreeLLMAPI writer/replica initially: 1;
- persistent SQLite/Volume is still optional until measured quota-history loss justifies it.

Do not add Redis/Postgres or a distributed router to scale a problem not yet observed.

---

## 15. Routing and reproducibility

Pinning software does not make dynamic free-model inference reproducible.

Distinguish:

### Code/runtime reproducibility

Pin:

- Hermes release/commit;
- Modal SDK version;
- framework Git SHA;
- important dependencies;
- FreeLLMAPI image/version when later introduced.

### Inference accountability

Record, where observable:

- requested model;
- actual provider/model;
- timestamp;
- route/fallback switches;
- degraded state;
- router/catalog identity when FreeLLMAPI exposes it.

Do not claim identical inference output from a pinned image when upstream routing/catalog behavior is dynamic.

---

## 16. State model

There is no framework database in v1.

| State | Canonical owner |
|---|---|
| project/business state | target project |
| Control lifecycle | Control |
| framework code/docs/config | GitHub |
| live invocation | Modal Function/process |
| Hermes conversational state | disposable for bounded worker |
| result | caller after return/persistence |
| canonical skills/instructions | Git after review |
| FreeLLM quota state | not present until FreeLLMAPI phase; optional persistence later |

No queue, worker registry or generic task-state database is introduced.

---

## 17. Scheduling and concurrency

V1 has no framework-owned business scheduler.

- Control-owned work is triggered by Control.
- Project-owned work is triggered by the project.
- Pilot work is invoked manually or by a minimal operator mechanism.
- Modal Schedule is considered only for standalone routines with no existing lifecycle owner.

Deployment/workspace concurrency is explicitly capped.

Retries are bounded and idempotence-aware.

A retry loop must never be able to consume unlimited monthly credits.

---

## 18. Mobile / interactive Hermes is a planned next capability

Hermes is intentionally retained as the runtime partly because the next product phase should allow Hermes to be controlled from a phone/mobile client.

This is **not** part of the first bounded-worker proof, but it is an explicit roadmap target.

Future topology:

```text
phone / mobile client
        |
        v
authenticated Modal endpoint
        |
        v
dedicated interactive Hermes service
        |
        +--> persistent Hermes session/memory state
        |
        v
approved model lane / protected FreeLLMAPI
```

The interactive service must remain separate from bounded worker business authority.

It requires its own decisions for:

- authentication;
- session persistence;
- `~/.hermes` / Hermes state;
- one-user concurrency;
- cold-start behavior;
- mobile approval UX;
- persistent memory scope.

It must not become Control mission state or a generic project database.

---

## 19. Project integration sequence

### Control

After the carrier is proven:

```text
Control
  -> bounded task
  -> Hermes/Modal carrier
  -> RESULT_READY
  -> Control accepts/rejects/continues
```

### SolidDesign

SolidDesign prospect research is **not** the first free-lane pilot because public prospect data may contain personal data.

Later integration requires an explicitly approved data/inference policy and starts result-only/no database writes.

### Scrub

Initial safe tasks may use synthetic/public material only.

Unredacted sensitive care/legal content is never sent through the generic free-provider lane.

---

## 20. Explicit non-goals for the first proof

Do not build yet:

- Pydantic AI or a second agent runtime;
- harness bake-off;
- FreeLLMAPI;
- Modal Sandbox;
- worker fan-out/orchestrator abstraction;
- task-profile resolver;
- framework database;
- queue/broker;
- generic scheduler;
- vector database;
- persistent Hermes gateway;
- Hermes Cron;
- Hermes Kanban/team;
- recursive swarms;
- project publisher;
- production write credentials;
- generic adapter/plugin registry;
- mobile client/service before the bounded worker is proven.

---

## 21. Evolution triggers

| Observed need | Candidate evolution |
|---|---|
| one free model/provider is unreliable or quota-limited | introduce FreeLLMAPI and approved provider pool |
| two independent workers materially improve quality/coverage | add Modal fan-out |
| shell/generated code/repo mutation becomes required | move that task class from Modal Function to Modal Sandbox |
| second capability/data class exists | introduce Git-backed task-profile mechanism |
| repeated project handoff has value | add one narrow project-specific publisher |
| mobile interaction is required after worker proof | dedicated authenticated interactive Hermes service |
| private-source analysis is required | credential-free source staging + approved private inference lane |
| durable async status is genuinely required | smallest caller-owned/checkpoint mechanism |
| free-provider quality remains insufficient after task simplification/provider changes | reconsider inference economics, not framework complexity |

Possible future need is not evidence to build now.

---

## 22. Definition of Done

### Architecture/documentation Done

- this document is the single current architecture truth;
- README matches this topology;
- roadmap matches this implementation sequence;
- historical rationale is marked non-canonical;
- no current document presents v0.2 carrier-first design as active;
- no Pydantic-AI bake-off remains in current architecture/roadmap;
- no stale/conflicting code or configuration remains.

### First-proof implementation Done

- pinned Hermes runs headlessly on Modal;
- one approved zero-cost/free provider is integrated;
- fixed safe tools work;
- model/tool/wall budgets are enforced;
- 20-run quality qualification is completed and recorded;
- trusted evidence verification is implemented and SSRF-hardened;
- provider/model and usage provenance is recorded;
- failure/429/timeout behavior is explicit;
- relevant tests pass;
- unused/superseded code/config is removed;
- README, architecture, roadmap and deployed behavior agree;
- no known material inconsistency is knowingly left behind.

---

## 23. Current implementation sequence

The canonical implementation sequence is maintained in [`ROADMAP.md`](ROADMAP.md).

In summary:

```text
Phase 1  Hermes + one direct free provider + fixed tools
   ↓
Phase 2  trusted evidence verifier
   ↓
Phase 3  independent two-worker diversity experiment
   ↓
Phase 4  FreeLLMAPI only if measured trigger fires
   ↓
Phase 5  Sandbox/profile capabilities only when earned
   ↓
Phase 6  Control/project integrations
   ↓
Phase 7  mobile interactive Hermes
```
