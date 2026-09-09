"""Bounded Hermes carrier for AGENT-R1-GAP-01.

Hermes is the only agent runtime and FreeLLMAPI is the only inference endpoint.
The first operational lane is PUBLIC_NON_PERSONAL and exposes only Hermes' web
toolset. Control is governance only; this module has no Control runtime path.
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
PROXY_KEY_ENV = "MODAL_PROXY_KEY"
PROXY_SECRET_ENV = "MODAL_PROXY_SECRET"


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
            raise CarrierConfigError("Phase 1 permits exactly one concurrent task")
        if self.max_turns > self.max_model_calls:
            raise CarrierConfigError("max_turns may not exceed max_model_calls")


def validate_freellmapi_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CarrierConfigError("FREELLMAPI_BASE_URL must be an absolute http(s) URL")
    if "\n" in value or "\r" in value:
        raise CarrierConfigError("FREELLMAPI_BASE_URL contains invalid control characters")
    return value


def render_hermes_config(base_url: str) -> str:
    """Return the minimal Hermes custom-provider configuration.

    All credential values stay in environment variables. The config only names
    the variables and the protected FreeLLMAPI endpoint.
    """
    base_url = validate_freellmapi_base_url(base_url)
    return (
        "model_aliases:\n"
        f"  {MODEL_ALIAS}:\n"
        f"    model: {json.dumps(MODEL_ID)}\n"
        "    provider: \"custom\"\n"
        f"    base_url: {json.dumps(base_url)}\n"
        f"    key_env: {json.dumps(KEY_ENV)}\n"
        "    api_mode: \"chat_completions\"\n"
        "    extra_headers:\n"
        f"      Modal-Key: \"${{{PROXY_KEY_ENV}}}\"\n"
        f"      Modal-Secret: \"${{{PROXY_SECRET_ENV}}}\"\n"
        "web:\n"
        "  keyless_fallback: true\n"
    )


def render_task_prompt(objective: str, budget: Budget) -> str:
    """Wrap a task in the stable Phase-1 output and safety contract."""
    objective = objective.strip()
    if not objective:
        raise CarrierConfigError("objective is required")
    return f"""You are executing one bounded PUBLIC_NON_PERSONAL research task.

Objective:
{objective}

Rules:
- Use the web toolset for at least one live public source lookup.
- Do not collect, infer, or return personal, sensitive, confidential, or credential data.
- Do not use terminal, filesystem mutation, browser automation, delegation, messaging, or project-write tools.
- Keep the work small. Do not exceed {budget.max_turns} model turns.
- Return ONLY valid JSON, without markdown fences or commentary, using exactly this shape:
{{
  "summary": "short answer",
  "claims": [
    {{"claim": "one supported factual claim", "source_url": "https://..."}}
  ]
}}
- Include at least one claim with an http(s) source URL.
"""


def build_hermes_command(*, prompt_file: Path, usage_file: Path, budget: Budget) -> list[str]:
    budget.validate()
    return [
        "hermes",
        "--ignore-rules",
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
        "modal_proxy_key_env": PROXY_KEY_ENV,
        "modal_proxy_secret_env": PROXY_SECRET_ENV,
        "model": MODEL_ID,
        "toolsets": ["web"],
        "budget": asdict(budget),
    }


def _require_runtime_secrets() -> None:
    missing = [
        name
        for name in (KEY_ENV, PROXY_KEY_ENV, PROXY_SECRET_ENV)
        if not os.environ.get(name)
    ]
    if missing:
        raise CarrierConfigError(f"missing runtime secret(s): {', '.join(missing)}")
    if not os.environ[KEY_ENV].startswith("freellmapi-"):
        raise CarrierConfigError(f"{KEY_ENV} must use the freellmapi- prefix")


def _parse_candidate_output(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
            if text.startswith("json\n"):
                text = text[5:].strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CarrierConfigError("Hermes did not return valid structured JSON") from exc
    if not isinstance(value, dict) or set(value) != {"summary", "claims"}:
        raise CarrierConfigError("Hermes result must contain exactly summary and claims")
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        raise CarrierConfigError("Hermes result summary must be non-empty")
    claims = value["claims"]
    if not isinstance(claims, list) or not claims:
        raise CarrierConfigError("Hermes result must contain at least one claim")
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {"claim", "source_url"}:
            raise CarrierConfigError("each claim must contain exactly claim and source_url")
        if not isinstance(claim["claim"], str) or not claim["claim"].strip():
            raise CarrierConfigError("claim text must be non-empty")
        source = validate_freellmapi_base_url(claim["source_url"])
        if not source.startswith(("http://", "https://")):
            raise CarrierConfigError("claim source_url must be http(s)")
    return value


def _validate_usage(usage: object, budget: Budget) -> dict | None:
    if usage is None:
        return None
    if not isinstance(usage, dict):
        raise CarrierConfigError("Hermes usage report must be a JSON object")
    api_calls = usage.get("api_calls")
    if isinstance(api_calls, int) and api_calls > budget.max_model_calls:
        raise CarrierConfigError("Hermes exceeded max_model_calls")
    if usage.get("failed") is True or usage.get("completed") is False:
        raise CarrierConfigError("Hermes usage report marks the run incomplete/failed")
    return usage


def execute_once(*, task_id: str, objective: str, base_url: str, budget: Budget) -> dict:
    """Run one bounded Hermes invocation against protected FreeLLMAPI.

    A successful Phase-1 invocation emits CANDIDATE. RESULT_READY is reserved
    for the later trusted evidence-verification boundary.
    """
    plan = build_plan(task_id=task_id, objective=objective, base_url=base_url, budget=budget)
    _require_runtime_secrets()

    with tempfile.TemporaryDirectory(prefix="agent-carrier-") as tmp:
        root = Path(tmp)
        hermes_home = root / ".hermes"
        hermes_home.mkdir(parents=True)
        (hermes_home / "config.yaml").write_text(render_hermes_config(base_url), encoding="utf-8")

        prompt_file = root / "prompt.txt"
        prompt_file.write_text(render_task_prompt(objective, budget), encoding="utf-8")
        usage_file = root / "usage.json"

        command = build_hermes_command(prompt_file=prompt_file, usage_file=usage_file, budget=budget)
        env = os.environ.copy()
        env["HERMES_HOME"] = str(hermes_home)

        try:
            completed = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                timeout=budget.max_wall_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {**plan, "status": "FAILED", "error": "wall-time budget exceeded"}

        usage = None
        if usage_file.exists():
            usage = json.loads(usage_file.read_text(encoding="utf-8"))

        if completed.returncode != 0:
            return {
                **plan,
                "status": "FAILED",
                "exit_code": completed.returncode,
                "error": completed.stderr.strip()[-4000:],
                "usage": usage,
            }

        try:
            structured = _parse_candidate_output(completed.stdout)
            usage = _validate_usage(usage, budget)
        except CarrierConfigError as exc:
            return {
                **plan,
                "status": "FAILED",
                "exit_code": completed.returncode,
                "error": str(exc),
                "candidate_output": completed.stdout.strip()[-8000:],
                "usage": usage,
            }

        return {
            **plan,
            "status": "CANDIDATE",
            "exit_code": 0,
            "result": structured,
            "usage": usage,
            "route": {
                "provider": usage.get("provider") if isinstance(usage, dict) else None,
                "model": usage.get("model") if isinstance(usage, dict) else None,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENT-R1-GAP-01 Hermes carrier")
    parser.add_argument("--task-id", default="bootstrap-smoke")
    parser.add_argument(
        "--objective",
        default="Return one concise fact about the HTTP protocol and cite a public source.",
    )
    parser.add_argument("--freellmapi-base-url", default=os.environ.get(BASE_URL_ENV, ""))
    parser.add_argument("--execute", action="store_true", help="Actually invoke the local Hermes binary")
    args = parser.parse_args()

    budget = Budget()
    if not args.freellmapi_base_url:
        raise CarrierConfigError(f"{BASE_URL_ENV} or --freellmapi-base-url is required")

    result = (
        execute_once(
            task_id=args.task_id,
            objective=args.objective,
            base_url=args.freellmapi_base_url,
            budget=budget,
        )
        if args.execute
        else build_plan(
            task_id=args.task_id,
            objective=args.objective,
            base_url=args.freellmapi_base_url,
            budget=budget,
        )
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") != "FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
