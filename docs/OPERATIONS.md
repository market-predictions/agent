# Agent Operations — Phase 1

**Scope:** deploy and run the first bounded Hermes -> FreeLLMAPI carrier on Modal.  
**Control:** frozen; these operations do not modify Control.  
**Data lane:** `PUBLIC_NON_PERSONAL` only.

## 1. What is already encoded in Git

The repository owns the runtime topology and exact software pins:

- Modal SDK `1.5.5`;
- Hermes `0.21.1` at exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8` at the exact image digest in `runtime_versions.py`;
- default FreeLLMAPI bootstrap providers: keyless `kilo` and keyless `ovh`;
- one Hermes Function and one protected FreeLLMAPI service;
- max one active container for each service;
- no direct-provider path.

Do not duplicate these values in another current config file.

## 2. Required Modal credentials

The deployment needs one Modal account/API token pair. Modal reads these from:

```text
MODAL_TOKEN_ID
MODAL_TOKEN_SECRET
```

Create/manage the token through Modal's normal account/CLI flow (`modal token new` / workspace settings). For GitHub deployment, store the two values as GitHub Actions secrets with exactly those names.

The repository never commits these credentials.

## 3. Create the gateway credentials

Generate a stable FreeLLMAPI unified key and a 64-hex-character encryption key locally:

```bash
python - <<'PY'
import secrets
print('FREELLMAPI_API_KEY=freellmapi-' + secrets.token_urlsafe(24))
print('ENCRYPTION_KEY=' + secrets.token_hex(32))
PY
```

Create one Modal proxy token:

```bash
modal workspace proxy-tokens create --json
```

Keep the returned `wk-...` key and `ws-...` secret. They protect the FreeLLMAPI web endpoint at the Modal boundary.

## 4. Create the two Modal Secrets

### `agent-hermes`

Contains only credentials needed by the Hermes client boundary:

```bash
modal secret create --force agent-hermes \
  FREELLMAPI_API_KEY="$FREELLMAPI_API_KEY" \
  MODAL_PROXY_KEY="$MODAL_PROXY_KEY" \
  MODAL_PROXY_SECRET="$MODAL_PROXY_SECRET"
```

Hermes receives this Secret. It does **not** receive upstream provider API keys.

### `agent-freellmapi`

For the zero-key first run, only the encryption key is required:

```bash
modal secret create --force agent-freellmapi \
  ENCRYPTION_KEY="$ENCRYPTION_KEY"
```

Without `FREEAPI_CONFIG_JSON`, the service uses the Git-controlled keyless bootstrap pool in `runtime/freellmapi.default.json` (`kilo` + `ovh`).

To enable additional FreeLLMAPI providers, add one complete declarative `FREEAPI_CONFIG_JSON` to this Secret. Because upstream selects the inline JSON in preference to `FREEAPI_CONFIG_PATH`, that JSON becomes the complete boot config and should include every provider you want eligible, including the keyless entries if you still want them.

Example shape only — never commit real key values:

```json
{
  "keys": [
    {"platform": "kilo", "label": "keyless"},
    {"platform": "ovh", "label": "keyless"},
    {"platform": "groq", "key": "<secret>"},
    {"platform": "google", "key": "<secret>"}
  ],
  "routing": {"strategy": "balanced"}
}
```

Store real provider keys only in the Modal Secret.

## 5. Deploy

From a machine with the Modal token active:

```bash
python -m pip install -r requirements.txt
modal deploy modal_app.py
```

Or use the GitHub Actions workflow:

```text
.github/workflows/deploy-modal.yml
```

The GitHub workflow requires only `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`; provider credentials remain inside Modal.

## 6. Run the real smoke test

```bash
modal run modal_app.py::smoke
```

The smoke succeeds only when the bounded remote Hermes worker returns a structured `CANDIDATE` through the protected FreeLLMAPI gateway. It deliberately does not emit `RESULT_READY`; that status belongs to the later trusted-verifier phase.

Expected path:

```text
local Modal CLI
  -> Modal Hermes Function
  -> protected FreeLLMAPI Modal web service
  -> eligible free provider/model
  -> Hermes web tool lookup
  -> structured CANDIDATE
```

## 7. Failure semantics

Fail closed on:

- missing Modal or gateway credentials;
- missing/invalid FreeLLMAPI unified key;
- FreeLLMAPI health/auth failure;
- no eligible model/provider;
- Hermes wall-time timeout;
- invalid/non-structured Hermes result;
- Hermes usage report that exceeds the configured model-call budget;
- any attempt to use a non-`PUBLIC_NON_PERSONAL` task in this generic lane.

There is no paid fallback, project-write fallback, direct-provider bypass, or second runtime.

## 8. What is intentionally not operational yet

- trusted evidence verifier;
- `RESULT_READY` status;
- two-worker fan-out;
- persistent FreeLLMAPI SQLite state;
- Modal Sandbox execution;
- project writes/publisher;
- mobile/interactive Hermes.

Those capabilities follow the canonical roadmap only after the current carrier is proven.
