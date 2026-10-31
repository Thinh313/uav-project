# MAVFLIGHT37 — completion and verification

14/10/2026. **DONE within restricted offline mock/replay scope.** Status: `MOCK_ADAPTER_VERIFIED`. One agent implemented and then verified in separate interpreter invocations, with a distinct upstream serialization/parser implementation; this is not independent review or actual firmware acceptance.

## Delivered behavior

- An 18-message binary MAVLink1/2 encoder/stream decoder, pinned to local minimal/standard/common/ardupilotmega XML and checked against upstream Python v1/v2 schema generators/parsers.
- Geofence polygon/circle/inclusion/exclusion mapping to MISSION_ITEM_INT with degreesE7 coordinates, float32 radius and independently hashed original/quantized geometry. <=64 items in this restricted adapter. Quantization geometry is revalidated and errors reported.
- One bounded mock upload/readback transaction per link instance. Upload ACK starts readback; proof needs every item and each requested raw parameter value to match. Wrong sender/recipient/mission/context, partial data, mismatches, loss, reboot, stale/slow fragment assembly, writer cancellation/failure and excess duplicates cannot produce a completed proof. Serialized receipts cannot restore the live proof capability.
- Named readonly parameter request/match for 14 arbitrary fence/GCS/RC/EKF/battery expectations in the corpus. Only REAL32 encoding is admitted; other parameter types stay unverified. No normalized policy or active enforcement is inferred from raw values.
- Telemetry translation for heartbeat, landed state, GNSS accuracy, estimator/sensor flags, primary battery, Home and altitude frames. Packet and first/last-byte receipt times are retained; the oldest contributing receipt controls freshness. Pinned EKF2/3 square-root test ratios are squared before comparing with the core innovation-ratio threshold.
- APFLIGHT36 preflight/failsafe assessments using translated wire fields and separately labeled synthetic supplements. Wire-only inputs cannot invent remaining Wh, Home datum confirmation, throttle context, AP-side GCS heartbeat history or RC availability. ACK, fence breach and observed RTL remain separate observations with physical execution/cause unproven.

All outgoing packets end in `MOCK_BUFFER_ONLY`, `networkSent:false`; no network transport exists. No frozen source/candidate edits, Fly/native integration, APK/software build, dependency install, new SITL/emulator, software/MAVLink signing, trust selection or ENDURE restart occurred. No Ragas application source was introduced.

## Requirement coverage

8/8 requirements implemented and verified in the TIP's mock scope; runtime/firmware/hardware checks are explicitly deferred.

| Requirement | Verification | Result |
|---|---|---|
| R1 — bounded binary codec, order/CRC/truncation/extensions | 144 upstream vectors; exact pack/decode, every byte split, CRC mutation and flags/bounds checks | PASS |
| R2 — fence mapping and quantization | circle/polygon/exclusion corpus, coordinate/radius errors, collapsed-geometry refusal | PASS |
| R3 — transaction/readback/correlation and faults | ACK-only/partial/wrong peers/types/config, disconnect/reboot/stale/writer/duplicate scenarios; live proof checks | PASS |
| R4 — telemetry clock/unit/identity/sentinel semantics | epoch/session/sender/boot/packet sequencing, first-byte age, stale independent sources, sentinel/nonfinite/primary battery/Home/EKF ratio checks | PASS |
| R5 — bounded named readonly params and restricted outputs | 14 parameter expectations; wrong type/value, no clear/ARM/general command/parameter write | PASS |
| R6 — preflight/failsafe bridge and explicit missing evidence | wire-only UNKNOWN, full synthetic supplements, GCS/RC/battery modeled triggers and configuration mismatch | PASS |
| R7 — no execution claim and semantic tamper resistance | ACK/breach/RTL observations separated; six hash/rehashed-outcome/forbidden-operation bites | PASS |
| R8 — regression, frozen evidence and resource budget | original 33-case receipt reproduced exactly; preservation hashes; bounded allocation and disk checks | PASS |

## Current-source validation

- `logic4.json`: **634/634** checks pass. Of these, 576 are four checks per 144 reference vectors; the remaining 58 cover adapter boundaries/faults plus the aggregate original corpus regression. Do not sum prior attempts into this result.
- `replay4.json` + `corpus4.json`: **41/41** scenario outcomes match, **6/6** tamper bites rejected. A fresh, separate invocation reproduces the complete replay result exactly.
- `oracle-check2.json`: **880/880** separate upstream parser checks pass, covering 144 JS-produced vector frames and 736 mock-dialogue RX/TX-buffer frames. These overlap the codec/replay checks and are separate evidence, not additional unique flight scenarios.
- APFLIGHT36: **33/33** original cases pass and reproduce the original `evidence/apflight36/replay6.json` result exactly. No original receipt was overwritten or new original-namespace test output written.
- `verification1.json`: **14/14** verification gates pass; **9/9** JavaScript syntax checks pass. No APK/build/typecheck/lint/runtime acceptance is claimed.

Current code has no network/process/transport import in the adapter core. Raw CRC-checked packets are unsigned and unauthenticated; this module does not supply a security or real flight-admission guarantee.

## Preservation and resource result

**13,482/13,482** admission protected paths retain their exact expected SHA; zero missing files or changed bytes in this inventoried set. This includes the earlier restored 9,365-path historical inventory, APFLIGHT36 receipts and the separate RESTORE41 evidence. ENDURE's **5,051-file** inventory and protected bytes remain unchanged. Additional mapping-source pins match their read-only observations; they do not establish the running firmware.

Original incident/repair/ENDURE verdicts remain historical and unchanged. Continuous original-path presence is not claimed; previous failed ENDURE intervals are not recombined, resumed or promoted to 24-hour acceptance.

At verification, source/evidence allocation was approximately **6.58 MiB**, under the 8 MiB scoped budget, and available disk approximately **27.01 GiB**, above the 20 GiB floor. No whole-project copies, installs, scratch/build directories or caches were created; no temporary files or other user data were deleted. Generated Python oracles are retained as bounded test evidence, not production artifacts.

## Issues resolved and retained

`generation-attempt01.json`, `oracle-vectors1.json`, `logic1.json`, `corpus1.json` and `replay1.json` remain intact. The first XML traversal omitted standard.xml; v2-generated oracle output forced to a v1 header did not match a genuine v1 schema; a test mutated a shared coordinate in RAM; two initial replay expectations were too permissive for missing context/config. A later source review found square-root EKF test-ratio semantics, corrected with a threshold case that detects the earlier comparison error. Current receipts are from the corrected source; earlier PASS or FAIL receipts are not used in their place.

The local upstream parser's unrelated CAMERA_TRACKING_STATUS_FLAGS_IDLE bitmask warning is retained in interpretation notes; all 18 selected layouts and CRCs agree. Details: `pilot/mavflight37/REFERENCES.md`.

## Deferred and next gate

Actual AP wire/session/firmware conformance, parameter cast capability, complete firmware-specific failsafe/options/altitude configuration mapping, authenticated replay protection, real retry/high-rate sequence policy, SITL enforcement, Android/APK/emulator, Hera SDK/device, calibration and physical flight outcomes are **NOT_CHECKED** in this task. No automatic software-release gate opens from this mock result.

The next preparation step is a pinned firmware/capability mapping contract for parameter encoding and failsafe/altitude semantics, with negative corpus cases. Then, under separate authorization, validate on actual pinned ArduPilot SITL in a new isolated namespace before any live/native/Fly integration. See `delivery/ROADMAP-MAVFLIGHT37.md`.

## Reproduce scoped checks

From the aeris root: `node pilot/mavflight37/tests.mjs`, `node pilot/mavflight37/replay.mjs`, `node pilot/mavflight37/oracle-dialogues.mjs`, `python3 -B pilot/mavflight37/oracle-check.py`, `python3 -B pilot/mavflight37/verify.py`. Test/replay/verifier receipts append by attempt. The verification script binds the current accepted logic4/replay4/oracle-check2 receipts; it does not silently accept a changed source or newest unreviewed run. Generator reruns refuse existing definitions; do not overwrite generation history.

All new source/evidence/docs are bound by `evidence/mavflight37/artifact-fingerprints.json`; existing protected manifests and canonical SOT remain untouched.
