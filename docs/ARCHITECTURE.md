# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Version:** 0.4 — Hermes + FreeLLMAPI bounded carrier  
**Status:** operational carrier proven and Phase-1 qualification measured; external review convergence in progress  
**Date:** 2026-09-10  
**Canonical:** yes — this document is the single current architecture truth.

Historical rationale lives in `docs/DESIGN_REVIEW_10_ITERATIONS.md`; implementation sequence in `docs/ROADMAP.md`; operations in `docs/OPERATIONS.md`.

---

## 1. Purpose

`agent` is a reusable carrier for **bounded autonomous AI work across multiple projects**.

```text
bounded authorized task
  -> Hermes
  -> FreeLLMAPI
  -> free routed model
  -> bounded tools
  -> structured CANDIDATE
  -> later independent verification
  -> caller/project authority
```

It is not a project database, Control replacement, scheduler, queue/broker, publisher, or production authority plane. Target projects own business truth and irreversible actions. Control remains Mission/lifecycle authority when it is the caller.

---

## 2. Governing doctrine

- solid but simple;
- no overengineering;
- first-principles reasoning;
- do not reinvent the wheel;
- one source of truth per concern;
- least privilege;
- deterministic work stays deterministic;
- verification is part of implementation;
- remove stale/conflicting implementation instead of preserving parallel truth.

Consequential work fresh-reads the canonical Google Drive **Execution & Engineering Constitution** referenced from `control/PROJECT_GOVERNANCE.md`.

---

## 3. Fixed decisions

1. **Hermes is the only agent runtime.**
2. **FreeLLMAPI is the only inference gateway.** There is no direct-provider bypass.
3. **The first generic data lane is `PUBLIC_NON_PERSONAL`.**
4. **One worker is proven before fan-out.**
5. **Generation and verification are separate authorities.** Phase-1 success is `CANDIDATE`; only a later trusted verifier may emit `RESULT_READY`.
6. **GitHub is code/config/docs truth.** GitHub Actions also supplies the reproducible end-to-end qualification environment.
7. **Modal is the selected cloud deployment target**, not a second business/state plane. The same pinned carrier is deployed there through one explicit promotion workflow.

---

## 4. Current proven carrier

The exact implementation has been exercised end-to-end on a GitHub-hosted runner and through a live Modal remote smoke:

```text
PUBLIC_NON_PERSONAL objective
        |
        v
Hermes 0.21.1
exact commit 2237be355906fbe6065ce1815711eee52b2d646e
script one-shot (-z)
web toolset only
        |
        v
named Hermes provider: freellmapi
OpenAI-compatible /v1
        |
        v
FreeLLMAPI 0.9.8
exact image digest
stable unified bearer
keyless Kilo + OVH bootstrap
        |
        v
real free routed model
        |
        v
Hermes live web lookup
        |
        v
strict structured CANDIDATE
```

The GitHub proof starts from fresh installs, pulls the exact FreeLLMAPI image, performs a direct `model=auto` call, requires `X-Routed-Via`, then executes the actual Hermes carrier. The Modal proof deploys the same pins and carrier and executes a real remote smoke. These are real model/tool loops, not mocks or dry runs.

The live Modal topology is:

```text
Modal Hermes Function
  -> internally resolved protected FreeLLMAPI Modal web service
  -> free provider pool
  -> CANDIDATE
```

The worker resolves the deployed FreeLLMAPI service URL inside trusted runtime code. Callers cannot provide or redirect the credential-bearing gateway destination.

Both functions scale to zero and are capped at one active container in Phase 1.

---

## 5. Runtime pinning

`runtime_versions.py` owns correctness-relevant runtime identities:

- Modal SDK `1.5.5`;
- Hermes `0.21.1`, tag `v2026.9.7`, exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8` at one exact GHCR SHA-256 digest.

Hermes intentionally rejects ordinary wheel/sdist distribution. Both CI and the Modal image use the upstream-supported editable source installation from the exact checked-out commit.

GitHub Actions are pinned by full commit SHA and checkout uses `persist-credentials: false`.

---

## 6. Hermes worker boundary

The worker:

1. accepts one bounded objective;
2. resolves the canonical deployed FreeLLMAPI endpoint inside trusted Modal runtime code;
3. creates a disposable Hermes home;
4. configures the canonical named provider `freellmapi` with model `auto`;
5. resolves its client credential through `FREELLMAPI_API_KEY`;
6. adds Modal proxy headers from environment when running against the protected Modal endpoint;
7. invokes Hermes through the top-level script one-shot path (`-z`), which is intended for programmatic final-response output;
8. exposes only the Hermes `web` toolset;
9. requires at least one **successful** live public web lookup, proven by native tool-hook telemetry rather than prompt compliance alone;
10. accepts only a strict JSON candidate shape;
11. records Hermes usage and bounded policy telemetry and exits.

Explicitly absent:

- caller-selected inference/gateway endpoint;
- terminal/shell toolset;
- project/filesystem mutation tools;
- browser automation;
- delegation/swarm;
- messaging;
- Hermes gateway/Cron/Kanban;
- persistent Hermes memory;
- target-project production credentials.

Current hard bounds:

- one concurrent task;
- outer wall timeout 600 seconds;
- Hermes iteration limit 12 via `HERMES_MAX_ITERATIONS`;
- maximum 12 actual provider/model executions enforced by Hermes `llm_execution` middleware and cross-checked against usage when available;
- maximum 20 tool executions enforced before execution by the `pre_tool_call` hook;
- maximum one run-global provider retry enforced at the actual provider execution boundary;
- fixed tool allow-list of `web_search` and `web_extract`;
- at least one successfully completed allowed web tool call before `CANDIDATE`;
- Modal worker timeout 660 seconds.

The budget plugin persists metadata-only counters/state. Missing or inconsistent plugin telemetry fails a successful-looking run closed.

---

## 7. FreeLLMAPI boundary

### Authentication

FreeLLMAPI requires its unified `freellmapi-...` bearer. On Modal the web service additionally uses `requires_proxy_auth=True`.

Hermes receives only the gateway client key and Modal proxy key/secret. The endpoint itself is resolved internally from the deployed `freellmapi` Modal Function before credentials are attached. Upstream provider keys never enter the Hermes worker.

### Stable headless key

FreeLLMAPI v0.9.8 generates a random unified key on a fresh DB and does not expose an environment override. `runtime/freellmapi-bootstrap.mjs` uses FreeLLMAPI's own exported `initDb()` and `setSetting()` APIs to install the stable key. Bootstrap stdout is discarded so the temporary migration-generated key is not logged.

No raw SQLite edit or custom authentication service exists.

### Provider bootstrap

`runtime/freellmapi.default.json` configures the current upstream keyless providers `kilo` and `ovh`, giving a true zero-provider-key first model path. A complete `FREEAPI_CONFIG_JSON` supplied through the FreeLLMAPI service secret can replace the default declarative startup config and add the desired providers.

Phase 1 uses ephemeral FreeLLMAPI SQLite state. No Volume, Redis, Postgres, router cluster, or multi-writer architecture exists.

### Modal credential bootstrap

GitHub Actions authenticates to Modal only with repository secrets `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`. `scripts/bootstrap_modal_runtime.py` then creates exactly the runtime material needed by this topology when absent:

- Modal Secret `agent-hermes` containing the stable FreeLLMAPI client key and one Modal proxy credential pair;
- Modal Secret `agent-freellmapi` containing the FreeLLMAPI encryption key;
- one Modal proxy token protecting the web service.

The bootstrap is idempotent, preserves the complete existing pair, fails closed on partial Secret state, and does not print generated secret values. Runtime credentials stay in Modal, not Git.

---

## 8. Data and authority

The generic free-provider lane permits only `PUBLIC_NON_PERSONAL`: public technical standards, non-personal product/vendor information, public non-sensitive repositories, and synthetic fixtures.

It does not permit person-linked prospecting, proprietary/internal material, client/customer content, personal/sensitive dossiers, secrets, credentials, or production DB contents.

Current execution states are:

```text
FAILED
CANDIDATE
```

Phase 2 may add `PARTIAL` and `RESULT_READY` after independent evidence verification. `RESULT_READY` still does not mean business `DONE`; caller/project/Control owns acceptance.

---

## 9. Verification and deployment

`.github/workflows/ci.yml` proves each candidate once through two jobs:

- deterministic code/config/topology tests;
- exact upstream/runtime integration including real free inference and real Hermes web-tool execution.

The expensive live model proof runs on pull requests and on merged `main`, not twice for both branch push and PR.

`.github/workflows/deploy-modal.yml` is the only Modal deployment path. It is explicit-dispatch in its steady state, authenticates with `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`, idempotently bootstraps the named runtime Secrets, deploys `modal_app.py`, and can execute the remote smoke or the fixed qualification sample. Provider/runtime credentials remain in Modal Secrets, not GitHub source or Hermes.

The first live promotion and remote smoke have succeeded. One-time branch triggers used only when a candidate workflow is not yet present on `main` are removed immediately after the bounded proof; no second deployment workflow or parallel deployment architecture is retained.

The fixed 20-run qualification and its human source review are recorded in `qualification/PHASE1_QUALIFICATION_REVIEW.md`. External exact-candidate review remains a separate acceptance gate and any review finding invalidates a clean-review claim until repaired and freshly reviewed.

---

## 10. Deliberate non-goals until evidence earns them

Do not add yet:

- second agent runtime;
- direct-provider integration;
- worker fan-out/recursive delegation;
- framework database or queue;
- persistent Hermes gateway/memory inside the bounded worker;
- FreeLLMAPI persistence unless measured necessary;
- Sandbox unless executable tooling is required;
- project publisher or production writes.

A separate authenticated interactive Hermes service may proceed only under the current governed Mission sequence and must remain isolated from bounded-worker, Control and project-business authority.

The next architecture changes are driven by measured need, not anticipated complexity.
