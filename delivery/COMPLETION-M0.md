# Completion and Verify · M0

Date: 12/10/2026 (Asia/Ho_Chi_Minh). Status: **DONE for M0 local rehearsal scope**. Overall: **READY for local project review; NOT READY for operational flight or commercial release**.

Historical technical receipt: the user subsequently rejected the M0 interface design. Its visual acceptance is not established by the browser checks below. [UX01](COMPLETION-UX01.md) replaces the presentation and records new verification; M0 results remain historical.

## Delivered

Runnable dependency-free Plan/Fly workbench, synthetic rectangular survey engine, camera feasibility and rehearsal mission round-trip; simulated command acceptance/state reconciliation and fault injection; Inspect accurately states unavailable payload/video; Review exports actual rehearsal events. Versioned product requirements, architecture decisions, risk/input register, roadmap and scoped TIP. Nine primary/derived source captures with hashes, eleven external claims, deterministic derived research registry, ten internal intent/proposal/unknown records and a digest-bound SOT gate.

## Verify report

| AC / requirements | Result | Evidence |
|---|---|---|
| AC-01 / REQ-001 | PASS at documentation/API scope | `research/ragas-baseline/sources.json`, `claims.jsonl`, `registry.json`; `evidence/evidence-integrity.txt`, `refinery-build.txt` |
| AC-02 / REQ-002 | PASS for applicable integrity gates | `evidence/refinery-applicable-bites.txt`, `sot-check.txt`, `sot-bites.txt`, `sot-gate.txt`, `sot-status.txt`; unverified numbers remain null/claims |
| AC-03 / REQ-003/004 | PASS in synthetic planar model | Three hand-derived fixtures and 36 coverage/spacing combinations; `tests/mission.test.mjs`; actual `evidence/unit-tests.txt` |
| AC-04 / REQ-005 | PASS | Fixture semantic round-trip; browser local save/load/download/import/malformed import; core tests + `evidence/browser-qa.json` |
| AC-05 / REQ-006/007 | PASS in rehearsal adapter | ACK/observed separation, wrong target/session, delayed/future/malformed data, freshness, rejection, deadline tests; browser rehearsal receipts |
| AC-06 / REQ-008/009 | PASS in Chromium | Nineteen browser scenarios; all workspaces at 1440/1024/768/390px; screenshots, downloaded mission/event receipts; zero external requests and page/console errors |
| AC-07 / REQ-010 | PASS | TIP, files, reports, evidence receipts, hash manifest and explicit integration gaps |

REQUIREMENT COVERAGE: M0 10/10 required requirements implemented and checked in their stated scope. Next integration requirements REQ-101–108: 0/8, explicitly not implemented. Whole-program completion must not be inferred from M0 coverage.

SCENARIO RESULTS: 27 Node core tests PASS, 0 FAIL; 19 browser scenarios PASS, 0 FAIL. Golden expectations are analytical/self-reviewed, not expert-validated field fixtures. TECHNICAL HEALTH: syntax checks PASS, 0 reported syntax errors; no compilation/bundle needed; TypeScript/lint checks N/A for this dependency-free JS increment. SOT: six injected faults detected. Refinery: four applicable original bites plus two derived-output tamper tests pass; ten configured-inapplicable bites marked N/A.

## Verification limits and deviations

Single agent specification/build/verify, including visual inspection of desktop/mobile render. Not independent review. Testing on the user's actual controller, Safari/Android, operator usability, hardware performance, MAVLink wire protocol, SITL/HIL, geospatial/DEM/altitude validity and flight behavior are NOT_CHECKED.

Original Refinery full-suite receipt `evidence/refinery-bites.txt` records a denominator-bite failure: it removes an already-null universe while rollup is disabled, so no distribution gate can trigger. Applicability is recorded in a project wrapper (ADR D-007), preserving all applicable checks and the original failure. Parent toolkit code is unchanged. N/A is not PASS.

Initial restricted shell network/server/browser attempts were retried through approved tool escalation; public captures, loopback server and browser QA completed. No unresolved approval rejection.

## Remaining work and next decisions

Actual RAGAS/Ghidorah source and exact controller/drone/camera/radio configuration remain missing. Public API returned two repositories (ragas-release, supersplat); connector returned no accessible owner repos, which does not prove no private source exists. Next milestone: source/hardware audit, geospatial mission fixtures, QGC interoperability and actual SITL transport/transactions. Production GCS stack and commercial budget/deadline remain uncommitted.

## Hygiene

No whole project copied to /tmp, no Next.js output, Docker image, downloaded binary or npm dependency tree created. YAML dependencies are pinned in project `.venv` (about 15 MB). Bite scratch contained only small SOT/Refinery data copies and was removed in `finally`: `/private/tmp/codex-tmp-aeris-20261012`. Browser temporary profiles were cleaned by Playwright. The loopback server is retained for review; its static allowlist cannot serve SOT/research/source documents or receive UAV commands.
