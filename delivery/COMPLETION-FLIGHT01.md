# Completion / VERIFY · FLIGHT01 v0.4

STATUS: DONE for the scoped local simulator increment. NOT READY for physical aircraft, HeraHub APK or commercial release. Reviewer: Codex single-agent Contractor/Builder/Verify phases; no independent review claim.

## Outcome

RtR independent GCS architecture is now explicit in canonical SOT/ADR008/requirements/roadmap. No RAGAS application source reuse or source-access prerequisite. RAGAS is the black-box A/B comparator. Full control/mission/payload/media ambition preserved; survey remains first workflow. AI-native development is supported by pure validated contracts, simulator scenarios, machine-readable traces and deterministic evaluations; no deployed LLM/autonomous flight authority claimed.

Implemented a Node loopback TCP MAVLink development adapter, generated23-message official XML dialect, simulator-only survey compiler, upload/readback transactions, fresh observed command outcomes, preflight including EKF and ArduPilot pre-arm-ready, live SITL UI/local journal export and A/B configuration packet. Mission completion requires final reached + fresh disarmed/on-ground telemetry, even when ArduPilot resets MISSION_CURRENT to0. Ambiguous timeout locks commands; reconnect clears readiness. Existing local survey/rehearsal cores remain available.

## Requirement / acceptance coverage

Scoped acceptance:10/10 AC implemented and checked (100% within TIP-FLIGHT01, not whole product). REQ109 implemented; REQ110 scenario and honest comparison records implemented, actual B run NOT_CHECKED; REQ111 development seam implemented, runtime AI deferred. REQ104 partial product coverage: actual flat-world SITL slice passed, wider vehicle/terrain/payload matrix pending. No global readiness percentage inferred.

| AC | Result | Evidence |
|---|---|---|
|01 owner intent/SOT | PASS | truth-review.json, generated20intent/proposal/unknown facts +34Hera facts; baseline/check/bites/gate receipts |
|02 independent architecture/A/B | PASS | ADR008, roadmap, AB-EVALUATION, ab01-run.json; B NOT_CHECKED |
|03 official protocol/framing | PASS | public-inputs.json, runtime-integrity.txt, generated definitions, unit corruption/fragment/signing tests |
|04 compiler/datum/readback | PASS | compiler tests, exact manifest, actual16-item compiled mission and normalized download |
|05 actual simulator/telemetry | PASS | sitl-qa.json/journal, observedArduCopter4.7.1, session identity and freshness checks |
|06 transactions | PASS | actualACK/readback plus negative prematureACK/duplicates/rejection/mismatch/concurrency/timeout tests |
|07 command outcomes | PASS | GUIDED/arm/AUTO accepted + postACK observed telemetry; negative rejected/timeout/preACK cases |
|08 connected UI/journal | PASS | browser-qa.json, journal export, layout-qa/screenshots; legacy rehearsal separate |
|09 execution/camera | PASS | complete survey/RTL/landing/disarm in actualSITL; DataFlash CAM simulator trigger records; unit negatives |
|10 A/B reproducibility | PASS | hashes/build/params/world/scenario packet and explicit B NOT_CHECKED; no comparison result invented |

Technical health:69unit/API tests passed, syntax checks passed;16liveSITL browser workflow checks,19survey regression checks,6layout/SOT-view checks passed. Direct SITL harness9checks passed. All17evidence-pipeline stages passed including6SOT injected-fault bites. Zero browser runtime errors or external UI asset requests. Screenshots reviewed at1280×800,1280×720,1440×900 and390×844; scroll panes fit viewport with controls≥44px. No new app dependencies/whole-project copies/build directories.

## Findings repaired during Verify

Cold boot may report GPS and pre-arm-ready before GUIDED has an absolute EKF position; add EKF_STATUS_REPORT gating, preserve actual ArduPilot checks, never force-arm. Original browser failure receipts retained. Host-defense unit originally used a fetch Host override that the client ignored; rawHTTP verifies real Host rejection. Non-ASCII token now rejected safely. ArduPilot resets mission index after landing; completion observes final reached + disarmed + ON_GROUND rather than index. The prior incorrect harness-condition receipt is preserved. Camera readback normalizes only documented non-navigation/home frames; finite navigation/trigger values remain checked.

## Boundaries and remaining work

No physical flight/HIL, native Android/HeraHub SDK/input/video/lifecycle integration, map tiles/DEM/geoid/offline package, real camera images/calibration, QGC ComplexItem interoperability, signedAPK or operational release. No RAGAS A/B operator run or comparative DJI score. Simulation5×/Dockerx86 onMacARM is not a HeraHub performance benchmark. MAVLink signing verification and broader link/reboot/failsafe campaigns remain future increments. Next: geographic/terrain/offline and pinned interchange correctness, plus observed HeraHub SDK/config matrix; then native integration/HIL.

## Disk hygiene / preview

Raw task-owned simulator state/logs were archived with hash then removed; compact retained DataFlash evidence and extraction metadata are listed in runtime-cleanup.json/camera-log.json. Kernel scratch `/private/tmp/codex-tmp-aeris-flight01-20261012` removed in finally. Docker dangling-image prune performed; no volumes/other containers pruned. Fixed `aeris-sitl` container and loopback Node server intentionally remain available for project preview. No project copies, dependency venv or task-specific Next build outputs created.
