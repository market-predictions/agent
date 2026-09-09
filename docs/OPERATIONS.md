# Agent Operations — Phase 1

**Scope:** operate the proven bounded Hermes -> FreeLLMAPI carrier and promote the same code to Modal when account credentials are available.  
**Control:** frozen; these operations do not modify Control.  
**Data lane:** `PUBLIC_NON_PERSONAL` only.

## 1. Current operational fact

The carrier core is already proven on a clean GitHub-hosted runner:

```text
pinned Hermes 0.21.1
  -> named FreeLLMAPI provider
  -> pinned FreeLLMAPI 0.9.8
  -> real free routed model
  -> Hermes live web tool
  -> strict CANDIDATE
```

The CI proof starts from a clean machine, installs the exact Hermes commit, starts the exact FreeLLMAPI image, performs a direct authenticated `model=auto` inference with route metadata, and then runs the real Hermes carrier.

Modal is the selected cloud deployment target. Cloud deployment is a promotion of this proven carrier, not a substitute for proving the code works.

## 2. Git-owned runtime identity

`runtime_versions.py` is the single current source for:

- Modal SDK `1.5.5`;
- Hermes `0.21.1` at exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8` at the exact GHCR image digest;
- stable Modal app/Secret names.

The default FreeLLMAPI declarative bootstrap in `runtime/freellmapi.default.json` enables current keyless `kilo` and `ovh`; therefore **no provider API key is required for the first model run**.

Do not duplicate these pins in another current config file.

## 3. External Modal account prerequisite

GitHub deployment requires the account-owned Modal token pair:

```text
MODAL_TOKEN_ID
MODAL_TOKEN_SECRET
```

The repository and current connected tools cannot create, recover, or read this account credential. An earlier deployment attempt already demonstrated that these values are currently absent from GitHub, so no live Modal deployment is claimed.

Create/manage the token through Modal's normal account/CLI flow, then store both values as GitHub Actions secrets with exactly those names. Never commit them.

## 4. Runtime credentials for Modal

Generate a stable FreeLLMAPI unified key and encryption key outside Git:

```bash
python - <<'PY'
import secrets
print('FREELLMAPI_API_KEY=freellmapi-' + secrets.token_urlsafe(24))
print('ENCRYPTION_KEY=' + secrets.token_hex(32))
PY
```

Create one Modal proxy token through Modal's normal workspace CLI/account flow and retain its `wk-...` key and `ws-...` secret as:

```text
MODAL_PROXY_KEY
MODAL_PROXY_SECRET
```

These protect the FreeLLMAPI web endpoint at the Modal boundary.

## 5. Create the two Modal Secrets

### `agent-hermes`

Contains only credentials needed by the Hermes client boundary:

```bash
modal secret create --force agent-hermes \
  FREELLMAPI_API_KEY="$FREELLMAPI_API_KEY" \
  MODAL_PROXY_KEY="$MODAL_PROXY_KEY" \
  MODAL_PROXY_SECRET="$MODAL_PROXY_SECRET"
```

Hermes does **not** receive upstream provider API keys.

### `agent-freellmapi`

The first zero-provider-key deployment requires only:

```bash
modal secret create --force agent-freellmapi \
  ENCRYPTION_KEY="$ENCRYPTION_KEY"
```

Without `FREEAPI_CONFIG_JSON`, the Git-controlled default config uses keyless Kilo + OVH.

If additional providers are later needed, add one complete declarative `FREEAPI_CONFIG_JSON` to `agent-freellmapi`. FreeLLMAPI gives inline JSON precedence over the file path, so that JSON becomes the complete startup config and must include every provider that should remain eligible. Store real provider keys only in the Modal Secret.

## 6. Promote to Modal

The canonical cloud promotion workflow is:

```text
.github/workflows/deploy-modal.yml
```

It is **workflow-dispatch only** while the external account token is absent. Once the GitHub token secrets and the two named Modal Secrets exist, dispatch the workflow with `run_smoke=true`.

It then:

1. checks out source with no persisted GitHub credential;
2. installs the pinned Modal CLI;
3. fails closed if the Modal account token is absent;
4. deploys `modal_app.py`;
5. runs the remote smoke when requested.

Manual equivalent from an authenticated machine:

```bash
python -m pip install -r requirements.txt
modal deploy modal_app.py
modal run modal_app.py::smoke
```

## 7. Remote smoke success criterion

The smoke passes only when the remote chain returns a structured `CANDIDATE`:

```text
Modal Hermes Function
  -> protected FreeLLMAPI Modal service
  -> eligible free provider/model
  -> Hermes live web lookup
  -> structured CANDIDATE
```

Do not call this `RESULT_READY`; independent evidence verification is Phase 2.

## 8. Failure semantics

Fail closed on:

- missing Modal account/deployment credentials;
- missing required named Modal Secrets;
- invalid FreeLLMAPI unified key;
- FreeLLMAPI health/auth failure;
- no eligible model/provider;
- Hermes wall-time/iteration exhaustion;
- invalid/non-structured Hermes result;
- Hermes usage exceeding the configured model-call budget;
- any task outside `PUBLIC_NON_PERSONAL` in this generic free lane.

There is no paid fallback, direct-provider bypass, project-write fallback, second runtime, queue, or shadow scheduler.

## 9. Verification commands without Modal

The canonical repository verification is GitHub Actions. For local deterministic checks:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m compileall -q agent_carrier.py modal_app.py runtime_versions.py tests
```

The real free-model/Hermes integration logic is kept in `scripts/ci_runtime_probe.sh` and is run by `.github/workflows/ci.yml` from a clean GitHub-hosted environment.

## 10. Later phases, not current operations

Not part of the first operational carrier:

- trusted evidence verifier / `RESULT_READY`;
- multi-worker fan-out;
- persistent FreeLLMAPI state;
- Modal Sandbox execution;
- project writes/publisher;
- mobile/interactive Hermes.

Those capabilities are added only when the canonical roadmap's evidence trigger is met.
