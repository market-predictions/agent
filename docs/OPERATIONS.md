# Agent Operations

**Scope:** operate the bounded Hermes -> FreeLLMAPI carrier and the separate interactive Hermes Web Dashboard; promote the same pinned repository state to Modal through one canonical workflow.  
**Control:** frozen; these operations do not modify Control.  
**Generic bounded data lane:** `PUBLIC_NON_PERSONAL` only.

## 1. Current operational fact

Two distinct Hermes surfaces run in the same Modal app:

```text
bounded execution
  -> Hermes worker
  -> protected FreeLLMAPI
  -> real free routed model
  -> live web tool
  -> strict CANDIDATE

interactive browser
  -> Nous Portal OAuth
  -> native Hermes Web Dashboard/TUI
  -> protected FreeLLMAPI
  -> real free routed model
  -> web tools only
```

They share runtime pins and the inference boundary, but they do not share authority semantics. The dashboard is not Control state and is not a target-project write plane.

## 2. Git-owned runtime identity

`runtime_versions.py` is the single current source for Modal SDK `1.5.5`, Hermes `0.21.1` at exact commit `2237be355906fbe6065ce1815711eee52b2d646e`, FreeLLMAPI `0.9.8` at the exact GHCR digest, and stable Modal app/Secret/dashboard identities.

The default FreeLLMAPI bootstrap enables current keyless `kilo` and `ovh`; no provider API key is required for the first model run.

## 3. GitHub -> Modal credential boundary

GitHub Actions authenticates to Modal with exactly two repository Secrets:

```text
MODAL_TOKEN_ID
MODAL_TOKEN_SECRET
```

They must never be committed, echoed or placed in ordinary Variables.

`scripts/bootstrap_modal_runtime.py` idempotently creates runtime material when absent:

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

Generated values are not printed. Complete existing Secret state is preserved; partial state fails closed.

## 4. Promote to Modal

The only cloud promotion workflow is:

```text
.github/workflows/deploy-modal.yml
```

It is **workflow-dispatch only in steady state**. It performs checkout without persisted GitHub credentials, installs pinned Modal tooling, validates deployment credentials, bootstraps runtime Secrets, deploys `modal_app.py`, runs the dashboard auth-boundary smoke and optionally runs the bounded worker smoke or qualification sample.

Manual equivalent from an authenticated machine:

```bash
python -m pip install -r requirements.txt
python -m scripts.bootstrap_modal_runtime
modal deploy modal_app.py
python -m scripts.dashboard_smoke
modal run modal_app.py::smoke
```

When the available automation connector cannot issue a workflow dispatch, a temporary path-limited push trigger may be added to this same workflow for one deliberate promotion and must be removed immediately afterward. Do not create a second deployment workflow.

## 5. Bounded worker success criterion

The bounded smoke passes only when the chain returns a structured `CANDIDATE` after at least one completed allowed live web tool call. `CANDIDATE` is not `RESULT_READY`.

Fail closed on missing/invalid credentials, gateway failure, no eligible model/provider, wall/iteration/model/tool/retry budget violation, invalid result shape or work outside `PUBLIC_NON_PERSONAL`.

The GitHub live integration probe has a narrower responsibility than the 20-run quality qualification. It proves the real FreeLLMAPI/model/Hermes/web-tool path and the fail-closed policy boundary. A stochastic free model may therefore end in either a valid `CANDIDATE` or a recognized strict-output rejection; candidate quality/usefulness remains owned by the fixed measured qualification sample. The production parser is not relaxed for CI.

## 6. Interactive dashboard operation

Public endpoint:

`https://market-predictions--agent-carrier-dashboard.modal.run`

Expected boundary:

- native Nous Portal OAuth;
- anonymous `/api/sessions` rejected;
- provider/model fixed to FreeLLMAPI / `auto` with no fallback provider;
- `HERMES_TUI_TOOLSETS=web` in the dashboard runtime;
- only `web_search` and `web_extract` available to the interactive agent;
- one concurrent Hermes interactive session;
- one active dashboard container maximum;
- persistent `/data/hermes` Modal Volume for profiles/sessions/state;
- `security.allow_lazy_installs=false` so a web-only immutable image never mutates site-packages at runtime;
- auxiliary session-title generation disabled because it is cosmetic and its proxy-auth path is not required for chat;
- `agent.coding_context=off` so running the server from the Hermes source checkout does not auto-select a coding workspace posture.

The explicit `HERMES_TUI_TOOLSETS=web` pin is security-relevant. Do not replace it with the unrelated top-level `toolsets:` config key. In Hermes' TUI gateway, the operator environment pin resolves before coding posture and GUI toolset additions.

A fresh session banner should therefore no longer advertise `terminal`, `file`, `code_execution`, `delegation`, `memory` or other privileged model tools. If it does, treat that as a boundary regression.

## 7. WebSocket compatibility and recovery

The public dashboard previously entered a reconnect loop. Persistent `gui.log` showed browser-facing `/api/ws` connections closing with code `1002`, zero messages and no dispatch crash. Modal request concurrency was necessary but not sufficient. The remaining protocol failure matched `permessage-deflate` negotiation trouble across a WebSocket intermediary.

The dashboard image now applies `runtime/patch_hermes_dashboard.py` to the exact Hermes checkout before installation. It sets Uvicorn `ws_per_message_deflate=False` and fails the image build if the expected source anchor changes. The bounded worker image is not patched.

A later browser log also showed a separate operational failure mode: long event-loop stalls (13s, 10s and 55s) followed by heartbeat/send failure. The same fresh process then performed unnecessary lazy installs while an application-level 10-second Volume commit loop was also active. The dashboard was simplified instead of adding more watchdogs: the custom commit loop was removed, runtime lazy installs/title generation/coding-context were disabled, and Modal's native Volume background-commit mechanism remains the only persistence writer mechanism.

If chat reconnects repeatedly again:

1. confirm the deployed build reports `Hermes dashboard WebSocket compression disabled`;
2. inspect persistent `/data/hermes/logs/gui.log` for close codes, event-loop-stall warnings and message counts;
3. confirm no new `Lazy-installing ...` lines appear in the managed dashboard process;
4. distinguish browser-facing peers from internal `127.0.0.1` gateway peers;
5. do not blindly raise concurrency, add another commit loop or upgrade Hermes without evidence.

A real authenticated browser session has remained connected and completed a live web search after the compression fix. Long-lived stability after the later runtime simplification still requires browser observation.

## 8. Persistence verification

The dashboard mounts one Modal Volume at `/data/hermes`. Modal Volume mounts already use native background commits; there is deliberately no Agent-owned timer thread calling `Volume.commit()`.

The observed logs prove that the dashboard process/container has stopped and later cold-started again, but process restart alone does not prove that the expected interactive user/session state survived. Before calling persistence complete, reconnect after scale-down and verify a known prior profile/session can actually be recovered.

Until that state-recovery check is performed, report persistence as **implemented and restart observed, state recovery not yet proven**.

## 9. Verification without Modal

Canonical repository verification is GitHub Actions. Local deterministic checks:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m compileall -q agent_carrier.py modal_app.py runtime_versions.py scripts tests
```

The exact upstream real-model integration lives in `scripts/ci_runtime_probe.sh` and runs from a clean GitHub-hosted runner.

## 10. Recovery and rotation

If the GitHub Modal token is rotated, replace `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` in GitHub Actions Secrets and rerun a deliberate deployment.

If runtime Secrets must be rotated, treat the complete named pair as one credential boundary. Do not rely on bootstrap to repair partial state.

Never log or paste credential values into issues, PR comments, Actions output or chat.

## 11. Not current operations

Not yet part of the accepted bounded carrier:

- trusted evidence verifier / `RESULT_READY`;
- multi-worker fan-out;
- persistent FreeLLMAPI state;
- Modal Sandbox execution;
- target-project writes/publisher;
- native mobile client.

These capabilities require separate evidence and governance.