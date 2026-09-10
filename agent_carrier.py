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
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


DATA_CLASS = "PUBLIC_NON_PERSONAL"
PROVIDER_ID = "freellmapi"
MODEL_ID = "auto"
KEY_ENV = "FREELLMAPI_API_KEY"
BASE_URL_ENV = "FREELLMAPI_BASE_URL"
PROXY_KEY_ENV = "MODAL_PROXY_KEY"
PROXY_SECRET_ENV = "MODAL_PROXY_SECRET"
BUDGET_PLUGIN_NAME = "agent-budget"
BUDGET_STATE_ENV = "AGENT_BUDGET_STATE_PATH"
MAX_MODEL_CALLS_ENV = "AGENT_MAX_MODEL_CALLS"
MAX_TOOL_CALLS_ENV = "AGENT_MAX_TOOL_CALLS"
MAX_RETRIES_ENV = "AGENT_MAX_RETRIES"


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


def render_hermes_config(base_url: str, budget: Budget) -> str:
    """Return the minimal Hermes named-provider and hard-budget configuration."""
    budget.validate()
    base_url = validate_freellmapi_base_url(base_url)
    # Hermes' api_max_retries counts attempts per logical provider request, where
    # 1 means one attempt. Keep its native retry loop aligned with our stricter
    # run-global middleware cap; the middleware remains authoritative for every
    # actual provider execution, including special recovery paths.
    native_attempts = budget.max_retries + 1
    return (
        "model:\n"
        f"  default: {json.dumps(MODEL_ID)}\n"
        f"  provider: {json.dumps(PROVIDER_ID)}\n"
        "providers:\n"
        f"  {PROVIDER_ID}:\n"
        f"    base_url: {json.dumps(base_url)}\n"
        f"    key_env: {json.dumps(KEY_ENV)}\n"
        "    api_mode: \"chat_completions\"\n"
        f"    default_model: {json.dumps(MODEL_ID)}\n"
        "    discover_models: false\n"
        "    models:\n"
        f"      - {json.dumps(MODEL_ID)}\n"
        "    extra_headers:\n"
        f"      Modal-Key: \"${{{PROXY_KEY_ENV}}}\"\n"
        f"      Modal-Secret: \"${{{PROXY_SECRET_ENV}}}\"\n"
        "agent:\n"
        f"  api_max_retries: {native_attempts}\n"
        "plugins:\n"
        "  enabled:\n"
        f"    - {BUDGET_PLUGIN_NAME}\n"
        "  hook_callback_timeout: 5\n"
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
- Hard runtime limits are {budget.max_model_calls} provider executions, {budget.max_tool_calls} tool calls, {budget.max_retries} total provider retries, and {budget.max_wall_seconds} seconds.
- Return ONLY valid JSON, without markdown fences or commentary, using exactly this shape:
{{
  "summary": "short answer",
  "claims": [
    {{"claim": "one supported factual claim", "source_url": "https://..."}}
  ]
}}
- Include at least one claim with an http(s) source URL.
"""


def build_hermes_command(*, prompt: str, usage_file: Path, budget: Budget) -> list[str]:
    """Build the smallest programmatic Hermes invocation for 0.21.1."""
    budget.validate()
    if not prompt.strip():
        raise CarrierConfigError("prompt is required")
    return [
        "hermes",
        "--ignore-rules",
        "--usage-file",
        str(usage_file),
        "--model",
        MODEL_ID,
        "--provider",
        PROVIDER_ID,
        "--toolsets",
        "web",
        "-z",
        prompt,
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
        "provider": PROVIDER_ID,
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


def _install_budget_plugin(hermes_home: Path) -> None:
    """Install a tiny user plugin shim into this one disposable Hermes profile."""
    plugin_dir = hermes_home / "plugins" / BUDGET_PLUGIN_NAME
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.yaml").write_text(
        'name: agent-budget\nversion: "1.0.0"\ndescription: Hard Phase-1 execution budgets\n',
        encoding="utf-8",
    )
    (plugin_dir / "__init__.py").write_text(
        "from agent_budget_plugin import register\n",
        encoding="utf-8",
    )


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


def _read_budget_state(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _validate_budget_state(state: object, budget: Budget, *, require_web_tool: bool) -> dict:
    if not isinstance(state, dict) or state.get("plugin_ready") is not True:
        raise CarrierConfigError("Hermes hard-budget plugin did not report ready state")
    for field, limit in (
        ("model_calls", budget.max_model_calls),
        ("tool_calls", budget.max_tool_calls),
        ("retries", budget.max_retries),
    ):
        value = state.get(field)
        if not isinstance(value, int) or value < 0:
            raise CarrierConfigError(f"invalid hard-budget telemetry field: {field}")
        if value > limit:
            raise CarrierConfigError(f"hard budget exceeded: {field}")
    if state.get("budget_exceeded"):
        raise CarrierConfigError(f"hard budget exhausted: {state['budget_exceeded']}")
    if state.get("policy_violation"):
        raise CarrierConfigError(f"hard policy violation: {state['policy_violation']}")
    if require_web_tool:
        tool_calls = state.get("tool_calls", 0)
        completed = state.get("tool_calls_completed")
        successes = state.get("tool_successes")
        failures = state.get("tool_failures")
        for field, value in (
            ("tool_calls_completed", completed),
            ("tool_successes", successes),
            ("tool_failures", failures),
        ):
            if not isinstance(value, int) or value < 0:
                raise CarrierConfigError(f"invalid hard-budget telemetry field: {field}")
        if tool_calls < 1:
            raise CarrierConfigError("required live web tool call was not observed")
        if completed != tool_calls or successes + failures != completed:
            raise CarrierConfigError("Hermes tool loop did not complete cleanly")
        if successes < 1:
            raise CarrierConfigError("required live web lookup did not succeed")
    return state


def _telemetry(state: dict | None, wall_seconds: float) -> dict:
    value = dict(state or {})
    value["wall_seconds"] = round(max(wall_seconds, 0.0), 3)
    return value


def execute_once(*, task_id: str, objective: str, base_url: str, budget: Budget) -> dict:
    """Run one hard-bounded Hermes invocation against protected FreeLLMAPI."""
    plan = build_plan(task_id=task_id, objective=objective, base_url=base_url, budget=budget)
    _require_runtime_secrets()

    with tempfile.TemporaryDirectory(prefix="agent-carrier-") as tmp:
        root = Path(tmp)
        hermes_home = root / ".hermes"
        hermes_home.mkdir(parents=True)
        _install_budget_plugin(hermes_home)
        (hermes_home / "config.yaml").write_text(
            render_hermes_config(base_url, budget), encoding="utf-8"
        )

        usage_file = root / "usage.json"
        budget_state_file = root / "budget-state.json"
        prompt = render_task_prompt(objective, budget)
        command = build_hermes_command(prompt=prompt, usage_file=usage_file, budget=budget)
        env = os.environ.copy()
        env["HERMES_HOME"] = str(hermes_home)
        env["HERMES_MAX_ITERATIONS"] = str(budget.max_turns)
        env[BUDGET_STATE_ENV] = str(budget_state_file)
        env[MAX_MODEL_CALLS_ENV] = str(budget.max_model_calls)
        env[MAX_TOOL_CALLS_ENV] = str(budget.max_tool_calls)
        env[MAX_RETRIES_ENV] = str(budget.max_retries)

        started = time.monotonic()
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
            state = _read_budget_state(budget_state_file)
            return {
                **plan,
                "status": "FAILED",
                "error": "wall-time budget exceeded",
                "telemetry": _telemetry(state, time.monotonic() - started),
            }

        elapsed = time.monotonic() - started
        state = _read_budget_state(budget_state_file)
        usage = None
        if usage_file.exists():
            try:
                usage = json.loads(usage_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                usage = None

        if completed.returncode != 0:
            return {
                **plan,
                "status": "FAILED",
                "exit_code": completed.returncode,
                "error": completed.stderr.strip()[-4000:],
                "usage": usage,
                "telemetry": _telemetry(state, elapsed),
            }

        try:
            structured = _parse_candidate_output(completed.stdout)
            usage = _validate_usage(usage, budget)
            state = _validate_budget_state(state, budget, require_web_tool=True)
        except CarrierConfigError as exc:
            return {
                **plan,
                "status": "FAILED",
                "exit_code": completed.returncode,
                "error": str(exc),
                "candidate_output": completed.stdout.strip()[-8000:],
                "usage": usage,
                "telemetry": _telemetry(state, elapsed),
            }

        return {
            **plan,
            "status": "CANDIDATE",
            "exit_code": 0,
            "result": structured,
            "usage": usage,
            "telemetry": _telemetry(state, elapsed),
            "route": {
                "provider": state.get("provider")
                or (usage.get("provider") if isinstance(usage, dict) else None),
                "model": state.get("response_model")
                or (usage.get("model") if isinstance(usage, dict) else None),
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
