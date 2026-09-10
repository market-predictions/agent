"""Modal runtime for the Agent carrier and its separate interactive Hermes UI.

The bounded worker remains stateless and authority-limited. The browser-facing
Hermes dashboard is a separate one-user surface with persistent Hermes state,
while GitHub-managed policy keeps FreeLLMAPI and the web-only tool boundary
immutable through Hermes' native managed-scope overlay.
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
    HERMES_DASHBOARD_PORT,
    HERMES_REPOSITORY,
    HERMES_SOURCE_DIR,
    MODAL_APP_NAME,
    MODAL_FREELLMAPI_SECRET,
    MODAL_HERMES_DASHBOARD_AUTH_SECRET,
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

# The public dashboard uses Hermes' native Nous Portal OAuth provider. A public
# bind without this provider fails closed inside Hermes itself.
hermes_dashboard_auth_secret = modal.Secret.from_name(
    MODAL_HERMES_DASHBOARD_AUTH_SECRET,
    required_keys=["HERMES_DASHBOARD_OAUTH_CLIENT_ID"],
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

# Reuse Hermes upstream's pinned Node 26 base and its native web/TUI build
# sequence. This avoids a custom dashboard frontend and avoids a second Node
# installation mechanism.
hermes_dashboard_image = (
    modal.Image.from_registry(HERMES_DASHBOARD_NODE_IMAGE, add_python="3.12")
    .apt_install("git", "ripgrep")
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
    .env({"HERMES_HOME": HERMES_DASHBOARD_HOME})
    # Default copy=False mounts this policy file at container startup. It stays
    # outside the writable Hermes home and is the single GitHub-managed policy.
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
    """Start the pinned FreeLLMAPI server behind Modal proxy authentication."""
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
def run_agent(task_id: str, objective: str, gateway_root: str) -> dict:
    """Run one bounded headless Hermes task through protected FreeLLMAPI."""
    import agent_carrier

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
    secrets=[freellmapi_client_secret, hermes_dashboard_auth_secret],
    volumes={HERMES_DASHBOARD_HOME: hermes_dashboard_volume},
    cpu=1.0,
    memory=2048,
    timeout=3600,
    max_containers=1,
    min_containers=0,
    scaledown_window=300,
)
@modal.web_server(HERMES_DASHBOARD_PORT, startup_timeout=180)
def dashboard() -> None:
    """Serve native Hermes Web Dashboard with persistent interactive state."""
    client_id = os.environ.get("HERMES_DASHBOARD_OAUTH_CLIENT_ID", "").strip()
    if not client_id.startswith("agent:"):
        raise RuntimeError("Hermes dashboard OAuth client id is missing or invalid")

    gateway_root = freellmapi.get_web_url()
    if not gateway_root:
        raise RuntimeError("FreeLLMAPI web URL is unavailable")
    gateway_root = gateway_root.rstrip("/")
    _probe_gateway(gateway_root)

    os.makedirs(HERMES_DASHBOARD_HOME, exist_ok=True)
    env = os.environ.copy()
    env["HERMES_HOME"] = HERMES_DASHBOARD_HOME
    env["FREELLMAPI_BASE_URL"] = f"{gateway_root}/v1"

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
    gateway_root = freellmapi.get_web_url()
    if not gateway_root:
        raise RuntimeError("FreeLLMAPI web URL is unavailable")
    result = run_agent.remote("modal-smoke", objective, gateway_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("status") != "CANDIDATE":
        raise SystemExit(1)
