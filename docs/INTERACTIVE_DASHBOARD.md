# Interactive Hermes Dashboard

**Status:** implementation candidate; public OAuth registration completed; deployment verification pending  
**Runtime:** native Hermes `0.21.1` Web Dashboard on Modal  
**Endpoint:** `https://market-predictions--agent-carrier-dashboard.modal.run`

## Purpose

Expose Hermes' own browser chat/operations interface without making ChatGPT the execution runtime. GitHub remains source of truth for code and managed policy, Modal supplies compute and persistent interactive state, and FreeLLMAPI remains the only inference gateway.

This surface is separate from the stateless bounded Control worker. Interactive profiles, sessions and memory are user state only: they are not Control mission/runtime state, framework queue state or target-project business truth.

## Architecture

```text
browser / phone
      |
      | HTTPS + Nous OAuth
      v
native Hermes Web Dashboard
      |
      | persistent HERMES_HOME
      v
one Modal Volume
      |
      | managed provider=freellmapi / model=auto
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

Users may use native Hermes profiles, sessions, skills, memory and ordinary non-managed preferences. Managed inference/tool authority cannot be overridden through the dashboard config editor.

No terminal, filesystem mutation, browser automation, code execution or delegation is authorized in this first interactive layer. Those capabilities require the separately governed stronger-isolation path.

## Authentication

The public dashboard uses Hermes' native Nous Portal OAuth provider. A non-loopback Hermes dashboard fails closed when no valid auth provider is configured.

The Nous Portal registration is:

- dashboard name: `Agent Carrier Modal`;
- public base URL: `https://market-predictions--agent-carrier-dashboard.modal.run`;
- callback: `https://market-predictions--agent-carrier-dashboard.modal.run/auth/callback`.

`HERMES_DASHBOARD_OAUTH_CLIENT_ID` is an OAuth public client identifier, not a credential, so it is versioned with the public URL in `runtime_versions.py`. No extra Modal Secret exists for it. Real FreeLLMAPI and Modal proxy credentials remain in the existing protected `agent-hermes` Secret.

The older localhost-only Nous registration is intentionally left untouched until the public login path is verified, after which it can be revoked manually in Nous Portal.

## Persistence

Interactive `HERMES_HOME` is mounted from the single named Modal Volume `agent-hermes-home` at `/data/hermes`.

There is only one dashboard container. A small background commit loop persists Volume changes approximately every 10 seconds. This keeps normal profile/session/memory state across scale-down/restart without introducing Redis, Postgres or another state service.

## Deployment

The dashboard is part of the existing `agent-carrier` Modal App. It does not get a second deployment workflow. The canonical deployment remains:

```text
.github/workflows/deploy-modal.yml
    -> modal deploy modal_app.py
```

That workflow runs `modal_app.py::dashboard_smoke` after deployment. The smoke must prove:

1. the deployed URL exactly matches the registered public URL;
2. `/api/status` is reachable;
3. `auth_required=true`;
4. the `nous` auth provider is active.

The final user-facing verification is then browser login followed by a real `/chat` session through FreeLLMAPI and a persistence check across a container restart/scale-down.

## Domain

The first endpoint deliberately uses Modal's native hostname:

`https://market-predictions--agent-carrier-dashboard.modal.run`

A custom domain is presentation-only and may be added later after an already-owned domain is selected. It must not introduce a second proxy/orchestration architecture merely for branding.
