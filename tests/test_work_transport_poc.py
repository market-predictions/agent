"""Adversarial tests: Work POC comments are never semantic Control authority."""

import copy
import unittest

from scripts.work_transport_poc import InvalidProof, validate


HEAD = "5225f1d0131e144d243973b9874df71c478e6eda"
REQUEST = {
    "id": 6076243327,
    "body": "CONTROL_WORK_POC_REQUEST_20261009\n\nDiagnostic request only.",
    "created_at": "2026-10-09T07:11:30Z",
    "user": {"login": "market-predictions"},
}
REPLY = {
    "id": 6076248402,
    "body": "CONTROL_WORK_POC_RESULT_20261009 3 " + HEAD + " status=PASS",
    "created_at": "2026-10-09T07:11:54Z",
    "user": {"login": "market-predictions"},
}


class WorkTransportPocTests(unittest.TestCase):
    def setUp(self):
        self.event = {
            "action": "created",
            "repository": {"full_name": "market-predictions/agent"},
            "issue": {"number": 3, "pull_request": {"url": "https://api.github.com/pulls/3"}},
            "comment": copy.deepcopy(REPLY),
        }
        self.pr = {"number": 3, "state": "open", "head": {"sha": HEAD}}
        self.comments = [copy.deepcopy(REQUEST), copy.deepcopy(REPLY)]

    def check_rejects(self):
        with self.assertRaises(InvalidProof):
            validate(self.event, self.pr, self.comments)

    def test_real_pair_is_correlated_but_never_trusted(self):
        proof = validate(self.event, self.pr, self.comments)
        self.assertEqual(proof["verdict"], "CORRELATED_UNTRUSTED")
        self.assertEqual(proof["latency_seconds"], 24)
        self.assertEqual(proof["request_comment_id"], REQUEST["id"])
        self.assertEqual(proof["result_comment_id"], REPLY["id"])
        self.assertFalse(proof["control_event_authorized"])
        self.assertFalse(proof["work_origin_attested"])

    def test_wrong_repo(self):
        self.event["repository"]["full_name"] = "market-predictions/control-engine"
        self.check_rejects()

    def test_wrong_pr(self):
        self.event["issue"]["number"] = 4
        self.check_rejects()

    def test_missing_request(self):
        self.comments.pop(0)
        self.check_rejects()

    def test_stale_pr_head(self):
        self.pr["head"]["sha"] = "a" * 40
        self.check_rejects()

    def test_untrusted_author(self):
        self.event["comment"]["user"]["login"] = "unknown-user"
        self.check_rejects()

    def test_ambiguous_requests(self):
        other = copy.deepcopy(REQUEST)
        other["id"] = 70001
        other["created_at"] = "2026-10-09T07:11:31Z"
        self.comments.append(other)
        self.check_rejects()

    def test_duplicate_replies(self):
        other = copy.deepcopy(REPLY)
        other["id"] = 70002
        other["created_at"] = "2026-10-09T07:11:55Z"
        self.comments.append(other)
        self.check_rejects()

    def test_old_request(self):
        self.comments[0]["created_at"] = "2026-10-09T06:00:00Z"
        self.check_rejects()

    def test_incorrect_event_readback(self):
        self.event["comment"]["body"] += " extra"
        self.check_rejects()

    def test_oversized_comment_listing(self):
        self.comments.extend({"id": i} for i in range(100))
        self.check_rejects()

    def test_result_not_owner(self):
        self.comments[1]["user"]["login"] = "guest"
        self.check_rejects()

    def test_closing_pr_rejects(self):
        self.pr["state"] = "closed"
        self.check_rejects()


if __name__ == "__main__":
    unittest.main()
