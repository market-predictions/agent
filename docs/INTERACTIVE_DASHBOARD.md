# Interactive Hermes Dashboard

**Status:** implementation candidate; not yet publicly enabled  
**Runtime:** native Hermes 0.21.1 Web Dashboard on Modal  
**Intended endpoint:** `https://market-predictions--agent-carrier-dashboard.modal.run`

## Purpose

Expose Hermes' own browser chat/operations interface without making ChatGPT the execution runtime. GitHub remains source of truth for code and policy, Modal supplies compute and persistent interactive state, and FreeLLMAPI remains the only inference gateway.

This surface is intentionally separate from the stateless bounded Control worker. Its profiles, sessions and memory are user interaction state only: they are not Control mission/runtime state, framework queue state or target-project business truth.

## Architecture

```text
browser / phone
      |
      | HTTPS + Hermes OAuth
      v
native Hermes Web Dashboard
      |
      | persistent HERMES_HOME
      v
one Modal Volume
      |
      | model=auto / provider=freellmapi
      v
protected FreeLLMAPI service
      |
      v
configured free provider pool
```

The dashboard and TUI are built from the same exact Hermes commit as the bounded worker. Node uses Hermes upstream's pinned Node 26 image identity.

## Managed policy boundary

`runtime/hermes-managed-dashboard.yaml` is mounted at `/etc/hermes/config.yaml`. Hermes' native managed-scope overlay applies it above user/profile configuration.

The first interactive release pins:

- provider `freellmapi`;
- model `auto`;
- no fallback providers;
- `web` as the only agent toolset;
- one concurrent chat session;
- SQLite `journal_mode=delete` for the remote mounted state filesystem;
- a finite per-turn run budget.

Users may still use native Hermes profiles, sessions, skills, memory and ordinary non-managed preferences. Managed inference/tool authority cannot be overridden through the dashboard config editor.

No terminal, filesystem mutation, browser automation, code execution or delegation is authorized in this first interactive layer. Those capabilities require the separately governed stronger-isolation path.

## Authentication

A non-loopback Hermes dashboard must never be started without an auth provider.

The initial implementation uses Hermes' native Nous Portal OAuth provider rather than username/password on a public internet endpoint. Deployment therefore requires the Modal secret `agent-hermes-dashboard-auth` containing:

```text
HERMES_DASHBOARD_OAUTH_CLIENT_ID=agent:<provisioned-instance-id>
```

The client ID must be provisioned/registered through Nous Portal. It is not invented by this repository. Until that credential exists, the dashboard remains implemented but intentionally undeployed.

## Persistence

Interactive `HERMES_HOME` is mounted from the single named Modal Volume `agent-hermes-home` at `/data/hermes`.

There is only one dashboard container. A small background commit loop persists Volume changes approximately every 10 seconds. This means normal profile/session/memory changes survive container scale-down/restart while avoiding a second database or state service.

## Deployment

The dashboard is part of the existing `agent-carrier` Modal App. It does not get a second deployment workflow. The canonical deployment remains:

```text
.github/workflows/deploy-modal.yml
    -> modal deploy modal_app.py
```

When OAuth registration is available, deploy the exact reviewed candidate through that existing workflow and verify:

1. `/api/status` is reachable;
2. unauthenticated private dashboard/API routes are rejected;
3. Nous OAuth login succeeds;
4. `/chat` establishes its authenticated WebSocket/PTY path;
5. a chat reaches FreeLLMAPI and returns model output;
6. a new session survives container restart/scale-down;
7. managed provider/toolset policy remains effective after attempted UI configuration changes.

## Domain

The first endpoint deliberately uses Modal's native hostname:

`https://market-predictions--agent-carrier-dashboard.modal.run`

A custom domain is presentation-only and may be added later after an already-owned domain is selected. It must not introduce a second proxy/orchestration architecture merely for branding.
