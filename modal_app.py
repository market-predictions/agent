"""Modal runtime for the Agent carrier.

One protected FreeLLMAPI web service holds upstream provider credentials. The
bounded worker and the native interactive Hermes dashboard receive only the
gateway client credential and Modal proxy credential. Control is intentionally
not involved in either runtime path.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import urllib.request

import modal

from runtime_versions import (
    FREELLMAPI_IMAGE,
    FREELLMAPI_PORT,
    HERMES_COMMIT,
    HERMES_DASHBOARD_HOME,
    HERMES_DASHBOARD_PORT,
    HERMES_MANAGED_DIR,
    HERMES_REPOSITORY,
    HERMES_SOURCE_DIR,
    MODAL_APP_NAME,
    MODAL_FREELLMAPI_SECRET,
    MODAL_HERMES_DASHBOARD_SECRET,
    MODAL_HERMES_DASHBOARD_VOLUME,
    MODAL_HERMES_SECRET,
    NODE_LINUX_X64_SHA256,
    NODE_LINUX_X64_URL,
    NODE_VERSION,
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

dashboard_auth_secret = modal.Secret.from_name(
    MODAL_HERMES_DASHBOARD_SECRET,
    required_keys=["HERMES_DASHBOARD_OAUTH_CLIENT_ID"],
)

dashboard_state = modal.Volume.from_name(
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

# The dashboard is not a fork: it is the exact pinned Hermes source already used
# by the worker, with its native web assets built from the upstream lockfile.
# The host policy is installed into Hermes' supported bundled-plugin directory,
# so the same policy remains available when the native UI switches profiles.
# Node is exact-pinned and checksum-verified because it enters the executable
# build chain.
dashboard_image = (
    hermes_image
    .apt_install("curl", "xz-utils")
    .run_commands(
        f"curl -fsSLo /tmp/node.tar.xz {NODE_LINUX_X64_URL}",
        f"echo '{NODE_LINUX_X64_SHA256}  /tmp/node.tar.xz' | sha256sum -c -",
        "tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1",
        f'test "$(node --version)" = "v{NODE_VERSION}"',
        f"cd {HERMES_SOURCE_DIR} && npm ci",
        f"cd {HERMES_SOURCE_DIR} && npm run build --workspace web",
        f"mkdir -p {HERMES_MANAGED_DIR}",
        f"mkdir -p {HERMES_SOURCE_DIR}/plugins/agent-host-policy",
    )
    .add_local_python_source("interactive_dashboard")
    .add_local_file(
        "runtime/hermes-managed-config.json",
        f"{HERMES_MANAGED_DIR}/config.yaml",
    )
    .add_local_file(
        "runtime/hermes_host_policy/plugin.yaml",
        f"{HERMES_SOURCE_DIR}/plugins/agent-host-policy/plugin.yaml",
    )
    .add_local_file(
        "runtime/hermes_host_policy/__init__.py",
        f"{HERMES_SOURCE_DIR}/plugins/agent-host-policy/__init__.py",
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
    """Run one bounded headless Hermes task through the deployed FreeLLMAPI service."""
    import agent_carrier

    # Resolve the protected gateway inside trusted runtime code. Callers never
    # supply a credential-bearing destination, so they cannot redirect the
    # bearer/proxy credentials or bypass the canonical FreeLLMAPI service.
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


def _start_dashboard_volume_committer(interval_seconds: int = 30) -> None:
    """Persist interactive Hermes state without creating a second state service.

    Only one dashboard container is allowed, so there is no competing writer.
    The managed policy forces SQLite DELETE journaling rather than WAL on the
    mounted Volume. A daemon thread bounds normal cold-restart state loss to the
    commit interval; the dashboard remains the sole owner of its session/memory
    state and Control never reads or writes it.
    """
    stop = threading.Event()

    def commit_loop() -> None:
        while not stop.wait(interval_seconds):
            try:
                dashboard_state.commit()
            except Exception as exc:  # keep serving; next interval retries
                print(f"dashboard state commit failed: {type(exc).__name__}", flush=True)

    threading.Thread(
        target=commit_loop,
        name="hermes-dashboard-volume-commit",
        daemon=True,
    ).start()


@app.function(
    image=dashboard_image,
    secrets=[freellmapi_client_secret, dashboard_auth_secret],
    volumes={HERMES_DASHBOARD_HOME: dashboard_state},
    cpu=1.0,
    memory=2048,
    timeout=3600,
    startup_timeout=240,
    max_containers=1,
    min_containers=0,
    scaledown_window=300,
)
@modal.web_server(
    HERMES_DASHBOARD_PORT,
    startup_timeout=180,
)
def hermes_dashboard() -> None:
    """Start the exact native Hermes dashboard behind the hosted policy plugin."""
    import interactive_dashboard

    gateway_root = freellmapi.get_web_url()
    if not gateway_root:
        raise RuntimeError("FreeLLMAPI web URL is unavailable")
    gateway_root = gateway_root.rstrip("/")
    _probe_gateway(gateway_root)

    direct_secrets = interactive_dashboard.provider_secret_names()
    env = interactive_dashboard.build_dashboard_environment(
        gateway_root,
        os.environ,
        direct_provider_secret_names=direct_secrets,
    )
    interactive_dashboard.materialize_managed_env_policy(direct_secrets)
    os.makedirs(HERMES_DASHBOARD_HOME, exist_ok=True)
    _start_dashboard_volume_committer()
    subprocess.Popen(
        interactive_dashboard.dashboard_command(),
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
