# Agent Implementation Log

**Project:** `market-predictions/agent`  
**Candidate:** PR #1 / `bootstrap/agent-r1-gap-01`  
**Control baseline:** frozen; no Control runtime changes were made.

This log records consequential Phase-1 decisions and verification findings. Git history and live Actions remain the detailed evidence; this file is not runtime state.

## 2026-09-09 — bootstrap to operational carrier

### 1. Applied the canonical engineering doctrine

Fresh-read the canonical Google Drive **Execution & Engineering Constitution** and applied the required priorities: smallest complete solution, no overengineering, first principles, proven upstream primitives, autonomous verification, and cleanup/documentation alignment as part of Done.

### 2. Revalidated and pinned upstream runtimes

Selected exact identities:

- Modal SDK `1.5.5`;
- Hermes `0.21.1` / tag `v2026.9.7` / commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8` / exact GHCR digest stored in `runtime_versions.py`.

No `latest` runtime is used by the carrier.

### 3. Corrected the Hermes installation assumption

The first upstream integration run proved that Hermes intentionally rejects ordinary wheel/sdist installation:

```text
Building wheels or sdists for hermes-agent is not supported.
```

The implementation was changed to Hermes' supported source-development path:

```text
clone exact repository
-> checkout exact commit
-> assert HEAD
-> editable install
```

CI proves that exact path from a clean runner. `modal_app.py` uses the same method when building the cloud image.

### 4. Made FreeLLMAPI headless and deterministic

FreeLLMAPI v0.9.8 creates a random unified bearer during a fresh migration and has no environment override for it.

Added `runtime/freellmapi-bootstrap.mjs`, which uses upstream's own exported `initDb()` and `setSetting()` API to install the stable `FREELLMAPI_API_KEY`. Bootstrap stdout is suppressed so the temporary migration-generated key is not logged.

No raw SQLite editing or extra authentication service was introduced.

### 5. Added a true zero-provider-key bootstrap

Added `runtime/freellmapi.default.json` with current upstream keyless providers:

- `kilo`;
- `ovh`.

This gives the first carrier a real free model path without a temporary provider API key. `FREEAPI_CONFIG_JSON` may later replace the default declarative config through FreeLLMAPI's own startup mechanism.

### 6. Built and constrained the carrier

`agent_carrier.py` now:

- accepts `PUBLIC_NON_PERSONAL` work by contract;
- uses Hermes only;
- uses FreeLLMAPI only;
- configures the named Hermes provider `freellmapi` with model `auto`;
- exposes only Hermes' `web` toolset;
- requires a live public-source lookup in the task instruction;
- requires strict JSON with sourced claims;
- bounds concurrency, model turns/calls and wall time;
- reads Hermes usage when available;
- returns `CANDIDATE` on success and fails closed otherwise.

Upstream provider keys never enter Hermes.

### 7. Corrected two Hermes CLI/runtime integration defects discovered by real CI

The live integration sequence found two non-theoretical mistakes.

**CLI flag placement.** `--usage-file` is a top-level Hermes flag; placing it after `chat` caused argument rejection. This was fixed and locked with tests.

**Direct custom alias endpoint loss.** On the selected Hermes release, our initial `model_aliases -> provider: custom` path resolved the model but fell back to the OpenRouter default endpoint instead of the FreeLLMAPI URL. We removed the fragile alias path and switched to Hermes' canonical keyed `providers:` configuration:

```text
providers.freellmapi
  -> explicit base_url
  -> key_env=FREELLMAPI_API_KEY
  -> model=auto
```

The programmatic invocation was also simplified to Hermes' top-level `-z/--oneshot` path, which is designed to write only the final model response to stdout. The Hermes iteration bound is supplied through `HERMES_MAX_ITERATIONS`; the subprocess timeout remains the outer wall bound.

No compatibility shim was added around Hermes.

### 8. Proved the real free model path

The clean GitHub-hosted integration run proved:

```text
FreeLLMAPI ready
configured providers: Kilo + OVH
87 models exposed
model=auto request succeeds
X-Routed-Via present
```

One observed successful free route was Kilo -> `nvidia/nemotron-3-super-120b-a12b:free`. The route is dynamic and is evidence, not a hard-coded model dependency.

### 9. Proved the full Hermes chain

The same clean-run proof then completed:

```text
Hermes 0.21.1
-> named FreeLLMAPI provider
-> real free routed model
-> Hermes live web tool
-> strict structured CANDIDATE
```

The CI log reported:

```text
direct model route: OK
Hermes -> FreeLLMAPI -> model -> web: OK
```

This establishes a real operational carrier, not a mock/dry-run-only implementation.

### 10. Built the Modal deployment target without inventing credentials

`modal_app.py` contains one protected FreeLLMAPI service and one bounded Hermes Function, both scale-to-zero and capped at one active container in Phase 1. `.github/workflows/deploy-modal.yml` is the only cloud deployment path.

The initial attempt correctly stopped before deployment while the account-owned GitHub secrets `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` were still absent. No fallback credential or second deployment mechanism was invented.

### 11. Removed duplicate live-provider CI work

The live model/tool proof initially ran on both branch `push` and `pull_request`, consuming free-provider quota twice for one candidate. CI now runs the candidate proof on `pull_request` and the merged proof on `main` only.

Same evidence, less infrastructure and quota use.

### 12. Preserved the frozen Control boundary

No Control repository, Runner, Mission, queue, scheduler, prompt, carrier, or candidate-binding semantics were modified. The known Control handoff limitation is not worked around with a second Agent-side scheduler, poller, queue, or semantic actor.

---

## 2026-09-10 — first live Modal promotion

### 13. Bound GitHub Actions to the Modal workspace

The account-owned Modal API token was stored only as encrypted GitHub Actions repository Secrets:

```text
MODAL_TOKEN_ID
MODAL_TOKEN_SECRET
```

A live workflow authentication check confirmed that the GitHub runner could authenticate to the intended Modal workspace. Token values were neither committed nor logged.

### 14. Removed manual runtime-secret setup from the critical path

Added `scripts/bootstrap_modal_runtime.py` as a small idempotent first-deploy bootstrap. With the deployment token as its only external prerequisite it:

- generates a stable FreeLLMAPI client key;
- generates the FreeLLMAPI encryption key;
- creates one Modal proxy token;
- creates the canonical `agent-hermes` and `agent-freellmapi` Modal Secrets;
- preserves the pair on subsequent runs;
- fails closed on partial pre-existing state;
- rolls back newly created bootstrap material after an incomplete creation;
- never prints generated secret values.

This eliminated unnecessary human copy/paste and kept one credential path.

### 15. Fixed Modal image-order validation discovered by the real deploy

The first authenticated deployment exposed a Modal image-build rule: build steps may not be appended after local-file mounts. The FreeLLMAPI image definition was reordered so environment/build configuration is completed before `add_local_*` mounts.

No additional image abstraction was introduced.

### 16. Neutralized the upstream Docker ENTRYPOINT at the Modal boundary

The next real remote smoke showed that FreeLLMAPI's published Docker `ENTRYPOINT` drops privileges for ordinary container/PaaS operation. That conflicted with Modal's own Function runtime bootstrap and produced Modal package permission/import failures.

The image now explicitly uses `.entrypoint([])` for Modal and invokes FreeLLMAPI's existing `/usr/local/bin/docker-entrypoint.sh` only for the actual FreeLLMAPI bootstrap/server process. This preserves the upstream helper while letting Modal own the Function entrypoint.

### 17. Minimized cross-image Python imports

A subsequent smoke exposed that `modal_app.py` was imported inside the FreeLLMAPI Function image while `agent_carrier` existed only in the Hermes image. The fix moved `agent_carrier` import into `run_agent` and mounts only `runtime_versions` into the service image.

This is a narrower dependency boundary, not a compatibility layer.

### 18. Proved the live Modal carrier and removed the temporary trigger

The resulting deployment completed successfully:

```text
GitHub Actions token auth
-> idempotent Modal runtime-secret bootstrap
-> modal deploy modal_app.py
-> protected FreeLLMAPI service
-> bounded Hermes Function
-> real remote Hermes -> FreeLLMAPI smoke
-> CANDIDATE
```

The temporary branch-push trigger used only to exercise the first deployment was then removed. `deploy-modal.yml` is again explicit-dispatch only, so ordinary candidate pushes do not redeploy or consume Modal compute.

CI was also extended to compile the bootstrap helper.

---

## Current evidence boundary

**Proven:** working bounded Hermes + FreeLLMAPI carrier with real free model and live web tool on a clean GitHub-hosted runtime.

**Proven:** live Modal cloud deployment of the same pinned topology and successful remote smoke to structured `CANDIDATE`.

**Still not full Mission acceptance:** `AGENT-R1-GAP-01` requires Phase-1C qualification evidence including repeated runs, quality/usefulness measurements, exact-head validation and required external review.

**Not yet part of the first operational carrier:** Phase-2 trusted evidence verifier, fan-out, persistent router state, project writes, mobile/interactive Hermes.

`CANDIDATE` must not be misrepresented as `RESULT_READY` or business `DONE`.
