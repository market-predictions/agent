# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Version:** 0.4 — Hermes + FreeLLMAPI on Modal  
**Status:** implementation candidate; live Modal deployment evidence pending  
**Date:** 2026-09-09  
**Canonical:** yes — this document is the single current architecture truth.

Historical rationale lives in `docs/DESIGN_REVIEW_10_ITERATIONS.md`; implementation sequence in `docs/ROADMAP.md`; operations in `docs/OPERATIONS.md`.

---

## 1. Purpose

`agent` is a reusable carrier for **bounded autonomous AI work across multiple projects**.

Core contract:

```text
bounded authorized task
  -> Hermes
  -> FreeLLMAPI
  -> structured candidate
  -> later independent verification
  -> caller/project authority
```

It is not a project database, Control replacement, generic scheduler, queue/broker, publisher, or production authority plane.

Target projects own business truth and irreversible actions. Control remains Mission/lifecycle authority when it is the caller.

---

## 2. Governing doctrine

Hard principles:

- solid but simple;
- no overengineering;
- first-principles reasoning;
- do not reinvent the wheel;
- YAGNI;
- one source of truth per concern;
- least privilege;
- deterministic work stays deterministic;
- verification is part of implementation;
- stale/conflicting code/config/docs are removed rather than preserved as parallel current truth.

Consequential work must fresh-read the canonical Google Drive **Execution & Engineering Constitution** referenced from `control/PROJECT_GOVERNANCE.md`.

---

## 3. Fixed product decisions

1. **Hermes is the agent runtime.** No Pydantic AI/bake-off/fallback runtime exists in this phase.
2. **FreeLLMAPI is the only inference gateway.** No direct-provider bypass exists.
3. **Modal is runtime; GitHub is source of truth.**
4. **The first generic data lane is `PUBLIC_NON_PERSONAL`.**
5. **One worker is proven before fan-out.**
6. **Fixed-safe-tool work uses a Modal Function.** A Sandbox is added only when shell/generated-code/broad executable tooling is genuinely required.
7. **Generation and verification are separate authorities.** Phase-1 success is `CANDIDATE`; only a later trusted verifier may promote suitable output to `RESULT_READY`.
8. **Mobile/interactive Hermes is planned later** and remains separate from bounded-worker/Control/project state.

---

## 4. Current implemented topology

```text
                     CALLER
                       |
            PUBLIC_NON_PERSONAL task
                       |
                       v
              +------------------+
              | Modal Function   |
              |                  |
              | Hermes 0.21.1    |
              | exact Git commit |
              | one-shot         |
              | web toolset only |
              +--------+---------+
                       |
             OpenAI-compatible /v1
                       |
                       v
       +----------------------------------+
       | protected FreeLLMAPI web service|
       |                                  |
       | v0.9.8 exact image digest        |
       | stable unified bearer            |
       | Modal proxy authentication       |
       | max active containers: 1         |
       +----------------+-----------------+
                        |
                        v
              eligible free providers
                        |
                        v
                structured CANDIDATE
```

Both Modal components scale to zero (`min_containers=0`). Phase 1 caps each at one active container.

The trusted evidence verifier is **not part of this current operational candidate**; it is Phase 2.

---

## 5. Runtime pinning

`runtime_versions.py` owns the exact correctness-relevant runtime identities:

- Modal SDK `1.5.5`;
- Hermes `0.21.1`, tag `v2026.9.7`, commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8` at one exact GHCR SHA-256 image digest.

GitHub Actions are also pinned by full commit SHA and checkout uses `persist-credentials: false`.

Dynamic FreeLLMAPI routing is not falsely treated as deterministic. Runtime software is pinned; actual inference routing is observable/provenance data.

---

## 6. Hermes worker boundary

The worker:

1. receives one bounded objective;
2. creates a disposable Hermes home;
3. configures exactly one custom model alias (`freellm`) targeting FreeLLMAPI `model=auto`;
4. attaches FreeLLM unified auth plus Modal proxy headers through Hermes' native custom-provider config;
5. invokes Hermes once in headless mode;
6. exposes only the Hermes `web` toolset;
7. requires at least one live public web lookup by instruction;
8. requires a strict JSON candidate shape;
9. records Hermes usage where available;
10. exits.

Explicitly absent:

- terminal/shell toolset;
- filesystem/project mutation tools;
- browser automation;
- delegation/swarm;
- messaging;
- Hermes gateway/Cron/Kanban;
- persistent Hermes memory;
- target-project production credentials.

### Bounds

Current hard/runtime bounds include:

- one concurrent Hermes Function;
- max wall time 600 seconds for the Hermes subprocess;
- max turns 12;
- model-call budget checked against Hermes usage (`api_calls`) when reported;
- Modal Function timeout 660 seconds.

`max_tool_calls=20` is currently a declared contract target but Hermes' current usage file does not provide an exact tool-call count. It must not be represented as independently enforced until an upstream-stable counter or a simple verified wrapper exists.

---

## 7. FreeLLMAPI boundary

### 7.1 Authentication

FreeLLMAPI is protected twice:

1. Modal `requires_proxy_auth=True`;
2. FreeLLMAPI's unified `freellmapi-...` bearer.

Hermes receives only:

- unified FreeLLMAPI client key;
- Modal proxy key/secret;
- endpoint URL.

Hermes does not receive upstream provider keys.

### 7.2 Headless unified-key bootstrap

FreeLLMAPI v0.9.8 generates a random unified key on a fresh DB and does not expose an environment override for it.

`runtime/freellmapi-bootstrap.mjs` uses FreeLLMAPI's own exported `initDb()` and `setSetting()` API to set the stable key supplied through Modal Secret `agent-hermes`. Bootstrap stdout is discarded so the temporary migration-generated key is not logged.

No raw SQLite edits or custom auth server are used.

### 7.3 Provider bootstrap

`runtime/freellmapi.default.json` configures the current upstream keyless providers:

- `kilo`;
- `ovh`.

This gives a true zero-provider-key initial model path.

If Modal Secret `agent-freellmapi` supplies `FREEAPI_CONFIG_JSON`, upstream FreeLLMAPI treats that inline JSON as the declarative startup config. It may contain the full desired provider set. All correctly configured providers in that config are eligible under FreeLLMAPI routing.

### 7.4 State

Phase 1 deliberately uses ephemeral FreeLLMAPI SQLite state. No Modal Volume, Redis, Postgres, router cluster, or multi-writer design exists.

A single persistent Volume is considered only if measured loss of quota/cooldown/analytics state materially harms the carrier.

---

## 8. Data policy

The generic free-provider lane allows only `PUBLIC_NON_PERSONAL`, including public technical standards, product/vendor information not about natural persons, public non-sensitive repositories and synthetic fixtures.

It does not allow by default:

- identifiable-person/sole-trader prospect data;
- proprietary/internal data;
- customer/client content;
- personal/sensitive/regulatory data.

Never send credentials, production DB contents, unredacted care/legal dossiers, or other secrets through the generic free pool.

Modal isolation does not change upstream provider privacy obligations.

---

## 9. Result semantics

Current Phase-1 inner result:

```json
{
  "summary": "short answer",
  "claims": [
    {
      "claim": "supported public claim",
      "source_url": "https://..."
    }
  ]
}
```

The carrier wraps that with task, data class, budget, usage and route metadata.

Execution statuses currently relevant:

```text
FAILED
CANDIDATE
```

Future verifier phase adds:

```text
PARTIAL
RESULT_READY
```

`RESULT_READY` never means business `DONE`; caller/project/Control remains final acceptance authority.

---

## 10. Verification strategy

CI has two layers.

### Deterministic carrier tests

- syntax/compilation;
- unit/boundary tests;
- exact runtime-pin tests;
- Modal topology import;
- no Sandbox/Volume/second runtime in Phase 1;
- dry-run carrier contract.

### Real upstream integration

CI also exercises the actual pinned upstream components:

1. install Hermes from the exact commit;
2. pull the exact FreeLLMAPI image digest;
3. boot FreeLLMAPI with the same unified-key bootstrap and keyless provider config;
4. prove unauthenticated `/v1/models` is rejected;
5. prove authenticated model discovery;
6. call a real `model=auto` free-model route and require `X-Routed-Via`;
7. run the actual local Hermes -> FreeLLMAPI -> model -> Hermes web-tool carrier and require a structured `CANDIDATE`.

Live Modal deployment is a separate deployment proof because CI cannot fabricate a user's Modal account credentials.

---

## 11. Deployment and secrets

Modal named Secrets:

### `agent-hermes`

- `FREELLMAPI_API_KEY`;
- `MODAL_PROXY_KEY`;
- `MODAL_PROXY_SECRET`.

### `agent-freellmapi`

- `ENCRYPTION_KEY`;
- optional `FREEAPI_CONFIG_JSON` containing additional provider credentials/configuration.

GitHub deployment needs only:

- `MODAL_TOKEN_ID`;
- `MODAL_TOKEN_SECRET`.

Exact operator commands live in `docs/OPERATIONS.md`.

---

## 12. State and authority

No framework database or queue exists.

| Concern | Current truth |
|---|---|
| framework code/config/docs | GitHub |
| Control governed intent | Control Mission |
| Control lifecycle | Control runtime state |
| live worker state | disposable Modal Function/process |
| FreeLLM provider config | Git file default + Modal Secret override |
| temporary FreeLLM quota/cooldown | ephemeral FreeLLM SQLite |
| project/business state | target project |
| final acceptance | caller/project/Control as applicable |

The known frozen-Control candidate-binding limitation is not solved inside Agent and does not block Agent runtime implementation.

---

## 13. Next capability: trusted verifier

After the first carrier is proven, one separate trusted Modal Function will:

- accept structured candidate data only;
- validate schema;
- re-resolve/re-fetch HTTP(S) evidence;
- reject localhost/private/link-local/metadata destinations;
- revalidate redirects;
- enforce byte/time limits;
- establish deterministic evidence presence/support where feasible.

It never executes worker-supplied code/scripts/files.

Only after that gate may output become `RESULT_READY`.

---

## 14. Explicit current non-goals

Do not add yet:

- second agent runtime;
- direct-provider path;
- worker fan-out;
- Hermes recursive delegation;
- Modal Sandbox;
- persistent FreeLLM Volume;
- framework DB/queue/scheduler;
- task-profile engine;
- project publisher/write credentials;
- mobile service.

---

## 15. Definition of Done

A phase is Done only when:

- working behavior is demonstrated, not merely configured;
- relevant failures/security boundaries are exercised;
- exact software/runtime identities are recorded;
- unnecessary/superseded code and config are removed;
- README, architecture, roadmap, operations and actual behavior agree;
- known missing evidence is stated rather than implied away.

The Phase-1 carrier can be called operational only after a live Modal deploy plus remote smoke succeeds. Full `AGENT-R1-GAP-01` Mission acceptance additionally requires the later 20-run qualification evidence and external exact-candidate review.
