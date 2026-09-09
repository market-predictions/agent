# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Status:** Target architecture / pre-implementation  
**Version:** 0.4 — Evidence-First Hermes + FreeLLMAPI  
**Date:** 2026-09-09  
**Canonical:** yes — this document is the single current architecture truth.

Historical rationale is recorded in `docs/DESIGN_REVIEW_10_ITERATIONS.md`. The canonical implementation sequence is `docs/ROADMAP.md`.

---

## 1. Objective

`agent` is a standalone execution framework for **bounded autonomous AI work across multiple projects**.

Potential use includes:

- public non-personal research and evidence collection;
- SolidDesign support once its data-policy boundary is explicitly approved;
- synthetic Scrub test generation and edge-case discovery;
- code, pull-request and architecture critique;
- documentation consistency checks;
- adversarial review;
- future bounded project tasks.

Potential callers are Control, target projects, human operators and future automations that already own their lifecycle.

Core contract:

> **bounded task -> Hermes -> FreeLLMAPI -> evidence-backed candidate result -> independent verification -> caller authority**

`agent` is an execution carrier, not a Control replacement, project database, business scheduler, queue/broker or production authority plane.

Target projects own their business truth and irreversible actions. When Control is the caller, Control owns mission lifecycle, scheduling, acceptance and successor decisions.

---

## 2. Governing doctrine

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
- first principles;
- do not reinvent the wheel;
- every dependency/state plane must earn its existence;
- one source of truth per concern;
- least privilege;
- untrusted model/web/repository input is hostile-capable;
- deterministic work stays deterministic;
- evidence before further abstraction;
- Done includes verification, cleanup and documentation alignment;
- stale/conflicting code/config/docs are removed rather than retained as parallel current truth.

---

## 3. Fixed product decisions

### 3.1 Hermes is the agent runtime

There is no harness bake-off or fallback runtime in this phase.

Hermes is chosen because it provides a headless one-shot runtime, tools/skills and a coherent path to the planned later mobile/interactive Hermes capability.

Pydantic AI is not part of the current architecture or roadmap.

### 3.2 FreeLLMAPI is the inference gateway from Phase 1

There is no temporary direct-provider integration.

Reason:

- the real target contract is Hermes -> FreeLLMAPI;
- building direct-provider plumbing only to remove it later creates disposable architecture;
- provider credentials belong outside Hermes workers;
- routing, quota behavior and provider switching are part of the actual system that must be tested from the start.

Phase 1 does **not** restrict FreeLLMAPI to one provider. All providers for which valid FreeLLMAPI configuration/credentials are present are eligible for routing according to the pinned router's behavior.

There is no hand-maintained Phase-1 subset or allowlist.

This broad provider eligibility is acceptable only because the first lane is restricted to `PUBLIC_NON_PERSONAL` data. Sensitive or person-linked data does not enter the generic free pool.

### 3.3 Modal is the cloud runtime

```text
GitHub = architecture/code/config/history
Modal  = runtime
```

No PC or VPS is required for normal runtime operation.

### 3.4 Evidence-first still governs the build order

FreeLLMAPI being foundational does not justify building the full swarm first.

The first real uncertainty is:

> Can a short Hermes tool-loop, routed through FreeLLMAPI's real multi-provider free pool, reliably produce useful evidence-backed results within hard request and compute budgets?

Therefore the first proof has one Hermes worker and the real FreeLLMAPI path, but no fan-out, project writes, framework DB, queue, persistent Hermes memory or generic policy system.

---

## 4. Phase-1 target architecture

```text
                  HUMAN / CALLER
                       |
                       | bounded PUBLIC_NON_PERSONAL task
                       v
                +--------------------+
                | Modal Function     |
                |                    |
                | Hermes one-shot    |
                | fixed safe tools   |
                | hard budgets       |
                +---------+----------+
                          |
                          | OpenAI-compatible inference
                          v
             +-----------------------------+
             | Protected FreeLLMAPI        |
             | Modal service               |
             |                             |
             | all configured providers    |
             | eligible                    |
             | upstream provider keys here |
             | max active replica: 1       |
             +-------------+---------------+
                           |
                           v
                  free provider pool
                           |
                   routed responses
                           |
                           v
                 Hermes candidate result
                           |
                           v
                +--------------------+
                | Trusted verifier   |
                | separate Function  |
                | evidence re-fetch  |
                | SSRF protections   |
                +---------+----------+
                          |
                     RESULT_READY
                          |
                          v
                   CALLER AUTHORITY
```

Phase 1 has:

- one Hermes worker;
- one Modal Function for that fixed-safe-tool worker;
- one protected FreeLLMAPI Modal service;
- all configured FreeLLMAPI providers eligible;
- no worker fan-out;
- no task-profile resolver;
- no target-project mutation capability.

---

## 5. FreeLLMAPI configuration and state

### 5.1 Secret boundary

Hermes workers receive only:

- protected FreeLLMAPI endpoint;
- unified/revocable FreeLLMAPI client credential;
- Modal endpoint authentication material if required.

Hermes workers do not receive upstream provider API keys.

FreeLLMAPI receives provider keys, its own encryption material and router configuration. It receives no target-project production credentials.

### 5.2 Cold-start configuration

Phase 1 uses upstream FreeLLMAPI's declarative startup configuration rather than manually mutating a persistent database.

Required pattern:

```text
Modal Secrets
  -> fixed ENCRYPTION_KEY
  -> provider credentials/config
  -> FREEAPI_CONFIG_JSON or FREEAPI_CONFIG_PATH

FreeLLMAPI cold start
  -> migrations
  -> idempotent declarative config
  -> providers available
```

This means FreeLLMAPI can start from an ephemeral SQLite DB while still having configured providers after each cold start.

### 5.3 Persistence

Persistent SQLite/Modal Volume is **not** required for the first proof.

Consequences accepted in Phase 1:

- cross-cold-start quota/cooldown history may reset;
- local analytics may reset unless exported before termination;
- routing quality is evaluated despite that limitation.

Evolution trigger: add exactly one persistent single-writer Volume only if measured loss of quota/cooldown/analytics state materially harms useful capacity or observability.

Do not add Redis/Postgres or horizontally scale multiple FreeLLMAPI writers over one SQLite file.

### 5.4 Provider pool

All configured FreeLLMAPI providers are eligible from the start.

We do not try to make their privacy, quality, quota or routing behavior homogeneous. Instead:

- only `PUBLIC_NON_PERSONAL` input may enter this lane;
- actual provider/model provenance is captured where observable;
- route/fallback changes are treated as normal measured behavior;
- degraded/failure behavior is explicit;
- no provider availability is treated as an SLA.

---

## 6. Modal Function first, Sandbox later

The first Hermes worker receives only framework-owned fixed tools such as:

- `search(query)`;
- `web_fetch(url)`.

It has no autonomous shell, generated-code execution, repository mutation or broad filesystem authority.

Therefore the first worker runs in a normal Modal Function.

A Modal Sandbox becomes mandatory for a task class that requires:

- autonomous shell execution;
- generated code execution;
- broad filesystem tooling;
- repository mutation;
- untrusted executable artifacts.

```text
fixed safe tools only
  -> Modal Function

shell / generated code / broad executable tools
  -> Modal Sandbox
```

If Sandbox is later used, run the whole Hermes process inside it; do not make Hermes' remote `terminal.backend: modal` the primary containment model.

---

## 7. Hermes worker model

The first worker is intentionally narrow:

```text
1. receive bounded objective + structured inputs
2. run pinned Hermes headless/one-shot
3. call FreeLLMAPI only for inference
4. use only fixed registered tools
5. stop when result is complete or a hard budget fires
6. emit structured result + provenance + usage
7. terminate
```

Disabled/not used in Phase 1:

- Hermes gateway;
- Hermes Cron;
- Hermes Kanban;
- long-term/canonical Hermes memory;
- persistent agent team profiles;
- recursive/internal delegation;
- target-project write tools;
- shell/code execution.

Hermes remains the long-term runtime because mobile/interactive Hermes is a planned later capability.

---

## 8. Hard budgets

Wall time alone is insufficient for a free multi-provider inference lane.

Every worker must enforce at least:

- `max_model_calls`;
- `max_tool_calls`;
- `max_wall_seconds`;
- max retries;
- max concurrent tasks.

Initial targets:

```text
max_model_calls: 12
max_tool_calls: 20
max_wall_minutes: 10
max_retries: 1
concurrent_tasks: 1
```

FreeLLMAPI retries/failover must also be bounded by its own configured retry/wall-clock behavior.

Cost rule:

> **budget/credits exhausted -> fail closed; never silently switch to paid capacity.**

---

## 9. Data classification

### PUBLIC_NON_PERSONAL — permitted in generic FreeLLMAPI pool

- public technical documentation;
- public vendor/product information not about natural persons;
- public standards/specifications;
- public repositories without private/sensitive context;
- synthetic data;
- non-sensitive generated fixtures.

### Not permitted by default in generic free pool

- public data about identifiable natural persons;
- sole-trader/person-linked prospect data;
- proprietary source code;
- internal business information;
- personal data;
- client/customer content.

### Never through generic free pool

- credentials/secrets;
- production DB contents;
- unredacted sensitive legal/care documents;
- regulated/high-impact personal dossiers.

The first pilot therefore uses non-personal technology/product/standard research, not SolidDesign prospecting.

---

## 10. Result and provenance

The first result schema remains simple. It must include at least:

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
    "freellmapi_version": "...",
    "requested_model_or_route": "...",
    "actual_provider": "...",
    "actual_model": "...",
    "route_switches": []
  },
  "usage": {
    "model_calls": 0,
    "tool_calls": 0,
    "wall_seconds": 0
  }
}
```

Provider/model fields are best-effort where upstream metadata exposes them. Missing provenance is itself observable and must not be silently fabricated.

Pinning software does not make dynamic routing reproducible. The architecture promises **runtime pinning plus inference accountability**, not identical model output.

---

## 11. Independent evidence verification

A separate trusted Modal Function verifies candidate results.

For every evidence URL:

1. strict schema validation;
2. allow only approved HTTP(S) schemes;
3. resolve hostname;
4. reject localhost, private, loopback, link-local and metadata ranges;
5. fetch with strict byte/time limits;
6. revalidate every redirect;
7. normalize text;
8. verify that the cited evidence/excerpt is actually present or otherwise deterministically supported.

The verifier accepts structured data only and never executes worker-provided code, scripts or arbitrary files.

The verifier can establish evidence presence. It must not pretend subjective business acceptance is deterministic.

---

## 12. Authority and state

Framework execution states:

```text
REJECTED
FAILED
PARTIAL
RESULT_READY
```

`RESULT_READY` means only that candidate execution completed sufficiently and required deterministic/evidence checks passed.

It does not mean business accepted, merged, published, sent, mission complete or `DONE`.

Caller/project/Control remains acceptance authority.

There is no framework DB, queue or business scheduler in v1.

| State | Canonical owner |
|---|---|
| project/business state | target project |
| Control mission lifecycle | Control |
| framework code/docs/config | GitHub |
| live Hermes invocation | Modal Function/process |
| Hermes bounded-session state | disposable |
| FreeLLMAPI provider config | declarative config + Modal Secrets |
| FreeLLMAPI quota/cooldown state | ephemeral in first proof; optional single-writer persistence later |
| result | caller after return/persistence |
| canonical skills/instructions | Git after review |

---

## 13. Phase-1 qualification

Run the same `PUBLIC_NON_PERSONAL` research task 20 times through:

```text
Hermes -> FreeLLMAPI -> configured provider pool
```

Measure:

- valid structured output rate;
- multi-step tool-loop completion;
- verified evidence rate;
- unsupported/hallucinated claim rate;
- model/tool calls per run;
- FreeLLMAPI route/fallback behavior;
- number of provider/model switches per run where observable;
- 429/5xx/provider failure behavior;
- retries;
- wall time;
- human usefulness against a manually checked baseline.

Initial go/no-go target: approximately >=70% human-usable runs, no secret/data-boundary violation, explicit failures and bounded resource usage.

If quality is poor, simplify the task/instructions or tune FreeLLMAPI routing/configuration. Do not add fan-out or more infrastructure to mask weak task/model fit.

---

## 14. Parallelism and later capability growth

After one-worker quality is proven, test two independent Hermes workers on the same objective. Measure quality/coverage uplift rather than merely throughput.

If parallelism earns its place, Modal owns framework fan-out. Hermes internal delegation remains disabled until hierarchical reasoning itself is separately justified.

Task-profile machinery is added only when a second materially different capability/data class exists. Until then least privilege is hardcoded in the one worker configuration.

A project publisher is added only after repeated handoff proves value and must be narrow, separate from workers and accept only independently verified results.

---

## 15. Mobile / interactive Hermes

Mobile control is a planned later capability and one reason Hermes is fixed as the runtime.

Target topology:

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
protected FreeLLMAPI service
        |
        v
configured provider pool
```

This interactive service has separate auth/session/memory/cold-start/approval concerns and must not become Control state, project truth or the bounded worker framework database.

---

## 16. Explicit non-goals for first proof

Do not build yet:

- Pydantic AI or any second runtime;
- harness bake-off;
- Modal Sandbox for fixed safe research tools;
- worker fan-out;
- Hermes recursive delegation;
- task-profile framework;
- framework database;
- queue/broker;
- generic business scheduler;
- persistent Hermes gateway;
- Hermes Cron/Kanban;
- canonical persistent Hermes memory;
- persistent FreeLLMAPI Volume unless measured need appears;
- Redis/Postgres for FreeLLMAPI;
- project publisher;
- production writes;
- mobile service before bounded carrier proof.

---

## 17. Definition of Done

Architecture/documentation is Done only when README, architecture and roadmap describe the same current model and obsolete conflicting current documentation is removed or explicitly historical.

A runtime phase is Done only when:

- its actual outcome is achieved;
- relevant behavior is tested;
- failure/security boundaries are exercised;
- usage/provenance metrics are captured;
- important runtime dependencies are pinned;
- unused/superseded implementation/config is removed;
- architecture/roadmap/README match deployed behavior;
- no known material inconsistency is knowingly left behind.

---

## 18. Upstream implementation facts to revalidate before coding

Before implementation pin and revalidate:

- Hermes one-shot/headless behavior and exact custom OpenAI-compatible path;
- FreeLLMAPI version and declarative startup config semantics;
- FreeLLMAPI actual route/provenance headers/metadata;
- FreeLLMAPI retry/sticky-session behavior on the chosen endpoint;
- Modal Function limits, endpoint authentication and secret handling;
- Modal pricing/free credit policy;
- Modal Volume semantics before any persistence is introduced.
