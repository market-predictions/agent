"""Modal runtime for the bounded Agent carrier and separate interactive Hermes UI.

The bounded worker resolves the protected FreeLLMAPI endpoint inside trusted
runtime code. The interactive dashboard shares that inference boundary but has
separate persistent user-session state and no Control/project authority.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import urllib.request

import modal

from runtime_versions import (
    FREELLMAPI_IMAGE,
    FREELLMAPI_PORT,
    HERMES_COMMIT,
    HERMES_DASHBOARD_HOME,
    HERMES_DASHBOARD_NODE_IMAGE,
    HERMES_DASHBOARD_OAUTH_CLIENT_ID,
    HERMES_DASHBOARD_PORT,
    HERMES_DASHBOARD_PUBLIC_URL,
    HERMES_REPOSITORY,
    HERMES_SOURCE_DIR,
    MODAL_APP_NAME,
    MODAL_FREELLMAPI_SECRET,
    MODAL_HERMES_DASHBOARD_VOLUME,
    MODAL_HERMES_SECRET,
)

app = modal.App(MODAL_APP_NAME)

freellmapi_service_secret = modal.Secret.from_name(
    MODAL_FREELLMAPI_SECRET,
    required_keys=["ENCRYPTION_KEY"],
)

freellmapi_client_secret = modal.Secret.from_name(
    MODAL_HERMES_SECRET,
    required_keys=[
        "FREELLMAPI_API_KEY",
        "MODAL_PROXY_KEY",
        "MODAL_PROXY_SECRET",
    ],
)

# One writer only. This stores interactive profiles/sessions/memory; it is not
# Control state, a framework queue or target-project business truth.
hermes_dashboard_volume = modal.Volume.from_name(
    MODAL_HERMES_DASHBOARD_VOLUME,
    create_if_missing=True,
)

freellmapi_image = (
    modal.Image.from_registry(FREELLMAPI_IMAGE, add_python="3.12")
    .entrypoint([])
    .env({"FREEAPI_CONFIG_PATH": "/app/agent-freellmapi-default.json"})
    .add_local_python_source("runtime_versions")
    .add_local_file(
        "runtime/freellmapi-bootstrap.mjs",
        "/app/agent-freellmapi-bootstrap.mjs",
    )
    .add_local_file(
        "runtime/freellmapi.default.json",
        "/app/agent-freellmapi-default.json",
    )
)

hermes_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ripgrep")
    .run_commands(
        f"git clone --filter=blob:none {HERMES_REPOSITORY} {HERMES_SOURCE_DIR}",
        f"git -C {HERMES_SOURCE_DIR} checkout --detach {HERMES_COMMIT}",
        f'test "$(git -C {HERMES_SOURCE_DIR} rev-parse HEAD)" = "{HERMES_COMMIT}"',
        f"python -m pip install --disable-pip-version-check -e {HERMES_SOURCE_DIR}",
    )
    .pip_install(
        "exa-py==2.10.2",
        "firecrawl-py==4.17.0",
        "parallel-web==0.4.2",
    )
    .add_local_python_source("agent_carrier", "agent_budget_plugin", "runtime_versions")
)

# Native Hermes dashboard/TUI, built from the same exact upstream commit. The
# OAuth client id is ordinary public configuration. Protected gateway
# credentials remain in the existing agent-hermes Secret.
hermes_dashboard_image = (
    modal.Image.from_registry(HERMES_DASHBOARD_NODE_IMAGE, add_python="3.12")
    .apt_install("git", "ripgrep", "build-essential")
    .run_commands(
        f"git clone --filter=blob:none {HERMES_REPOSITORY} {HERMES_SOURCE_DIR}",
        f"git -C {HERMES_SOURCE_DIR} checkout --detach {HERMES_COMMIT}",
        f'test "$(git -C {HERMES_SOURCE_DIR} rev-parse HEAD)" = "{HERMES_COMMIT}"',
        f"python -m pip install --disable-pip-version-check -e {HERMES_SOURCE_DIR}",
        f"cd {HERMES_SOURCE_DIR} && npm install --prefer-offline --no-audit --fetch-retries=5",
        f"cd {HERMES_SOURCE_DIR}/web && npm run build",
        f"cd {HERMES_SOURCE_DIR}/ui-tui && npm run build",
        "mkdir -p /etc/hermes",
    )
    .pip_install(
        "exa-py==2.10.2",
        "firecrawl-py==4.17.0",
        "parallel-web==0.4.2",
    )
    .env(
        {
            "HERMES_HOME": HERMES_DASHBOARD_HOME,
            "HERMES_DASHBOARD_OAUTH_CLIENT_ID": HERMES_DASHBOARD_OAUTH_CLIENT_ID,
            "HERMES_DASHBOARD_PUBLIC_URL": HERMES_DASHBOARD_PUBLIC_URL,
        }
    )
    # modal_app imports runtime_versions when Modal hydrates the web function;
    # every function image must therefore carry that module explicitly.
    .add_local_python_source("runtime_versions")
    .add_local_file(
        "runtime/hermes-managed-dashboard.yaml",
        "/etc/hermes/config.yaml",
    )
)


def _bootstrap_freellmapi_unified_key() -> None:
    completed = subprocess.run(
        [
            "/usr/local/bin/docker-entrypoint.sh",
            "node",
            "/app/agent-freellmapi-bootstrap.mjs",
        ],
        cwd="/app",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"FreeLLMAPI bootstrap failed: {completed.stderr[-2000:]}")


@app.function(
    image=freellmapi_image,
    secrets=[freellmapi_service_secret, freellmapi_client_secret],
    max_containers=1,
    min_containers=0,
    scaledown_window=120,
    timeout=3600,
)
@modal.web_server(
    FREELLMAPI_PORT,
    startup_timeout=90,
    requires_proxy_auth=True,
)
def freellmapi() -> None:
    """Start pinned FreeLLMAPI behind Modal proxy authentication."""
    _bootstrap_freellmapi_unified_key()
    subprocess.Popen(
        [
            "/usr/local/bin/docker-entrypoint.sh",
            "node",
            "server/dist/index.js",
        ],
        cwd="/app",
        env=os.environ.copy(),
    )


def _gateway_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['FREELLMAPI_API_KEY']}",
        "Modal-Key": os.environ["MODAL_PROXY_KEY"],
        "Modal-Secret": os.environ["MODAL_PROXY_SECRET"],
    }


def _probe_gateway(gateway_root: str) -> None:
    request = urllib.request.Request(
        f"{gateway_root.rstrip('/')}/api/ping",
        headers=_gateway_headers(),
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"FreeLLMAPI health probe returned HTTP {response.status}")


def _start_volume_committer() -> None:
    """Persist the single dashboard writer's state with a small bounded lag."""

    def loop() -> None:
        while True:
            time.sleep(10)
            try:
                hermes_dashboard_volume.commit()
            except Exception as exc:  # pragma: no cover - observable runtime warning
                print(f"Hermes dashboard volume commit failed: {type(exc).__name__}")

    threading.Thread(target=loop, daemon=True, name="hermes-volume-commit").start()


def _validate_dashboard_effective_policy(gateway_root: str) -> None:
    """Fail closed if Hermes' expanded managed overlay is not effective."""
    from hermes_cli.config import load_config

    config = load_config()
    model = config.get("model") or {}
    provider = (config.get("providers") or {}).get("freellmapi") or {}
    # load_config() expands ${VAR} references. Compare the effective values to
    # the process secrets without ever logging those values.
    expected_headers = {
        "Modal-Key": os.environ["MODAL_PROXY_KEY"],
        "Modal-Secret": os.environ["MODAL_PROXY_SECRET"],
    }
    checks = {
        "model.default": model.get("default") == "auto",
        "model.provider": model.get("provider") == "freellmapi",
        "provider.base_url": provider.get("base_url") == f"{gateway_root.rstrip('/')}/v1",
        "provider.key_env": provider.get("key_env") == "FREELLMAPI_API_KEY",
        "provider.api_mode": provider.get("api_mode") == "chat_completions",
        "provider.default_model": provider.get("default_model") == "auto",
        "provider.extra_headers": provider.get("extra_headers") == expected_headers,
        "fallback_providers": config.get("fallback_providers") == [],
        "toolsets": config.get("toolsets") == ["web"],
        "max_concurrent_sessions": config.get("max_concurrent_sessions") == 1,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        # Field names are safe diagnostics; values may contain secrets and are
        # intentionally never emitted.
        raise RuntimeError(
            "Hermes managed dashboard policy is not effective: " + ", ".join(failed)
        )


@app.function(
    image=hermes_image,
    secrets=[freellmapi_client_secret],
    cpu=1.0,
    memory=2048,
    timeout=660,
    max_containers=1,
    min_containers=0,
    scaledown_window=60,
)
@modal.concurrent(max_inputs=1)
def run_agent(task_id: str, objective: str) -> dict:
    """Run one bounded headless Hermes task through protected FreeLLMAPI."""
    import agent_carrier

    gateway_root = freellmapi.get_web_url()
    if not gateway_root:
        raise RuntimeError("FreeLLMAPI web URL is unavailable")
    gateway_root = gateway_root.rstrip("/")
    _probe_gateway(gateway_root)
    return agent_carrier.execute_once(
        task_id=task_id,
        objective=objective,
        base_url=f"{gateway_root}/v1",
        budget=agent_carrier.Budget(),
    )


@app.function(
    image=hermes_dashboard_image,
    secrets=[freellmapi_client_secret],
    volumes={HERMES_DASHBOARD_HOME: hermes_dashboard_volume},
    cpu=1.0,
    memory=2048,
    timeout=3600,
    max_containers=1,
    min_containers=0,
    scaledown_window=300,
)
@modal.concurrent(max_inputs=20)
@modal.web_server(HERMES_DASHBOARD_PORT, startup_timeout=180)
def dashboard() -> None:
    """Serve native Hermes Web Dashboard with persistent interactive state."""
    if not HERMES_DASHBOARD_OAUTH_CLIENT_ID.startswith("agent:"):
        raise RuntimeError("Hermes dashboard OAuth client id is invalid")
    if not HERMES_DASHBOARD_PUBLIC_URL.startswith("https://"):
        raise RuntimeError("Hermes dashboard public URL must use HTTPS")

    gateway_root = freellmapi.get_web_url()
    if not gateway_root:
        raise RuntimeError("FreeLLMAPI web URL is unavailable")
    gateway_root = gateway_root.rstrip("/")

    os.makedirs(HERMES_DASHBOARD_HOME, exist_ok=True)
    env = os.environ.copy()
    env["HERMES_HOME"] = HERMES_DASHBOARD_HOME
    env["FREELLMAPI_BASE_URL"] = f"{gateway_root}/v1"
    env["HERMES_DASHBOARD_OAUTH_CLIENT_ID"] = HERMES_DASHBOARD_OAUTH_CLIENT_ID
    env["HERMES_DASHBOARD_PUBLIC_URL"] = HERMES_DASHBOARD_PUBLIC_URL
    os.environ.update(
        {
            "HERMES_HOME": HERMES_DASHBOARD_HOME,
            "FREELLMAPI_BASE_URL": f"{gateway_root}/v1",
            "HERMES_DASHBOARD_OAUTH_CLIENT_ID": HERMES_DASHBOARD_OAUTH_CLIENT_ID,
            "HERMES_DASHBOARD_PUBLIC_URL": HERMES_DASHBOARD_PUBLIC_URL,
        }
    )
    _validate_dashboard_effective_policy(gateway_root)

    _start_volume_committer()
    subprocess.Popen(
        [
            "hermes",
            "dashboard",
            "--host",
            "0.0.0.0",
            "--port",
            str(HERMES_DASHBOARD_PORT),
            "--no-open",
            "--skip-build",
        ],
        cwd=HERMES_SOURCE_DIR,
        env=env,
    )


@app.local_entrypoint()
def smoke(
    objective: str = (
        "Find one current public fact about the HTTP protocol from a public "
        "technical source and return the required structured result."
    ),
) -> None:
    result = run_agent.remote("modal-smoke", objective)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("status") != "CANDIDATE":
        raise SystemExit(1)
