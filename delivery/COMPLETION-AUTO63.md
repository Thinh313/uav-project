# AUTO63 — PARTIAL handoff

Handoff date: 2026-10-15. The user explicitly chose to deliver the checked work as PARTIAL after host free space fell below the 20 GiB floor. No additional mock/SITL qualification, APK build, installation or signing is authorized by this handoff. This report supersedes any interpretation of ADR078 as completed qualification: ADR078 describes the proposed v5 design.

## Outcome

An isolated application at http://127.0.0.1:8820/ implements KML → planning → preflight → upload/readback → AUTO mock → review. The running preview is server-v4 with v3 UI assets. It retains uncertainty from the unsuccessful actual run and does not restore flight authority. Draft v5 is not served or qualified.

Actual ArduPilot 4.7.1 SITL passed preflight and upload/readback of 16 mission items, including six camera-trigger-distance commands. It did **not** complete an AUTO flight. On ARM, the autopilot updated Home by centimetres; the immutable PREFLIGHT43 guard invalidated the session and blocked AUTO. ACKs are not flight execution or evidence of actual photographs. Actual images: zero.

## Verification matrix

| Requirement | Checked result | Remaining gap |
|---|---|---|
| KML polygon/corridor planning | Mock source/mission SHA and bounded mission compilation passed | Synthetic flat terrain only; no real mapping accuracy, DEM or terrain-clearance acceptance |
| Same-app journey | Mock planning, readonly preflight, readback, AUTO observations and review passed | End-to-end actual AUTO not accepted |
| Session/boot/freshness/target gates | Mock loss, reboot, foreign response, stale parameters and changed mission rejected | Draft post-arm Home confirmation needs fresh qualification |
| Camera and mission semantic readback | Actual b4 uploaded/read back 16 items; camera content checked by live comparator | b4 cycle-aware independent raw semantic verifier not run; no physical camera test |
| Durable capture, failures and restart | Latest scoped mock E2E 39/39; lifecycle fault checks 6/6; explicit nonfinite observations 3/3 | OS parent-loss fixture passed, but actual Docker crash auto-reaping is NOT_CHECKED |
| Actual execution evidence | b3 independent raw integrity passed, explicitly not execution acceptance | No actual AUTO acceptance; b4 review has accepted=false and autoObserved=false |
| Persistence and protected files | Mock cold restart retains plan/review and removes authority; 23,476 protected paths match SHA at final point check | b4 remains unfinished in operator workspace; run-level failed review/raw are retained on disk |

Counts refer to the latest applicable suites, not a sum across repeated versions. Independent raw comparison uses a different decoder/reference path; specification, implementation and review were performed sequentially by one agent, not an independent human assessor.

## Actual SITL attempts, all retained

| Attempt | Run | Result |
|---|---|---|
| b1 | sec2bff1c274e408c93e0 | Startup transport closed before upload/arm; owned simulator stopped |
| b2 | s9a86d5477d324e20a0ed | HOME quaternion NaN caused finite-only observation journal failure; original raw RX was already fsynced; orphan simulator identified and stopped manually |
| b3 | se44e2a0207a4481890d5 | Prearm rejected initial 400 Hz gyro preset; raw integrity independently checked, zero uploaded mission items; simulator stopped |
| b4 | s2742b2e741d641bb86d1 | 1200 Hz preset passed preflight and 16-item readback; Home changed after ARM, guard closed session before AUTO; simulator stopped |

The first startup diagnosis remains a hypothesis, not a proven socket root cause. b2 has a separate orphan-closure receipt, not an invented normal closure receipt. All failed runs and earlier test failures remain available.

## Draft fix and NOT_CHECKED work

v5 separates ARM from AUTO. The design seals the disarmed preflight inspection, reads fresh post-arm Home and mission again, and requires an explicit SHA-bound Home confirmation while still armed/GUIDED/on ground. A separate flight guard continues session, boot, firmware, parameters and freshness checks. It does not silently ignore Home changes.

The initial v5 mock exposed an incorrect fixture landed-state assumption. After correcting that fixture, the next run was refused by the disk admission gate before connection. Therefore the corrected v5 positive journey, cycle-aware raw verifier, UI confirmation flow and a fifth actual SITL attempt are **NOT_CHECKED**. No v5 qualification pins, new software signature or successful AUTO receipt were produced.

## Preservation and resources

New work is isolated under `pilot/auto63`, `evidence/auto63`, the AUTO63 TIPs and ADR074–078. Frozen app/source/candidate, canonical SOT and ENDURE evidence were not changed or restarted. Before/after point checks each covered 23,476 protected paths; final check reports zero missing/changed and zero not checked. These hashes do not establish continuous path presence or 24-hour ENDURE acceptance.

Host free space at handoff was approximately 18.08 GiB. The task stopped qualification below the agreed 20 GiB floor; it cannot claim that unrelated host activity maintained that floor. AUTO63 evidence uses about 36 MiB. No user files or evidence were deleted; no scratch project copy, dependency install or Docker build was created. No task-created temporary dependency/build directory needs cleanup.

Final process inspection found only the preview PID 23528, with no AUTO63 runtime controller; the owned `aeris-auto63` container was absent. The preview remains for inspection, with no active simulator and the failed-run uncertainty retained. No SDK/HeraHub, real vehicle, APK build, new signature or Fly integration is included.

## Next qualification when resources allow

Recheck actual disk headroom (at least 22 GiB for this small mission campaign), preserved pins and scoped process ownership. Qualify v5 mock/fault and UI flows first, then run a fresh bounded SITL attempt at speedup 1. Do not resume or reclassify b1–b4. Acceptance requires full readback, explicit post-arm Home approval, AUTO observed, required navigation reached, expected RTL, fresh ground/disarmed near Home and independent raw verification. A failure or unknown state remains unaccepted.

Evidence index: `evidence/auto63/handoff-partial.json`, `preservation-before.json`, `preservation-after-compact.json`, `tests/q8/result.json`, `tests/lifecycle03/result.json`, `tests/nonfinite-v3.json`, `tests/parent-loss03/result.json`, `b1-result.json` through `b4-result.json`, per-run raw/review/closure receipts, and `artifact-fingerprints.json`.
