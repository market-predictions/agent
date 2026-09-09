"""Minimal bootstrap carrier for AGENT-R1-GAP-01.

This is intentionally not the completed Phase-1 carrier. It establishes the
smallest project-local executable boundary prepared for later governed
convergence: Hermes is the only agent runtime, FreeLLMAPI is the only inference
endpoint, the initial data class is PUBLIC_NON_PERSONAL, and Hermes receives
only the read-only `web` toolset.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


DATA_CLASS = "PUBLIC_NON_PERSONAL"
MODEL_ALIAS = "freellm"
MODEL_ID = "auto"
KEY_ENV = "FREELLMAPI_API_KEY"
BASE_URL_ENV = "FREELLMAPI_BASE_URL"


class CarrierConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Budget:
    max_model_calls: int = 12
    max_tool_calls: int = 20
    max_wall_seconds: int = 600
    max_retries: int = 1
    max_concurrent_tasks: int = 1
    max_turns: int = 12

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if not isinstance(value, int) or value < 1:
                raise CarrierConfigError(f"{name} must be a positive integer")
        if self.max_concurrent_tasks != 1:
            raise CarrierConfigError("bootstrap candidate permits exactly one concurrent task")


def validate_freellmapi_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CarrierConfigError("FREELLMAPI_BASE_URL must be an absolute http(s) URL")
    if "\n" in value or "\r" in value:
        raise CarrierConfigError("FREELLMAPI_BASE_URL contains invalid control characters")
    return value


def render_hermes_config(base_url: str) -> str:
    """Return the smallest Hermes custom-provider config for FreeLLMAPI.

    The provider secret is referenced by environment-variable name; its value
    is never written into repository configuration.
    """
    base_url = validate_freellmapi_base_url(base_url)
    quoted_url = json.dumps(base_url)
    return (
        "model_aliases:\n"
        f"  {MODEL_ALIAS}:\n"
        f"    model: {json.dumps(MODEL_ID)}\n"
        "    provider: \"custom\"\n"
        f"    base_url: {quoted_url}\n"
        f"    key_env: {json.dumps(KEY_ENV)}\n"
    )


def build_hermes_command(*, prompt_file: Path, usage_file: Path, budget: Budget) -> list[str]:
    budget.validate()
    return [
        "hermes",
        "chat",
        "--oneshot",
        "--query-file",
        str(prompt_file),
        "--model",
        MODEL_ALIAS,
        "--toolsets",
        "web",
        "--max-turns",
        str(budget.max_turns),
        "--usage-file",
        str(usage_file),
    ]


def build_plan(*, task_id: str, objective: str, base_url: str, budget: Budget) -> dict:
    budget.validate()
    clean_base_url = validate_freellmapi_base_url(base_url)
    if not task_id.strip():
        raise CarrierConfigError("task_id is required")
    if not objective.strip():
        raise CarrierConfigError("objective is required")
    return {
        "task_id": task_id,
        "data_class": DATA_CLASS,
        "agent_runtime": "hermes",
        "inference_gateway": "freellmapi",
        "freellmapi_base_url": clean_base_url,
        "freellmapi_key_env": KEY_ENV,
        "model": MODEL_ID,
        "toolsets": ["web"],
        "budget": asdict(budget),
    }


def execute_once(*, task_id: str, objective: str, base_url: str, budget: Budget) -> dict:
    """Run one bounded local Hermes invocation against FreeLLMAPI.

    This bootstrap does not deploy Modal or FreeLLMAPI. It expects Hermes to be
    installed and a protected FreeLLMAPI endpoint plus unified key to be
    supplied externally. Those deployment facts remain open AGENT-R1-GAP-01
    work; this module does not create a second Control execution path.
    """
    plan = build_plan(task_id=task_id, objective=objective, base_url=base_url, budget=budget)
    if not os.environ.get(KEY_ENV):
        raise CarrierConfigError(f"{KEY_ENV} is required for --execute")

    with tempfile.TemporaryDirectory(prefix="agent-carrier-") as tmp:
        root = Path(tmp)
        hermes_home = root / ".hermes"
        hermes_home.mkdir(parents=True)
        (hermes_home / "config.yaml").write_text(render_hermes_config(base_url), encoding="utf-8")

        prompt_file = root / "prompt.txt"
        prompt_file.write_text(objective, encoding="utf-8")
        usage_file = root / "usage.json"

        command = build_hermes_command(prompt_file=prompt_file, usage_file=usage_file, budget=budget)
        env = os.environ.copy()
        env["HERMES_HOME"] = str(hermes_home)

        completed = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=budget.max_wall_seconds,
            check=False,
        )

        usage = None
        if usage_file.exists():
            usage = json.loads(usage_file.read_text(encoding="utf-8"))

        return {
            **plan,
            "exit_code": completed.returncode,
            "candidate_output": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "usage": usage,
            "status": "CANDIDATE" if completed.returncode == 0 else "FAILED",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENT-R1-GAP-01 bootstrap carrier")
    parser.add_argument("--task-id", default="bootstrap-smoke")
    parser.add_argument("--objective", default="Return one concise fact about the HTTP protocol and cite a public source.")
    parser.add_argument("--freellmapi-base-url", default=os.environ.get(BASE_URL_ENV, ""))
    parser.add_argument("--execute", action="store_true", help="Actually invoke the local Hermes binary")
    args = parser.parse_args()

    budget = Budget()
    if not args.freellmapi_base_url:
        raise CarrierConfigError(f"{BASE_URL_ENV} or --freellmapi-base-url is required")

    if args.execute:
        result = execute_once(
            task_id=args.task_id,
            objective=args.objective,
            base_url=args.freellmapi_base_url,
            budget=budget,
        )
    else:
        result = build_plan(
            task_id=args.task_id,
            objective=args.objective,
            base_url=args.freellmapi_base_url,
            budget=budget,
        )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
