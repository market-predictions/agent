# Agent Framework Architecture

**Repository:** `market-predictions/agent`  
**Version:** 0.5 candidate — bounded carrier + native interactive Hermes  
**Canonical Mission:** `AGENT_FRAMEWORK` / `2026-09-10-r2`  
**Date:** 2026-09-19  
**Canonical:** yes — this document is the current project architecture truth.

## 1. Purpose

`agent` is a reusable carrier for bounded autonomous AI work plus one separate, human-facing Hermes interaction surface.

```text
BOUNDED WORK
authorized task
  -> pinned Hermes worker
  -> protected FreeLLMAPI
  -> configured free-provider pool
  -> strict CANDIDATE
  -> later independent verifier
  -> caller/project authority

INTERACTIVE USER
phone/browser
  -> native pinned Hermes Web Dashboard
  -> native OAuth gate
  -> small host-owned policy fence
  -> GitHub-managed Hermes policy
  -> protected FreeLLMAPI
  -> configured free-provider pool
```

The framework is not a project database, Control replacement, business scheduler, generic queue, publisher or production authority plane. Target projects own business truth and irreversible actions. Control remains Mission/lifecycle authority when it is the caller.

## 2. Fixed architecture decisions

1. **Hermes is the only agent runtime.**
2. **FreeLLMAPI is the only inference gateway.** No direct-provider bypass is authorized.
3. **Modal is the selected bounded cloud execution target.** It is not a second business/state plane.
4. **GitHub owns code/config/docs truth.**
5. **The generic free-provider lane is `PUBLIC_NON_PERSONAL`.**
6. **Generation and verification are separate authorities.** Worker output is `CANDIDATE`; only the later trusted verifier may introduce `RESULT_READY`.
7. **Interactive Hermes is separate user state.** It cannot become Control runtime state, framework task truth or target-project canonical business data.
8. **Complexity is earned.** No second runtime, framework DB/queue, recursive swarm, custom dashboard, custom auth service or production credential bridge exists.

## 3. Runtime provenance

`runtime_versions.py` owns correctness-relevant identities:

- Modal SDK `1.5.5`;
- Hermes `0.21.1`, tag `v2026.9.7`, exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8`, exact GHCR digest;
- Node `22.22.0`, checksum-pinned for the upstream Hermes web build;
- stable Modal app/Secret/Volume names.

Hermes is installed through the upstream-supported editable source path from the exact commit. The native web frontend is built from the same source checkout and upstream npm lockfile; there is no forked frontend.

## 4. Bounded worker plane — integrated GAP-01

```text
PUBLIC_NON_PERSONAL objective
        |
        v
Hermes one-shot
exact pinned source
web toolset only
        |
        v
named provider: freellmapi
model: auto
        |
        v
protected FreeLLMAPI Modal web service
        |
        v
free routed model
        |
        v
Hermes live web lookup
        |
        v
strict CANDIDATE
```

Hard bounds include one concurrent worker task, bounded wall time, model executions, tool executions and retry count. The worker has no terminal/shell, project filesystem mutation, browser automation, messaging, delegation, persistent Hermes memory or target-project production credentials.

The fixed 20-run qualification achieved 90% human-usable output. This evidence does not create verifier or business-final authority.

## 5. FreeLLMAPI authority boundary

FreeLLMAPI holds provider configuration/credentials. Hermes gets only:

- stable `FREELLMAPI_API_KEY`;
- Modal proxy client key/secret for the protected FreeLLMAPI endpoint.

The credential-bearing gateway URL is resolved from the deployed Modal Function inside trusted runtime code; callers do not provide it.

FreeLLMAPI bootstrap uses its own exported initialization/settings APIs, not raw DB edits. The current first path can use keyless Kilo/OVH providers. No paid fallback is hidden behind the carrier.

## 6. Interactive Hermes plane — GAP-05 candidate

The human-facing layer is the **exact native Hermes Web Dashboard**:

```text
HTTPS Modal endpoint
  -> Hermes non-loopback auth gate
  -> Nous Portal OAuth
  -> hosted route/capability fence
  -> native dashboard / PTY / TUI
  -> managed effective policy
  -> protected FreeLLMAPI
```

No reverse proxy, custom auth server, frontend fork or second agent runtime is introduced. `interactive_dashboard.py` wraps the exact native app only long enough to apply the hosted Mission policy and then calls Hermes' own server.

### Effective managed policy

The dashboard image installs repository-owned config at:

```text
/etc/hermes/config.yaml
```

At startup, the host wrapper derives every upstream provider credential env name from the **exact pinned Hermes `provider_catalog()`** and materializes those names empty at:

```text
/etc/hermes/.env
```

This removes the previous duplicate provider-key inventory from this repository. Hermes itself remains the one credential-name source for the pinned runtime.

Pinned interactive capability:

- provider: `freellmapi`;
- model route: `auto`;
- tools: `web`, `memory`, `session_search`;
- approvals: `manual`;
- SQLite journal mode: `delete`.

Startup rejects any direct upstream provider credential already present in the dashboard process environment.

### Hosted administration fence

Hermes' native dashboard has broader self-hosted administration surfaces than this Mission authorizes. Before the native server starts, the wrapper removes mutation routes under:

```text
/api/config
/api/env
/api/providers
/api/mcp
/api/dashboard/plugins
/api/cron
```

Read-only/status paths remain where Hermes exposes them. The separate `/api/console` WebSocket is removed because it can dispatch mutating Hermes administration commands.

The normal `/api/pty` chat remains native. Its child environment inherits `HERMES_GATEWAY_SESSION=1`; on the exact pinned Hermes version that makes `bang_shell_enabled()` false, closing the direct local `!command` shell shortcut without changing Hermes source.

### Authentication

The public Modal URL requires a valid externally provisioned:

```text
HERMES_DASHBOARD_OAUTH_CLIENT_ID=agent:{instance_id}
```

held in Modal Secret `agent-hermes-dashboard`. Absence/malformed identity fails closed. Hermes' own non-loopback auth gate remains authoritative; the public endpoint does not downgrade to unauthenticated operation.

### Interactive state

Hermes home is mounted from one dedicated Modal Volume:

```text
agent-hermes-dashboard-state -> /root/.hermes
```

Only one dashboard container may run. The Volume is committed every 30 seconds and stores interactive Hermes session/memory state only. Control and target projects do not use it as canonical state. This is the sole persistence primitive added by GAP-05.

## 7. Authority separation

```text
Hermes worker/dashboard      generation + user interaction
FreeLLMAPI                   model routing boundary
future trusted verifier      evidence verification
Control                      Mission/lifecycle authority
caller/target project        business truth + irreversible acceptance
```

`CANDIDATE != RESULT_READY != business DONE`.

Interactive Hermes cannot self-grant project credentials, Control transitions, production writes or irreversible business actions. A future dashboard-triggered framework task must use the same governed caller/task contract as every other caller.

## 8. Deployment model

`.github/workflows/deploy-modal.yml` is the single deployment workflow and remains explicit-dispatch only.

Current Modal topology is one app containing:

- protected FreeLLMAPI web service;
- bounded Hermes worker Function;
- GAP-05 native Hermes dashboard web service candidate;
- exactly one dedicated dashboard state Volume.

Ordinary pushes do not deploy. A source merge is therefore not user-facing enablement.

GAP-05 requires exact-head CI, fresh external review and OAuth provisioning before the dashboard may be promoted for user-facing proof.

## 9. Verification

Candidate CI contains:

1. deterministic compile/tests/topology contracts;
2. exact pinned Hermes installation;
3. exact pinned provider-catalog-to-managed-env equality proof;
4. native managed-scope provider/tool immutability proof;
5. native non-loopback auth-gate proof;
6. native PTY environment inheritance + `bang_shell_enabled() == false` proof;
7. exact route-fence proof for config/env/provider/MCP/plugin/cron mutations and `/api/console`;
8. exact FreeLLMAPI image pull;
9. existing real Hermes → FreeLLMAPI → free model → web-tool probe.

Live mobile/session-persistence evidence remains an enablement gate after external exact-candidate review and OAuth provisioning.

## 10. Current Mission sequence

Mission revision `2026-09-10-r2` governs:

```text
GAP-01 bounded carrier        DONE
  -> GAP-05 interactive web   current candidate
  -> GAP-02 trusted verifier
  -> GAP-03 fan-out experiment
  -> GAP-04 bounded caller integration
```

Parallelism is still experimental until GAP-03 proves value. A framework DB/queue, Sandbox tooling or project publisher is not introduced speculatively.

## 11. Current non-goals

Do not add without a later concrete governed requirement:

- second agent runtime;
- direct model-provider integration;
- custom dashboard/auth implementation;
- recursive/unbounded delegation;
- framework business DB or queue;
- generic scheduler;
- target-project production credentials in Hermes;
- hidden paid inference fallback;
- project publisher/admin proxy;
- using interactive state as Control or project truth.

Implementation sequence is in `docs/ROADMAP.md`; interactive security/operations are in `docs/INTERACTIVE_DASHBOARD.md` and `docs/OPERATIONS.md`.
