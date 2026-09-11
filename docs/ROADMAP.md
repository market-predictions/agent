# Agent Framework Roadmap

**Repository:** `market-predictions/agent`  
**Architecture:** v0.5 — bounded carrier + isolated interactive Hermes dashboard  
**Status:** canonical implementation sequence  
**Date:** 2026-09-11

Hermes is the selected runtime. FreeLLMAPI is the sole inference gateway. There is no Pydantic AI path or direct-provider bypass.

---

## Roadmap principle

```text
smallest working carrier
        ↓
measured evidence
        ↓
next smallest justified capability
```

Control remains frozen during current Agent implementation.

---

# Phase 1A — Working Hermes + FreeLLMAPI carrier

## Status: PROVEN

Implemented and verified: pinned Hermes `0.21.1`; pinned FreeLLMAPI `0.9.8`; named `freellmapi` provider with model `auto`; bounded `web` toolset; strict `PUBLIC_NON_PERSONAL` candidate contract; hard wall/turn/model/tool/retry/concurrency bounds; keyless Kilo + OVH bootstrap; authenticated gateway; real routed model; live Hermes web-tool execution; provider credentials outside Hermes; full-SHA GitHub Actions.

Phase-1 output remains `CANDIDATE`, not `RESULT_READY`.

---

# Phase 1B — Modal cloud deployment

## Status: PROVEN

Implemented and verified:

- `modal_app.py` as the single cloud topology;
- protected FreeLLMAPI web service;
- bounded Hermes Function;
- exact upstream pins;
- Modal proxy auth + FreeLLM unified bearer;
- named Secrets `agent-hermes` and `agent-freellmapi`;
- GitHub authentication through `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`;
- idempotent runtime bootstrap in `scripts/bootstrap_modal_runtime.py`;
- `.github/workflows/deploy-modal.yml` as the only deployment workflow;
- successful live deployment and bounded remote smoke.

The deployment workflow is explicit-dispatch only in steady state; ordinary source pushes do not deploy or consume Modal compute.

---

# Phase 1C — Qualification / AGENT-R1-GAP-01 evidence

## Status: QUALIFIED — EXTERNAL REVIEW REMAINS

The fixed 20-run `PUBLIC_NON_PERSONAL` qualification completed against the measured runtime candidate. Results:

- attempted runs: **20**;
- strict structured candidates: **18/20 = 90%**;
- human-usable runs after source readback: **18/20 = 90%**;
- completed web-tool loops: **20/20 = 100%**;
- manually supported candidate claims: **18/18 = 100%**;
- model calls: **66**;
- tool calls: **47**;
- retries: **0**;
- provider errors: **0**;
- aggregate carrier wall time: **580.178 seconds**.

Both rejected runs remained fail-closed. The approximately 70% human-usefulness gate is satisfied at 90%. See [`qualification/PHASE1_QUALIFICATION_REVIEW.md`](../qualification/PHASE1_QUALIFICATION_REVIEW.md).

`max_tool_calls=20` is enforced before execution by the Hermes policy plugin. Remaining GAP-01 gate: final exact-head validation plus the required fresh external exact-candidate review.

Do not add fan-out to hide weak single-worker quality.

---

# Human-facing track — Interactive Hermes Web Dashboard

## Status: DEPLOYED; AUTHENTICATED BROWSER CHAT PROVEN; PERSISTENCE RESTART PROOF REMAINS

The first human-facing Agent layer is implemented as a separate native Hermes dashboard, stacked above the bounded carrier rather than widening its authority.

Implemented and verified:

- native Hermes `0.21.1` Web Dashboard/TUI;
- same FreeLLMAPI-only inference boundary;
- public Modal HTTPS endpoint;
- native Nous Portal OAuth with corrected client id;
- anonymous session access rejected fail-closed;
- one persistent Modal Volume for interactive profiles/sessions/state;
- one dashboard container maximum;
- enough Modal request concurrency for normal HTTP/WebSocket multiplexing;
- Hermes interactive session concurrency limited to one;
- hard `HERMES_TUI_TOOLSETS=web` operator pin so coding posture / GUI state cannot re-enable privileged tools;
- narrow dashboard-only Uvicorn `ws_per_message_deflate=False` compatibility patch after real browser `1002` protocol failures;
- real authenticated browser WebSocket/chat session completing a live Hermes web search and response;
- bounded worker unaffected and still exact upstream Hermes.

Still to prove before this layer is considered fully closed:

- state/session persistence across an intentional dashboard restart or scale-down;
- fresh exact-candidate external review after the final branch head is stable.

Native mobile UX is **not** implemented by this web-dashboard track.

---

# Phase 2 — Trusted evidence verifier

Add one separate trusted verifier that accepts only strict candidate data and independently re-fetches cited evidence.

Security boundary: HTTP(S) only; reject localhost/private/loopback/link-local/cloud-metadata destinations; re-resolve and revalidate redirects; byte/time limits; never execute worker-provided code/scripts/files.

Only this phase introduces `RESULT_READY`.

---

# Phase 3 — Test whether parallelism adds value

Compare one worker with two independent workers on the same bounded objective. Adopt fan-out only when verified quality/coverage improves enough to justify extra inference/compute. Keep Hermes recursive delegation disabled unless separately justified.

---

# Phase 4 — Persist FreeLLMAPI state only if measured need exists

Only if cold-start loss of quota/cooldown/analytics state materially harms useful capacity or diagnostics, add one Modal Volume with one writer. Do not add Redis, Postgres, horizontal router replicas, or multi-writer SQLite.

---

# Phase 5 — Capability-triggered isolation and profiles

Use Modal Sandbox only for a task class requiring autonomous shell, generated code, broad filesystem access, repository mutation, or untrusted executable artifacts. Add Git-backed task profiles only when at least two materially different capability/data classes exist.

---

# Phase 6 — Caller/project integration

Integrate verified results with bounded callers without duplicating Control/project state. No production write credential belongs in Hermes. Person-linked SolidDesign prospecting and sensitive Scrub data remain outside the generic free lane unless a new explicit data/inference policy is approved.

---

# Later — Native mobile client

Do not create a separate native mobile application until the web dashboard's value and required mobile-specific capabilities justify the additional surface. Responsive/browser access does not by itself justify a second client architecture.

---

## Continuous requirements

At every phase:

- GitHub remains code/config/docs truth;
- fresh-read the Execution & Engineering Constitution for consequential work;
- exact-pin correctness-relevant software;
- FreeLLMAPI remains the sole inference boundary;
- provider credentials remain outside Hermes;
- generic free lane remains `PUBLIC_NON_PERSONAL`;
- fail closed instead of silently switching to paid capacity;
- deterministic work stays deterministic;
- remove superseded code/config/docs;
- keep README, architecture, roadmap, operations and observed behavior aligned.