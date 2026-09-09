"""Modal runtime for the first operational Agent carrier.

One protected FreeLLMAPI web service holds upstream provider credentials. One
bounded Hermes Function receives only the gateway client credential and Modal
proxy credential. Control is intentionally not involved in this runtime path.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request

import modal

import agent_carrier
from runtime_versions import (
    FREELLMAPI_IMAGE,
    FREELLMAPI_PORT,
    HERMES_GIT_SPEC,
    MODAL_APP_NAME,
    MODAL_FREELLMAPI_SECRET,
    MODAL_HERMES_SECRET,
)

app = modal.App(MODAL_APP_NAME)

# Service-only secret. Expected keys:
#   ENCRYPTION_KEY        64 hex chars used by FreeLLMAPI for provider keys
#   FREEAPI_CONFIG_JSON   optional declarative provider/routing configuration
freellmapi_service_secret = modal.Secret.from_name(
    MODAL_FREELLMAPI_SECRET,
    required_keys=["ENCRYPTION_KEY"],
)

# Client boundary secret. The same stable unified key is supplied to the
# FreeLLMAPI service and Hermes, but upstream provider keys are not.
# Expected keys:
#   FREELLMAPI_API_KEY
#   MODAL_PROXY_KEY
#   MODAL_PROXY_SECRET
freellmapi_client_secret = modal.Secret.from_name(
    MODAL_HERMES_SECRET,
    required_keys=[
        "FREELLMAPI_API_KEY",
        "MODAL_PROXY_KEY",
        "MODAL_PROXY_SECRET",
    ],
)

freellmapi_image = (
    modal.Image.from_registry(FREELLMAPI_IMAGE, add_python="3.12")
    .add_local_file(
        "runtime/freellmapi-bootstrap.mjs",
        "/app/agent-freellmapi-bootstrap.mjs",
    )
)

hermes_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ripgrep")
    .pip_install(
        HERMES_GIT_SPEC,
        # Pin the web backends used by Hermes' built-in keyless web ring rather
        # than allowing a first agent run to lazy-install moving dependencies.
        "exa-py==2.10.2",
        "firecrawl-py==4.17.0",
        "parallel-web==0.4.2",
    )
    .add_local_python_source("agent_carrier", "runtime_versions")
)


def _bootstrap_freellmapi_unified_key() -> None:
    """Set the stable unified gateway key using FreeLLMAPI's exported DB API.

    Upstream v0.9.8 generates a temporary random key during its first migration.
    Bootstrap stdout is suppressed because upstream intentionally prints that
    temporary key. The pinned shim then overwrites only the unified-key setting.
    """
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
def run_agent(task_id: str, objective: str, gateway_root: str) -> dict:
    """Run one bounded headless Hermes task through protected FreeLLMAPI."""
    gateway_root = gateway_root.rstrip("/")
    _probe_gateway(gateway_root)
    return agent_carrier.execute_once(
        task_id=task_id,
        objective=objective,
        base_url=f"{gateway_root}/v1",
        budget=agent_carrier.Budget(),
    )


@app.local_entrypoint()
def smoke(
    objective: str = (
        "Find one current public fact about the HTTP protocol from a public "
        "technical source and return the required structured result."
    ),
) -> None:
    """Run the smallest real end-to-end Hermes -> FreeLLMAPI smoke test."""
    gateway_root = freellmapi.get_web_url()
    if not gateway_root:
        raise RuntimeError("FreeLLMAPI web URL is unavailable")
    result = run_agent.remote("modal-smoke", objective, gateway_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("status") != "CANDIDATE":
        raise SystemExit(1)
