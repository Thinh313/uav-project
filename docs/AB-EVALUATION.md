# RtR GCS A/B evaluation · independent implementation

A=AERIS independent build; B=installed RAGAS binary operated as a black box. No RAGAS source reuse. Survey is the first scored workflow, followed by preflight/live control, payload/video, offline recovery, RTK and post-flight evidence.

## AB01 fixture / reproducibility

`evidence/flight01/ab01-survey.json`: 45×45m local square expressed in WGS84, simulated flat world,15m relative altitude,6m/s,30% overlap, explicitly demo camera. Compiler output and full readback stored in journal. Reference runtime: official ArduCopter4.7.1, same copter+aeris params and home; Ubuntu x86 emulator, --speedup5. It is simulator correctness evidence, not controller latency evidence. Execute A and B sequentially against freshly reset identical simulator state. If RAGAS cannot run in the same controller/runtime environment, mark those measures non-comparable and later repeat on identical HeraHub hardware.

Test fixtures/config/build hashes must be recorded before either run. Freeze AERIS package+app/services, RAGAS APK version/build/hash when legally accessible, autopilot binary/version/params and radio/controller/camera revisions. Public release version alone does not identify installed binary. Never change simulator checks/tuning between arms or invent B results.

| Metric | Evidence / interpretation |
|---|---|
| Task success | Operator completes plan→review→upload→readback→execute→recover records. |
| Mission correctness | Same area/altitude/speed and explicit camera command semantics; normalized autopilot readback. |
| State truthfulness | ACK/observed state separated, stale data visible, no false “running” after reconnect. |
| Interaction burden | Recorded touches, task duration, errors/recovery; no inferred usability score. |
| Reliability | Controlled packet loss/reboot/rejection/missing-data scenarios with exact conditions. |
| Performance | Input/video/telemetry timings and frame/memory/power measured on the same HeraHub/config. |

Current A evidence: local SITL telemetry/upload/readback/commands/progress/landing and simulated camera log. Current B: NOT_CHECKED. No assertion that AERIS is already superior to RAGAS/DJI. Long-term differentiation: coherent operator UX, verified mission behavior, native device integration and AI assistance with bounded authority.

## AB02 geographic fixture / SURVEY02

`evidence/survey02/ab02-request.json` fixes the same 45×45 m WGS84 square,15 m nominal height,6 m/s,30% overlaps and demo camera, now with pinned geographic manifest and explicit sim-dsm-offset policy.16 items retain speed, camera trigger and RTL semantics; variable NAV altitude is downloaded and compared through documented ArduPilot centimetre normalization. Source/query/date/hash, DSM EGM2008 limits and flat simulator ground remain explicit.

`ab02-bundle.json` is a post-run audited A pilot evidence bundle with build/runtime/fixture/journal hashes, observed mission completion and controlled fault receipts. It is reproducible A preparation, not a precommitted comparative A/B trial. Freeze its inputs before either arm in a formal A/B run; record RAGAS installed APK/config hash and same device/runtime, or mark measures non-comparable. B is NOT_CHECKED. Operator task timing/usability and native latency are null; automated upload/readback timing is not an operator/performance superiority score. Native intake is in HERAHUB-NATIVE-INTAKE.md.

## BENCH06 frozen engineering preparation

`app/fixtures/bench06/suite.json` pins three accepted patterns and four rejected requests, with source/compile hashes and exact QGC derivation lineage. `evidence/bench06/freeze.json` was created before the final campaign and records app/services/runner/build, simulator binary/defaults/image/arguments, world and profile. `run.json` carries fresh-reset v2 execution records, conservative outcomes and negative rejection receipts. `wire-qa.json` independently captures actual socket writes on a fresh read-only link, avoiding a false zero from the bounded 10,000-frame journal. Run this mandatory supplemental check after the campaign with `node tools/bench06_wire_qa.mjs`.

The evidence page `/benchmark.html` validates the package before displaying it. Engineering PASS requires observed command modes in the planned sequence as well as completion/stop evidence; STOPPED alone does not certify a HOLD→RTL trial. B observations cannot be invented through an import. A formal comparative collector for installed RAGAS and human metrics is still a future contract; current operator duration/touches/native performance and winner remain null. Digests prove consistency, not signed authenticity or actual hardware configuration.
