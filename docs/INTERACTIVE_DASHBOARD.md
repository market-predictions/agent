# Interactive Hermes Dashboard

**Status:** corrected Nous client id deployed; local production auth boundary and bounded-worker smoke green; real browser OAuth/chat/persistence verification pending  
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

### OAuth registration correction

The first real browser authorization attempt reached Nous Portal but returned `agent_not_found`. The root cause was a one-character transcription error in the configured client id: a lowercase `l` had been recorded as digit `1`.

The operator-supplied corrected client id is now the repository source of truth and was deployed to the production Modal image on 2026-09-11. Deployment run `34644978301` proved:

- the live image contains the corrected client id;
- Hermes exposes the native `nous` auth provider;
- `/auth/login?provider=nous` constructs an HTTPS Nous authorization request with the configured client id and exact callback;
- anonymous `/api/sessions` access is rejected with HTTP 401;
- the bounded Hermes -> FreeLLMAPI -> model -> web smoke returns a strict `CANDIDATE`.

This proves the local production boundary and exact deployment configuration. It does not yet prove the final Portal authorization round trip because that requires the user's authenticated Nous browser session.

No Portal bearer token or account credential belongs in GitHub, Modal configuration, or chat.

## Persistence

Interactive `HERMES_HOME` is mounted from the single named Modal Volume `agent-hermes-home` at `/data/hermes`.

There is only one dashboard container. A small background commit loop persists Volume changes approximately every 10 seconds. This keeps normal profile/session/memory state across scale-down/restart without introducing Redis, Postgres or another state service.

## Deployment

The dashboard is part of the existing `agent-carrier` Modal App. It does not get a second deployment workflow. The canonical deployment remains explicit-dispatch only:

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

It explicitly reports Portal provisioning as `UNVERIFIED`. A green smoke must never be interpreted as proof that Nous Portal completed an authenticated browser authorization.

The pinned Hermes release may protect `/api/status` differently from newer upstream revisions, so `/api/status` is not used as the auth-gate oracle.

## Remaining user-facing verification

1. browser Nous OAuth login with the corrected client id;
2. a real `/chat` round trip through FreeLLMAPI;
3. persistence across dashboard restart/scale-down;
4. final exact-head CI and fresh external exact-candidate review.

## Domain

The first endpoint deliberately uses Modal's native hostname:

`https://market-predictions--agent-carrier-dashboard.modal.run`

A custom domain is presentation-only and may be added later after an already-owned domain is selected. It must not introduce a second proxy/orchestration architecture merely for branding.
