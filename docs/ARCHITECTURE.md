# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Status:** Target architecture / pre-implementation  
**Version:** 0.2  
**Date:** 2026-09-09  
**Canonical:** yes — this document is the single current architecture truth.

Historical/adversarial rationale is recorded in `docs/DESIGN_REVIEW_10_ITERATIONS.md`. That file explains decisions but does not override this document.

---

## 1. Objective

`agent` is a standalone, reusable execution framework for **bounded autonomous AI work across multiple projects**.

It exists to make tasks such as these cheap, parallel and reusable:

- public-web research and evidence collection;
- SolidDesign prospect discovery/qualification support;
- synthetic Scrub test generation and edge-case discovery;
- code, pull-request and architecture critique;
- documentation consistency checks;
- adversarial review;
- future project-specific bounded work.

Potential callers are:

- Control;
- a target project;
- a human operator;
- a future automation that already owns its own lifecycle.

The governing execution contract is:

> **bounded task + machine-enforced profile -> isolated autonomous execution -> independent verification -> result back to caller authority**

`agent` is an **execution carrier**, not:

- a Control replacement;
- a project CRM/database;
- a business workflow engine;
- a generic scheduler;
- a persistent multi-agent social system;
- a production authority plane.

The target project remains authoritative for its business state and irreversible actions. When Control is the caller, Control remains authoritative for mission lifecycle, scheduling, acceptance and successor decisions.

---

## 2. Governing engineering doctrine

This architecture follows the project-level Execution & Engineering Constitution.

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
- every dependency/state plane must earn its existence;
- one source of truth per concern;
- least privilege;
- treat untrusted model/web/repository input as hostile-capable;
- deterministic work stays deterministic;
- implementation is not Done without verification and cleanup;
- stale/conflicting architecture and code are removed rather than retained as parallel current truth.

Canonical expanded doctrine:

`https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit`

---

## 3. Core decision

### 3.1 Modal is the default execution substrate

V1 uses **Modal serverless compute**, not GitHub Actions or a VPS, as the headless runtime.

Reasons:

- no PC must remain online;
- no VPS patching/operations;
- scale to zero when idle;
- native isolated Sandboxes;
- native bounded parallel fan-out;
- explicit CPU/memory/time constraints;
- optional Volumes/snapshots if a later proven workload needs persistence;
- Starter currently includes a monthly free compute credit, suitable for experimentation when budgets are enforced.

GitHub remains the source of truth for code/configuration and is the deployment control surface. Modal is runtime, not source of truth.

### 3.2 Entire Hermes workers run inside Modal Sandboxes

Do **not** base v1 on Hermes' `terminal.backend: modal`.

That upstream mode keeps Hermes elsewhere and uses Modal only for terminal/file execution. It therefore does not provide the desired whole-agent headless cloud boundary and currently has open upstream reliability issues affecting remote Modal execution.

Instead:

```text
Modal Sandbox
  -> pinned Hermes process
       -> `hermes -z <task>` / one-shot
       -> local terminal/files inside Sandbox
```

The Modal Sandbox is the worker process-isolation boundary.

### 3.3 Modal owns parallel worker fan-out

V1 does not combine Modal-level fan-out with Hermes recursive subagent orchestration.

```text
Modal orchestrator
  -> Sandbox / Hermes worker A
  -> Sandbox / Hermes worker B
```

Hermes internal delegation is disabled in the first carrier proof.

Reason: one concurrency/failure authority is simpler and more observable than nested Modal workers plus Hermes children.

Hermes delegation becomes an evolution option only after measured evidence shows a benefit for hierarchical reasoning that Modal-level independent workers cannot provide simply.

---

## 4. Target architecture

```text
                 CONTROL / PROJECT / HUMAN
             objective + lifecycle + authority
                           |
                           | bounded task
                           v
                +-------------------------+
                | Modal orchestrator      |
                |                         |
                | validate task contract  |
                | resolve task profile    |
                | enforce worker budget   |
                | deterministic partition |
                +------------+------------+
                             |
                  bounded parallel fan-out
                             |
          +------------------+------------------+
          |                                     |
          v                                     v
+----------------------+              +----------------------+
| Modal Sandbox A      |              | Modal Sandbox B      |
| UNTRUSTED WORKER     |              | UNTRUSTED WORKER     |
|                      |              |                      |
| pinned Hermes        |              | pinned Hermes        |
| headless one-shot    |              | headless one-shot    |
| local task tools     |              | local task tools     |
| no target write key  |              | no target write key  |
+----------+-----------+              +-----------+----------+
           |                                          |
           | inference only                           |
           +-------------------+----------------------+
                               |
                               v
                 +-----------------------------+
                 | Protected FreeLLMAPI        |
                 | Modal service               |
                 |                             |
                 | approved provider pool      |
                 | upstream provider keys      |
                 | max active replica: 1       |
                 +-------------+---------------+
                               |
                               v
                    approved model providers

Worker candidate results
           |
           v
+-----------------------------+
| Trusted verifier            |
| separate Modal Function     |
|                             |
| schema                      |
| deterministic checks        |
| evidence/provenance checks  |
+-------------+---------------+
              |
         RESULT_READY
              |
              v
      CALLER / PROJECT AUTHORITY
  accepts / rejects / persists / acts
```

---

## 5. Component responsibilities

| Component | Owns | Does not own |
|---|---|---|
| Caller / Control / project | objective, lifecycle, durable business state, acceptance | worker implementation, provider routing |
| GitHub `agent` repo | architecture, contracts, task profiles, runtime/deployment code, version history | live business state |
| Modal orchestrator | contract/profile enforcement, deterministic partition, worker creation, resource limits | project acceptance |
| Modal Sandbox/Hermes | bounded reasoning/tool execution | production authority, durable project truth |
| FreeLLMAPI | approved provider/model routing, quota/cooldown behavior within its available state | task planning, business decisions |
| Trusted verifier | deterministic/schema/evidence checks | subjective business acceptance |
| Target project | canonical business data and final actions | generic worker orchestration |

---

## 6. Invocation and task contract

### 6.1 V1 invocation

Do not build a generic public task API, queue or dashboard before the carrier works.

The first carrier may be invoked through Modal's native deployment/client mechanisms or a minimal operator entry point.

Control/project integration is added after the carrier proof, reusing the same task/result contract.

### 6.2 Task contract

A task describes **what outcome is requested**, not its security authority.

Conceptual form:

```json
{
  "contract_version": "1",
  "task_id": "caller-stable-id",
  "profile": "public-research-v1",
  "objective": "Find and evidence candidate businesses in Rotterdam",
  "inputs": {
    "sector": "loodgieters",
    "location": "Rotterdam"
  },
  "requested_limits": {
    "max_workers": 2,
    "max_wall_minutes": 45
  },
  "output_schema": "research-result-v1"
}
```

Natural-language objective text is **not** a permission system.

---

## 7. Machine-enforced task profiles

V1 introduces exactly one small policy mechanism: a Git-backed task profile.

Example:

```yaml
id: public-research-v1
data_class: PUBLIC
network: PUBLIC_WEB
target_mutation: NONE
inference_lane: FREE_PUBLIC
max_workers: 2
max_wall_minutes: 45
```

Rules:

- profiles are repository-controlled canonical configuration;
- the orchestrator resolves the profile before creating workers;
- callers may request stricter limits but may not dynamically widen profile authority;
- Hermes receives the resulting capability environment, not the authority to choose its own environment;
- v1 does not implement a generic policy DSL, role builder or plugin permission system.

Task profiles exist because model instructions cannot be a security boundary.

---

## 8. Worker lifecycle

Each worker is disposable.

```text
1. CREATE Sandbox
2. load pinned worker image
3. inject bounded task/profile context
4. inject FreeLLMAPI client credentials only
5. run headless Hermes one-shot
6. require structured result file/output
7. collect result + usage/provenance metadata
8. terminate Sandbox
```

Default worker rules:

- one Hermes process per Sandbox;
- no Hermes gateway;
- no Hermes Cron;
- no Hermes Kanban/profile team;
- no canonical long-term Hermes memory;
- no nested delegation in v1;
- no target-project write credentials;
- no Docker socket;
- explicit CPU/memory/time caps;
- outbound network only as required by the selected profile.

Hermes memory/skills may generate proposed improvements, but no worker may silently mutate canonical framework instructions. Durable skill changes become reviewed Git changes.

---

## 9. Deterministic work versus agent work

Use code/native functions for anything that does not require semantic judgment.

### Deterministic

- schema validation;
- input normalization;
- exact partitioning;
- deduplication;
- URL syntax/allowlist checks;
- hashing;
- test execution;
- builds/lint/type checks;
- result packaging;
- hard resource limits.

### Agent/Hermes

- research;
- qualitative classification;
- design/website critique;
- code/architecture reasoning;
- adversarial review;
- hypothesis generation;
- synthesis across evidence.

The framework must not spend LLM tokens on a problem solved more reliably by a normal function.

---

## 10. FreeLLMAPI inference boundary

### 10.1 Why it is separate

FreeLLMAPI runs outside worker Sandboxes so compromised workers do not automatically receive all upstream provider keys.

Worker receives only:

- protected FreeLLMAPI URL;
- FreeLLMAPI unified bearer/token;
- Modal proxy-auth material required for that endpoint.

FreeLLMAPI receives:

- provider keys;
- its own encryption material;
- approved provider configuration.

FreeLLMAPI receives **no target-project production credentials**.

Hermes supports custom OpenAI-compatible endpoints and custom extra headers, so the protected gateway does not require a custom provider adapter.

### 10.2 Provider policy

Do not enable every provider.

Start with a small allowlisted pool selected for:

- current terms of service;
- public/synthetic data suitability;
- tool-call quality;
- model quality;
- quota/availability;
- reliable OpenAI-compatible behavior.

Free capacity is optimization, not an SLA.

### 10.3 V1 persistence policy

Do **not** require persistent FreeLLMAPI SQLite state for the first carrier proof.

V1:

- protected service;
- maximum active FreeLLMAPI replica = 1;
- quota/cooldown state may reset when the service fully cold-starts;
- conservative per-task limits;
- provider quota exhaustion is expected degraded behavior.

Why not persist immediately:

- Modal Volumes require explicit commit/reload semantics;
- they are not a distributed database;
- concurrent modification of the same SQLite file is unsafe as an architectural assumption;
- persistence is unnecessary before proving useful workload economics.

Evolution trigger: if measured lost quota/cooldown knowledge materially wastes free capacity, add exactly one persistent Volume and keep FreeLLMAPI single-writer.

Do not add Redis/Postgres merely to make FreeLLMAPI horizontally scalable.

### 10.4 Routing reproducibility

- pin the exact FreeLLMAPI release/image digest;
- use an exact tested wire path from Hermes;
- prefer explicit tested routing over clever virtual profiles initially;
- log actual served provider/model metadata where available;
- prompt compression off initially;
- persistent response cache off initially;
- Fusion only for candidate critique/synthesis, never authority;
- route substitution/degradation must be observable in result metadata.

---

## 11. Security and trust boundaries

### 11.1 Core assumption

Hermes workers process potentially hostile:

- public websites;
- repository content;
- documents;
- model output;
- tool output.

Prompt injection and incorrect reasoning are expected threat classes.

Security rule:

> **Do not rely on the model to protect a credential it never needed to receive.**

### 11.2 Worker secrets

Workers must not receive by default:

- Supabase service-role keys;
- production database passwords;
- Cloudflare production credentials;
- unrestricted GitHub PATs;
- deployment credentials;
- upstream FreeLLM provider keys;
- unrelated-project secrets;
- customer/client credentials.

A fully compromised worker should have a bounded blast radius: its own temporary files, task data, public-web access allowed by the profile, and a revocable inference-gateway credential.

### 11.3 Modal endpoint protection

The FreeLLMAPI service must use Modal's native endpoint proxy authentication plus FreeLLMAPI's own bearer/authentication.

Do not publish an unauthenticated FreeLLMAPI endpoint or dashboard.

### 11.4 Private project source

V1 does not solve proprietary/private-repository execution.

Future private-source integration must stage an exact source snapshot into the worker without leaving broad repository credentials available to Hermes. Prefer caller-side/preparation capabilities over giving a worker a reusable GitHub token.

Do not design a generic credential broker preemptively.

---

## 12. Data classification

### FREE_PUBLIC inference lane — allowed by default

- public web data;
- public repositories;
- public documentation;
- synthetic data;
- non-sensitive generated fixtures;
- non-sensitive bounded project context.

### Requires explicit provider/privacy approval

- proprietary private source code;
- internal non-public business information;
- personal data;
- client/customer content.

### Not sent through generic free-provider pool

- credentials/secrets;
- production database contents;
- unredacted sensitive legal/care documents;
- regulated/high-impact personal dossiers.

Modal compute isolation does not change upstream LLM-provider privacy obligations.

---

## 13. Result and authority model

The framework produces candidate work/evidence.

Framework execution statuses are limited to:

```text
REJECTED
FAILED
PARTIAL
RESULT_READY
```

`RESULT_READY` means:

- worker execution completed enough to produce candidate output;
- the result contract passed the applicable independent verification.

It does **not** mean:

- commercially accepted;
- merged;
- published;
- sent;
- mission complete;
- business `DONE`.

Those remain caller/project authority.

Every result should contain, where applicable:

- task ID;
- contract/profile versions;
- framework Git SHA;
- Hermes version/commit;
- FreeLLMAPI version/digest;
- worker count;
- actual execution status;
- structured result;
- evidence/provenance;
- deterministic verification result;
- provider/model routing metadata where available;
- degraded/failure information;
- runtime and resource/usage metrics.

---

## 14. Independent verification

The verifier is a separate trusted Modal Function, not the Hermes worker that generated the result.

It may perform:

- schema validation;
- mandatory-field checks;
- duplicate checks;
- URL/evidence shape checks;
- hashes;
- deterministic tests;
- exact acceptance checks that can actually be machine verified.

It may not turn subjective business judgment into fake determinism.

V1 has **no publisher** and no target-project mutation capability.

A future project-specific publisher must:

- run outside worker Sandboxes;
- receive a narrow project capability only;
- accept only an independently verified result contract;
- expose only the exact operation required;
- never become a general database/admin proxy.

---

## 15. State model

There is no framework database in v1.

| State | Canonical owner |
|---|---|
| project/business state | target project |
| Control mission/task lifecycle | Control |
| framework architecture/contracts/profiles | `market-predictions/agent` Git |
| live worker state | Modal Sandbox/process |
| current invocation | Modal Function execution |
| worker conversational state | disposable |
| result | caller after return/persistence |
| FreeLLM quota/cooldown state | ephemeral in v1; optional single-writer Volume later |
| canonical learned skills | Git after review |

Do not create a second durable state plane because an agent framework happens to be capable of one.

---

## 16. Scheduling

V1 has no framework-owned business scheduler.

Rules:

- if Control owns lifecycle, Control triggers work;
- if a target project owns lifecycle, that project triggers work;
- a human may manually invoke the pilot;
- Modal Schedule is only considered for a truly standalone routine with no existing lifecycle owner.

Do not combine Modal Schedule with a persistent Hermes gateway and Hermes Cron for the same workload.

---

## 17. Mobile / interactive Hermes

A phone-accessible Hermes is technically possible but is **not part of v1**.

Current Hermes exposes an OpenAI-compatible API server through `hermes gateway`, and Modal can expose authenticated serverless HTTP services. A later dedicated interactive adapter could therefore use:

```text
phone / mobile web client
        |
        v
protected Modal web endpoint
        |
        v
dedicated interactive Hermes service
        |
        v
same protected FreeLLMAPI service
```

This future service would require separate decisions for:

- session persistence;
- `~/.hermes/state.db`;
- concurrency/max containers;
- cold-start client retries;
- memory scope;
- mobile authentication;
- interactive approval UX.

It must not become the execution carrier's project state or Control authority.

Do not build it until the worker carrier is proven and interactive access is a concrete requirement.

---

## 18. Project integration patterns

### 18.1 Control

```text
Control authority
   -> bounded task/profile
   -> Modal agent carrier
   -> RESULT_READY evidence
   -> Control verification/acceptance/successor
```

No second Control queue, scheduler or mission state exists in `agent`.

### 18.2 SolidDesign

Initial use:

- public-web prospect research;
- independent workers cover separate partitions;
- qualitative opportunity assessment;
- deterministic dedupe/validation;
- result returned as JSON/CSV/artifact;
- no autonomous promotion;
- no production database credentials in workers.

### 18.3 Scrub

Initial use:

- generate synthetic adversarial documents;
- discover masking/entity edge cases;
- review public/source code where data policy permits;
- propose deterministic regression cases.

Real unredacted legal/care documents are outside the generic FREE_PUBLIC lane.

### 18.4 Future projects

Reuse the same contract/profile/result boundary.

Do not create a generic plugin/adapter framework in advance. Add a project-specific handoff only when a real project proves the need.

---

## 19. Failure and degraded-mode behavior

Fail closed for authority; fail honestly for capacity.

Examples:

- invalid task/profile -> `REJECTED`;
- provider quota exhausted -> FreeLLMAPI may use another approved route;
- all approved inference unavailable -> `FAILED` or `PARTIAL`, never fabricated success;
- one independent worker fails -> collect remaining results and mark `PARTIAL` if contract allows;
- worker timeout -> terminate Sandbox and report it;
- verifier rejects schema/evidence -> not `RESULT_READY`;
- caller/project unavailable after result -> caller-specific persistence/retry concern, not justification for a generic framework DB;
- requested capability exceeds profile -> reject before worker creation.

A weaker model does not gain more authority because it is available.

---

## 20. Cost and resource control

Modal's free Starter credits are a **budget**, not unlimited infrastructure.

V1 defaults:

- 2 workers;
- max worker depth: none/0 internal delegation;
- bounded CPU and memory;
- 30–45 minute worker wall budget for first pilot;
- max one FreeLLMAPI service container;
- explicit task-level worker/runtime limits;
- collect Modal runtime/usage metrics after every pilot.

Optimization target:

> **accepted useful output per unit of compute/inference**, not maximum agents or nominal token volume.

Raise concurrency only after measured quality/throughput justifies it.

---

## 21. Supply-chain and reproducibility rules

Do not execute floating upstream software in authoritative tests.

Pin:

- exact Hermes release/commit;
- exact FreeLLMAPI release/container digest;
- exact Modal SDK version;
- base image and important dependencies;
- framework Git SHA.

Do not use `latest` as the production/review identity.

Hermes and FreeLLMAPI are fast-moving upstream dependencies. Upgrades require:

1. explicit version change;
2. carrier integration test;
3. security/behavior regression check;
4. documentation update if assumptions changed.

The first integration test must prove the exact Hermes custom OpenAI-compatible request path against the pinned FreeLLMAPI build, including tool calls and route observability.

---

## 22. V1 carrier proof

The first implementation is deliberately one use case.

### Pilot

**Task:** public-web candidate-company research for one sector/location.  
**Data class:** PUBLIC.  
**Authority:** artifact/result only; no project mutation.

### Execution

```text
manual/caller invocation
  -> task/profile validation
  -> deterministic split into 2 partitions
  -> 2 Modal Sandboxes
  -> pinned Hermes one-shot in each
  -> protected pinned FreeLLMAPI
  -> structured worker results
  -> deterministic verifier
  -> RESULT_READY
```

### Initial worker limits

- workers: 2;
- internal Hermes delegation: disabled;
- CPU: start small, measure;
- memory: start small, measure;
- wall time: max 45 minutes per worker;
- target credentials: none;
- public web only;
- output: versioned JSON plus human-readable summary.

### Carrier proof success criteria

1. whole Hermes process runs headlessly inside Modal without PC/VPS dependency;
2. both workers are independently isolated and bounded;
3. FreeLLMAPI provider keys are not exposed to workers;
4. tool calls work on the exact pinned Hermes -> FreeLLMAPI route;
5. result contract validates;
6. failures/timeouts are explicit, not silently successful;
7. actual model/provider provenance is captured where available;
8. compute/inference usage is measured;
9. useful result quality is compared with a single-worker baseline;
10. no target-project write capability exists.

Only after this proof is green may the framework add another task class or automated caller integration.

---

## 23. Explicit v1 non-goals

Do not build:

- VPS;
- GitHub Actions as worker compute;
- Kubernetes;
- Redis;
- queue/broker;
- framework database;
- vector database;
- generic task dashboard;
- generic RBAC/policy builder;
- custom model router;
- persistent Hermes gateway;
- Hermes Cron;
- Hermes Kanban/profile team;
- recursive swarms;
- canonical Hermes memory store;
- interactive/mobile Hermes service;
- project publisher;
- autonomous production deployment;
- autonomous database administration;
- target-project production write credentials in workers;
- persistent FreeLLMAPI Volume before measured need;
- horizontally scaled FreeLLMAPI over one SQLite file;
- project adapter/plugin registry.

---

## 24. Evolution triggers

Architecture grows only after measured limitation.

| Observed need | Candidate evolution |
|---|---|
| lost FreeLLM quota/cooldown state materially wastes capacity | one persistent single-writer FreeLLMAPI Modal Volume |
| a task benefits materially from hierarchical reasoning | enable bounded Hermes internal delegation for that profile only |
| private source analysis is required | add credential-free source staging with approved private inference lane |
| repeated target handoff is valuable | one narrow project-specific publisher capability |
| interactive phone access is a real requirement | separate authenticated interactive Hermes Modal service |
| caller needs asynchronous durable task status | add the smallest caller-owned/checkpoint mechanism; do not default to framework DB |
| 2 workers are a measured throughput bottleneck | raise profile concurrency within cost/security limits |
| free-provider quality is insufficient | approved paid/frontier inference lane |

The existence of a possible future need is not evidence to implement it now.

---

## 25. Architectural invariants

1. Target projects own their business truth.
2. Control owns Control mission authority when it is the caller.
3. `agent` is an execution carrier, not a competing control plane.
4. GitHub is canonical for framework architecture/code/contracts/profiles.
5. Modal is runtime, not canonical source state.
6. Modal owns v1 worker fan-out.
7. One fresh Sandbox contains one complete headless Hermes worker.
8. Hermes' remote Modal terminal backend is not a v1 dependency.
9. Hermes internal delegation is disabled in the first carrier.
10. Worker authority comes from machine-enforced profiles, not prompt prose.
11. Worker Sandboxes are untrusted.
12. Workers receive no target-project production write credentials.
13. Upstream inference-provider keys remain outside worker Sandboxes.
14. FreeLLMAPI is an inference gateway, not task/business authority.
15. FreeLLMAPI provider access is allowlisted.
16. No framework database/queue exists without observed need.
17. Conversational memory is disposable by default.
18. Canonical skills/instructions change only through Git review/change control.
19. Deterministic work remains deterministic.
20. Result verification is separate from worker generation.
21. `RESULT_READY` is not business `DONE`.
22. V1 has no project publisher or direct production mutation.
23. Public/free inference handles only approved data classes.
24. All important runtime dependencies are pinned.
25. Done requires implementation + verification + cleanup + documentation alignment.

---

## 26. Definition of Done

### Architecture/documentation change is Done when

- this document reflects the current target architecture;
- README points to this document and contains no conflicting topology;
- design rationale is clearly marked non-canonical;
- obsolete GitHub-Actions-first architecture is no longer presented as current;
- no stale/conflicting current documentation remains.

### V1 implementation will be Done only when

- the carrier proof success criteria in section 22 are met;
- tests verify contract/profile enforcement and result validation;
- exact runtime dependencies are pinned;
- security boundaries are exercised, not just documented;
- relevant regressions are checked;
- unused/superseded code/config is removed;
- architecture/README/status match actual deployed behavior;
- no known material inconsistency is knowingly left behind.

---

## 27. Current upstream assumptions to revalidate before implementation

As of 2026-09-09:

- Modal Starter advertises monthly free compute credits and serverless scale-to-zero behavior;
- Modal Sandboxes provide isolated cloud containers and optional persistent Volumes/snapshots;
- Modal Volumes require explicit synchronization and are not a distributed-locking database;
- Hermes supports scripted one-shot execution via `hermes -z` / `--oneshot`;
- Hermes supports custom OpenAI-compatible providers and extra request headers;
- Hermes documents a Modal terminal backend, but v1 intentionally does not rely on it;
- Hermes has current open issues affecting its remote Modal backend, reinforcing whole-process Sandbox containment;
- FreeLLMAPI v0.9.x provides OpenAI-compatible routing and SQLite-backed quota/cooldown tracking;
- FreeLLMAPI is local-first/single-user in upstream scope and therefore must be protected when deployed remotely.

These are implementation dependencies, not permanent architecture truths. Revalidate them when pinning the first carrier versions.

### Reference implementations/documentation

- Hermes Agent: `https://github.com/NousResearch/hermes-agent`
- Hermes CLI one-shot: `https://hermes-agent.nousresearch.com/docs/reference/cli-commands`
- Hermes custom providers: `https://hermes-agent.nousresearch.com/docs/user-guide/configuring-models`
- Modal: `https://modal.com/docs`
- Modal Sandboxes: `https://modal.com/products/sandboxes`
- Modal pricing: `https://modal.com/pricing`
- FreeLLMAPI: `https://github.com/tashfeenahmed/freellmapi`
