# Interactive Hermes Dashboard

**Mission:** `AGENT_FRAMEWORK`  
**Revision:** `2026-09-10-r2`  
**Gap:** `AGENT-R1-GAP-05`  
**Status:** candidate; user-facing enablement remains gated by exact-head CI, fresh external review and deployment proof.

## Purpose

The first human-facing Agent capability is the **native Hermes Web Dashboard** running on Modal. It is not a new runtime or framework layer.

```text
phone / browser
    |
    v
native Hermes Web Dashboard
native Hermes OAuth gate
    |
    v
bundled Agent host-policy plugin
GitHub-owned Hermes managed policy
    |
    v
protected FreeLLMAPI Modal endpoint
    |
    v
configured free-provider pool
```

Interactive session and memory state belongs only to Hermes. It is not Control state, not a framework task database and not target-project business truth.

## Exact runtime boundary

- Hermes stays pinned to commit `2237be355906fbe6065ce1815711eee52b2d646e`.
- The exact upstream dashboard application/frontend remains the implementation; there is no UI/runtime fork, reverse proxy or second auth server.
- The process starts through the normal upstream command: `hermes dashboard --host 0.0.0.0 --port 9119 --no-open`. This preserves Hermes' native plugin and dashboard-auth bootstrap.
- `runtime/hermes_host_policy/` is installed into Hermes' supported bundled-plugin directory in the image. It extends the pinned runtime without patching Hermes core and remains available when the native UI switches profiles.
- The upstream frontend is built from its own lockfile using checksum-pinned Node `22.22.0`.
- FreeLLMAPI remains the only inference gateway.
- The dashboard receives only the FreeLLMAPI client credential, Modal proxy credential and OAuth client id.
- Upstream provider credential names are derived from the **exact pinned Hermes provider catalog** and materialized empty in managed scope at startup. This repository carries no parallel provider-key denylist.
- One dashboard container is allowed. There is no framework queue, DB, scheduler or second Control lifecycle.

## GitHub-managed effective policy

`runtime/hermes-managed-config.json` is copied to `/etc/hermes/config.yaml`, the native Hermes managed-scope location. Managed values override profile/user values at their owned leaves.

The policy pins:

- provider `freellmapi` and model route `auto`;
- the managed FreeLLMAPI endpoint definition;
- both Hermes fallback lists to empty;
- interactive toolsets `web`, `memory`, `session_search`;
- approval mode `manual`;
- only the `agent-host-policy` general plugin enabled;
- plugin callback timeout `5` seconds;
- SQLite journal mode `delete` for the single-container mounted-volume topology.

At startup `interactive_dashboard.py` imports pinned Hermes' own `provider_catalog()` and writes every declared upstream API-key env name as an empty managed value in `/etc/hermes/.env`. It also rejects startup if any such direct-provider credential is already present in the dashboard process environment.

## Enforcement at native execution boundaries

Managed configuration is necessary but not the final security boundary because a live Hermes session can attempt session-scoped changes. The bundled host-policy plugin therefore enforces the effective capability where work actually executes.

### Inference

Hermes' native `llm_execution` middleware checks every provider execution. Downstream provider I/O is invoked only when all three values still match:

```text
provider = freellmapi
model    = auto
base_url = FREELLMAPI_BASE_URL
```

Any session-scoped `/model` attempt outside that route is short-circuited before downstream provider I/O. Both configured fallback mechanisms are managed empty, so failure cannot escape through a fallback provider.

### Tools

The plugin resolves the exact pinned Hermes tool catalog for the three allowed toolsets. Current resolved names are:

```text
web_search
web_extract
memory
session_search
```

Hermes' native fail-closed `pre_tool_call` hook blocks every other tool. This remains authoritative even if a UI or slash command attempts to widen the displayed/enabled toolset.

## Hosted browser boundary

The host policy is a pure ASGI middleware around the native app. It does not remove or replace Hermes routes.

HTTP `GET`/`HEAD`/`OPTIONS` remain native. Other HTTP methods are denied by default except the smallest required native mutation surfaces:

```text
/auth/*                 authentication lifecycle
/api/auth/*             authenticated WS ticket/session auth
/api/sessions/*         native session lifecycle
/api/chat/image-upload  native chat image attachment
```

This makes config, environment, provider, MCP, plugin, cron, file, git, update/restart and other host-management writes unavailable without maintaining an expanding mutation denylist.

WebSocket policy:

- `/api/console` is denied;
- `/api/pty` is accepted only with Hermes' keep-alive `attach` token;
- the legacy no-attach 1:1 PTY path is denied because it bypasses the native PTY registry;
- the pinned native PTY registry is capped at exactly one session.

The normal managed chat PTY inherits `HERMES_GATEWAY_SESSION=1`. On the pinned Hermes version this makes `bang_shell_enabled()` false and closes the direct `!command` local-shell shortcut without modifying Hermes core.

## Authentication

A non-loopback native Hermes dashboard must be authenticated. The deployment uses pinned Hermes **Nous Portal OAuth** for the internet-facing Modal endpoint.

Required Modal Secret:

```text
name: agent-hermes-dashboard
key:  HERMES_DASHBOARD_OAUTH_CLIENT_ID
value shape: agent:{instance_id}
```

The OAuth client id is externally provisioned. It is intentionally not generated by repository code and is never committed to Git.

Because startup now uses the normal `hermes dashboard` command, Hermes' own plugin discovery, OAuth-provider registration and non-loopback auth gate remain authoritative. Missing/malformed OAuth configuration fails closed; no custom authentication path exists.

## Persistence and concurrency

`agent-hermes-dashboard-state` is a dedicated Modal Volume mounted at `/root/.hermes`.

- Modal permits at most one dashboard container;
- the native Hermes PTY registry is additionally capped at one managed interactive PTY;
- legacy PTY creation outside that registry is rejected;
- Hermes uses SQLite `journal_mode=delete` on the mounted state;
- the container commits the Volume every 30 seconds;
- a normal cold restart can therefore lose at most the latest uncommitted interval;
- Control never reads or writes this Volume.

The plugin is installed as a bundled Hermes extension while its enablement is managed globally, so the same inference/tool policy applies when an existing Hermes profile is selected.

## Cold start

The dashboard scales to zero. Native web assets and the bundled policy plugin are baked into the image; cold start does not run npm, clone Hermes or fetch plugin code.

Startup is fail-closed:

1. resolve the deployed protected FreeLLMAPI endpoint internally;
2. prove the gateway responds under existing bearer + Modal proxy credentials;
3. derive all direct-provider credential names from the pinned Hermes catalog;
4. reject any direct-provider credential already present in the dashboard environment;
5. validate repository-managed config and materialize empty managed credential names;
6. validate the OAuth client id;
7. start the normal native `hermes dashboard` command;
8. native plugin discovery activates the host policy before the server starts.

## Security verification

Candidate CI verifies against the exact pinned Hermes source/runtime:

- policy drift fails closed;
- direct-provider credentials in the dashboard environment are rejected;
- missing gateway credentials and malformed OAuth identity are rejected;
- managed credential names equal the exact pinned Hermes provider catalog;
- both fallback lists remain empty under managed overlay;
- profile/user attempts to replace provider, toolsets or enabled plugins are overridden;
- the bundled host-policy plugin is discovered by native Hermes;
- the exact three toolsets resolve to the four expected safe tools and representative unsafe tools are vetoed by Hermes' own pre-tool hook;
- a valid FreeLLMAPI provider execution reaches the downstream call while a direct OpenAI route is short-circuited before it;
- exact Hermes requires auth for `0.0.0.0`;
- native PTY registry concurrency is exactly one;
- `/api/console` and legacy no-attach `/api/pty` are refused while managed attach PTY remains admitted;
- native PTY children inherit `HERMES_GATEWAY_SESSION=1` and `bang_shell_enabled()` is false;
- existing bounded-worker and real Hermes → FreeLLMAPI runtime probes remain regression gates.

A fresh **external exact-candidate review** is mandatory before user-facing enablement.

## Deployment / enablement

`.github/workflows/deploy-modal.yml` remains the single deployment path and is explicit-dispatch only. Merging source does not automatically expose the dashboard.

Before first dashboard deployment an operator must provision `agent-hermes-dashboard` with the Nous Portal OAuth client id. After deployment verify from a mobile browser:

1. unauthenticated access is rejected/redirected by native Hermes auth;
2. valid owner login succeeds;
3. a public/non-personal chat turn routes through FreeLLMAPI;
4. a session survives a normal container recycle within the documented persistence interval;
5. host-management mutations are unavailable;
6. `/api/console`, legacy PTY creation and `!command` shell execution are unavailable;
7. a second simultaneous managed PTY is refused;
8. an attempted provider/tool widening cannot escape the execution fences.

No target-project production action is part of this proof.

## Governed task boundary

Interactive chat is a user capability, not autonomous project authority. A later feature that submits framework work must use the same governed caller/task contract as every other caller. The dashboard may never self-issue Control acceptance, project `DONE`, production credentials or irreversible business authority.
