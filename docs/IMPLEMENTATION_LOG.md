# Agent Implementation Log

**Project:** `market-predictions/agent`  
**Bounded candidate:** PR #1 / `bootstrap/agent-r1-gap-01`  
**Interactive candidate:** PR #2 / `feature/hermes-dashboard`  
**Control baseline:** frozen; no Control runtime changes were made.

This log records consequential decisions and verification findings. Git history and live Actions remain the detailed evidence; this file is not runtime state.

## 2026-09-09 — bootstrap to operational bounded carrier

- Fresh-read and applied the canonical Execution & Engineering Constitution.
- Pinned Modal SDK `1.5.5`, Hermes `0.21.1` at exact commit `2237be355906fbe6065ce1815711eee52b2d646e`, and FreeLLMAPI `0.9.8` at an exact image digest.
- Corrected the Hermes install path to the upstream-supported exact-source editable installation after ordinary wheel/sdist installation failed by design.
- Added `runtime/freellmapi-bootstrap.mjs` using FreeLLMAPI's own DB API to establish a stable unified key without raw SQLite edits.
- Added a true zero-provider-key Kilo + OVH bootstrap.
- Built the bounded `PUBLIC_NON_PERSONAL` carrier around Hermes only, FreeLLMAPI only, strict sourced JSON candidates, web-only tools and fail-closed budgets.
- Fixed the Hermes CLI `--usage-file` placement and replaced a fragile custom-alias provider path with Hermes' canonical named `providers.freellmapi` configuration.
- Proved direct real `model=auto` inference with `X-Routed-Via` and the full Hermes -> FreeLLMAPI -> real free model -> live web tool -> `CANDIDATE` chain.
- Preserved the frozen Control boundary; no second Agent scheduler/queue/poller was introduced.

## 2026-09-10 — live Modal carrier and qualification

- Bound GitHub Actions to Modal through encrypted `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` only.
- Added idempotent `scripts/bootstrap_modal_runtime.py` for runtime Secrets and the Modal proxy token.
- Fixed Modal image build ordering and neutralized FreeLLMAPI's container entrypoint at the Modal Function boundary while still invoking the upstream helper for the service itself.
- Minimized cross-image imports by keeping `agent_carrier` inside the bounded worker image.
- Proved live Modal deployment and remote bounded smoke to `CANDIDATE`.
- Removed temporary deployment triggers after promotion; kept one canonical explicit-dispatch workflow.
- Completed the fixed 20-run qualification: 18/20 strict candidates, 18/20 human-usable, 18/18 candidate claims manually supported, 0 retries, 0 provider errors. Both rejected runs remained fail-closed.
- Kept `CANDIDATE` distinct from future `RESULT_READY`.

## 2026-09-11 — interactive Hermes dashboard, WebSocket root cause and authority hardening

### Native dashboard instead of custom frontend

Added a separate native Hermes Web Dashboard/TUI on Modal, reusing the pinned Hermes identity and FreeLLMAPI-only inference boundary. The dashboard has one persistent Modal Volume for interactive profiles/sessions/state and no Control/project business authority.

Native Nous Portal OAuth was retained rather than inventing a second authentication layer. A one-character OAuth client-id transcription error discovered during real browser login was corrected and production-auth smoke verifies the resulting boundary.

### Real browser WebSocket failure investigated from evidence

The dashboard initially loaded but chat repeatedly closed. Raising Modal request concurrency fixed ASGI/request starvation but did not fix the connection lifecycle.

Persistent Hermes `gui.log` then showed the decisive evidence:

```text
ws accepted ...
ws closed ... reason=client_disconnect(code=1002,reason=) messages=0
```

The browser-facing socket failed at the WebSocket protocol layer before Hermes processed an application message. Internal localhost gateway sockets were healthy.

An upstream Hermes issue documented the same reconnect signature behind a WebSocket intermediary when `permessage-deflate` was negotiated incorrectly. Rather than upgrade across hundreds of unrelated upstream commits or add another proxy, the dashboard image received one narrow source-anchor-checked patch: Uvicorn `ws_per_message_deflate=False`.

The patch is applied only after checking out the exact pinned Hermes commit and fails the image build if the expected source anchor changes. The bounded worker remains unpatched exact upstream Hermes.

Production deployment explicitly logged:

```text
Hermes dashboard WebSocket compression disabled
```

A subsequent authenticated browser session remained live and completed a real Hermes `Web Search` request with an answer, providing end-to-end browser proof that the WebSocket/chat path works.

### Screenshot exposed a second, security-relevant defect

The successful browser screenshot also showed the Hermes banner advertising `terminal`, `code_execution`, `delegation`, `file`, `memory`, `skills` and other tools even though the intended dashboard policy was web-only.

Pinned Hermes source review showed why: the dashboard/TUI does not use the top-level `toolsets: [web]` key as its session selector. It resolves `platform_toolsets.cli` and may also auto-select coding posture when started inside a repository. The earlier config therefore looked restrictive without actually owning the TUI tool boundary.

Hermes already provides the correct operator-level mechanism: `HERMES_TUI_TOOLSETS`. Its pinned upstream tests explicitly prove that this environment pin wins before coding posture and that GUI surface resolution cannot re-add tools.

The dashboard image is now hard-pinned to:

```text
HERMES_TUI_TOOLSETS=web
```

The ineffective top-level `toolsets:` policy was removed. Startup validation now fails closed unless the operator pin is present. Tests lock this contract.

The authority fix passed exact-head deterministic and upstream-runtime CI and was promoted through the same canonical Modal workflow. Production deploy run `34651151183` completed deployment, dashboard auth smoke and bounded worker smoke successfully. The temporary path-limited promotion trigger was removed immediately afterward.

## 2026-09-12 — restart evidence, event-loop stalls and runtime simplification

### Restart was observed, state recovery was not yet proven

A later browser log showed the prior dashboard process ending and a fresh Hermes process starting again roughly twenty minutes later. This is direct evidence that the scale-down/restart path occurred. The new process opened the persistent `/data/hermes` state area, but the log alone does not prove that a known prior session/profile was successfully restored. Persistence therefore remains implemented with restart observed, while state-recovery proof stays open.

### Long stalls were a separate failure mode from the compression bug

Before the old socket closed, Hermes logged event-loop stalls of roughly 13 seconds, 10 seconds and 55 seconds (`GIL pressure suspected`), followed by heartbeat/send failures. This differs from the earlier `1002` protocol close with zero messages and was not treated as the same bug.

The fresh process also performed runtime lazy installs for unused Bedrock/STT dependencies. At the same time, Agent had its own thread calling `hermes_dashboard_volume.commit()` every 10 seconds.

Upstream/platform review established that both behaviors were unnecessary for this web-only surface:

- Hermes supports `security.allow_lazy_installs=false`;
- auxiliary title generation can be disabled and was already failing through an unnecessary proxy-auth path;
- coding-context detection can be disabled for the dashboard server;
- Modal Volume mounts already provide native background commits, so the custom periodic commit thread duplicated platform functionality.

The smallest root-cause-oriented response was therefore deletion/suppression, not more orchestration:

- removed the custom Volume commit thread;
- set `security.allow_lazy_installs=false`;
- disabled auxiliary title generation;
- set `agent.coding_context=off`;
- kept `HERMES_TUI_TOOLSETS=web` unchanged.

Repository tests now assert these constraints and dashboard startup fails closed if the managed runtime policy is not effective.

### Corrected a flaky live-CI control-flow defect without weakening the carrier

The first exact-head live integration runs after the dashboard-only changes exposed two stochastic free-model output failures: malformed JSON and Markdown-fenced JSON. In both cases the real FreeLLMAPI route and Hermes web-tool loop succeeded and the production carrier correctly rejected the final output.

`scripts/ci_runtime_probe.sh` already contained the intended semantic validation for exactly these fail-closed outcomes, but shell `set -e` terminated on the carrier CLI's expected exit code `1` before that validator could run.

The probe was corrected to capture carrier exit code `0` or `1`, then run the existing semantic assertions. Any other process exit remains a hard integration failure. The production parser, task contract and carrier behavior were not relaxed. Output quality remains governed by the fixed 20-run qualification rather than one stochastic live CI sample.

Exact-head CI #163 then passed both deterministic and live upstream-runtime jobs.

### Simplified dashboard promoted

The smaller runtime was promoted through the single canonical workflow. Deploy run `34653728334` succeeded end-to-end:

```text
deployment                         PASS
dashboard auth-boundary smoke      PASS
bounded-worker smoke               PASS
```

The temporary branch/path promotion trigger was removed immediately afterward, restoring explicit-dispatch-only steady-state deployment.

### Current evidence boundary

**Proven:** bounded Hermes + FreeLLMAPI carrier, 90% qualification, live Modal deployment, real browser OAuth, browser WebSocket/chat with a real web search after the compression fix, production web-only authority pin, observed dashboard process restart, and successful production deployment of the simplified dashboard runtime.

**Still to prove in the browser:** privileged tools remain absent in a fresh post-deploy session; long-lived WebSocket stability after the simplification; recovery of a known prior profile/session after restart/scale-down.

**Still externally gated:** fresh exact-candidate review required by governance before acceptance/merge.

No result from the interactive dashboard is promoted to `RESULT_READY` and no target-project production write authority has been added.