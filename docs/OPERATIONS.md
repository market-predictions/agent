# Agent Operations — Phase 1

**Scope:** operate the proven bounded Hermes -> FreeLLMAPI carrier and explicitly promote the same pinned code to Modal.  
**Control:** frozen; these operations do not modify Control.  
**Data lane:** `PUBLIC_NON_PERSONAL` only.

## 1. Current operational fact

The carrier is proven in two environments:

```text
clean GitHub-hosted runner
  -> pinned Hermes 0.21.1
  -> named FreeLLMAPI provider
  -> pinned FreeLLMAPI 0.9.8
  -> real free routed model
  -> Hermes live web tool
  -> strict CANDIDATE

explicit Modal promotion
  -> protected FreeLLMAPI web service
  -> bounded Hermes Function
  -> real remote smoke
  -> strict CANDIDATE
```

Modal is the selected cloud deployment target. Cloud deployment is a promotion of the proven carrier, not a substitute for proving the code works.

## 2. Git-owned runtime identity

`runtime_versions.py` is the single current source for:

- Modal SDK `1.5.5`;
- Hermes `0.21.1` at exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8` at the exact GHCR image digest;
- stable Modal app/Secret names.

The default FreeLLMAPI declarative bootstrap in `runtime/freellmapi.default.json` enables current keyless `kilo` and `ovh`; therefore **no provider API key is required for the first model run**.

Do not duplicate these pins in another current config file.

## 3. GitHub -> Modal deployment credential

GitHub Actions authenticates to the Modal workspace with exactly two repository Secrets:

```text
MODAL_TOKEN_ID
MODAL_TOKEN_SECRET
```

They are account-owned credentials and must never be committed, echoed, copied into runtime config, or placed in ordinary GitHub Variables. The repository only consumes them through Actions Secrets.

The current GitHub/Modal binding has been verified by a successful authenticated deployment. Rotation is performed in Modal and then by replacing the two GitHub repository Secret values; no code change is required.

## 4. Runtime credentials are bootstrapped, not hand-copied

`scripts/bootstrap_modal_runtime.py` is the canonical first-deploy bootstrap. It runs after Modal authentication and before deployment.

When neither named runtime Secret exists, it generates in-process:

- one stable `FREELLMAPI_API_KEY`;
- one 64-hex `ENCRYPTION_KEY`;
- one Modal proxy token protecting the FreeLLMAPI web endpoint.

It then creates:

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

Secret values are not printed. If both named Secrets already exist, bootstrap is a no-op and preserves them. If exactly one exists, bootstrap fails closed rather than guessing or silently creating a mixed credential state. If creation fails mid-flight, newly created bootstrap material is rolled back.

Do not manually create a second parallel credential path unless recovery from a specific failure requires it.

## 5. Promote to Modal

The canonical cloud promotion workflow is:

```text
.github/workflows/deploy-modal.yml
```

It is **workflow-dispatch only**. A deployment therefore happens only when deliberately requested; ordinary source pushes do not deploy or spend Modal compute.

With `run_smoke=true` it performs:

1. checkout with no persisted GitHub credential;
2. installation of the pinned Modal CLI;
3. fail-closed verification of the Modal account token;
4. idempotent runtime-Secret bootstrap;
5. `modal deploy modal_app.py`;
6. one real remote Hermes -> FreeLLMAPI smoke.

Manual equivalent from an authenticated machine:

```bash
python -m pip install -r requirements.txt
python -m scripts.bootstrap_modal_runtime
modal deploy modal_app.py
modal run modal_app.py::smoke
```

The first live deployment and smoke have already succeeded. Repeat deployment only for an intentional promotion or operational verification; do not use redeployment as routine polling.

## 6. Remote smoke success criterion

The smoke passes only when the remote chain returns a structured `CANDIDATE`:

```text
Modal Hermes Function
  -> protected FreeLLMAPI Modal service
  -> eligible free provider/model
  -> Hermes live web lookup
  -> structured CANDIDATE
```

Do not call this `RESULT_READY`; independent evidence verification is Phase 2.

## 7. Failure semantics

Fail closed on:

- missing/invalid Modal account deployment credentials;
- partial named Modal runtime-Secret state;
- invalid FreeLLMAPI unified key;
- FreeLLMAPI health/auth failure;
- no eligible model/provider;
- Hermes wall-time/iteration exhaustion;
- invalid/non-structured Hermes result;
- Hermes usage exceeding the configured model-call budget;
- any task outside `PUBLIC_NON_PERSONAL` in this generic free lane.

There is no paid fallback, direct-provider bypass, project-write fallback, second runtime, queue, or shadow scheduler.

## 8. Recovery and rotation

If the GitHub deployment token is rotated, replace `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` in GitHub Actions Secrets and rerun an explicit deployment.

If a named Modal runtime Secret must be rotated, treat the pair as one deliberate credential boundary. Do not delete only one and rely on bootstrap to repair it: partial state intentionally fails closed. Either replace values through Modal's normal Secret management or remove/recreate the complete runtime Secret pair in one controlled maintenance action, then rerun deployment and smoke.

Do not log or paste credential values into issues, PR comments, Actions output, or chat.

## 9. Verification commands without Modal

The canonical repository verification is GitHub Actions. For local deterministic checks:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m compileall -q agent_carrier.py modal_app.py runtime_versions.py scripts tests
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
