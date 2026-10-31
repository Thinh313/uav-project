# NATIVE87 — Android workspace recovery and SITL cockpit

Status: **PASS in the scoped Android/SITL qualification, with a recorded UI observation**. 2026-10-17T23:25:53.653416+07:00

Implemented in `native/native87`, package `vn.rtr.aeris.native87`; development07 is installed-byte verified on owned emulator-5582, Android33 ARM64/WebView101.0.4951.61,1280×800. No HeraHub or production qualification.

## Delivered and verified

- Durable file-operation journal before SAF picker. Late completion remains discoverable after the JS timeout; restart produces UNKNOWN for an unconfirmed transaction. No retry, invented success, auto activation or deletion.
- Final export held beyond65seconds, provider bytes/readback SHA matched. Wrong archive rejected; exact original reselected after restart. Import staging survived restart, required explicit reconciliation and activation, retained the original generation and all SITL reviews.
- Current composite mock+SITL HEAD binds export/fresh guard. An older export cannot authorize a changed SITL journal; quota failures retain evidence.
- Explicit mock/SITL sources. Real firmware4.7.1 position, Home/MSL, mode, armed, battery and data ages feed main Fly; stale observations clear. The illustrative terrain/camera background is hidden in all final SITL views.
- Actual Android KML→compile→readonly→preflight→grant→upload/readback→arm→separate fresh Home approval→AUTO→waypoints→terminal RTL item→observed land/disarm→committed Android review.
- Accepted run `s8ed14645457e45388ac8`:16items including Home,2readback cycles,6camera commands,5635raw records,0actual photos and0MAVLink PARAM_SET. A separate full-stream JS verifier and pinned upstream Python dialect checked bytes/CRC/target/mission/camera semantics; geometry establishes takeoff rather than ACK alone.
- Disarmed telemetry loss and owned ArduPilot guest/process restart invalidate the session, clear observations and do not reconnect or restore authority. App restart and Android reboot preserve exact journals. Imported generation and completed mock review also survive app restart.
- Final APK mock journey separately completed with2observed points; ACK leaves cursor unchanged; review remains `COMPLETED_MOCK`,0images, no physical execution claim.

## Coverage

| Requirement | Result | Evidence |
|---|---|---|
| REQ87-01 file outcomes/recovery/quota | PASS in tested scopes | `evidence/native87/verification.json` |
| REQ87-02 actual readonly Fly | PASS | readonly prefix, main Fly screenshots, freshness tests |
| REQ87-03 actual Android AUTO→review | PASS | accepted run/raw verification/upstream oracle |
| REQ87-04 restart/loss | PASS for ground/process/app/Android cases | restart receipts; in-flight and wire reboot NOT_CHECKED |
| REQ87-05 regression/UI/preservation/closure | PASS with UI observation | UI QA, runtime closure,53496-file SHA audit |

Regression sets:31controls,46freshness/history,14takeoff,24protocol mock,16workflow; JVM Policy22/DraftStore31/ArchiveEdges4/FileOps12/Composite3/Workspace12/History11.48modules pass syntax. Captured Android semantic replay verifies23unique records:17mock,2plans,4reviews, including exactly1accepted SITL review. These counts describe distinct suites, not independent review teams.

## UI QA and remaining limits

91selected renderer snapshots across mock plan/preflight/Fly/review and day/night. Telemetry/logo gutter delta0CSSpx; left/right island centre delta0CSSpx when both visible. One snapshot during scrolling records `confirm-route` under the sticky footer; fully revealed checkbox and the explicit confirmation path pass. Per-control coordinates were not captured in that snapshot. Do not claim zero overlap across every scroll state. A heading near north may round to360°; engineering reason codes and the SITL control panel remain prototype UX. No GPU/FPS/thermal or exhaustive pixel qualification.

The workspace ZIP verifies included journal bytes and hashes; **it does not contain the full host raw-flight files**. They remain at `evidence/native87/runs/s8ed14645457e45388ac8`. The exported ZIP predates the later mock run, by design; no claim it contains later revisions.

HeraHub input/radio/vendor SDK, physical cameras/gimbals/video, actual mapping images, flight performance, in-flight failure qualification and production signing remain NOT_CHECKED. ArduPilot restart here is a disarmed guest/process restart; the MAVLink firmware reboot command was not tested. No pacing or24h ENDURE PASS is inferred.

## Artifact, preservation and closure

APK: `native/native87/dist/aeris-native87-development07.apk`  
SHA256: `f3ccd593cab839fb32da8c00e57c55f7f483435311e419182fcdbf47b6ec55e4`  
Development certificate: `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`. v2/v3signature; INTERNET permission only; no WebView debugging/backup.

53496protected paths match SHA before/after, including prior Native86. Frozen source/candidate/ENDURE and canonical SOT remain unchanged. This confirms present bytes; it does not rewrite historical missing-path incidents or claim continuous presence. Build then QA used the same agent, with separate deterministic replay paths; no independent-team claim.

All owned simulator/bridge/emulator PIDs and ports closed; token removed. Runtime controller minimum free41.48GiB; final observation41.52GiB. Removed only6temporary unsigned APKs plus native87 `__pycache__` (~19.5MB); reusable SDK86,AVD87,signed APKs and evidence retained. Docker image prune reclaimed0B; no volume/container prune.

## Next priority

Close the recorded UI details and replace engineering status codes with actionable operator outcomes. Add an explicit, separately authorized in-flight disconnect/background acceptance campaign and receiver handoff including full raw evidence. Then qualify payload/input/video on HeraHub when hardware/SDK is available. Do not expand mock results into commercial or hardware readiness.
