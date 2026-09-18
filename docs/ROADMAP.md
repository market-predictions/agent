# Agent Framework Roadmap

**Repository:** `market-predictions/agent`  
**Canonical Mission:** `AGENT_FRAMEWORK` / `2026-09-10-r2`  
**Status:** current implementation sequence  
**Date:** 2026-09-18

Hermes is the only agent runtime. FreeLLMAPI is the canonical inference gateway. GitHub is code/config/docs truth. Control owns Mission/lifecycle authority; this repository does not duplicate Control runtime state.

## Governing sequence

```text
AGENT-R1-GAP-01  bounded carrier
        ↓
AGENT-R1-GAP-05  native authenticated web/mobile Hermes
        ↓
AGENT-R1-GAP-02  independent evidence verifier
        ↓
AGENT-R1-GAP-03  one-vs-two-worker value experiment
        ↓
AGENT-R1-GAP-04  bounded real caller integration
```

This order comes from Mission revision `2026-09-10-r2`. Earlier repo documentation that placed the interactive dashboard after verifier/fan-out is superseded.

---

## AGENT-R1-GAP-01 — bounded Hermes + FreeLLMAPI carrier

**State:** integrated / Control `DONE`.

Proven current path:

- Hermes `0.21.1`, exact commit `2237be355906fbe6065ce1815711eee52b2d646e`;
- FreeLLMAPI `0.9.8`, exact image digest;
- protected Modal FreeLLMAPI service;
- one bounded Modal Hermes worker;
- `PUBLIC_NON_PERSONAL` lane;
- web-only fixed tools in the bounded worker;
- hard model/tool/retry/time/concurrency limits;
- real Hermes → FreeLLMAPI → free model → web-tool loop;
- 20-run qualification at 90% human-usable output;
- no direct-provider bypass, framework DB/queue, production project writes or hidden paid fallback.

The worker still returns `CANDIDATE`; GAP-01 did not create verifier authority or business `DONE` authority.

---

## AGENT-R1-GAP-05 — native authenticated Hermes web dashboard

**State:** candidate in progress under owner-approved replenishment A8.

Smallest complete design:

- exact pinned native Hermes Web Dashboard; no fork;
- dedicated Modal web endpoint;
- native Nous Portal OAuth gate for the internet-facing endpoint;
- existing protected FreeLLMAPI as the sole inference route;
- GitHub-managed Hermes policy pins provider/model/tool capability and manual approvals;
- direct-provider API-key names are immutable/empty in managed scope;
- one dashboard container;
- one dedicated Modal Volume for interactive Hermes session/memory state;
- no Control state, framework task DB or target-project business truth in the dashboard.

Candidate enablement gates:

1. deterministic and exact-upstream CI green;
2. dashboard auth credential externally provisioned;
3. fresh external exact-candidate review PASS;
4. only then explicit user-facing Modal deployment/mobile proof.

See `docs/INTERACTIVE_DASHBOARD.md`.

---

## AGENT-R1-GAP-02 — independent evidence verifier

**State:** dependency-blocked on GAP-05.

After GAP-05 completes, add one separate trusted verifier that accepts strict candidate data only, independently re-fetches evidence and applies SSRF-hardened network rules. Only this gap may introduce `RESULT_READY`.

Do not execute worker-provided code/scripts/files and do not let generation verify itself.

---

## AGENT-R1-GAP-03 — parallelism value experiment

**State:** dependency-blocked on GAP-02.

Compare one worker against two independent workers on the same bounded objectives. Adopt Modal fan-out only if verified useful output improves enough to justify the extra inference/compute. Recursive Hermes delegation remains disabled unless a later Mission revision explicitly authorizes it.

---

## AGENT-R1-GAP-04 — bounded caller/project integration

**State:** dependency-blocked on GAP-03; integration policy `HOLD_AFTER_PASS`.

Connect at least one bounded real caller to verified `RESULT_READY/FAILED/PARTIAL` results without creating a second Control lifecycle or project database. The first integration remains result-only and holds no target-project production write credential.

Caller acceptance/business `DONE` remains outside Hermes and the verifier.

---

## Continuous constraints

Every gap must preserve:

- exact/proven runtime provenance;
- FreeLLMAPI as the sole model gateway;
- no upstream provider credentials in Hermes;
- least-privilege tools and data classification;
- no hidden paid fallback;
- no second runtime, generic queue, framework business DB or duplicate scheduler without a concrete later requirement;
- no target-project production authority;
- current docs matching actual behavior;
- exact-head validation and the Mission-required review policy;
- removal of superseded/conflicting current artifacts rather than parallel truth.
