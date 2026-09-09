# Agent Implementation Log

**Project:** `market-predictions/agent`  
**Candidate:** PR #1 / `bootstrap/agent-r1-gap-01`  
**Control baseline:** frozen; no Control runtime changes were made.

This log records consequential Phase-1 implementation decisions. Git history remains the detailed audit trail; this file is not runtime state.

## 2026-09-09 — from bootstrap skeleton to deployable carrier

### 1. Re-read mandatory engineering doctrine

Fresh-read the canonical Google Drive **Execution & Engineering Constitution** before implementation. Applied: smallest complete solution, YAGNI, first principles, proven upstream primitives, autonomous execution, verification as implementation, and cleanup/documentation alignment as part of Done.

### 2. Revalidated upstream facts before coding

Verified current exact implementation assumptions rather than relying on earlier research summaries:

- Hermes current selected release: `0.21.1` / tag `v2026.9.7` / exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- Hermes supports headless one-shot, custom OpenAI-compatible providers, `model_aliases`, env-backed keys, extra request headers, web-only toolsets, max turns and a JSON usage file;
- Hermes has a keyless web-search/extract fallback ring suitable for the first public non-personal smoke;
- FreeLLMAPI selected release: `0.9.8`, pinned by exact GHCR image digest;
- FreeLLMAPI exposes OpenAI-compatible `model=auto`, tool calling, `X-Routed-Via`, declarative startup config and keyless providers;
- FreeLLMAPI v0.9.8 creates a random unified bearer on first DB migration and has no environment override for that setting;
- FreeLLMAPI exports its own DB API (`initDb`, `setSetting`), so the stable deployment key can be installed without raw SQLite edits;
- Modal SDK `1.5.5` supports exact registry images, scale-to-zero Functions, protected `web_server` endpoints and named Secrets.

### 3. Centralized exact runtime pins

Added `runtime_versions.py` as the one current source for:

- Modal SDK version;
- Hermes version/tag/commit/git install spec;
- FreeLLMAPI version/image digest/port;
- stable Modal app/Secret names.

No `latest` runtime identity is used by the carrier.

### 4. Built the Modal topology

Added `modal_app.py`:

```text
Modal App: agent-carrier

FreeLLMAPI web service
  - exact image digest
  - proxy auth required
  - max containers 1
  - min containers 0
  - service + client Secrets

Hermes worker Function
  - exact Hermes commit
  - exact web backend dependencies
  - max containers 1
  - min containers 0
  - only client Secret
```

The Hermes Function does not receive FreeLLM/provider credentials.

### 5. Made FreeLLMAPI headless authentication deterministic

Added `runtime/freellmapi-bootstrap.mjs`.

Reason: FreeLLMAPI v0.9.8 generates a random unified key on a fresh DB. A headless service needs one stable key known to the Hermes client.

The shim:

1. invokes FreeLLMAPI's exported `initDb()`;
2. validates `FREELLMAPI_API_KEY` uses the upstream `freellmapi-` convention;
3. writes only the `unified_api_key` setting through upstream `setSetting()`.

Bootstrap stdout is discarded so the temporary migration-generated key is not logged.

No raw DB mutation or custom authentication service was added.

### 6. Added zero-provider-key model bootstrap

Added `runtime/freellmapi.default.json` with FreeLLMAPI's current keyless providers:

- `kilo`;
- `ovh`.

This gives the first deployment a real free model pool without asking for temporary provider API keys. A later `FREEAPI_CONFIG_JSON` in the service Secret can configure the full desired provider set through FreeLLMAPI's native declarative mechanism.

### 7. Hardened the Hermes carrier

`agent_carrier.py` now:

- accepts `PUBLIC_NON_PERSONAL` tasks only by contract;
- routes inference only to FreeLLMAPI model `auto`;
- adds Modal proxy-auth headers through Hermes' native custom-provider configuration;
- exposes only Hermes' `web` toolset;
- bounds one worker, max turns/model calls and wall time;
- requires live web lookup in the task instruction;
- requires strict JSON output with sourced claims;
- parses and validates structured output;
- reads Hermes usage/provenance where available;
- fails closed on timeout, runtime failure or invalid result.

A successful Phase-1 run returns `CANDIDATE`, not `RESULT_READY`. Independent evidence verification is Phase 2.

### 8. Added CI and deployment paths

CI now uses full-SHA GitHub Actions and `persist-credentials: false`.

Deterministic job:

- compiles source;
- runs unit/boundary tests;
- imports the Modal topology;
- validates a bounded dry-run plan.

Upstream-runtime job:

- installs Hermes from the exact commit;
- pulls the exact FreeLLMAPI digest;
- boots FreeLLMAPI with the same bootstrap shim and keyless config;
- proves unauthenticated `/v1/models` is rejected;
- proves authenticated model discovery works;
- calls a real free model through `model=auto` and requires `X-Routed-Via`;
- executes the actual local Hermes -> FreeLLMAPI -> model -> Hermes web-tool carrier.

Deployment workflow `.github/workflows/deploy-modal.yml` deploys the same pinned `modal_app.py` and can run the real Modal smoke test.

### 9. Preserved the frozen Control boundary

No Control repository, Runner, queue, scheduler, prompt, carrier or candidate-binding semantics were changed.

The known Control bootstrap-handoff limitation remains separate from Agent implementation and is not worked around with a second Agent-side state/transport plane.

## Remaining evidence before the full GAP-01 acceptance is satisfied

The deployable carrier is not the same as complete Mission acceptance. Still required by the canonical Mission after the first operational deployment:

- successful live Modal deployment/readback;
- real remote Hermes -> protected FreeLLMAPI smoke result;
- hard exact tool-call counter if it remains a Mission requirement and upstream cannot expose it directly;
- 20 measured qualification runs;
- approximately 70% initial human-usefulness gate;
- final exact-head validation and required external review;
- documentation readback after observed runtime behavior.

These remaining items must not be misrepresented as already proven.
