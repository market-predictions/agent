# Interactive Hermes Dashboard

**Status:** implementation candidate; public OAuth registration completed; deployment verification in progress  
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

After deployment the workflow runs `python -m scripts.dashboard_smoke` directly against the production hostname. It deliberately does not use `modal run` for dashboard verification, because a Modal local entrypoint creates temporary `-dev.modal.run` web functions and therefore is not a production-endpoint test.

The production smoke proves:

1. `/api/auth/providers` is publicly reachable for login bootstrap;
2. the `nous` OAuth provider is registered;
3. anonymous access to `/api/sessions` is rejected fail-closed (401 or a same-origin redirect to `/login`);
4. redirects are not followed by the probe, so an OAuth browser round-trip cannot masquerade as a health check.

The pinned Hermes release may protect `/api/status` differently from newer upstream revisions, so `/api/status` is not used as the auth-gate oracle. Provider bootstrap plus rejection of a genuinely gated API route tests the security property directly.

The final user-facing verification is browser login followed by a real `/chat` session through FreeLLMAPI and a persistence check across a container restart/scale-down.

## Domain

The first endpoint deliberately uses Modal's native hostname:

`https://market-predictions--agent-carrier-dashboard.modal.run`

A custom domain is presentation-only and may be added later after an already-owned domain is selected. It must not introduce a second proxy/orchestration architecture merely for branding.
