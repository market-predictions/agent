"""Fail-closed objective checks for isolated Work diagnostic only."""

import copy
import unittest

from scripts.work_objective_poc import InvalidEvidence, source_finding, validate


SHA = "5225f1d0131e144d243973b9874df71c478e6eda"
MODAL = """
hermes_build_image = create_image()
dashboard_image = (
    hermes_build_image
    .add_local_python_source("interactive_dashboard")
    .add_local_file("config.json", "/app/config.json")
)
"""
DASHBOARD = "from runtime_versions import MODAL_APP_NAME\n"
REQUEST = {
    "id": 81001,
    "body": "CONTROL_WORK_POC_REQUEST_20261009\nNATIVE_OBJECTIVE_PROOF_20261009",
    "user": {"login": "github-actions[bot]"},
    "created_at": "2026-10-09T10:00:00Z",
}
REPLY = {
    "id": 81002,
    "body": (
        "CONTROL_WORK_OBJECTIVE_RESULT_20261009 pr=3 head=" + SHA +
        " request_comment_id=81001 finding=RUNTIME_VERSIONS_NOT_MOUNTED"
    ),
    "user": {"login": "market-predictions"},
    "created_at": "2026-10-09T10:00:22Z",
}


class ObjectiveEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.event = {
            "action": "created",
            "repository": {"full_name": "market-predictions/agent"},
            "issue": {"number": 3, "pull_request": {"url": "pr"}},
            "comment": copy.deepcopy(REPLY),
        }
        self.pr = {"number": 3, "head": {"sha": SHA}, "state": "open"}
        self.comments = [copy.deepcopy(REQUEST), copy.deepcopy(REPLY)]
        self.modal = MODAL
        self.dashboard = DASHBOARD

    def check_rejects(self):
        with self.assertRaises(InvalidEvidence):
            validate(self.event, self.pr, self.comments, self.modal, self.dashboard)

    def test_positive_evidence_not_semantic_pass(self):
        verdict = validate(self.event, self.pr, self.comments, self.modal, self.dashboard)
        self.assertEqual(verdict["verdict"], "OBJECTIVE_EVIDENCE_VERIFIED")
        self.assertFalse(verdict["control_event_authorized"])
        self.assertFalse(verdict["work_origin_attested"])
        self.assertFalse(verdict["semantic_external_pass"])

    def test_wrong_pr(self):
        self.event["issue"]["number"] = 4
        self.check_rejects()

    def test_stale_head(self):
        self.pr["head"]["sha"] = "f" * 40
        self.check_rejects()

    def test_wrong_event_author(self):
        self.event["comment"]["user"]["login"] = "guest"
        self.check_rejects()

    def test_mismatched_readback_author(self):
        self.comments[1]["user"]["login"] = "guest"
        self.check_rejects()

    def test_duplicate_replies(self):
        copy_reply = copy.deepcopy(REPLY)
        copy_reply["id"] = 81003
        copy_reply["created_at"] = "2026-10-09T10:00:24Z"
        self.comments.append(copy_reply)
        self.check_rejects()

    def test_stale_response(self):
        self.event["comment"]["created_at"] = "2026-10-09T11:00:00Z"
        self.comments[1]["created_at"] = "2026-10-09T11:00:00Z"
        self.check_rejects()

    def test_missing_bot_request(self):
        self.comments[0]["user"]["login"] = "market-predictions"
        self.check_rejects()

    def test_wrong_request_id(self):
        self.event["comment"]["body"] = self.event["comment"]["body"].replace(
            "request_comment_id=81001", "request_comment_id=81009"
        )
        self.check_rejects()

    def test_source_fixed_must_fail(self):
        self.modal = MODAL.replace(
            '.add_local_python_source("interactive_dashboard")',
            '.add_local_python_source("interactive_dashboard", "runtime_versions")'
        )
        self.check_rejects()

    def test_inherited_base_mount_fails(self):
        self.modal = MODAL.replace(
            "hermes_build_image = create_image()",
            'hermes_build_image = create_image().add_local_python_source("runtime_versions")'
        )
        self.check_rejects()

    def test_dashboard_changed_must_fail(self):
        self.dashboard = "import math\n"
        self.check_rejects()

    def test_wrong_image_base_fails_closed(self):
        self.modal = MODAL.replace("hermes_build_image\n", "hermes_image\n")
        self.check_rejects()

    def test_invalid_comment_count(self):
        self.comments.extend({"id": i} for i in range(110))
        self.check_rejects()


if __name__ == "__main__":
    unittest.main()
