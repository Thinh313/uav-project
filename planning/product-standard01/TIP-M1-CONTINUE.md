# M1 Integrated Operational Alpha: reprise after prearm bootstrap failure

2026-10-20. User authorizes sequential implementation of the product baseline. Personal Vibecode Kit6.3: Root Contractor, existing Builder and independent QA. Source/candidate/canonicalSOT/ENDURE and all old receipts remain frozen. No realHera/SDK/production publication. RAGAS parity is not an acceptance target.

## Outcome and current diagnosis

Close existing INTEGRATION03 I01–I10 using the exact developmentAPK04/source07 if no app defect requires a separately reviewed repair. P1 OPERATOR01 scope remains accepted; no automatic transfer to this source/configuration. Do not call a mock fix DONE for M1.

Most recent run sb3f198d1ac1f6fb249ef accepted a bootstrap TCP connection then returned EOF,0bootstrap/observer records, no arm. Controller then stopped AP; Android ECONNREFUSED downstream. Guest console was SERIAL0 waiting. Cause UNKNOWN. Plausible published-port/guest-listener readiness race; spontaneous AP exit/OOM also not excluded because pre-stop state was not captured. Preserve that uncertainty.

## First bounded repair

New QA-rig files only under planning/integration03/runtime and new evidence/integration03-bootstrap04. Never modify runtime.py, old run directories, source-ready07, app/host/observer source, or historical fingerprints. A single runtime04.py may be an explicit small derivative of runtime.py with source lineage/diff; no project copy. Reuse peers, APbinary/params, APK04, observer and all authority/WAL/frame/clock settings unchanged.

Implement fail-closed readiness before the bootstrap's single TCP connect: verify exact ownedcontainerID/running state and guest SERIAL0 TCP LISTEN on5760 using read-only Docker inspect + /proc/net/tcp{,6}; constrain identity, types, parsing/size/elapsed bounds. Log readiness observations with host monotonic timestamps in bounded sidecar. Port published on host alone is insufficient. Initial passive readiness polling≤30s is allowed; no mutation/connection retry. After one connect, EOF/refusal/timeout fails the window, never reconnects. Bootstrap remains read-only/0TX.

Before owned shutdown, capture inspect Running/Status/ExitCode/OOMKilled/Error/start/finish times plus guest/probe status and boundedlogs, distinguishing controller-requested stop from spontaneous exit. Readiness/probe failure must close only ownedruntime and preserve original error even if inspect/log/stop throws. No readiness diagnostics on every data frame. Native connects only after actual AP stream readiness; user intents/flight commands remain in Android.

Keep AP2CPU/512MiB/speedup1; emulator referenceAPI33ARM64/4CPU2048MiB/GPUhost/1280×800. No APK build needed for rig-only repair. No token/authority/1500ms delivery/3000ms cohort/fsync/frame-retention/cap500ms/clock-policy changes. Do not modify source to match mocks.

## Verification and budgets

Builder runs bounded offline mocks with injected probes/socket factories; no actual Docker/AP/Android/network launch. QA independently tests unpublished ordering/identity/state/listener/clock/failure vectors, singleconnect/noTX/noEOF-retry, cleanup error preservation, and source-lineage diff. Demonstrating a synthetic proxy race is not a reproduction/proof of the old actual cause. Source≤256KiB, mock scratch≤10MiB removed, evidence≤16MiB, no dependencies/install.

Root may launch real runtime only after independent rig QA, unchangedAPK/source/observer pins, explicit new resource/window admission and sufficient measured headroom. Initial referenceentry≥29GiB stable for30s; postboot≥26.25GiB; runtime guard21GiB; userfloor20GiB. Remaining runtimewrites≤768MiB, transientallowance5GiB, shutdown/externalmargin512MiB. Currentfree~24GiB permits small source/mock work only. No lower-reference-profile trick or relaxedgate to run.

This user resume allows an L2 budget reassessment: at most3 new windows after gate (nominal, corridor+Bpartition, pilotloss), each≤900s. Four earlier launches remain failed/unaccepted and are not combined. The first new failure stops dependent windows for cause review; no automatic campaign retry or run-directory reuse. Budget does not override resource/authority. Root records freshIDs/admission when actually eligible; this TIP is not itself a launch receipt.

## Remaining product gates unchanged

Three successive actual >20k-frame preflight cohorts including declared load; typed/freshness controls; KML/QGC subset and unsupportedrefusal; nominalAndroid AUTO→ground/disarm→acceptedreview; B independent mTLS consent and same-sessioncapture,3cameras/device1+2; Bpartition/pendingUNKNOWN/revoke/rejoin0rights/Acontinuity; pilotforegroundloss/APfailsafe; readonlysame-run/plan/pose3D with qualifying30sRAF and opt-in syntheticaudio; exactselectedrun SAF+independentreceiver; process/coldboot/privatepreservation/noauthorityrestore; fullUI and allprotectedhashes/managedclosures.

No realmedia/calibratedHera/production/DJI-superiority claim. Hardware inputs remain a later gate. Completion/Verify reports actualaccepted scope, failures/notrun, cost/resources and READY/NOTREADY; M1 is NOTREADY until all mandatory gates pass. If resource gate remains unavailable, finish useful offline repair/QA, preserve runtime shutdown, and report that exact blocker without claiming M1done.

## L2 clarification: passive bootstrap read silence

Initial connect is exactly once with3s connection timeout; EOF/refusal/connect-timeout is terminal. Preserve old post-connect0.5s recv timeout as passive idle polling under existing≤900s window, no reconnect/TX. Do not introduce3s idle-read failure. An idle socket read is not retrying a mutation/connection. Native freshness and common flight lifecycle remain separate and unchanged.
