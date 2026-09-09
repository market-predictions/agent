# Agent Framework — Ten-Iteration Adversarial Design Review

**Repository:** `market-predictions/agent`  
**Review date:** 2026-09-09  
**Purpose:** design rationale and adversarial review history  
**Authority:** non-canonical rationale; `docs/ARCHITECTURE.md` is the single current architecture truth.

## Review method

The starting proposal combined:

- GitHub as source of truth and deployment control;
- Modal as free/near-free headless cloud compute;
- Hermes as autonomous agent runtime;
- FreeLLMAPI as pooled low-cost/free inference gateway;
- parallel agents for project work;
- optional phone/mobile interaction;
- Control and target projects as callers/authority.

The design was attacked ten times from first principles. Every iteration had to answer:

1. Does this component directly serve a current business outcome?
2. Is there a simpler proven/native mechanism?
3. Does it create duplicate authority, state, scheduling or orchestration?
4. What happens when an agent is fully compromised?
5. Can behavior be verified independently of the LLM?
6. Can obsolete/conflicting architecture be deleted rather than supported forever?

The governing doctrine is the Execution & Engineering Constitution: business outcome first; solid but simple; no overengineering; first principles; proven/native solutions; least privilege; verification; one source of truth; and cleanup as part of Done.

---

## Iteration 1 — Attack the scope: execution framework or everything-agent?

### Attack

The proposal mixed two materially different products:

- a reusable project-work execution carrier;
- a persistent interactive personal Hermes reachable from a phone.

A shared technology stack does not make them one responsibility. The interactive path introduces session continuity, persistent memory, long-lived API/gateway state, UI/client behavior and different availability expectations.

### Failure mode

Trying to support both in v1 would force the core framework to solve persistence, mobile sessions and always-addressable endpoints before proving that bounded project work is useful.

### Decision

**Remove interactive Hermes from v1.**

The core framework is only:

> bounded task in -> isolated autonomous execution -> independently verified result out.

A phone/mobile interactive adapter remains an explicit future evolution. It may reuse Hermes and FreeLLMAPI, but it is not part of the execution carrier's state or authority model.

### Improvement

One product, one lifecycle, one definition of success.

---

## Iteration 2 — Attack duplicate orchestration: Modal fan-out plus Hermes subagents

### Attack

The proposal could create workers twice:

```text
Modal orchestrator
  -> Hermes supervisor
       -> Hermes subagents
```

Both Modal and Hermes can provide parallelism. Using both immediately creates two concurrency models, two failure trees, more token use and harder observability.

### Failure mode

A parent Hermes process can create children while Modal also creates Sandboxes. Worker counts and cost become opaque; retries can multiply; nested delegation can duplicate work.

### Decision

**Modal owns worker fan-out in v1.**

Each independent worker is one fresh Modal Sandbox containing one complete headless Hermes process. Hermes internal delegation is disabled for the initial carrier.

```text
Modal orchestrator
  -> Sandbox/Hermes A
  -> Sandbox/Hermes B
```

### Evolution trigger

Hermes internal delegation may be introduced only if measured tasks prove that hierarchical reasoning inside one worker materially improves accepted output versus simpler Modal-level fan-out.

### Improvement

One concurrency authority and one worker lifecycle.

---

## Iteration 3 — Attack the Hermes/Modal boundary

### Attack

Hermes documents `terminal.backend: modal`, but that architecture leaves Hermes itself running elsewhere and moves only terminal/file execution to a Modal Sandbox.

That does not satisfy the desired operating model:

- no PC required;
- no VPS required;
- whole agent process isolated in headless cloud compute.

There are also current upstream Hermes issues affecting its remote Modal backend, including sandbox detachment/lost work and remote execute-code behavior.

### Decision

**Run the entire Hermes worker inside a Modal Sandbox.**

Inside the Sandbox Hermes uses its ordinary local terminal. Modal is the process/container isolation boundary.

```text
Modal Sandbox
  -> Hermes one-shot
       -> local tools inside Sandbox
```

Do not make Hermes' `terminal.backend: modal` a critical dependency of v1.

### Improvement

Whole-process containment and fewer moving parts.

---

## Iteration 4 — Attack FreeLLMAPI placement

### Attack

Putting FreeLLMAPI beside Hermes inside every worker is simpler operationally, but it gives the same compromised worker environment access to all upstream provider credentials.

A separate FreeLLMAPI service is one extra component. Does it earn its complexity?

### Failure mode

A prompt-injected or compromised worker that can read local environment/process/files could exfiltrate every provider key if they are co-located.

### Decision

**A separate protected FreeLLMAPI Modal service is justified by a concrete security boundary.**

Hermes workers receive only:

- the FreeLLMAPI endpoint;
- a revocable unified FreeLLMAPI credential;
- Modal endpoint proxy authentication material scoped to that endpoint/environment.

FreeLLMAPI alone receives upstream provider keys.

### Constraint

FreeLLMAPI remains a single-user/internal gateway. It must not be exposed as an unauthenticated public endpoint.

### Improvement

Worker compromise does not automatically disclose all upstream provider accounts.

---

## Iteration 5 — Attack persistence: do we need durable FreeLLMAPI state now?

### Attack

FreeLLMAPI tracks quotas/cooldowns in SQLite. Persisting its database across scale-to-zero runs can preserve useful routing state. Modal Volumes can persist files.

But a persistent Volume introduces state lifecycle, commit/reload semantics and SQLite concurrency constraints.

### Failure mode

Multiple FreeLLMAPI replicas writing one SQLite file on a Modal Volume risk conflicting last-writer-wins updates; Modal Volumes are not a distributed database and provide no distributed file locking.

### Decision

**Do not require persistent FreeLLMAPI state for the first carrier proof.**

V1 starts with:

- one protected FreeLLMAPI service;
- `max_containers = 1`;
- ephemeral quota/cooldown state acceptable;
- conservative per-task inference budgets;
- 429/provider exhaustion treated as an expected degraded condition.

### Evolution trigger

Add one persistent Modal Volume for FreeLLMAPI only after measurements show that lost cross-run quota/cooldown state materially wastes available capacity.

If persistence is enabled, keep FreeLLMAPI single-writer. Do not add Redis/Postgres merely to scale the router.

### Improvement

Security boundary retained without premature persistent infrastructure.

---

## Iteration 6 — Attack task constraints: prompt text is not policy

### Attack

A task saying `no production writes` or `public data only` in natural language is not enforcement. Hermes may misunderstand it, a website may prompt-inject it, or a future skill may conflict with it.

### Decision

Introduce one small proven pattern: **Git-backed task profiles**.

The caller supplies an objective and selects an existing profile. The profile is resolved before worker creation and defines the effective capability envelope.

Example:

```yaml
id: public-research-v1
data_class: PUBLIC
network: PUBLIC_WEB
target_mutation: NONE
max_workers: 2
max_wall_minutes: 45
inference_lane: FREE_PUBLIC
```

The caller may narrow a profile's limits but cannot widen them dynamically.

### Explicit non-goal

This is not a generic policy language, plugin framework or RBAC builder. V1 needs one profile.

### Improvement

Authority is machine-enforced outside the LLM.

---

## Iteration 7 — Attack framework state and asynchronous task management

### Attack

A generic headless agent platform naturally tempts creation of:

- task database;
- queue;
- status API;
- retry scheduler;
- agent registry.

But Control and target projects already own durable lifecycle where required. Modal already provides invocation/execution primitives.

### Decision

**No framework database, queue or task scheduler in v1.**

The initial carrier runs one bounded invocation to completion and returns a result. The caller owns durable task state and successor decisions.

Framework statuses are execution facts only:

- `REJECTED`;
- `FAILED`;
- `PARTIAL`;
- `RESULT_READY`.

The framework does not emit `DONE` as business authority.

### Evolution trigger

Add minimal checkpoint/state only when a proven task cannot be expressed as a bounded invocation and the state clearly does not belong to Control or the target project.

### Improvement

No second Control plane.

---

## Iteration 8 — Attack verification and publication

### Attack

If Hermes both produces and judges its own output, the swarm can confidently agree on a wrong result. If the worker also has project write credentials, validation becomes advisory rather than a boundary.

### Decision

Separate execution from verification:

```text
untrusted Sandbox/Hermes workers
  -> structured candidate results
  -> trusted deterministic verifier Function
  -> RESULT_READY
```

The verifier runs outside worker Sandboxes and performs only deterministic/schema/evidence checks that are actually machine-verifiable.

### Publication

V1 has **no target-project write capability**.

A future publisher, if justified, must be a separate trusted Modal Function with a narrow project-specific capability and must accept only a verified result contract.

### Improvement

Agent completion cannot silently become project authority.

---

## Iteration 9 — Attack mobile interaction

### Attack

Hermes exposes an OpenAI-compatible API server and can support mobile/web frontends. Modal can host HTTP servers with scale-to-zero behavior. It is technically attractive to add a mobile Hermes immediately.

But Hermes API-server state, session continuity, memory, cold-start behavior and a persistent `~/.hermes/state.db` create an independent stateful service. A normal Hermes messaging gateway is also a continuously running process.

### Decision

**Do not build mobile/interactive Hermes in v1.**

Document the future pattern only:

```text
phone/mobile client
  -> authenticated Modal web endpoint
  -> dedicated interactive Hermes service
  -> same protected FreeLLMAPI gateway
```

It must have its own state and security review and must not become the task/authority store for the worker framework.

### Improvement

The core carrier remains serverless and bounded; interactive product concerns stay optional.

---

## Iteration 10 — Attack reproducibility, supply chain and Done

### Attack

Hermes and FreeLLMAPI are fast-moving projects. Using `latest`, install scripts at runtime or unpinned Actions/containers makes a result impossible to reproduce and can silently change security behavior.

### Decision

Before implementation is considered complete:

- pin Hermes to an exact release/commit;
- pin FreeLLMAPI to an exact release/image digest;
- pin the Modal Python SDK version;
- pin the worker base image/dependencies;
- record framework Git SHA, task profile version, Hermes version and FreeLLMAPI version in every result;
- record actual routed provider/model metadata where available;
- keep FreeLLMAPI prompt compression and persistent response caching off initially;
- test the exact Hermes -> FreeLLMAPI OpenAI-compatible wire path used by the worker;
- treat provider/model substitution as observable degraded behavior, never silent correctness evidence.

### Cleanup requirement

The previous GitHub-Actions-first architecture is superseded and must be replaced rather than kept as a competing current design. README and canonical architecture must agree. No obsolete implementation exists yet, so there is no code migration debt at this stage.

### Improvement

Current repository truth becomes reproducible, auditable and clean.

---

# Result after ten iterations

The resulting smallest complete design is:

```text
Control / project / manual caller
          |
          | bounded task + profile
          v
Modal orchestrator Function
          |
          | deterministic partition
          v
    +-----+-----+
    |           |
    v           v
Sandbox A    Sandbox B
Hermes -z    Hermes -z
    |           |
    +-----+-----+
          |
          v
protected single FreeLLMAPI service
          |
          v
approved free-provider pool

worker results
    |
    v
trusted deterministic verifier
    |
    v
RESULT_READY
    |
    v
caller / project authority
```

V1 deliberately contains no:

- VPS;
- GitHub Actions execution carrier;
- Hermes remote Modal terminal backend;
- Hermes gateway;
- Hermes Cron;
- Hermes Kanban/profile team;
- recursive swarm;
- framework database;
- queue/broker;
- vector database;
- custom model router;
- project publisher;
- target-project write credentials;
- interactive/mobile Hermes service;
- persistent FreeLLMAPI database.

This is the architecture implemented by the canonical `docs/ARCHITECTURE.md` target design.