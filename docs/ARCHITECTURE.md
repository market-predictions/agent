# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Version:** 0.4 — Hermes + FreeLLMAPI bounded carrier  
**Status:** operational carrier proven in GitHub Actions; Modal deployment-ready but not yet account-deployed  
**Date:** 2026-09-09  
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
7. **Modal is the selected cloud deployment target**, not a second business/state plane. Cloud deployment requires account-bound credentials and is not claimed until remote smoke passes.

---

## 4. Current proven carrier

The exact current implementation has been exercised end-to-end on a GitHub-hosted runner:

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

The live proof starts from fresh installs, pulls the exact FreeLLMAPI image, performs a direct `model=auto` call, requires `X-Routed-Via`, then executes the actual Hermes carrier. This is a real model/tool loop, not a mock or dry run.

The same carrier is encoded for Modal in `modal_app.py`:

```text
Modal Hermes Function
  -> protected FreeLLMAPI Modal web service
  -> free provider pool
  -> CANDIDATE
```

The Modal topology is deployment-ready, but a live Modal deployment is not current fact until the external Modal token and named Modal Secrets are configured and `modal run modal_app.py::smoke` succeeds.

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
2. creates a disposable Hermes home;
3. configures the canonical named provider `freellmapi` with model `auto`;
4. resolves its client credential through `FREELLMAPI_API_KEY`;
5. adds Modal proxy headers from environment when running against the protected Modal endpoint;
6. invokes Hermes through the top-level script one-shot path (`-z`), which is intended for programmatic final-response output;
7. exposes only the Hermes `web` toolset;
8. requires at least one live public web lookup by instruction;
9. accepts only a strict JSON candidate shape;
10. records Hermes usage where available and exits.

Explicitly absent:

- terminal/shell toolset;
- project/filesystem mutation tools;
- browser automation;
- delegation/swarm;
- messaging;
- Hermes gateway/Cron/Kanban;
- persistent Hermes memory;
- target-project production credentials.

Current bounds:

- one concurrent task;
- outer wall timeout 600 seconds;
- Hermes iteration limit 12 via `HERMES_MAX_ITERATIONS`;
- maximum model calls checked against Hermes `api_calls` usage when reported;
- Modal worker timeout 660 seconds.

`max_tool_calls=20` remains a declared contract target, not a falsely claimed independently enforced counter: Hermes 0.21.1 does not provide a stable exact tool-call count through the selected usage file path.

---

## 7. FreeLLMAPI boundary

### Authentication

FreeLLMAPI requires its unified `freellmapi-...` bearer. On Modal the web service additionally uses `requires_proxy_auth=True`.

Hermes receives only the gateway client key, endpoint, and — on Modal — proxy key/secret. Upstream provider keys never enter the Hermes worker.

### Stable headless key

FreeLLMAPI v0.9.8 generates a random unified key on a fresh DB and does not expose an environment override. `runtime/freellmapi-bootstrap.mjs` uses FreeLLMAPI's own exported `initDb()` and `setSetting()` APIs to install the stable key. Bootstrap stdout is discarded so the temporary migration-generated key is not logged.

No raw SQLite edit or custom authentication service exists.

### Provider bootstrap

`runtime/freellmapi.default.json` configures the current upstream keyless providers `kilo` and `ovh`, giving a true zero-provider-key first model path. A complete `FREEAPI_CONFIG_JSON` supplied through the FreeLLMAPI service secret can replace the default declarative startup config and add the desired providers.

Phase 1 uses ephemeral FreeLLMAPI SQLite state. No Volume, Redis, Postgres, router cluster, or multi-writer architecture exists.

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

`.github/workflows/deploy-modal.yml` is the only Modal deployment path. It runs on explicit dispatch or `main` and fails closed if `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` are absent. Provider credentials remain in Modal Secrets, not GitHub or Hermes.

---

## 10. Deliberate non-goals until evidence earns them

Do not add yet:

- second agent runtime;
- direct-provider integration;
- worker fan-out/recursive delegation;
- framework database or queue;
- persistent Hermes gateway/memory;
- FreeLLMAPI persistence unless measured necessary;
- Sandbox unless executable tooling is required;
- project publisher or production writes;
- mobile/interactive service before bounded-carrier qualification.

The next architecture changes are driven by measured need, not anticipated complexity.
