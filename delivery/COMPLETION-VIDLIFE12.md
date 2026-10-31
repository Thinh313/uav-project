# VIDLIFE12: native direct and video lifecycle

31/10/2026. **PARTIAL, integrated beta NOT READY.** Source publication does not qualify a new release, real aircraft, camera, or completed video-measure run.

## Result

- Added bounded native/direct and video lifecycle diagnostics, first-failure context, and source-age validation substages. Heartbeat replies retain their own journal durability without waiting for an unrelated payload queue; revoke/background obligations remain.
- Corrected explicit ArduPilot telemetry cadence: heartbeat id0 at200000us, attitude/position30/33 at50000us, other declared streams unchanged. Android–SITL observed9accepted serialized ACKs and qualified post-ACK gaps271ms/64ms/64ms.
- Actual S01 stopped before video/AUTO at navigation readiness: all95EKF reports had flags167, missing absolute horizontal position; battery25.148–25.150V passed. ArduPilot reported `Fence enabled, need position estimate`. No guardian fault, ARM, RC or video-start.
- Retained39,239 matching RX/INTENT/localSEND/STAGE groups; unknown sends0. Recording remains incomplete and is not accepted as a completed flight/media record.
- R02 changes only the cold navigation initialization wait from30to60hostseconds. Eleven targeted mock checks pass, including refusal of bad EKF and stale actual data. Live convergence and video-measure remain NOT CHECKED.

## Current blocker and next gate

The exact pure allocation plan needs8,466,432B against the unchanged8,388,608B cumulative artifact cap, an excess of77,824B (76KiB). Current artifacts remain8,220,672B. No R02 candidate or S02 actor was created. This is the campaign artifact cap, not a shortage of free host disk. No evidence was removed or reclassified to fit.

Before another run, resolve that artifact budget within an authorized release plan. Then verify cold navigation, qualified decoded/warm frames and video-measure before the full AUTO/video/payload/link-loss/reboot/restart/SAF journey. The existing 10-minute target and real HeraHub/payload/production gates remain open.

## Product status

AERIS remains an engineering alpha with substantial isolated Android/SITL and mock capability. Integrated beta is not yet qualified. This milestone proves the cadence correction, not end-to-end video stability or readiness to operate a real Hera. No overall maturity percentage is claimed.

## Preservation and verification

- Fresh preservation:17,117legacy entries,29sealed inventories,5ENDURE identities,7old candidates,467IPC10files,270HOSTDIAG11files and125held planning files. The165preexisting missing paths remain a separate incident; no restoration or continuous path-presence claim.
- Both new frozen preparation candidates were loaded in separate fresh processes. All175S01files remain unchanged after managed failure disposal.
- Freshness250ms, HostHealth100ms, lifecycle1000ms, flight1500ms and hard-heartbeat3000ms remain unchanged, as do speedup1/catchup500ms and fsync-before-send/sensor.
- Owned processes/container stopped, ports8895/8896closed, publisher tab closed. No build/signing/download or production selection. Docker image prune reclaimed0B; no container/volume or evidence deletion.

## Source repository scope

This commit includes VIDLIFE12 and previously uncommitted supporting runtime, diagnostic, simulator and native source baselines needed to review its imports and source contracts. Historical milestones retain their own qualification; inclusion is not a new acceptance.

Raw evidence, frozen candidates, APKs, compiler output, host runtimes and signing material stay host-local under the existing repository policy. The compiled simulator `.so` is excluded. Existing working-tree missing paths are not staged as deletions; unrelated pending milestone reports remain outside this commit. A fresh clone still requires the declared pinned host artifacts for runtime reproduction.

## Host-local evidence fingerprints

- `evidence/vidlife12/qa/COLD-S01.json`: `8fd9882d07657bc80ff0627709da82158738b86c2886ddda0877c2642bb2b616`
- `evidence/vidlife12/qa/SOURCE-REVIEW05.json`: `3b8af767a88893d5837cdb326358df4346eb9575f68726149f5805b3dde9a412`
- `evidence/vidlife12/FREEZE-PREVIEW03.json`: `b9f038682016e9263696b755a23f98b8b3627436a34938aefa2628bc43862a74`
- `evidence/vidlife12/qa/FROZEN-FINAL01.json`: `00355347f60d5ad7cd4426a066b921a6c82cd71fea6c4f92848aa5ca7c7501b2`
- `evidence/vidlife12/qa/FINAL-SCOPE01.json`: `f627b7dca7bcfb8d08a3d4700616d40639906a34d771f011496df569676d1277`
- `evidence/vidlife12/reports/COMPLETION-VIDLIFE12.json`: `2576367832485fdab4285be0b686c3947243d72abcd4bbb952f0f8775c837f0e`

Detailed local report: `evidence/vidlife12/reports/COMPLETION-VIDLIFE12.html`. Git maintenance receipts are under `evidence/vidlife12/git/` and remain host-local.
