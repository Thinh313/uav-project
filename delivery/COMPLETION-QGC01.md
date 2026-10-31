# Completion · QGC01 v0.7 / M2 bounded interchange

2026-10-12. Owner authorizes SDK/HeraHub-independent development with QGC mission compatibility and SITL priority. Single-agent Contractor/Builder/Verify; no independent-review claim. No RAGAS application code, SDK/device/emulator installation or production release.

Delivered: pinned QGC v5.1.5 schema/fixture references, lossless original Plan import/export and hashed local intake, standard SimpleItem survey export with hash-bound simulator lineage, current/legacy parameter support, Survey v4/v5 cached command snapshot preview, deterministic simulator envelope/strict execution profile, integrated Plan/Fly links and QGC route display, actual ArduCopter mission execution/camera/fault journals. Source intent updated in58fact SOT; external QGC claims remain sourced in Refinery.

OVERALL: PASS_FOR_BOUNDED_QGC_SCHEMA_AND_LOCAL_SITL_PROFILE. This increment does not close all M2, QGC application interoperability or physical flight/HeraHub acceptance. Original complex configuration is preserved; execution flattens stored commands only. AERIS-generated fixtures are clearly distinct from official upstream legacy fixture and from a QGC application export.

| TIP AC | Result / evidence | Limit |
|---|---|---|
| AC01 | PASS: v5.1.5 commit3a67d31…;9official snapshots,6context-reviewed sourced claims; upstream fixture bytes/license hash | One QGC origin; no binary/Qt linked; legal/compatibility certification not claimed |
| AC02 | PASS: Plan v1/mission v2, current and legacy params, null/metadata/original bytes, bounded atomic import/reload/removal | Other complex/version patterns explicitly rejected |
| AC03 | PASS: GCS SimpleItem export, proper Home/AltitudeMode1/doJumpId, speed/camera and SHA-bound lineage | Standard Plan cannot enforce simulator-only use outside AERIS |
| AC04 | PASS bounded snapshot: cached Survey Items/polygon/camera retained; imported source and flattened trace shown | QGC-generated complex fixture/regeneration/open-save remain NOT_CHECKED |
| AC05 | PASS: bounded Copter profile and negative tests; no datum/Home relocation or unsupported-command dropping | Only pinned quad relative-home/takeoff/waypoint/speed/distance-trigger/RTL profile |
| AC06 | PASS:23Chromium QGC/offline/layout/source checks and9actual browser→SITL upload/recovery gates | Desktop/responsive touch emulation; no controller UX acceptance |
| AC07 | PASS:22actual SITL gates across2missions;16items each, accepted ACK/full readback, GUIDED/ARM/AUTO/final reached+landed+disarmed;30CAM events;24fault gates across2drop/timeout/recovery/disarmed-reboot cycles | Loopback, flat world; not RF/HIL/in-flight failsafe or physical imaging |
| AC08 | PASS local scope:118Node unit/API tests,0syntax errors,27GCS layout,19legacy browser,17native-intake regression,28receipt integrity gates;23successful SOT/Refinery stages incl6SOTbites | One external source check NOT_CHECKED: missing current BOM original; canonical hash/lineage checked |

Evidence: `evidence/qgc01` contains exact frozen requests, actual simple/complex MAVLink journals, standard roundtrip plans/lineage, CAM format/records and compressed DataFlash, two fault/reboot journals, browser/actual-operator/regression receipts, source manifest and source-integrity review. The dev diagnostic APK remains v0.6, unchanged and hash-checked; native runtime remains NOT_CHECKED. RAGAS B/operator timings/DJI superiority remain unmeasured.

Fault result and repair: initial real inbound-drop test exposed position remaining fresh briefly after heartbeat expiry. Live position/GPS/health now require fresh heartbeat plus own sample; a focused unit test and both repeated actual fault cycles pass. Browser actual-telemetry test exposed our strict coordinate helper receiving extra telemetry fields; map adapter now passes only lat/lon, and actual upload/recovery/no-runtime-error gates pass. Readback now compares autocontinue; current-item remains live progress. False autocontinue is rejected for the pinned Copter profile.

Verification repairs retained: initial restricted unit/API run could not bind loopback (EPERM), then authorized host checks passed. Browser helper needed textContent for collapsed raw JSON and explicit opening of offline details; no product bypass. Initial Refinery capture bite removed an unclaimed HTML extra, while claims used tagged .txt snapshots. Project wrapper now removes a claim's actual snapshot; unchanged transfer engine and all applicable bites pass. Receipt checker initially referenced execution at the wrong journal path; it now checks observed.mission.execution and actual completion proofs. First failed fault/operator/Refinery receipts remain archived. See verification-notes.md.

SOT: only INTENT.QGC01 added to canonical product_truth; adapter reviewed, explicit baseline accept, check/bites/gate and local export completed.58facts:17CONFIRMED_INTENT,3PROPOSED,9UNKNOWN,28BOM_LISTED,1FLAGGED. Digest7fdb0c08b944f661. No automatic promotion from mission source, BOM listing or controller JSON to operational capability.

Deferred hardware-free gates: QGC application open/save and independently QGC-generated golden corpus/complex regeneration parity; other mission/payload/vehicle/datum patterns; repeated in-flight GCS failsafe/link and flight restart campaigns; operational vertical-reference/launch validation. Native SDK/input/video/HIL/field gates wait for an exact device/configuration; absence does not block these software increments.

Cleanup: no dependency install or project copy. Method-bite scratch `/private/tmp/codex-tmp-aeris-qgc01-20261012` removed. Raw simulator00000002.BIN removed after preserving initial CAM snapshot and complete closed-log gzip, validating original prefix/final hashes. Duplicate downloaded diagnostic APK and legacy screenshot copies removed. Docker image prune reclaimed0B; volumes/other containers untouched. Task-owned disarmed simulator and localhost preview retained for review.
