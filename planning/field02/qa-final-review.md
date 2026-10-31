# FIELD02 independent QA final review

Snapshot: 2026-10-22T01:55:04.964166+00:00

**Recommendation: NOT READY for the full milestone.** Five AC have positive evidence in their declared selected scope. Mandatory video, payload-revocation, UI contrast and final-closure gaps remain. This is Android emulator plus localhost companion and synthetic payload/media, not native-direct or Hera acceptance.

| AC | Recommendation | Evidence and practical boundary |
|---|---|---|
| 1 | PASS_DECLARED_EMULATOR_SCOPE | Actual development APK ran on Android 13/API 33 arm64, WebView 101, 1280×716. Root-collected Android touch journeys and SAF journals show execution. The architecture is explicitly a localhost host companion. No Xiaomi, HeraHub, native-direct MAVLink or physical camera qualification. |
| 2 | PASS_SELECTED_POLYGON_CORRIDOR_CORPUS | Two actual Android–SITL runs completed the selected polygon and corridor. Saved KML/model/plan, upload, two readback cycles, camera semantics, zero PARAM writes, terminal RTL and ground state were independently checked. The missing takeoff reached event uses an explicit validated climb/current-transition proof. Internal AP quad on flat terrain; not Hera dynamics or arbitrary terrain/KML qualification. |
| 3 | FAIL_ACCEPTANCE_FPS_AND_COLD_START_UNRESOLVED | Selected actual Android window: 705 samples, 23.4803548 fps, below the 24 fps target. The calibrated latency p95 upper bound 178.260875 ms passes 300 ms. New network bootstrap passed five independent VM policy tests. Root app09 first start still timed out; explicit viewer restart displayed frames. No accepted new cold-start/recovery/30-second performance window in this snapshot. Synthetic source-to-canvas timing is not camera exposure or photon latency. |
| 4 | PARTIAL_MANDATORY_GAP | Three synthetic JPEGs were independently checked against exact bytes and raw run/boot/model/plan/position. Corridor capture was 9.133 m above Home during landing. Mock gimbal readback and explicit revocation were retained, with no accepted capture afterward. Active lease invalidation at reboot NOT_OBSERVED. Grant intent has no persisted timing or success receipt; source clearing does not substitute for runtime observation. No physical Phase One, Sony, gimbal or thermal driver tested. Thermal-look is not radiometry. Polygon photos were near ground or disarmed; these do not establish airborne mapping coverage. |
| 5 | PASS_OBSERVED_FAULT_CASES_WITH_SCOPE_LIMITS | Actual TCP cut and owned Docker AP process restart preserved raw logs and incomplete reviews. Flight authority was revoked; position/armed state became unknown. No reconnect or command retry was observed. Reboot intent followed a fresh 9.692 m position. C2 manual cut last position was 1.836 m, below the planned 5 m point; earlier maximum height cannot replace height at cut. No new MAVLink boot observed, physical FC reboot, terminal RTL, ground disarm or physical failsafe inferred. Concurrent video outage during AUTO with responsive control/WAL and fresh-frame recovery is NOT_OBSERVED. Payload lease invalidation gap remains under AC4. |
| 6 | PASS_OBSERVED_RESTART_CASES | Actual cold Activity launch preserved the native journal prefix and appended one UNKNOWN_AFTER_RESTART. The pending stage SHA matched. Canonical corridor mission, captures and reviews survived; effective authority remained NONE. Host restart also preserved the shared workspace. Ordinary amstart first restored an orphan DocumentsUI task without the app PID: retained NOT_EXERCISED. Only explicit cold own-Activity launch proves recovery. No host power-loss or Android storage hardware durability qualification. |
| 7 | PASS_SELECTED_SAF_AND_RECEIVER_CASES | Actual SAF workspace export/import and four-file delivery matched native receipts and provider bytes. The independent receiver passed fourteen adversarial groups with unchanged success ledger on refusals. Actual picker cancellation retained its stage; corrupted import was rejected without saving a mission. Actual changed-head-while-picker-open race not exercised; CAS policy is supported by source/mock checks. Integrity receipt is not sender authentication or physical image/position quality. |
| 8 | FAIL_DAY_CONTRAST_PARTIAL_WORKFLOW_UI | Actual touch journeys completed. Nine independent position-helper cases reject stale/invalid GNSS and missing/wrong context, allow legitimate 0/0 with valid GNSS and never mint a token. Final screenshot shows balanced header/metrics and unknown telemetry as dashes, but pale error text on day glass remains a contrast defect. Day-theme low-contrast error/video-age text is a P1 operational readability issue; no blanket UI PASS. Small paint-order token-status inconsistency reported: header is fenced, but dialog status was computed before token clearing. No exhaustive compact 900×500 or every-device pixel audit. |
| 9 | NOT_FINAL_ROOT_CLOSURE_PENDING | Earlier protected baseline checked 1,486 files with zero differences. Latest source-check05 manifests independently rehash without drift. Builder reported 50 syntax checks and 57 flight pins with zero drift. Emulator01 closed cleanly; final emulator02/app09 closure is pending. Final preservation, disk and owned-process closure are outside this snapshot. Corrected budget is seven total requests and six actual AP starts; prelaunch refusals remain retained. No ENDURE acceptance, new soak or production signing implied. |

## Mandatory gaps

- AC3: cold network decoder still failed on first Android app09 start at 1500 ms. One explicit viewer restart succeeded, but a new 30-second window is pending. Retained earlier 23.480 fps fails the 24 fps target.
- AC4: active payload lease invalidation at actual reboot is NOT_OBSERVED; expired postfault lease cannot retrospectively prove revocation. Source/mock evidence only.
- AC8: day-theme error/video age text has inadequate contrast on light glass. Do not declare all UI accepted.
- AC9: final owned-process/resource closure and protected fingerprints await root.

## Evidence audit

All 59 source-check05 manifest paths independently matched their recorded SHA. Builder syntax checks: 50 marked PASS; flight pins: 57, zero drift. Independent helper checks: 9 position cases and 5 actual-viewer VM cases. These are policy checks, not Android media performance acceptance.

Actual Android media retained: 705 samples in 30.0251 seconds, 23.4803548 fps FAIL against 24 fps, latency p95 upper bound 178.260875 ms PASS against 300 ms. Its fault-window list is empty. Root app09 still failed the first cold startup at 1500 ms; an explicit viewer restart displayed frames. The new measurement remains outside this snapshot.

Final day screenshot was independently viewed. Header and telemetry align without visible overlap in this frame, and absent telemetry stays unknown. Pale error text against day glass remains difficult to read. No claim of an exhaustive pixel audit follows.

Reboot evidence retains 9,263 raw records, 12 uploaded items, 24 readback items, 4 camera commands and zero PARAM writes. Last position was 9.692 m above Home, 139.446 ms before intent. Same owned container restarted with changed PID and StartedAt; its console contains two AP starts. No new MAVLink boot, physical failsafe or completed flight is inferred. Active payload lease revocation at reboot remains NOT_OBSERVED.

Actual SAF cancellation preserved the correct operation stage. Tampered import left mission/captures/reviews unchanged. Four actual provider files passed exact native receipt matching and independent receiver checks, separate from earlier host-only exports.

Root owns app09 final UI/media verification, resource/process closure and final preservation. All earlier failures and original snapshots remain. Counts do not establish product maturity or superiority.

Machine-readable evidence and per-AC fingerprints: `evidence/field02/qa-final-independent01.json`.
