"""Run the governed AGENT-R1-GAP-01 Phase-1 qualification sample.

This is deliberately a measurement harness, not a verifier. It executes exactly
20 fixed PUBLIC_NON_PERSONAL research tasks through the deployed Modal carrier,
records the carrier's returned telemetry/result envelope, and leaves human
usefulness/source-support judgments explicitly pending.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import modal

from runtime_versions import MODAL_APP_NAME

QUALIFICATION_ID = "AGENT-R1-GAP-01-PHASE1-20"
DATA_CLASS = "PUBLIC_NON_PERSONAL"
OUTPUT_PATH = Path("qualification/evidence/phase1-qualification.json")

OBJECTIVES = (
    "Using a current public technical source, state one factual property of the HTTP GET method and cite the source.",
    "Using a current public technical source, state the meaning of HTTP status code 201 and cite the source.",
    "Using a current public technical source, state the meaning of HTTP status code 429 and cite the source.",
    "Using a current public technical source, state one factual property of TLS 1.3 and cite the source.",
    "Using a current public technical source, state what DNS is used for and cite the source.",
    "Using a current public technical source, state one factual property of an IPv6 address and cite the source.",
    "Using a current public technical source, state one factual property of JSON syntax and cite the source.",
    "Using a current public technical source, state one factual property of UTF-8 and cite the source.",
    "Using a current public technical source, state one factual property of TCP and cite the source.",
    "Using a current public technical source, state what the HTML doctype declaration is used for and cite the source.",
    "Using a current public technical source, state one factual property of robots.txt and cite the source.",
    "Using a current public technical source, state what Content-Security-Policy is used for and cite the source.",
    "Using a current public technical source, state what CORS controls in web browsers and cite the source.",
    "Using a current public technical source, state one factual property of OAuth 2.0 bearer tokens and cite the source.",
    "Using a current public technical source, state one factual property of the WebSocket protocol and cite the source.",
    "Using a current public technical source, state the output length of SHA-256 and cite the source.",
    "Using a current public technical source, state the conventional role of TCP port 25 in SMTP and cite the source.",
    "Using a current public technical source, state one factual property of URI syntax and cite the source.",
    "Using a current public technical source, state what a DNS TTL value controls and cite the source.",
    "Using a current public technical source, state one factual property of HTTP caching and cite the source.",
)


def _is_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _run_metrics(result: object) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {
            "candidate": False,
            "structured_claims": 0,
            "http_source_claims": 0,
            "tool_loop_completed": False,
        }

    claims: list[object] = []
    payload = result.get("result")
    if isinstance(payload, dict) and isinstance(payload.get("claims"), list):
        claims = payload["claims"]

    http_source_claims = sum(
        1
        for claim in claims
        if isinstance(claim, dict) and _is_http_url(claim.get("source_url"))
    )
    telemetry = result.get("telemetry")
    tool_loop_completed = bool(
        isinstance(telemetry, dict)
        and isinstance(telemetry.get("tool_calls"), int)
        and telemetry.get("tool_calls", 0) >= 1
        and telemetry.get("tool_calls_completed") == telemetry.get("tool_calls")
    )
    return {
        "candidate": result.get("status") == "CANDIDATE",
        "structured_claims": len(claims),
        "http_source_claims": http_source_claims,
        "tool_loop_completed": tool_loop_completed,
    }


def _aggregate(runs: list[dict[str, Any]]) -> dict[str, Any]:
    results = [run.get("carrier_result") for run in runs]
    telemetry = [
        result.get("telemetry")
        for result in results
        if isinstance(result, dict) and isinstance(result.get("telemetry"), dict)
    ]

    def _sum_int(field: str) -> int:
        return sum(
            value
            for item in telemetry
            if isinstance((value := item.get(field)), int) and value >= 0
        )

    def _sum_number(field: str) -> float:
        return round(
            sum(
                float(value)
                for item in telemetry
                if isinstance((value := item.get(field)), (int, float))
                and not isinstance(value, bool)
                and value >= 0
            ),
            3,
        )

    candidate_runs = sum(1 for run in runs if run["metrics"]["candidate"])
    structured_runs = sum(
        1
        for run in runs
        if run["metrics"]["structured_claims"] >= 1
        and run["metrics"]["http_source_claims"] >= 1
    )
    completed_tool_loops = sum(
        1 for run in runs if run["metrics"]["tool_loop_completed"]
    )
    return {
        "attempted_runs": len(runs),
        "candidate_runs": candidate_runs,
        "failed_or_non_candidate_runs": len(runs) - candidate_runs,
        "structured_source_bearing_runs": structured_runs,
        "completed_web_tool_loops": completed_tool_loops,
        "structural_candidate_rate": round(candidate_runs / len(runs), 3) if runs else 0.0,
        "total_model_calls": _sum_int("model_calls"),
        "total_tool_calls": _sum_int("tool_calls"),
        "total_retries": _sum_int("retries"),
        "total_provider_errors": _sum_int("provider_errors"),
        "total_wall_seconds": _sum_number("wall_seconds"),
    }


def main() -> int:
    if len(OBJECTIVES) != 20:
        raise RuntimeError("Phase-1 qualification must contain exactly 20 fixed tasks")

    gateway = modal.Function.from_name(MODAL_APP_NAME, "freellmapi")
    runner = modal.Function.from_name(MODAL_APP_NAME, "run_agent")
    gateway_root = gateway.get_web_url()
    if not gateway_root:
        raise RuntimeError("deployed FreeLLMAPI web URL is unavailable")

    runs: list[dict[str, Any]] = []
    for index, objective in enumerate(OBJECTIVES, start=1):
        task_id = f"phase1-q-{index:02d}"
        try:
            result: object = runner.remote(task_id, objective, gateway_root)
            exception = None
        except Exception as exc:  # preserve a complete 20-run sample
            result = None
            exception = f"{type(exc).__name__}: {exc}"[:2000]

        runs.append(
            {
                "index": index,
                "task_id": task_id,
                "objective": objective,
                "exception": exception,
                "metrics": _run_metrics(result),
                "carrier_result": result,
            }
        )

    document = {
        "schema_version": "1.0",
        "qualification_id": QUALIFICATION_ID,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "candidate_sha": os.environ.get("GITHUB_SHA"),
        "modal_app": MODAL_APP_NAME,
        "data_class": DATA_CLASS,
        "sample_design": {
            "fixed_task_count": 20,
            "sequential": True,
            "tasks": list(OBJECTIVES),
        },
        "summary": _aggregate(runs),
        "human_evaluation": {
            "status": "PENDING_MANUAL_SOURCE_REVIEW",
            "required_initial_usefulness_rate": "approximately 0.70 or better",
            "supported_claim_rate": None,
            "human_usable_run_rate": None,
        },
        "runs": runs,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(document["summary"], sort_keys=True))
    print(f"qualification evidence: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
