# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Status:** Target architecture / pre-implementation  
**Version:** 0.1  
**Date:** 2026-09-09

## 1. Purpose

`agent` is a standalone, reusable execution framework for bounded autonomous AI work across multiple projects.

It is not a SolidDesign extension, a Control replacement, a second project database, or a new business workflow engine. It provides an execution capability that can be invoked by:

- Control;
- individual project repositories;
- a human operator;
- scheduled framework-owned jobs where no other system already owns the schedule.

Examples include:

- discovering and evaluating candidate businesses for SolidDesign;
- generating synthetic adversarial documents and test cases for Scrub;
- reviewing code, pull requests, architecture and tests;
- research and evidence collection;
- documentation consistency checks;
- future bounded tasks for projects that do not yet exist.

The governing principle is:

> **Task contract in -> isolated autonomous execution -> validated evidence/result out.**

The target project remains authoritative for its own business state, permissions, acceptance criteria and production actions.

## 2. Governing doctrine

This architecture follows the project-level **Execution & Engineering Constitution**:

- business outcome first;
- solid but simple;
- no overengineering;
- first-principles reasoning;
- prefer proven/native capabilities;
- one clear source of truth;
- least privilege;
- verification is part of implementation;
- autonomous execution continues until the objective is achieved or genuinely blocked.

Canonical master:

`https://docs.google.com/document/d/1Zf9DvT282-EDsU-SoXinJKQX5LcQC2wabkoTL0doDh0/edit`

## 3. Architectural position

The framework occupies an **execution layer**, not an authority layer.

```text
PROJECT / CONTROL / HUMAN
        |
        | bounded task contract
        v
+--------------------------------------------------+
| market-predictions/agent                         |
|                                                  |
| GitHub Actions                                   |
| - trigger / ephemeral compute                    |
| - trusted prepare + validate + publish steps     |
|                                                  |
|        +----------------------------------+      |
|        | UNTRUSTED AGENT EXECUTION       |      |
|        |                                  |      |
|        | Hermes supervisor                |      |
|        |   |                              |      |
|        |   +-- worker A                   |      |
|        |   +-- worker B                   |      |
|        |   +-- worker C                   |      |
|        |                                  |      |
|        | FreeLLMAPI inference sidecar     |      |
|        +----------------+-----------------+      |
|                         |                        |
|                  structured output               |
|                         v                        |
|        deterministic validation / packaging      |
+-------------------------+------------------------+
                          |
                          | artifact / bounded handoff
                          v
              PROJECT SOURCE OF TRUTH
```

### Layer responsibilities

| Layer | Responsibility | Explicitly not responsible for |
|---|---|---|
| Control / caller | objective, authority, lifecycle, acceptance | model routing, worker implementation |
| Agent framework | execute bounded work, isolate agents, package evidence | owning project business state |
| Hermes | agent loop, tools, delegation, parallel reasoning | production authority |
| FreeLLMAPI | model/provider routing, quota/failover | task planning or project decisions |
| Target project | canonical state and final business action | generic agent orchestration |

## 4. Primary deployment model

### 4.1 GitHub Actions is the default compute substrate

Version 1 uses GitHub-hosted ephemeral Actions runners rather than an always-on VPS.

Reasons:

- the repository is public and standard GitHub-hosted runners are currently free for public repositories;
- each normal hosted job receives a fresh VM;
- no local PC must remain online;
- no server patching, daemon management or idle infrastructure is required;
- bounded agent jobs naturally fit ephemeral execution;
- the framework can move to another compute backend later without changing the task boundary.

GitHub-hosted jobs currently have a six-hour maximum execution time. A task that cannot complete within a bounded run must checkpoint externally or be decomposed into successor tasks; the framework must not depend on an immortal process.

### 4.2 No persistent framework server in v1

Do not add by default:

- VPS;
- Kubernetes;
- Redis;
- message broker;
- framework database;
- vector database;
- permanent Hermes gateway;
- permanent FreeLLMAPI service;
- second scheduler when the caller already owns scheduling.

These may be introduced only after an observed requirement proves GitHub Actions insufficient.

## 5. Invocation model

One canonical task contract is used regardless of caller.

### 5.1 Supported ingress

Initial ingress surfaces:

1. **`workflow_dispatch`** — human/manual execution and early pilots.
2. **`repository_dispatch`** — machine invocation from Control or another project.
3. **`schedule`** — only for standalone routines whose schedule is owned by this framework.

If Control owns a mission/task lifecycle, the framework must not create a competing internal queue or scheduler for that same work. Control dispatches the bounded task and remains authoritative for its lifecycle.

### 5.2 Task contract

The exact machine schema will be versioned before implementation. Conceptually every task contains:

```json
{
  "contract_version": "1",
  "task_id": "caller-stable-id",
  "caller": "control-or-project",
  "project": "soliddesign",
  "task_type": "research",
  "objective": "Build a validated pool of candidate businesses",
  "source": {
    "repository": "solidprivacy-nl/soliddesign",
    "ref": "main"
  },
  "constraints": [
    "no production mutations",
    "public data only"
  ],
  "acceptance": [
    "output conforms to declared result schema",
    "each candidate has source evidence"
  ],
  "output_mode": "artifact"
}
```

The contract contains the objective and boundaries, not an implementation script. Hermes may determine the execution plan inside those boundaries.

Large source material is referenced by exact repository/ref/artifact identifiers rather than embedded into dispatch payloads.

## 6. Execution lifecycle

A run is deliberately staged so secrets and authority do not cross into the agent zone.

```text
1. RECEIVE
   task contract
      |
2. VALIDATE
   schema + caller + bounds
      |
3. PREPARE [trusted]
   exact source/ref -> workspace
   credentials removed after preparation
      |
4. EXECUTE [untrusted]
   Hermes supervisor
   -> bounded parallel workers
   -> FreeLLMAPI
      |
5. COLLECT
   structured candidate result
      |
6. TERMINATE AGENT ZONE
   stop/remove Hermes workers
      |
7. VERIFY [trusted]
   schema / deterministic checks / tests / dedupe
      |
8. PUBLISH [trusted]
   artifact by default
   optional narrowly bounded target capability
      |
9. RETURN
   result + evidence + status to caller
```

The agent zone is destroyed **before** any target-project write credential is introduced.

## 7. Hermes execution model

Hermes is the default agent runtime because it provides tool use, autonomous agent loops and parallel delegation while remaining model-provider agnostic.

### 7.1 Flat swarm by default

Version 1 uses a flat supervisor/worker topology:

```text
Hermes supervisor
    |
    +-- worker 1
    +-- worker 2
    +-- worker 3
    +-- worker 4
```

Rules:

- delegation depth is `1` by default;
- workers do not recursively spawn their own swarms;
- initial concurrency is small and explicitly capped;
- increase concurrency only after measuring provider quota, runner resources and result quality;
- parallelism is used when workstreams are materially independent.

This avoids exponential fan-out, duplicated work and opaque authority.

### 7.2 Agents are for judgment, not commodity mechanics

Use deterministic code for:

- schema validation;
- normalization;
- deduplication;
- URL syntax checks;
- exact filtering;
- hashing;
- test execution;
- builds/lint/type checks;
- result packaging.

Use agents for:

- research;
- classification where rules are insufficient;
- qualitative website/design analysis;
- code/architecture critique;
- adversarial review;
- hypothesis generation;
- synthesis across evidence.

Do not spend LLM tokens on work a simple deterministic function can perform more reliably.

### 7.3 Memory and self-improvement

Hermes memory or self-generated skills are **not** an authoritative state plane.

On ephemeral runners:

- conversational memory is disposable by default;
- a worker may propose a learned skill or improved instruction as output;
- no agent may silently persist or mutate canonical framework skills;
- durable skills/instructions become repository content only through normal Git review/change control.

This preserves reproducibility and prevents autonomous instruction drift.

## 8. FreeLLMAPI inference layer

FreeLLMAPI is the default model gateway beneath Hermes.

Its role is narrow:

- expose one compatible inference endpoint;
- route across an explicitly approved provider pool;
- track quotas/rate limits;
- fail over when providers are unavailable;
- make low-cost parallel agent execution economically practical.

It does **not** become an agent framework, task authority, project database or reliability guarantee.

### 8.1 Provider policy

Do not enable every available provider merely because it is supported.

Start with a small approved set and evaluate each provider for:

- model/tool-call quality;
- quota and availability;
- terms of service;
- data retention/training policy;
- privacy/security suitability;
- task-specific quality.

Free-tier routing has variable capacity, latency and effective model intelligence. No task may assume a specific model class is continuously available.

### 8.2 Routing policy

Default principles:

- use explicit, tested routing behavior;
- log the actually routed model/provider when available;
- keep prompt compression off initially, or use only a proven lossless mode;
- keep persistent response caching off initially;
- use multi-model/Fusion only for candidate analysis or critique, never as release/business authority;
- pin framework versions and test upgrades rather than tracking unverified latest behavior.

## 9. Security and trust boundaries

### 9.1 Treat the agent zone as untrusted

Hermes processes untrusted websites, repositories, documents and LLM outputs. Therefore prompt injection, malformed content or incorrect agent reasoning are expected threat classes.

The security rule is:

> **Do not rely on the model to protect secrets it never needed to receive.**

### 9.2 No target-project secrets in Hermes

Hermes must not receive by default:

- Supabase service-role or database credentials;
- Cloudflare production credentials;
- unrestricted GitHub PATs;
- deployment secrets;
- production API keys;
- customer/client secrets;
- credentials for unrelated projects.

For private source repositories, a trusted preparation step fetches the exact required ref and then provides a credential-free workspace to the worker.

### 9.3 Isolate FreeLLMAPI provider credentials

FreeLLMAPI runs as a sidecar/container separated from Hermes.

Hermes receives only the local gateway endpoint and the minimum unified gateway credential required to request inference. It receives neither upstream provider keys nor Docker/host control.

Worker container requirements:

- no Docker socket;
- no host PID namespace;
- no host home-directory mount;
- only required workspace mounts;
- explicit CPU/memory/time limits;
- no target-project write credentials;
- outbound network only where the task requires it.

### 9.4 Data classification

Default FreeLLMAPI/free-provider lane:

**Allowed by default**

- public web data;
- public repositories;
- synthetic data;
- non-sensitive generated test fixtures;
- public documentation;
- bounded non-sensitive project context.

**Requires explicit provider/privacy approval**

- proprietary private source code;
- internal business information;
- personal data;
- client/customer content.

**Not routed through the generic free-provider pool**

- credentials/secrets;
- production database contents;
- unredacted sensitive legal/care documents;
- regulated or high-impact personal dossiers.

A task that needs restricted data must use an explicitly approved model/provider lane or remain outside this framework until such a lane exists.

## 10. Output and authority model

The framework returns **candidate work products and evidence**. It does not silently make irreversible project decisions.

### 10.1 Default output: artifact

Every run produces a structured result artifact containing at least:

- task ID and contract version;
- outcome/status;
- structured result;
- evidence/provenance references;
- validation results;
- model/router metadata where available;
- errors/degraded-mode information;
- timing/usage metrics where available.

GitHub workflow logs are operational evidence, not the durable project source of truth.

### 10.2 Supported delivery classes

From safest to most privileged:

1. **Artifact only** — default and initial pilot mode.
2. **Issue/comment/report** — bounded GitHub output.
3. **Project ingest capability** — narrow API such as “submit discovery candidate”.
4. **Proposed code change** — future: patch/PR only, never autonomous merge by default.
5. **Direct production mutation** — excluded from the baseline architecture.

Every higher privilege requires a concrete project-specific need and separate least-privilege review.

### 10.3 Trusted publisher

If a project later needs automated handoff, a separate trusted publishing step owns the target credential.

Example:

```text
Hermes swarm
    |
    v
candidates.json
    |
    v
deterministic validator
    |
    v
[Hermes containers terminated]
    |
    v
trusted publisher + narrow secret
    |
    v
project ingest API
```

The agent must not be able to call the privileged publisher with arbitrary parameters outside the validated result contract.

## 11. Project integration patterns

### 11.1 Control

Control may use the framework as a bounded execution carrier.

```text
Control authority
   |
   | task contract
   v
Agent framework
   |
   | evidence/result
   v
Control verification / successor decision
```

Control remains authoritative for mission state, scheduling and acceptance when it is the caller. `agent` must not introduce a competing Control queue, state machine or semantic authority.

### 11.2 SolidDesign

Example use:

- parallel discovery agents identify candidate businesses;
- specialist agents assess website/design/commercial opportunity;
- deterministic code validates, normalizes and deduplicates;
- result is initially exported as a contract-valid artifact/CSV;
- later, a narrow trusted publisher may submit candidates into SolidDesign's existing Discovery ingest;
- human/project authority retains promotion/rejection.

Hermes receives no SolidDesign production database credential.

### 11.3 Scrub

Example use:

- generate synthetic adversarial documents;
- discover masking/entity edge cases;
- review code/tests;
- propose regression cases.

The generic free-provider lane must not receive unredacted sensitive legal/care source documents.

### 11.4 Future projects

New integrations reuse the same task and result boundaries. Do not build a generic plugin platform in advance.

A project-specific adapter is added only when the project requires a capability that cannot be expressed through the existing contract/artifact model.

## 12. State model

There is no framework database in version 1.

Canonical state remains distributed by responsibility:

| State | Canonical owner |
|---|---|
| project/business data | target project |
| Control mission/task lifecycle | Control |
| framework code/config/skills | `market-predictions/agent` Git repository |
| current execution | GitHub Actions run |
| run output | artifact until caller persists it |
| provider quota ledger during run | FreeLLMAPI runtime |

If durable cross-run agent state becomes necessary, first determine whether it belongs in the caller/project. Add framework-owned durable state only when no existing authority is correct for it.

## 13. Failure and degraded-mode behavior

The framework is fail-closed for authority and fail-soft for research capacity.

Examples:

- provider quota exhausted -> FreeLLMAPI may route to another approved provider;
- all suitable providers unavailable -> task reports `BLOCKED`/`DEGRADED`, not fabricated success;
- worker fails -> other independent workers may complete; supervisor reports partial evidence;
- result schema invalid -> trusted publisher refuses handoff;
- target project unavailable -> preserve validated artifact and report delivery failure;
- GitHub runner reaches time budget -> return checkpoint/partial result if contract permits, otherwise fail without claiming completion;
- requested capability exceeds task contract -> reject it.

A weaker fallback model may discover or draft evidence, but must never gain additional authority because a stronger model is unavailable.

## 14. Verification and observability

A framework run is not successful merely because Hermes exits with code `0`.

Where applicable capture:

- exact task contract/version;
- exact source repository/ref/commit;
- Hermes and FreeLLMAPI versions;
- actual model/provider route metadata;
- worker count and task decomposition summary;
- deterministic validation/test results;
- structured final status;
- artifacts and hashes;
- failure/degraded conditions.

Evaluation must be task-class specific. Initial adoption should compare the framework against historical real tasks for:

- valid findings/results;
- false-positive rate;
- duplicate rate;
- acceptance/test success;
- throughput;
- provider failures;
- token/cost use;
- escalation rate to stronger models/humans.

## 15. Version 1 scope

The smallest useful first implementation should provide only:

1. one versioned task-contract schema;
2. manual `workflow_dispatch`;
3. GitHub Actions ephemeral runner;
4. isolated FreeLLMAPI sidecar with a small approved provider set;
5. isolated Hermes supervisor with flat delegation;
6. one or two bounded task types for the pilot;
7. structured result schema;
8. deterministic validation;
9. artifact output;
10. tests proving the security boundaries and contract behavior.

The first pilot should require **no target-project write credential**.

Only after quality and economics are proven should automated project handoff be added.

## 16. Explicit non-goals

Do not build in version 1:

- a second Control implementation;
- a generic workflow/BPM platform;
- a generic plugin marketplace;
- multi-tenant SaaS;
- a framework CRM/database;
- autonomous production deployment;
- autonomous database administration;
- recursive unbounded swarms;
- an agent-owned canonical memory store;
- a custom model router competing with FreeLLMAPI;
- a custom container scheduler;
- a bespoke secret broker;
- provider abstractions already provided by FreeLLMAPI;
- direct production database access merely for convenience.

## 17. Evolution triggers

Architecture may grow only in response to measured limitations.

| Add only when observed | Candidate evolution |
|---|---|
| Actions runtime/time limits block real tasks | persistent cloud worker/VPS/serverless backend |
| repeated cross-run continuation is required | minimal checkpoint mechanism owned by correct authority |
| multiple projects need identical safe write handoff | shared bounded publisher abstraction |
| free-provider quality is insufficient for a task class | approved paid/frontier route |
| agent concurrency is bottlenecked by one runner | GitHub job matrix or additional isolated runners |
| private/sensitive data has a real use case | approved privacy-controlled inference lane |

The existence of a possible future need is not sufficient reason to implement it now.

## 18. Architectural invariants

1. The target project owns its business truth.
2. Control owns Control mission authority when it is the caller.
3. `agent` is an execution framework, not a competing project control plane.
4. One versioned task contract crosses into the framework.
5. One versioned result contract crosses out.
6. Hermes is treated as an untrusted reasoning/tool-execution zone.
7. Hermes receives no target-project production write credentials by default.
8. Target secrets are introduced only after the agent zone has terminated and only to trusted bounded publishing code.
9. FreeLLMAPI is an inference gateway, not an authority layer.
10. Provider access is allowlisted, not “enable everything”.
11. Swarms are bounded and flat by default.
12. Deterministic work stays deterministic.
13. Agent memory/skills do not silently become canonical state.
14. GitHub Actions is ephemeral compute, not project business state.
15. Artifact-only integration is the default safe mode.
16. Irreversible actions require explicit project-specific authority outside the generic agent loop.
17. No new persistent infrastructure without observed need.
18. Framework success requires verification evidence, not merely agent completion.

## 19. Current technology choices

| Capability | Initial choice | Reason |
|---|---|---|
| source/config | GitHub repository | existing source of truth and review history |
| scheduler/compute | GitHub Actions | ephemeral, native, currently free for standard runners in public repos |
| agent runtime | Hermes Agent | provider-agnostic tools, delegation and parallel agents |
| inference gateway | FreeLLMAPI | pooled free-provider routing and quota/failover management |
| durable project data | existing target project | prevents second state plane |
| default result transport | GitHub Actions artifact | zero target-project authority required |
| secrets | GitHub Actions secrets, step-scoped | native capability; no custom broker |

## 20. External implementation references

These references describe the current capabilities on which the initial architecture relies. They are implementation dependencies, not architectural authority.

- Hermes Agent: `https://github.com/NousResearch/hermes-agent`
- Hermes documentation: `https://hermes-agent.nousresearch.com/docs/`
- FreeLLMAPI: `https://github.com/tashfeenahmed/freellmapi`
- FreeLLMAPI architecture: `https://github.com/tashfeenahmed/freellmapi/blob/main/docs/en/architecture/00-high-level-index.md`
- GitHub Actions hosted runners: `https://docs.github.com/en/actions/concepts/runners/github-hosted-runners`
- GitHub Actions limits: `https://docs.github.com/en/actions/reference/limits`

### Upstream facts verified for this architecture on 2026-09-09

- Hermes supports model-provider independence, tool execution, isolated delegated subagents and cloud/serverless execution backends.
- FreeLLMAPI exposes a self-hosted compatible inference gateway with pooled provider routing, rate-limit tracking and failover; it is single-user/local-first and has no SLA.
- Standard GitHub-hosted Actions runners in public repositories are currently free; normal hosted jobs execute on fresh VMs and have a six-hour maximum job runtime.

If any of these upstream assumptions changes materially, update this document before changing the architecture around stale facts.
