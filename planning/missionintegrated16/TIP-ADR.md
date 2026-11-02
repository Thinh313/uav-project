# MISSIONINTEGRATED16: one Android simulator product journey

Authorized user 2026-11-01: complete end-to-end Android–SITL mission, then integrated ten-minute video/payload, link-loss, reboot and persistence checks. Personal Vibecode Kit6.3: Root Contractor writes requirements/QA, delegated Builder implements, Root independently verifies. Deterministic simulator/runtime integration, no LLM/agent superiority claim or baseline required.

## Outcome and scope

An engineer can plan/compile/save a polygon mission, consent/preflight on actual Android, connect owned ArduPilot ARM SITL, observe typed39/current Home/navigation, explicitly grant/upload/readback/arm/review Home/start AUTO, interact with mock payload/gimbal and host synthetic video, use Android manual/assisted input, return to AUTO/land, close accepted review, replay, save/restart and recover workspace without restoring authority. Nominal short actual acceptance must precede a continuous 600-second integrated workload; startup/close do not count toward 600 seconds. Then fault cases prove link-loss and AP reboot detection/revocation, incomplete honest reviews and restart recovery. No real aircraft/controller/SDK, physical camera, production signing or certification.

## Existing baseline and architecture

Reuse exact WRITERSTAGE15 filesystem/trace/HostHealth/clock/physics/native APK/AP ARM/image/spec and original operational `scenario-app09.py`/managed seal/drain/SAF code where valid. WRITERSTAGE15 S02 is a disarmed readiness proof only, never a short flight prerequisite. Its journal remains INCOMPLETE_RECORDING. Do not wrap its intentional failed-disposal sentinel into nominal flight PASS.

Selected source-only isolation: `planning/missionintegrated16`; all new evidence/candidates/campaigns: `evidence/missionintegrated16`. No whole-project copy. Preserve every prior source/candidate/raw/ENDURE/handoff byte and mode; no changes to old external pinned inputs. New source-owned graph and versioned entrypoints include any copied/modified component. Do not simply relabel or continue old campaigns.

One public Android journey supplies operational intents; Root supplies admitted actors and finite management only. Host video publisher is genuine browser rendering opened once by Root using CUA after host ready. No hidden HTTP flight shortcut, fabricated native input, host refresh of source clock/lease, simulated ACK as execution, repeated video publisher retry or substituted SAF bytes.

Fault architecture must be explicit. Current selected UI cut/reboot controls are hidden and the operational server lacks those routes. A mock payload fault is not AP failure. Owned-process/transport injection must retain original raw traffic, PID/container identity and actual boot observation where claimed. All guards stay live. Expected source/authority loss may end an interrupted case; never accept it as a completed mission. Reconnect requires new session/boot/discovery, explicit consent/preflight/grant, never automatic authority restoration. Builder must propose any lifecycle change before implementing it.

## Invariants and admission

HostHealth100ms, product writer200ms, freshness250ms and native lease200ms unchanged. Keep source/CRC/Home/typed39/EKF/navigation/video quality, physics speedup1/catchup500ms, durable fsync before sensor and every frame. Keep all metadata64MiB, owner/counter/native/export quotas, artifact10MiB across ALL historical pools plus new, disk floor10GiB+reserve256MiB+actual per-case peak, actual power/lid/forecast/process/closure guards. Existing duration policies180/760 may be selected explicitly, not numerically relaxed; select matching preview/bootstrap/monitor/recording budgets and actual duration consistently. One case/campaign and diagnosticChildren4 remain. No downloads, new native build/signature, delete/prune evidence or reset native lifetime counters.

Pure source/freeze forecast and actual admission precede actors. A refusal is not bypassed by changing classification, omitting a pool, cached stat, fake AC or metadata. Do source/mock work and make an exact forecast before escalation. Root QA receipts are actual metadata and must fit; no unbounded trace or repeated giant logs.

## Gates and finite execution

G0 scan/ADR, preservation entry and reusable dependency inventory.
G1 source implementation plus meaningful mocks for one complete journey and negative cases: stale Home/clock/typed params, missing video, payload targeting/grant/revocation, late/unknown commit, loss/reboot, rejected/replayed short receipt, restart without authority and full-byte SAF receiver. Preserve unchanged existing tests; count unique methods, not reruns.
G2 HOLD: exact source graph/native/artifact/source-contract checks, Root independent behavioral/byte verification; pure freeze and both180/760 forecasts, then fresh live admission. No runtime before Root releases HOLD.
G3 one short actual nominal Android–SITL case, original UI/workspace/native input/video/payload and managed flight closure. Root cold verifies raw frames/clocks/mission/readback/ground/native input signatures/video interval/product seal/SAF bytes, closure and no actor remains. A disarmed/summary-only/failed-disposal result does not satisfy G3.
G4 only after a digest-bound Root G3 receipt for SAME candidate/config/native/AP/source, one760-policy case with at least600 continuous seconds observed integrated workload. Keep wall and source intervals distinct; no addition of interrupted intervals. Same complete close/receiver verification as G3. Video remains measurable through interval, payload actions occur in interval.
G5 bounded separate link and AP-reboot cases preserve interrupted originals and prove revocation/boot/discovery/restart/persistence as applicable. No automatic restore or promotion to nominal acceptance. Native app restart is not AP reboot.
G6 independent disposition/report: requirement coverage, scenario PASS/FAIL/NOT_CHECKED, evidence limits and preserved old SHA. Beta-ready only if all required gates actually proved.

Closed slots: s01 initial short, s02 one measured short repair if Root issues explicit L2 revision after retained failure, l01 ten-minute, f01 link fault, f02 AP reboot. No automatic retry/campaign resume, at most five actual launches total, no use of elapsed old attempts. Source edits after HOLD invalidate same-candidate short prerequisite; preserve failed candidate and regenerate new source/gate. Stop on guard failure; diagnose actual first cause before deciding a remaining slot. No manual intervention inside workload to rescue a failing run.

## Required deliverables

Builder HOLD with source hashes, exact changed-vs-WRITERSTAGE15 scope, tests and pass/fail counts, all guard/cap/pool proof, planned/runtime duration distinction, unresolved items. Root independent verification and launch receipts, untouched raw/logs/failed cases, complete managed closure or honest failure, one completion report and machine-readable receipt. No commit/push or publication requested in this milestone.

## Contractor G4 workload clarification, revision2

Independent review found that the legacy600-second continuously-held pointer prevents genuine payload UI actions and leaves its initial payload lease expired. User asks an integrated ten-minute workload, not600seconds of continuousmanualinput. Use600continuousseconds of actual airborne telemetry and video with deliberate manual/assisted segments: genuine Android manual input briefly, UP-to-HELD; explicit public UI payload grants and observed gimbal/capture checkpoints at start/middle/end while no pointer is held; optionally another manual segment; then explicit AUTO resume, normal mission completion and review. Keep flight/video continuous across segments; no implicit payload renewal, synthesized input, relaxedlease or adjusted numericguard. Record actualmanualintervals separately and NEVER claim600seconds continuousmanual. Same760case policy and actualoverall deadlines remain; if segments cannot fit the original budget, fail honestly. Cold acceptance joins actualtelemetry/video throughout600seconds and originalgrants/commands/readback/capture at declared checkpoints, not mereoldpayloadcamera state.

## Contractor actual-preview scope correction, revision3

Root independently ran real pure resource previews after HOLD01: s01 admitted, l01 refused at Inventory.__init__ because that copied allowlist still accepts only s01/s02. Its prelude classification also omits l01. These are source-scope bugs; numeric budget tests and mocked orchestration did not exercise this path. Preserve HOLD01 and archive exact affected inputs before repair. Use the central closed nominal slot map for Inventory preview and sibling-domain classification, retain strict unknown/symlink refusal and all quota accounting. Run both real no-actor pure previews and behavioral current/sibling/unknown-path checks, regenerate source pins/HOLD02. No candidate or actor exists yet; no old release/ENDURE is changed. Artifact10MiB refusal remains independent and cannot be bypassed; the requested11MiB amendment is pending, not authorized.

## User artifact amendment, revision4

User explicitly approved artifact11MiB only: `Cho phép artifact 11 MiB, giữ các guard còn lại`. Exact receipt: evidence/missionintegrated16/ARTIFACT11-AUTHORIZATION01.json. Archive exactHOLD02 inputs first (TIP snapshot already saved as TIP-HOLD02.md). Amend only the shared candidate cap10→11MiB, corresponding error labels and conservative artifact reserves/peak/requiredFree fields by1MiB; all ten pools count. Keep metadata envelope, counters, source timing/durability/physics, power/lid/disk floors and100/200/250ms unchanged. Add exact-delta and actor-family boundary regression, preserve superseded mocks/receipts, regenerate source pins/HOLD03. Root independently verifies delta/closure before pure freeze, actual full-load/resource admission and one nominal s01. No APK/build/signature, old source/candidate/ENDURE/handoff changes or automatic retries. All gates remain, including true short acceptance before l01. Earlier pending/NOT_READY receipts remain historical.
