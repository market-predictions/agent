"""Read-only diagnostic for the isolated GitHub -> Work -> GitHub POC.

This does not authenticate a Work execution. Owner-authored comments are untrusted
observations; a matching reply can NEVER authorize a Control EVENT or target write.
"""

from __future__ import annotations

from datetime import datetime
import json
import os
import re
import sys
from urllib.request import Request, urlopen

REPOSITORY = "market-predictions/agent"
PR_NUMBER = 3
OWNER = "market-predictions"
REQUEST = "CONTROL_WORK_POC_REQUEST_20261009"
RESULT = re.compile(
    r"CONTROL_WORK_POC_RESULT_20261009 3 ([0-9a-f]{40}) status=PASS"
)
WINDOW_SECONDS = 600
API = "https://api.github.com"


class InvalidProof(ValueError):
    """The observed transport pair is missing, stale, ambiguous or mismatched."""


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise InvalidProof("invalid GitHub timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidProof("invalid GitHub timestamp") from exc


def _owner(comment: dict) -> bool:
    return isinstance(comment.get("user"), dict) and comment["user"].get("login") == OWNER


def validate(event: dict, pr: dict, comments: list[dict]) -> dict:
    """Correlate one exact POC request/reply; never confer execution authority."""
    if (
        event.get("action") != "created"
        or (event.get("repository") or {}).get("full_name") != REPOSITORY
        or (event.get("issue") or {}).get("number") != PR_NUMBER
        or not (event.get("issue") or {}).get("pull_request")
    ):
        raise InvalidProof("not the exact POC PR comment event")
    if (
        pr.get("number") != PR_NUMBER
        or pr.get("state") != "open"
        or (pr.get("head") or {}).get("sha") is None
    ):
        raise InvalidProof("PR identity unavailable or closed")
    if not isinstance(comments, list) or len(comments) >= 100:
        raise InvalidProof("comment scan missing or not provably bounded")
    result = event.get("comment") or {}
    if not isinstance(result, dict) or not isinstance(result.get("id"), int):
        raise InvalidProof("event result identity invalid")
    body = result.get("body")
    match = RESULT.fullmatch(body) if isinstance(body, str) else None
    if not match or not _owner(result):
        raise InvalidProof("result format or author invalid")
    if match.group(1) != pr["head"]["sha"]:
        raise InvalidProof("result PR head is stale")
    created = _time(result.get("created_at"))
    same = [c for c in comments if c.get("id") == result["id"]]
    if len(same) != 1 or same[0].get("body") != body:
        raise InvalidProof("event/result readback mismatch")
    requests = [
        c for c in comments
        if isinstance(c.get("body"), str)
        and (c["body"] == REQUEST or c["body"].startswith(REQUEST + "\n"))
        and _owner(c)
        and 0 < (created - _time(c.get("created_at"))).total_seconds() <= WINDOW_SECONDS
    ]
    if len(requests) != 1:
        raise InvalidProof("missing or ambiguous predecessor request")
    started = _time(requests[0]["created_at"])
    replies = [
        c for c in comments
        if isinstance(c.get("body"), str)
        and c["body"].startswith("CONTROL_WORK_POC_RESULT_20261009")
        and 0 < (_time(c.get("created_at")) - started).total_seconds() <= WINDOW_SECONDS
    ]
    if len(replies) != 1 or replies[0].get("id") != result["id"]:
        raise InvalidProof("ambiguous result for request")
    return {
        "verdict": "CORRELATED_UNTRUSTED",
        "request_comment_id": requests[0]["id"],
        "result_comment_id": result["id"],
        "pr_number": PR_NUMBER,
        "head_sha": match.group(1),
        "latency_seconds": int((created - started).total_seconds()),
        "control_event_authorized": False,
        "work_origin_attested": False,
    }


def _get(path: str) -> object:
    token = os.environ.get("GITHUB_TOKEN", "")
    request = Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "control-work-poc-readonly",
            **({"Authorization": "Bearer " + token} if token else {}),
        },
        method="GET",
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def main() -> int:
    try:
        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
            event = json.load(f)
        pr = _get(f"/repos/{REPOSITORY}/pulls/{PR_NUMBER}")
        comments = _get(f"/repos/{REPOSITORY}/issues/{PR_NUMBER}/comments?per_page=100")
        evidence = validate(event, pr, comments)
    except (InvalidProof, KeyError, OSError, ValueError) as exc:
        print("CONTROL_WORK_POC_REJECTED: " + str(exc))
        return 1
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
