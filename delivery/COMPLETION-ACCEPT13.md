# ACCEPT13 · completion report

**DONE / READY for bounded host-local receiver engineering scope · v1.8.0.** 9/9 requirements implemented/pass (100%). Single-agent Contractor → Builder → Verify; no independent audit. User authorization covers dedicated simulator flights and local recipient implementation, not physical/commercial acceptance.

Recipient expectations bind exact manifest, immutable record, original mission and versioned profile SHA plus duplicate-aware file name/SHA/byte inventory. Fresh full receiver byte verification precedes the rubric and publication. Explicit reviewer/source/scope declaration, note and typed plan digest are required. Accepted/conditional/rejected decisions are sealed, immutable and chained to the previous decision/receipt/plan. Stale/forged plans, unsupported physical acceptance, incorrect/extra/missing files and corrupt/incomplete packets are refused. Original flight outcome and payload bytes are unchanged. Reviewer identity remains DECLARED_UNSIGNED, capture null, survey quality NOT_CHECKED. The receiving UI is a bounded engineering workflow; recipient expectations must come from a reviewed source/order, not self-approval of the incoming package.

Actual final campaign: six completed patterns (narrow, rotated, actual-QGC-relative, triangle, trapezoid, multi-strip), one interrupted multi-strip; each performs source/compiler/profile/readback → actual SITL observation → declared synthetic engineering report/planned GeoJSON → raw checkpoint transfer → fresh receiver rubric/decision → identical re-export. The interrupted record is STOPPED, full acceptance refused, then conditional only with explicit reflight condition. All seven decisions and wire digests survive a real main-server restart. Four compiler negatives still reject before mission writes. No PARAM_SET/force arm, and handoff/acceptance send no flight commands. Journal checks compare preserved session prefixes and refuse truncated windows instead of vacuous absence assertions.

**582 canonical checks PASS, 0 FAIL; syntax PASS, 0 skipped unit tests.** Unit/API 285 (14 new acceptance tests); shared control geometry 99; receiver UI 20 plus actual restarted-preview UI 2; storage regression 19; resume regression 18; actual E2E 87; actual restart 23; method/SOT/kernel 29. Source/corpus/runtime freeze is digest-bound; full final source manifest is checked. UI verified at six sizes with readable dark controls/full-width inputs and offline/tamper/stale revocation. All preexisting files including historical QGC record remain byte-identical (see legacy-preservation.json).

| Requirement | Evidence |
|---|---|
| A13-01 | unit-tests.txt, campaign.json: independent known-source expectations and exact comparison |
| A13-02 | browser-qa.json, unit-tests.txt, interrupted receiver journal: explicit engineering decisions |
| A13-03 | unit-tests.txt, restart-qa.json: immutable chain, tamper/gap/torn history refusal, real restart |
| A13-04 | unit-tests.txt, browser-qa.json, per-trial journal: token/origin/stale guards, no flight writes |
| A13-05 | frozen six-accepted/four-negative corpus, seven actual records/journals |
| A13-06 | campaign.json and per-trial expectation/receiver receipts/digests |
| A13-07 | unit adversarial cases + full-acceptance refusal on actual STOPPED trial |
| A13-08 | browser-qa.json, acceptance-desktop.png, portable browser acceptance audit |
| A13-09 | lifecycle/resume regressions, legacy-preservation, SOT gate and cleanup |

Initial attempt exposed a harness defect: QGC has no internal-survey polygon, so an empty generated FeatureCollection was correctly refused by intake after its completed flight. No QGC receipt/acceptance was published. Fixed to use the validated compiled planned navigation LineString, added a targeted intake test, then reran all seven trials on a new frozen source. Initial failed attempt and actual records remain preserved in attempt01/runtime; excluded from canonical counts. This fixes engineering product generation, not QGC semantic/editor or achieved-coverage assertions.

SOT adds only INTENT.ACCEPT13; 70 facts, digest ae68e11233d97368. Canonical BOM preserved; original external locator still NOT_CHECKED. SDK/HeraHub/native/HIL, physical camera/quality/field datum/power-loss, signed/remote/client acceptance and human DJI/RAGAS A/B remain NOT_CHECKED. No dependency install or project/tmp copy. Kernel scratch removed: /private/tmp/codex-tmp-aeris-accept13-20261013. Unit/browser synthetic roots and the one generated finalize_acceptance.cpython-314.pyc cache removed;  real flight records, small declared products, receiver bytes and decision audit retained for inspection. Fixed-tag SITL restored normal/disarmed/disconnected, Docker image prune only, no volume/container pruning. Next roadmap increment is operational geographic/datum/quality review contracts and deployment preparation under explicit target configurations.
