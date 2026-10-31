# Independent QA: FIELD02 repair01

**NOT READY.** Source/mock repairs are useful engineering results. The complete Android flight-controller milestone is not accepted.

| AC | Recommendation | Evidence and limit |
|---|---|---|
| 1 | PARTIAL_RUNTIME_OBSERVED | Actual Android 13 / WebView 101 runtime and host-companion topology observed. The final resource abort prevents complete qualification; no Hera, Xiaomi or standalone-controller claim. |
| 2 | HISTORICAL_PASS_NEW_SOURCE_NOT_CHECKED | Original polygon and corridor SITL evidence remains historical. The final repair01 connection is MOCK; no current-source Android–SITL nominal AUTO with concurrent media was run. |
| 3 | FAIL | Final actual 239 frames / 30.0448 s = 7.9548 FPS < 24; calibrated p95 upper 573.079 ms > 300. Initial ready 1337.9 ms and recovery 708.9 ms pass only this window. Final-source cold boot was not checked. |
| 4 | MOCK_PASS_LIVE_NOT_CHECKED | Final authority tests passed 10 groups; actual app-handler tests passed 4 groups with local WAL. Active-lease invalidation during actual AP reboot was not observed. No actual postfault old-context request was sent. |
| 5 | HISTORICAL_FAULT_PROOF_NEW_SOURCE_NOT_CHECKED | Original actual TCP cut and owned guest AP reboot remain incomplete-flight evidence, not physical failsafe proof. Repair01 has no actual AP start or reboot and no live active-lease acceptance. |
| 6 | HISTORICAL_PASS_AFFECTED_REGRESSION_NOT_CHECKED | Prior Android pending, cancel, tamper and restart evidence remains unchanged. Affected final-source restart and persistence regression was not run. |
| 7 | HISTORICAL_PASS_AFFECTED_REGRESSION_NOT_CHECKED | Prior actual SAF provider bytes and independent receiver evidence remains unchanged. Final-source SAF regression was not run. Host artifacts are not new SAF proof. |
| 8 | TARGETED_ACTUAL_PIXEL_PASS_LIMITED_UI_COVERAGE | Actual Android DAY error contrast 5.67:1 and fresh-age contrast 7.12:1 pass the selected 4.5:1 ROI gate. No claim covers every screen, pixel or device. |
| 9 | FAIL_RESOURCE_FLOOR_PRESERVATION_PASS | Declared 1486 protected files, 1081 old evidence files and current native 7 have zero differences. The Android minimum 421421056 bytes = 0.39248 GiB violates the 20 GiB floor; later closure does not retroactively pass it. |

The last Android connection created `m93498c6ac9f741b39d44`, explicitly `mode:mock` with `mock-boot`. All 72 successful observer rows identify that mock run. The 277-row observer also contains 205 failed reads; they do not establish continued flight state. The 6228-row raw hash chain and review file digests are intact. Its review remains accepted:false, aborted:true, AUTO:false and execution incomplete. The separate s-prefixed synthetic-media identity is not proof of an ArduPilot start.

Final media arithmetic independently reproduces 239 frames / 30044.8 ms, 7.9547875 FPS and 573.079 ms calibrated p95 upper. Initial ready 1337.9 ms and 500 ms relay recovery 708.9 ms pass only their own gates. Source cadence mock math passes, but no sustained performance gain or isolated root cause is proven. Snapshot counters show 900 scheduled slots, 817 eligible callbacks, 83 missed slots and 574 credit skips. Rolling encode-output wait includes queue and callback scheduling.

The resource guard recorded 421421056 bytes minimum, about 0.39248 GiB. Host and emulator closed, but this is a real continuous-floor failure. The source of disk consumption or release is unknown. Recovered free space does not change that conclusion.

The declared 1486 protected files and 1081 original FIELD02 evidence files remain exact. Current native 7 matches approved freeze02. My first QA preservation report used older freeze01 for native; its two approved APK02 changes are explicitly explained in the retained supplement. An initial raw-chain parser also stripped one nested data SHA. Correct top-level-only parsing gives zero raw issues. Neither QA parser/baseline error is hidden or treated as product-data corruption.

Current-source AP nominal and reboot active-lease tests, postfault old-context rejection, final cold boot and affected restart/SAF regressions remain NOT_CHECKED. Existing historical FIELD02 evidence remains valid only in its stated scope. Further production repairs or live attempts require a new bounded decision and independent runtime evidence.

Evidence: `qa-final-repair01.json`, `qa-resource-incident-final02.json`, `qa-media07.json`, `qa-media07-source.json`, `qa-native-preservation-final02.json`. Root owns final process closure and cleanup evidence. QA launched no AP, emulator or UI session and created no external scratch, dependency or cache.
