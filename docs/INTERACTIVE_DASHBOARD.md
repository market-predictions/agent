# Interactive Hermes Dashboard

**Status:** local production auth boundary proven; browser OAuth blocked because Nous Portal reports the configured client id as unknown/unprovisioned  
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

The intended self-hosted Portal registration is:

- dashboard name: `Agent Carrier Modal`;
- public base URL: `https://market-predictions--agent-carrier-dashboard.modal.run`;
- callback: `https://market-predictions--agent-carrier-dashboard.modal.run/auth/callback`.

`HERMES_DASHBOARD_OAUTH_CLIENT_ID` is a public OAuth client identifier, not a credential, so the selected id is versioned with the public URL in `runtime_versions.py`. Real FreeLLMAPI and Modal proxy credentials remain in the existing protected `agent-hermes` Secret.

### Current external blocker

A real browser authorization attempt on 2026-09-11 reached Nous Portal, but the Portal returned `agent_not_found` and reported the configured `agent:...` client id as unknown or unprovisioned. Therefore:

- local Hermes provider activation is proven;
- the local fail-closed auth gate is proven;
- the OAuth request wiring can be verified without following the external redirect;
- **Portal-side provisioning is not proven and the current browser login is not functional.**

The authoritative fix is to provision or re-provision this self-hosted dashboard in Nous Portal and then replace `HERMES_DASHBOARD_OAUTH_CLIENT_ID` with the client id actually returned by the Portal. Do not invent an `agent:` id and do not substitute a weaker public authentication mechanism.

Preferred operator path:

1. open Nous Portal **Local Dashboards** and create/update `Agent Carrier Modal`;
2. use the exact callback `https://market-predictions--agent-carrier-dashboard.modal.run/auth/callback`;
3. copy only the returned public `agent:...` client id into this repository;
4. never copy Portal bearer tokens or account credentials into GitHub or chat.

Hermes' native CLI is the equivalent supported path for an authenticated local operator:

```text
hermes dashboard register \
  --name "Agent Carrier Modal" \
  --redirect-uri "https://market-predictions--agent-carrier-dashboard.modal.run/auth/callback"
```

The CLI obtains the user's Portal access token locally, submits the self-hosted-client registration to the Portal, and writes the returned client id to the local Hermes environment. That access token is not needed by this repository.

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

The production smoke proves only properties that the deployed Hermes service can establish without an authenticated Portal user:

1. `/api/auth/providers` is publicly reachable for login bootstrap;
2. the `nous` OAuth provider is active locally;
3. `/auth/login?provider=nous` constructs an HTTPS authorization request to `portal.nousresearch.com` with the configured client id and the exact public callback;
4. anonymous access to `/api/sessions` is rejected fail-closed (401 or a same-origin redirect to `/login`).

It explicitly reports Portal provisioning as `UNVERIFIED`. A green smoke must never be interpreted as proof that Nous Portal recognizes the client id.

The earlier deployed runtime candidate `9e64d603978fff3c51e17882d6e5c36716629793` proved the local auth gate and exact Hermes/FreeLLMAPI runtime path. The subsequent real browser attempt exposed the missing external provisioning proof, so the earlier `status=OK` result is scoped to the local auth boundary rather than end-to-end OAuth.

The pinned Hermes release may protect `/api/status` differently from newer upstream revisions, so `/api/status` is not used as the auth-gate oracle.

After Portal provisioning is corrected, remaining user-facing verification is:

1. browser Nous OAuth login;
2. a real `/chat` round trip through FreeLLMAPI;
3. persistence across dashboard restart/scale-down;
4. final exact-head CI and fresh external exact-candidate review.

## Domain

The first endpoint deliberately uses Modal's native hostname:

`https://market-predictions--agent-carrier-dashboard.modal.run`

A custom domain is presentation-only and may be added later after an already-owned domain is selected. It must not introduce a second proxy/orchestration architecture merely for branding.
