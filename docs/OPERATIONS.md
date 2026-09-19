# Agent Framework Operations

**Scope:** bounded worker plus the governed GAP-05 interactive-dashboard candidate.  
**Canonical Mission:** `AGENT_FRAMEWORK` / `2026-09-10-r2`.  
**Data lane:** generic free-provider work remains `PUBLIC_NON_PERSONAL` only.

## 1. Operational topology

```text
bounded task path
  -> pinned Hermes worker
  -> protected FreeLLMAPI
  -> free-provider pool
  -> CANDIDATE

interactive user path (GAP-05 candidate)
  -> native Hermes Web Dashboard
  -> native OAuth gate
  -> hosted route/capability fence
  -> GitHub-managed Hermes policy
  -> protected FreeLLMAPI
  -> free-provider pool
```

The paths share Hermes and FreeLLMAPI but not authority/state. Interactive session/memory state is not Control state or target-project business truth.

## 2. Runtime identity

`runtime_versions.py` is the single source for correctness-relevant pins and Modal object names, including:

- Modal SDK `1.5.5`;
- Hermes `0.21.1`, exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8`, exact image digest;
- Node `22.22.0`, exact Linux-x64 archive checksum for the native Hermes frontend build;
- Modal app, Secret and dashboard Volume names.

Do not duplicate these pins elsewhere.

## 3. GitHub → Modal credential

GitHub Actions uses encrypted repository Secrets:

```text
MODAL_TOKEN_ID
MODAL_TOKEN_SECRET
```

Never commit, echo or paste them. They authenticate deployment only; they are not exposed to Hermes.

## 4. Existing runtime-secret bootstrap

`scripts/bootstrap_modal_runtime.py` remains the canonical bootstrap for the bounded carrier and FreeLLMAPI. It creates/preserves:

### `agent-hermes`

```text
FREELLMAPI_API_KEY
MODAL_PROXY_KEY
MODAL_PROXY_SECRET
```

### `agent-freellmapi`

```text
ENCRYPTION_KEY
```

It is idempotent, hides generated values and fails closed on partial state.

## 5. Dashboard OAuth prerequisite

The public Modal dashboard uses the native pinned Hermes Nous Portal OAuth provider. Before the **first user-facing dashboard deployment**, provision a separate Modal Secret:

```text
name: agent-hermes-dashboard
HERMES_DASHBOARD_OAUTH_CLIENT_ID=agent:{instance_id}
```

This value is provisioned externally through the Hermes/Nous OAuth registration flow. Repository code deliberately does not invent or persist it.

If the Secret/key is absent or malformed, the dashboard must not start. Do not substitute native basic-auth merely to bypass this prerequisite.

## 6. Managed interactive policy

The dashboard image installs:

```text
/etc/hermes/config.yaml <- runtime/hermes-managed-config.json
```

At container startup `interactive_dashboard.py` imports the exact pinned Hermes `provider_catalog()` and materializes every declared upstream provider credential env name as an empty managed value in:

```text
/etc/hermes/.env
```

There is deliberately no repository-maintained provider-key denylist. Pinned Hermes is the one provider credential-name source.

Pinned effective policy:

- provider `freellmapi`;
- model `auto`;
- toolsets `web`, `memory`, `session_search`;
- approvals `manual`;
- SQLite journal mode `delete`.

Startup rejects a process environment containing any pinned upstream-provider credential.

## 7. Hosted management boundary

Before calling Hermes' own `web_server.start_server()`, the wrapper removes native mutation routes under:

```text
/api/config
/api/env
/api/providers
/api/mcp
/api/dashboard/plugins
/api/cron
```

Read/status routes remain. `/api/console` is removed completely because that WebSocket can invoke mutating Hermes administration commands.

The native `/api/pty` chat remains. Its child process inherits:

```text
HERMES_GATEWAY_SESSION=1
```

On the exact pinned Hermes runtime this disables local `!command` bang-shell execution. No Hermes source patch is carried.

## 8. Interactive state

Dedicated Modal Volume:

```text
agent-hermes-dashboard-state -> /root/.hermes
```

Operational rules:

- exactly one GAP-05 persistence primitive: this dashboard Volume;
- at most one dashboard container;
- no competing interactive-state writer;
- Volume commit interval 30 seconds;
- normal cold-restart state-loss bound is the latest uncommitted interval;
- the Volume is not inspected/mutated by Control;
- never place target-project canonical data or production credentials in it.

## 9. Verification before enablement

GAP-05 remains non-user-facing until all are true:

1. exact candidate head/base is frozen;
2. both Agent CI jobs pass on that exact head;
3. fresh external exact-candidate review passes;
4. OAuth client id is provisioned;
5. explicit Modal deployment/mobile proof succeeds.

Source merge and runtime deployment are separate operations. Ordinary pushes do not deploy.

## 10. Canonical deployment

Single path:

```text
.github/workflows/deploy-modal.yml
```

It remains workflow-dispatch only. For the bounded carrier, `run_smoke=true` executes a real remote Hermes → FreeLLMAPI smoke.

After GAP-05 external review has passed and the OAuth Secret exists, deploy the same `modal_app.py`. The dashboard endpoint is part of that one topology; do not create a second deployment workflow.

Manual equivalent from an authenticated operator environment:

```bash
python -m pip install -r requirements.txt
python -m scripts.bootstrap_modal_runtime
modal deploy modal_app.py
```

Do not perform this user-facing dashboard promotion before the external-review gate.

## 11. Post-deploy GAP-05 proof

From a phone/mobile browser and an unauthenticated browser session verify:

1. unauthenticated access is gated and cannot enter dashboard APIs/WebSockets;
2. the owner OAuth login succeeds;
3. Hermes `/api/status` reports authentication required with the expected provider;
4. a public/non-personal chat turn succeeds through FreeLLMAPI;
5. direct-provider API-key/OAuth/custom-provider writes are unavailable;
6. config/MCP/plugin/cron mutation surfaces are unavailable;
7. `/api/console` is unavailable and `!command` does not execute a local shell in chat;
8. effective provider/model/tool settings remain the GitHub-managed FreeLLMAPI safe set;
9. a session is visible after a normal dashboard container recycle within the documented persistence semantics;
10. no Control/project production action is available from the interactive toolset.

Preserve only non-secret evidence needed for external review/acceptance.

## 12. Failure semantics

Fail closed on:

- missing/invalid Modal deployment credentials;
- partial bounded-runtime Secret state;
- invalid FreeLLMAPI auth/health;
- no eligible free model route;
- missing/malformed dashboard OAuth client id;
- unavailable/empty pinned Hermes provider catalog;
- direct upstream provider credential in the dashboard process environment;
- native route-fence mismatch on the pinned dashboard;
- invalid/non-structured bounded-worker result;
- budget exhaustion;
- disallowed data or requested authority.

There is no paid fallback, direct-provider bypass, production-write fallback, second runtime, framework queue or shadow scheduler.

## 13. Local/CI verification

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m compileall -q agent_carrier.py agent_budget_plugin.py interactive_dashboard.py modal_app.py runtime_versions.py scripts tests
```

`.github/workflows/ci.yml` additionally installs the exact pinned upstream Hermes commit and proves:

- pinned provider-catalog credential coverage;
- native managed-scope provider/tool enforcement;
- mandatory non-loopback dashboard authentication;
- PTY inheritance of gateway-session mode and disabled bang-shell;
- removal of hosted config/env/provider/MCP/plugin/cron mutations and `/api/console`;
- exact FreeLLMAPI image plus the existing real Hermes/FreeLLMAPI tool path.

## 14. Next governed capability

After GAP-05 is accepted, Mission r2 makes `AGENT-R1-GAP-02` (independent trusted evidence verifier) the next eligible gap. Do not start it under A8 authority.
