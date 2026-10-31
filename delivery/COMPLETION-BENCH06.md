# Completion · BENCH06 v1.2 / mission matrix and A/B preparation

12/10/2026. REQ-BENCH06:1/1 implemented, AC01–07 PASS for the bounded hardware-free increment. Single-agent Contractor→Builder→Verify; no independent review or commercial/physical acceptance. No SDK/device install, source RAGAS, parameter writer, forced ARM or field flight.

| AC | Verification |
|---|---|
| AC01 | Hash-bound7-case suite: narrow/rotated generated surveys and exact QGC-source relative derivation; concave/datum/radius/camera-rate requests remain rejected. Compiler/profile command set unchanged. |
| AC02 | Pre-run freeze includes79 app/services/pilot/build files and exact simulator binary/defaults/image/model/home/speedup5. Four final attempts have distinct fresh reset/session/profile boundaries. Source/runtime still match freeze. |
| AC03 |30 final actual SITL checks:3 completed flights,1 ordered HOLD/LOITER→RTL interruption,4 rejects, final disarmed;12 independent socket-write probe checks support zero negative writes without journal-ring inference. |
| AC04 | Validated run import/export and read-only latest receipt. Case/source/compiled/build/profile/reset bindings reject corruption/reuse/misclassification. Ordered observed mode proofs qualify success; B/actor/native measures and winner remain null. |
| AC05 |192 unit/API tests,99 shared-control/responsive/offline checks,19 evidence-page browser checks including false-B tamper, retained-good-package and offline tests; zero browser POST. |
| AC06 |27 map/command-visibility/drag and23 QGC import/export/offline regressions; syntax, source/freeze/dataflash integrity pass. Previous receipts and legacy execution records preserved. |
| AC07 |63-fact SOT with sole INTENT.BENCH06 addition,29 applicable kernel checks; original external BOM locator remains NOT_CHECKED while canonical bytes/cell lineage pass. Local gated export digest3d85611e0bf3fa83. |

Implementation: `app/core/benchmark.mjs`, hash-bound suite/builder, pre-run freezer and simulator driver, socket probe, read-only benchmark UI, fixed GET-only local receipt endpoint, offline cache and shared control gate extension. Record schema stays v2; new records identify build1.2.0-BENCH06. Profile definition remains v1.0.0 with the same four read-only expectations; no new operational defaults.

Retained investigations: attempt01 completed three patterns but its test wrongly expected POSHOLD for the existing HOLD→LOITER mapping; cleanup observed disarmed. attempt02 refused startup because a historical disconnected sessionId was mistakenly treated as active; the guard now checks connection/active attempt. attempt03 passed30 checks and is preserved before the final procedure-proof qualification/source freeze. The final campaign passed30/30 on final sources. Initial browser QA waited for a hidden install control; the driver now opens its disclosure, and the19-check run passes. These test-driver findings did not change autopilot command/compiler behavior or hide failed receipts.

Cleanup: transfer scratch `/private/tmp/codex-tmp-aeris-bench06-20261012` removed; all UUID unit-test stores removed.13 closed simulator DataFlash files verified and compressed into `evidence/bench06/dataflash`, removing129,098,609 raw bytes and retaining47,957,544 archive bytes. No project copies, installs, extra build folders or new image tags. Image prune reclaimed0B; no container/volume deletion. Final normal simulator observed disarmed with a fresh matching profile; preview8788 and historical records retained. Disk51GiB free before cleanup.

OVERALL: READY for local review, with explicit deferred hardware/SDK/HIL/field datum, complete aircraft configuration, signed/power-loss/long-duration evidence and formal operator/RAGAS A/B collection. Engineering preparation does not establish usability or product superiority. Receipts: `evidence/bench06/verification-summary.json`; contract: `docs/BENCH06-CONTRACT.md`.
