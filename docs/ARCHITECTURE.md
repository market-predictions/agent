# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Version:** 0.5 — bounded carrier + isolated interactive Hermes dashboard  
**Status:** bounded Phase-1 carrier qualified; interactive web path deployed/browser-proven; long-lived post-simplification stability and state-recovery proof remain  
**Date:** 2026-09-12  
**Canonical:** yes — this document is the single current architecture truth.

Historical rationale lives in `docs/DESIGN_REVIEW_10_ITERATIONS.md`; implementation sequence in `docs/ROADMAP.md`; operations in `docs/OPERATIONS.md`.

---

## 1. Purpose

`agent` is a reusable carrier for **bounded autonomous AI work across multiple projects** plus a separate, least-privilege human-facing Hermes interface.

```text
bounded authorized task
  -> Hermes worker
  -> FreeLLMAPI
  -> free routed model
  -> bounded web tools
  -> structured CANDIDATE
  -> later independent verification
  -> caller/project authority

human browser
  -> Nous OAuth
  -> native Hermes Web Dashboard/TUI
  -> FreeLLMAPI
  -> free routed model
  -> web tools only
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
3. **The generic bounded data lane is `PUBLIC_NON_PERSONAL`.**
4. **One bounded worker is proven before fan-out.**
5. **Generation and verification are separate authorities.** Phase-1 success is `CANDIDATE`; only a later trusted verifier may emit `RESULT_READY`.
6. **GitHub is code/config/docs truth.**
7. **Modal is the selected cloud runtime**, not a second business/state plane.
8. **Interactive Hermes is a separate capability surface**, never an expansion of the bounded worker's authority.

---

## 4. Current bounded carrier

The exact bounded implementation has been exercised end-to-end on a GitHub-hosted runner and through a live Modal remote smoke:

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
FreeLLMAPI 0.9.8 / exact image digest
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
strict structured CANDIDATE or fail-closed rejection
```

The worker resolves the deployed FreeLLMAPI service URL inside trusted runtime code. Callers cannot provide or redirect the credential-bearing gateway destination.

The production parser remains strict. The fixed 20-run qualification owns output-quality measurement. The single-sample live CI probe owns transport/runtime integration and therefore treats a recognized strict-output rejection as successful fail-closed integration evidence after the real model/tool path has completed. This avoids making CI depend on a stochastic free model producing perfect JSON on every run without weakening runtime acceptance.

---

## 5. Interactive dashboard boundary

The human-facing layer is the upstream native Hermes Web Dashboard/TUI, not a custom frontend.

Current topology:

```text
browser
  -> public Modal HTTPS endpoint
  -> native Nous Portal OAuth
  -> Hermes dashboard web server
  -> Hermes TUI gateway
  -> FreeLLMAPI protected service
  -> free provider/model
  -> web_search / web_extract only
```

Properties:

- same Hermes source identity as the bounded worker;
- same FreeLLMAPI-only inference boundary;
- one persistent Modal Volume for interactive profiles/sessions/state only;
- no Control state or target-project business truth in that Volume;
- one active dashboard container maximum;
- Modal request concurrency up to 20 to support the native dashboard's concurrent HTTP/WebSocket transport;
- Hermes `max_concurrent_sessions=1`;
- model/provider/fallback boundary validated fail-closed at startup;
- interactive model tool authority hard-pinned with `HERMES_TUI_TOOLSETS=web`;
- runtime package mutation disabled with `security.allow_lazy_installs=false`;
- auxiliary session-title generation disabled;
- automatic coding-workspace posture disabled with `agent.coding_context=off`.

The `HERMES_TUI_TOOLSETS` pin is deliberate. Hermes' TUI/dashboard otherwise resolves `platform_toolsets.cli` and may auto-select a coding posture when started inside a repository. The explicit operator pin resolves before those paths and prevents GUI/session state from re-adding terminal, file, browser, code-execution, delegation or memory tools.

### Modal WebSocket compatibility

A real browser exposed repeated WebSocket disconnects. Hermes' persistent `gui.log` showed browser-facing connections closing with protocol code `1002`, zero application messages and no dispatch crashes. This matched an upstream Hermes report where `permessage-deflate` negotiation across an intermediary caused protocol errors.

Only the dashboard image therefore applies one narrow compatibility patch to the exact pinned Hermes checkout: its Uvicorn config sets `ws_per_message_deflate=False`. The patch is source-anchor-checked and fails the image build if the expected upstream source no longer matches. The bounded worker remains exact upstream Hermes without this patch.

A subsequent authenticated browser session remained connected long enough to perform a live Hermes web search and return a sourced answer. This proves the real browser WebSocket/chat path, not just HTTP health.

### Runtime simplification after long-stall evidence

A later production log showed a distinct issue: event-loop stalls around 13s, 10s and 55s, followed by heartbeat/send failure. The same cold-start also performed unnecessary lazy installs for capabilities outside the web-only lane. The application additionally ran its own 10-second `Volume.commit()` thread even though Modal Volume mounts already provide native background commits.

The response was simplification, not another reliability layer:

- delete the custom Volume commit thread;
- rely on Modal's native Volume background-commit mechanism;
- disable Hermes runtime lazy installs;
- disable cosmetic auxiliary title generation whose proxy-auth path was failing/falling back;
- disable coding-context detection for this non-coding dashboard surface.

This smaller runtime was successfully deployed through the canonical workflow. Production deployment and dashboard auth-boundary smoke passed; bounded worker smoke also remained green.

The logs prove that a dashboard process/container stopped and later cold-started. They do not by themselves prove restoration of a known prior user/session object. State-recovery persistence and long-lived WebSocket stability after the simplification therefore remain explicit runtime verification items.

---

## 6. Runtime pinning

`runtime_versions.py` owns correctness-relevant runtime identities:

- Modal SDK `1.5.5`;
- Hermes `0.21.1`, tag `v2026.9.7`, exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8` at one exact GHCR SHA-256 digest.

Hermes intentionally rejects ordinary wheel/sdist distribution. CI and both Modal Hermes images use the upstream-supported editable source installation from the exact checked-out commit. The dashboard then applies only the explicit WebSocket compatibility patch described above.

GitHub Actions are pinned by full commit SHA and checkout uses `persist-credentials: false`.

---

## 7. Bounded Hermes worker boundary

The worker:

1. accepts one bounded objective;
2. resolves the canonical deployed FreeLLMAPI endpoint inside trusted Modal runtime code;
3. creates a disposable Hermes home;
4. configures named provider `freellmapi` with model `auto`;
5. resolves its client credential through `FREELLMAPI_API_KEY`;
6. adds Modal proxy headers from environment when required;
7. invokes Hermes through the top-level script one-shot path (`-z`);
8. exposes only `web_search` and `web_extract`;
9. requires at least one successful live public web lookup through native tool-hook telemetry;
10. accepts only a strict JSON candidate shape;
11. records usage/policy telemetry and exits.

Explicitly absent from the bounded worker: caller-selected gateway endpoint, shell, project/filesystem mutation, browser automation, delegation, messaging, Hermes gateway/Cron/Kanban, persistent Hermes memory and target-project production credentials.

Current hard bounds are one concurrent task, 600-second outer wall timeout, 12 Hermes iterations, 12 actual provider/model executions, 20 tool executions, one run-global provider retry and a fixed allow-list of `web_search`/`web_extract`. Missing or inconsistent telemetry fails closed.

---

## 8. FreeLLMAPI boundary

FreeLLMAPI requires its unified `freellmapi-...` bearer. On Modal the service additionally uses `requires_proxy_auth=True`.

Hermes receives only the gateway client key and Modal proxy key/secret. Upstream provider keys never enter Hermes.

`runtime/freellmapi-bootstrap.mjs` uses FreeLLMAPI's own exported DB APIs to establish the stable unified key. `runtime/freellmapi.default.json` configures the upstream keyless Kilo and OVH providers. Phase 1 keeps FreeLLMAPI state ephemeral; no Redis, Postgres, router cluster or multi-writer persistence exists.

GitHub Actions authenticates to Modal only with `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`; `scripts/bootstrap_modal_runtime.py` idempotently creates the named runtime Secrets and Modal proxy token without printing generated values.

---

## 9. Data and authority

The generic free-provider lane permits only `PUBLIC_NON_PERSONAL`: public technical standards, non-personal product/vendor information, public non-sensitive repositories and synthetic fixtures.

It does not permit person-linked prospecting, proprietary/internal material, client/customer content, personal/sensitive dossiers, secrets, credentials or production DB contents.

Bounded execution states are currently:

```text
FAILED
CANDIDATE
```

A later trusted verifier may introduce `RESULT_READY`. `RESULT_READY` still does not mean business `DONE`; caller/project/Control owns acceptance.

The interactive dashboard does not receive target-project write credentials and is not a bypass around this authority model.

---

## 10. Verification and deployment

`.github/workflows/ci.yml` proves each candidate through deterministic code/config/topology tests plus exact upstream/runtime integration with a real free model and real Hermes web-tool execution. The integration probe validates either a real strict `CANDIDATE` or an explicitly recognized fail-closed output rejection after the model/tool path succeeds; the 20-run qualification remains the quality gate.

`.github/workflows/deploy-modal.yml` is the only Modal deployment path. It is explicit-dispatch in steady state, bootstraps the named runtime Secrets, deploys all three runtime surfaces, runs the dashboard auth-boundary smoke and may run the bounded worker smoke or qualification sample.

Temporary branch/path triggers used only because the available GitHub connector cannot dispatch the workflow are removed immediately after each deliberate promotion; no second deployment workflow remains.

The fixed 20-run qualification and human source review are recorded in `qualification/PHASE1_QUALIFICATION_REVIEW.md`. External exact-candidate review remains a separate acceptance gate.

---

## 11. Deliberate non-goals until evidence earns them

Do not add yet:

- second agent runtime;
- direct-provider integration;
- worker fan-out/recursive delegation;
- framework database or queue;
- persistent FreeLLMAPI state unless measured necessary;
- Sandbox unless executable tooling is required;
- project publisher or production writes;
- native mobile client unless separately justified.

The next architecture changes are driven by measured need, not anticipated complexity.