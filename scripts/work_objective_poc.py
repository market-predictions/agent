"""Temporary read-only proof: Work finding independently checked against exact PR code.

Never admits a Control TICK/EVENT or grants semantic authority. Every result is
untrusted Work content until independently corroborated by GitHub Actions.
"""

from __future__ import annotations

import ast
import base64
from datetime import datetime
import json
import os
import re
import sys
from urllib.request import Request, urlopen

OWNER = "market-predictions"
REPO = "market-predictions/agent"
NUMBER = 3
REQUEST_PREFIX = "CONTROL_WORK_OBJECTIVE_REQUEST_20261009"
REPLY_RE = re.compile(
    r"CONTROL_WORK_OBJECTIVE_RESULT_20261009 pr=3 head=([0-9a-f]{40}) "
    r"request_comment_id=([1-9][0-9]*) finding=RUNTIME_VERSIONS_NOT_MOUNTED"
)
API = "https://api.github.com"
WINDOW_SECONDS = 600


class InvalidEvidence(ValueError):
    pass


def ts(s: str) -> datetime:
    if not isinstance(s, str) or not s.endswith("Z"):
        raise InvalidEvidence("invalid timestamp")
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidEvidence("invalid timestamp") from exc


def source_finding(modal_source: str, dashboard_source: str) -> bool:
    """Prove one narrow P1 import/mount defect; other patterns fail closed."""
    modal_tree = ast.parse(modal_source)
    dashboard_tree = ast.parse(dashboard_source)
    imports_runtime_versions = any(
        (isinstance(x, ast.ImportFrom) and x.module == "runtime_versions")
        or (isinstance(x, ast.Import) and any(y.name == "runtime_versions" for y in x.names))
        for x in dashboard_tree.body
    )
    if not imports_runtime_versions:
        raise InvalidEvidence("dashboard import assumption changed")
    assignments = [
        node for node in modal_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "dashboard_image" for target in node.targets)
    ]
    if len(assignments) != 1:
        raise InvalidEvidence("dashboard image assignment not unique")
    image = assignments[0].value
    # Narrow to the reviewed exact architecture: dashboard derives from the
    # build-only image and therefore must mount its own local Python sources.
    if not any(isinstance(x, ast.Name) and x.id == "hermes_build_image" for x in ast.walk(image)):
        raise InvalidEvidence("dashboard base is no longer build-only")
    bases = [
        node for node in modal_tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "hermes_build_image" for target in node.targets)
    ]
    if len(bases) != 1:
        raise InvalidEvidence("build-only base identity not unique")
    if any(
        isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
        and call.func.attr == "add_local_python_source"
        and any(isinstance(a, ast.Constant) and a.value == "runtime_versions" for a in call.args)
        for call in ast.walk(bases[0].value)
    ):
        raise InvalidEvidence("runtime_versions is already mounted in inherited base")
    names = [
        arg.value for call in ast.walk(image)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
        and call.func.attr == "add_local_python_source"
        for arg in call.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
    ]
    if "interactive_dashboard" not in names:
        raise InvalidEvidence("dashboard source mount not found")
    if "runtime_versions" in names:
        raise InvalidEvidence("finding is fixed or no longer present")
    return True


def validate(event: dict, pr: dict, comments: list[dict], modal_source: str, dashboard_source: str) -> dict:
    """Correlate Work output AND independently establish the exact objective."""
    if (
        event.get("action") != "created"
        or (event.get("repository") or {}).get("full_name") != REPO
        or (event.get("issue") or {}).get("number") != NUMBER
        or not (event.get("issue") or {}).get("pull_request")
        or pr.get("number") != NUMBER
        or pr.get("state") != "open"
    ):
        raise InvalidEvidence("wrong PR/event identity")
    if not isinstance(comments, list) or len(comments) >= 100:
        raise InvalidEvidence("unbounded or missing comment readback")
    result = event.get("comment") or {}
    body = result.get("body")
    match = REPLY_RE.fullmatch(body) if isinstance(body, str) else None
    if not match or (result.get("user") or {}).get("login") != OWNER:
        raise InvalidEvidence("result format/author wrong")
    if not isinstance(result.get("id"), int):
        raise InvalidEvidence("result ID wrong")
    sha, request_id = match.groups()
    if (pr.get("head") or {}).get("sha") != sha:
        raise InvalidEvidence("stale candidate head")
    live = [c for c in comments if c.get("id") == result["id"]]
    if (
        len(live) != 1
        or live[0].get("body") != body
        or live[0].get("created_at") != result.get("created_at")
        or (live[0].get("user") or {}).get("login") != OWNER
    ):
        raise InvalidEvidence("result event/readback mismatch")
    requests = [
        c for c in comments if c.get("id") == int(request_id)
        and (c.get("user") or {}).get("login") == "github-actions[bot]"
        and isinstance(c.get("body"), str) and c["body"].startswith(REQUEST_PREFIX + "\n")
        and "NATIVE_OBJECTIVE_PROOF_20261009" in c["body"]
    ]
    if len(requests) != 1:
        raise InvalidEvidence("unique bot request unavailable")
    dt = (ts(result.get("created_at")) - ts(requests[0].get("created_at"))).total_seconds()
    if not 0 < dt <= WINDOW_SECONDS:
        raise InvalidEvidence("response outside request window")
    matches = [
        c for c in comments if isinstance(c.get("body"), str)
        and c["body"].startswith("CONTROL_WORK_OBJECTIVE_RESULT_20261009")
        and 0 < (ts(c["created_at"]) - ts(requests[0]["created_at"])).total_seconds() <= WINDOW_SECONDS
        and f"request_comment_id={request_id}" in c["body"]
    ]
    if len(matches) != 1 or matches[0]["id"] != result["id"]:
        raise InvalidEvidence("duplicate/ambiguous reply")
    source_finding(modal_source, dashboard_source)
    return {
        "verdict": "OBJECTIVE_EVIDENCE_VERIFIED",
        "pr": NUMBER,
        "head_sha": sha,
        "request_comment_id": int(request_id),
        "result_comment_id": result["id"],
        "latency_seconds": int(dt),
        "independent_check": "dashboard imports runtime_versions; build-only Modal image does not mount it",
        "work_origin_attested": False,
        "control_event_authorized": False,
        "semantic_external_pass": False,
    }


def get(path: str) -> object:
    req = Request(API + path, headers={
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "Accept": "application/vnd.github+json",
        "User-Agent": "control-work-objective-poc",
    })
    with urlopen(req, timeout=15) as resp:
        return json.load(resp)


def file_at_head(name: str, sha: str) -> str:
    data = get(f"/repos/{REPO}/contents/{name}?ref={sha}")
    if not isinstance(data, dict) or data.get("encoding") != "base64":
        raise InvalidEvidence("file payload invalid")
    return base64.b64decode(data["content"]).decode("utf-8")


def main() -> int:
    try:
        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
            event = json.load(f)
        pr = get(f"/repos/{REPO}/pulls/{NUMBER}")
        comments = get(f"/repos/{REPO}/issues/{NUMBER}/comments?per_page=100")
        sha = pr["head"]["sha"]
        evidence = validate(
            event, pr, comments, file_at_head("modal_app.py", sha),
            file_at_head("interactive_dashboard.py", sha)
        )
    except (InvalidEvidence, KeyError, ValueError, OSError, SyntaxError) as exc:
        print("CONTROL_WORK_OBJECTIVE_REJECTED: " + str(exc))
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
