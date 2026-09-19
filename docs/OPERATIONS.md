# Agent Framework Operations

**Scope:** bounded worker plus governed GAP-05 interactive-dashboard candidate.  
**Canonical Mission:** `AGENT_FRAMEWORK` / `2026-09-10-r2`.  
**Data lane:** generic free-provider work remains `PUBLIC_NON_PERSONAL` only.

## 1. Operational topology

```text
bounded task
  -> pinned Hermes worker
  -> protected FreeLLMAPI
  -> CANDIDATE

interactive user
  -> native Hermes Web Dashboard
  -> native OAuth gate
  -> bundled agent-host-policy plugin
  -> managed Hermes policy
  -> protected FreeLLMAPI
```

The paths share Hermes and FreeLLMAPI but not authority/state. Interactive session/memory state is not Control state or target-project business truth.

## 2. Runtime identity

`runtime_versions.py` is the single source for correctness-relevant pins and Modal object names:

- Modal SDK `1.5.5`;
- Hermes `0.21.1`, exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8`, exact image digest;
- Node `22.22.0`, checksum-pinned for the native Hermes frontend build;
- stable Modal app, Secret and dashboard Volume names.

Do not duplicate these pins elsewhere.

## 3. Deployment credentials

GitHub Actions deployment uses repository Secrets `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`. Never commit, echo or expose them to Hermes.

`scripts/bootstrap_modal_runtime.py` remains canonical for the bounded carrier/FreeLLMAPI Secrets:

```text
agent-hermes:      FREELLMAPI_API_KEY, MODAL_PROXY_KEY, MODAL_PROXY_SECRET
agent-freellmapi:  ENCRYPTION_KEY
```

It is idempotent and fails closed on partial state.

## 4. Dashboard OAuth prerequisite

Before first user-facing dashboard deployment provision:

```text
Modal Secret: agent-hermes-dashboard
HERMES_DASHBOARD_OAUTH_CLIENT_ID=agent:{instance_id}
```

The value comes from the Hermes/Nous OAuth registration flow. Repository code does not invent or persist it. Missing/malformed identity must prevent dashboard startup.

## 5. Managed interactive policy

The dashboard image installs:

```text
/etc/hermes/config.yaml <- runtime/hermes-managed-config.json
```

The effective policy pins:

- provider `freellmapi`, model `auto`;
- `fallback_providers=[]` and `fallback_model=[]`;
- toolsets `web`, `memory`, `session_search`;
- approvals `manual`;
- only general plugin `agent-host-policy` enabled;
- plugin callback timeout `5` seconds;
- SQLite journal mode `delete`.

At startup `interactive_dashboard.py` derives every upstream-provider API-key env name from exact pinned Hermes `provider_catalog()` and materializes it empty in `/etc/hermes/.env`. There is no repository-maintained provider-key denylist. Startup also rejects any direct upstream-provider credential already present in the dashboard environment.

## 6. Native host-policy plugin

`runtime/hermes_host_policy/` is copied into the pinned Hermes bundled-plugin directory in the dashboard image. This is an upstream-supported extension seam and remains available when Hermes selects another profile.

The process starts through:

```text
hermes dashboard --host 0.0.0.0 --port 9119 --no-open
```

Do not reintroduce a custom `start_server()` wrapper; the native CLI path owns plugin discovery and dashboard-auth registration.

### Inference

The plugin's `llm_execution` middleware invokes downstream model I/O only when provider/model/base URL remain exactly the managed FreeLLMAPI route. A session-local provider change therefore fails before direct provider I/O.

### Tools

The plugin resolves pinned Hermes' own `web`, `memory`, `session_search` toolsets. Current exact allowed tools are:

```text
web_search
web_extract
memory
session_search
```

Every other tool is vetoed by native `pre_tool_call`. Hermes already treats a timed-out `pre_tool_call` plugin callback as fail-closed.

### Browser/PTY

Pure ASGI policy:

- read methods remain native;
- non-read HTTP methods default-deny;
- allowed mutations are limited to `/auth/*`, `/api/auth/*`, `/api/sessions/*` and `/api/chat/image-upload`;
- `/api/console` WebSocket is denied;
- `/api/pty` requires the native keep-alive `attach` token;
- the pinned native PTY registry maximum is set to one;
- legacy no-attach 1:1 PTY creation is denied;
- `HERMES_GATEWAY_SESSION=1` is inherited by the PTY child, disabling pinned Hermes `!command` bang-shell mode.

## 7. Interactive state

Dedicated Modal Volume:

```text
agent-hermes-dashboard-state -> /root/.hermes
```

Rules:

- max dashboard containers: one;
- max managed interactive PTYs: one;
- one persistence primitive: this Volume;
- no competing interactive-state writer;
- Volume commit every 30 seconds;
- normal cold-restart loss bound is the latest uncommitted interval;
- Control never reads/writes the Volume;
- never store target-project canonical data or production credentials there.

## 8. Verification before enablement

GAP-05 remains non-user-facing until all are true:

1. exact final candidate head/base frozen;
2. both Agent CI jobs pass on that exact head;
3. fresh external exact-candidate review PASS;
4. OAuth client id provisioned;
5. explicit Modal deployment/mobile proof succeeds.

Source merge and runtime deployment are separate operations. Ordinary pushes do not deploy.

## 9. Canonical deployment

Single deployment path:

```text
.github/workflows/deploy-modal.yml
```

It remains workflow-dispatch only. Do not create a separate dashboard deployment workflow.

Manual equivalent from an authenticated operator environment:

```bash
python -m pip install -r requirements.txt
python -m scripts.bootstrap_modal_runtime
modal deploy modal_app.py
```

Do not perform user-facing GAP-05 promotion before the external-review gate.

## 10. Post-deploy GAP-05 proof

From a phone/mobile browser and an unauthenticated browser session verify:

1. unauthenticated dashboard access cannot enter native APIs/WebSockets;
2. owner OAuth login succeeds;
3. a public/non-personal chat turn succeeds through FreeLLMAPI;
4. attempted direct-provider model switching does not generate downstream provider I/O;
5. unsafe tool execution is denied;
6. host-management HTTP mutations are unavailable;
7. `/api/console`, legacy PTY and `!command` shell execution are unavailable;
8. a second managed PTY is refused;
9. session state survives normal container recycle within documented persistence semantics;
10. no Control/project production action is available.

Preserve only non-secret evidence needed for review/acceptance.

## 11. Failure semantics

Fail closed on:

- invalid Modal deployment/runtime credentials;
- FreeLLMAPI health/auth failure;
- missing/malformed dashboard OAuth client id;
- empty/unavailable pinned provider catalog;
- direct upstream-provider credential in dashboard environment;
- managed policy drift or non-empty provider fallback;
- host-policy plugin unavailable/not enabled;
- provider execution outside FreeLLMAPI;
- tool execution outside the four resolved safe tools;
- legacy PTY/concurrency bypass;
- invalid/non-structured bounded-worker result or budget exhaustion.

There is no paid fallback, direct-provider inference fallback, production-write fallback, second runtime, framework queue or shadow scheduler.

## 12. Local/CI verification

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m compileall -q agent_carrier.py agent_budget_plugin.py interactive_dashboard.py modal_app.py runtime_versions.py runtime/hermes_host_policy scripts tests
```

CI additionally installs exact pinned Hermes and proves plugin discovery, managed provider/tool/plugin/fallback authority, native auth, exact tool veto, LLM short-circuit, PTY concurrency/legacy-path fence, disabled bang-shell, exact FreeLLMAPI image and the real Hermes → FreeLLMAPI → web-tool regression path.

## 13. Next governed capability

After GAP-05 is accepted, Mission r2 makes `AGENT-R1-GAP-02` (independent trusted evidence verifier) the next eligible gap. Do not start it under A8 authority.
