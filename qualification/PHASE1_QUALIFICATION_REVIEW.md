# AGENT-R1-GAP-01 — Phase-1 Qualification Review

**Qualification:** `AGENT-R1-GAP-01-PHASE1-20`  
**Runtime candidate:** `a74871525458e47f69fa2c01ba6d0bdfc4a01202`  
**GitHub Actions run:** `34508260175`  
**Artifact:** `phase1-qualification-a74871525458e47f69fa2c01ba6d0bdfc4a01202` / ID `10165105109`  
**Artifact digest:** `sha256:8abf93fce9586e53ca526b417d320f053aff6340091ecf30308ff39cb58f2bad`  
**Observed:** 2026-09-10T17:37:07Z  
**Data class:** `PUBLIC_NON_PERSONAL`

This is a human evidence review of the fixed 20-run qualification artifact. It is not the later trusted runtime verifier and does not upgrade `CANDIDATE` to `RESULT_READY`.

## Verdict

**PASS — initial Phase-1 usefulness gate.**

- attempted runs: **20/20**
- strict structured `CANDIDATE`: **18/20 = 90%**
- human-usable runs: **18/20 = 90%**
- completed web-tool loops: **20/20 = 100%**
- source-bearing structured candidates: **18/20 = 90%**
- manually source-supported candidate claims: **18/18 = 100%**
- provider errors: **0**
- retries: **0**
- model calls: **66**
- tool calls: **47**
- aggregate carrier wall time: **580.178 s**

The Mission's initial usefulness requirement is approximately 70% or better. The observed 90% human-usable rate passes that gate without weakening the strict output contract.

## Human-evaluation rule

A run is counted human-usable only when it:

1. returns `CANDIDATE` under the strict carrier schema;
2. answers the requested factual objective;
3. includes at least one public source URL; and
4. manual readback of that cited source directly supports the material claim without a contradictory qualification.

A structurally invalid result is unusable even when its tool loop completed or its prose may have contained a correct answer.

## Per-run review

| # | Runtime result | Manual verdict | Observed route/model | Source / failure |
|---:|---|---|---|---|
| 1 | CANDIDATE | PASS | `openrouter/free` | https://http.dev/get |
| 2 | CANDIDATE | PASS | `kilo-auto/free` | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/201 |
| 3 | CANDIDATE | PASS | `poolside/laguna-s-2.1:free` | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429 |
| 4 | CANDIDATE | PASS | `poolside/laguna-s-2.1:free` | https://www.ietf.org/rfc/rfc8446.html |
| 5 | CANDIDATE | PASS | `gpt-oss-120b` | https://www.cloudflare.com/learning/dns/what-is-dns/ |
| 6 | CANDIDATE | PASS | `poolside/laguna-s-2.1:free` | https://www.rfc-editor.org/rfc/rfc4291.txt |
| 7 | CANDIDATE | PASS | `nvidia/nemotron-3-super-120b-a12b:free` | https://datatracker.ietf.org/doc/html/rfc8259/ |
| 8 | CANDIDATE | PASS | `nvidia/nemotron-3-super-120b-a12b:free` | https://dwheeler.com/secure-programs/Secure-Programs-HOWTO/character-encoding.html |
| 9 | CANDIDATE | PASS | `openrouter/free` | https://www.rfc-editor.org/rfc/rfc9293.html |
| 10 | CANDIDATE | PASS | `openrouter/free` | https://html.spec.whatwg.org/multipage/syntax.html#doctype-class |
| 11 | CANDIDATE | PASS | `openrouter/free` | https://www.rfc-editor.org/rfc/rfc9309.html |
| 12 | CANDIDATE | PASS | `openrouter/free` | MDN Content Security Policy documentation; the supplied legacy MDN path resolves to the current CSP documentation |
| 13 | FAILED | FAIL | — | `Hermes did not return valid structured JSON` |
| 14 | CANDIDATE | PASS | `openrouter/free` | RFC 6750; supplied `tools.ietf.org` URL resolves to the current IETF/RFC copy |
| 15 | CANDIDATE | PASS | `openrouter/free` | https://www.rfc-editor.org/rfc/rfc6455.html |
| 16 | CANDIDATE | PASS | `openrouter/free` | https://www.rfc-editor.org/rfc/rfc6234 |
| 17 | FAILED | FAIL | — | `Hermes result must contain exactly summary and claims` |
| 18 | CANDIDATE | PASS | `openrouter/free` | https://www.rfc-editor.org/rfc/rfc3986.txt |
| 19 | CANDIDATE | PASS | `openrouter/free` | https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/ |
| 20 | CANDIDATE | PASS | `openrouter/free` | https://www.rfc-editor.org/rfc/rfc9111.html |

## Source-support findings

Manual readback confirmed the substantive claims, including the more failure-prone cases:

- TLS 1.3 early data/0-RTT is PSK-bound and can be sent in the first flight under the RFC conditions.
- HTML DOCTYPE is a required preamble for legacy rendering-mode reasons.
- `robots.txt` is not authorization and listing paths exposes them publicly.
- CSP controls permitted resource loading and is used as defense in depth against XSS.
- OAuth bearer-token possession is sufficient to use the token without proof-of-possession key material.
- WebSocket uses an opening handshake followed by message framing over TCP.
- SHA-256 produces a 256-bit digest.
- RFC 3986 defines URI components including scheme, authority, path, query and fragment.
- DNS TTL controls cache duration and therefore update propagation delay.
- RFC 9111 is STD 98, published June 2022, obsoletes RFC 7234 and defines HTTP caching semantics.

## Failure analysis

The two unusable runs are retained as evidence rather than repaired away:

- **Run 13 — CORS:** Hermes completed its web-tool loop but did not return valid structured JSON.
- **Run 17 — SMTP port 25:** Hermes exhausted the configured model-call budget while repeatedly failing the exact `summary` + `claims` output contract; the carrier correctly rejected the result.

Both failures demonstrate that the strict schema and hard execution budgets remain fail-closed. No parser relaxation or hidden retry/fallback path is justified because the measured usefulness rate already exceeds the Mission threshold.

## Routing/provenance observation

The 18 successful candidates exposed multiple free route/model identities: `openrouter/free` (11), `poolside/laguna-s-2.1:free` (3), `nvidia/nemotron-3-super-120b-a12b:free` (2), `kilo-auto/free` (1), and `gpt-oss-120b` (1).

Hermes reports its configured provider surface as `custom` for this named OpenAI-compatible endpoint, so that field is not treated as the underlying FreeLLMAPI provider identity. The response-model identity is preserved as observed provenance; the separate direct FreeLLMAPI CI probe proves routed `model=auto` operation and `X-Routed-Via` where that gateway response exposes it.

## Acceptance boundary

This review satisfies the repeated-run and initial human-usefulness/source-support evidence portion of `AGENT-R1-GAP-01`. It does **not** satisfy the required fresh external exact-candidate review. Final candidate cleanup, exact-head CI and independent review remain required before the gap can pass.
