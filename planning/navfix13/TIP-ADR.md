# NAVFIX13: GPS/Home/clock/EKF preflight diagnosis and isolated repair

Authorized2026-10-31. Contractor TIP/ADR. Continue private AERIS development only; public research handoff, Git tags, master/private supplement and receiver s02 remain immutable.

## Outcome and evidence
Determine why preflight rejects a real Android–ArduPilot SITL session; repair the responsible path only after a falsifiable cause is established. Retain cold failure evidence as a control. New tests do not certify beta.

Entry result: GPSfix6/satellites10, static coordinates near Home10.854/106.807/10m; actual EKF flags167(0xA7), no absolute horizontal bit16. EKF origin/tilt/yaw messages exist. Wrong or absent GPS/Home is not established. APboot is a simulated clock; owner startup and host observation clocks must not be conflated. delAngBiasLearned/gpsDataToFuse/source selection remain unobserved hypotheses. No fabricated convergence from flags or origin alone.

## Isolation and invariant contract
Write new source/tests only planning/navfix13, new raw/reports only evidence/navfix13; root may add a final delivery report. Existing planning/vidlife12, evidence/vidlife12, receiver-workspace, old candidates, ENDURE/SOT/trust and public repos remain unchanged. Root owns admission, candidate freeze and actual actors; Builder only builds/replays/mocks in the new scope. No APK/signing/build/download; reuse byte-verified APK8bc0a7... and AP77344f... only if their real gates pass. No source substitution or runtime monkeypatch.

Keep clock/input250ms, lease200ms, HostHealth100ms, lifecycle1000ms, flight1500ms, hard heartbeat3000ms, speedup1/cap500ms, fsync-before-sensor and every frame. Preserve the existing finite closure/native quotas, storage floor10GiB and peak/reserve admission, power/lid guard, artifact8MiB and metadata64MiB. Do not reset quota, delete evidence, reclaim historical artifact accounting or restore authority. Battery use follows actual current guard, no fakeAC.

## Investigation and smallest repair
1. Verify original s02 raw CRC/hash chain and exact frozen dialect. Join GPS/Home/EKF/STATUSTEXT within original stream clocks; derive APclock progression and model steps from their own evidence, label cross-clock bounds. Reject wrong target, stale/rollback/corrupt evidence.
2. Separate confirmed sensor facts from estimator internal unknowns. Check exact cached ArduPilot source revision read-only. Do not treat a longer wait, force-origin/set-home/parameter waiver or ACK as a repair.
3. Add a bounded deterministic navigation diagnostic contract for the adapter, with mock/replay cases for GPS/Home/date/boot/freshness and estimator readiness. New diagnostics may report pending/unknown/refused; they must never grant preflight or dispatch commands. A true causal repair requires additional evidence.
4. Before any runtime integration, independently verify the changed source closure, unchanged guards and exact allocation plan. Existing union8220672/8388608B leaves167936B; priorR02 plan8466432B was correctly refused. No cap bypass. If the new exact candidate does not fit, stop before writes/actors and retain the plan.
5. Only after mocks and exact full admission, run at most one new180s Android–SITL diagnostic slot. Every actual native/API/physics frame and failure log retained; no retry, no10minute or beta declaration until short acceptance. Any second repair/run requires a new measured cause and bounded gate.

## Acceptance / stop
Cold replay must identify facts and unknowns without modifying originals. Negative cases must refuse readiness; no automatic authority. All new code/imports are pinned before runtime. A mock PASS is only mock acceptance. Functional PASS requires fresh APposition/EKF/Home through original preflight in Android and complete cold frame/clock proof. Missing internal estimator facts remain UNKNOWN.

If candidate cap, source pin, power, disk, native lifetime, stale clock or any other guard refuses, preserve all bytes and report the specific blocker. Do not claim the requested preflight repair or beta stable achieved. No external publication, push or new handoff update in this task.

## Contractor refinement: measured disarmed probe, not a claimed repair

Cold raw cannot identify which internal GPS-use predicate remains false. Builder may prepare a new source-only isolated runtime copying only the selected117Python files and9JS/transitive overlay files (about2MiB), with independent writable inodes and a recorded before/after map. Namespace is NAVFIX13; all six old artifact pools stay included before its new pool, with8MiB unchanged. Every new source/metadata byte is counted. No private/public handoff changes.

Probe scenario performs real Android survey/compile/save/connect and observes read-only initialization up to60hostseconds within the original180s profile. This is an explicit investigative cold-start window already prototyped by historicalR02, not evidence that waiting cures the estimator. Every existing safety/freshness and authority predicate stays unchanged. On fresh readiness it may invoke original preflight once; no arm/grant/upload/manual/video. It records the actual transition or lack of it. Candidate/code pins and actualparametercohorts remain enforced; no setting Home/origin/estimator parameter to fabricate navigation.

The diagnostic owner must physically revoke/dispose all owned actors and preserve raw/native state. A planned diagnostic end is neither a completed flight nor an accepted journal; do not fabricate seal/footer or use failure disposal as evidence of normal airborne closure. Newowner/scenario must be included in the readonly source graph. Boundedmock requires exact guards and refusal of absent/stale/foreign/badEKF, disarmed-only behavior, firstfailure, capture and cleanup errors. Root freezes only after independent tests and pure exact allocation preview. No sidecar/source rewrites after HOLD. No secondlive slot in this refinement.

## User-approved artifact budget amendment, revision2

User explicitly replied: “Cho phép artifact9MiB, giữ các guard còn lại”. This supersedes only the NAVFIX13artifact8MiB restriction above. Keep all six historical pools and the new pool charged. New candidate/preview/guardian artifact limit is9MiB; originals retain8MiB and every old receipt remains intact.

Source accounting must also reserve the extra1MiB in the new campaign/case artifact category and increase their computed taskHardPeak/requiredFreeBytes by exactly1MiB. This is conservative peak accounting, not lower disk/closure/native guards. Floor10GiB, reserve256MiB and all other budget categories stay unchanged. Never replace journal segment8MiB or unrelated literal8values. Builder regenerates new source pins and emits HOLD02; Root independently verifies exactdelta, mock, allocation and full admission before at most one new180s disarmed Android–SITL probe. No APK/build/signing.

## Contractor targeted repair after measured S01, revision3

ActualS01 booted Android but ended41.08hostseconds before APK/companion/AP. The single rootrequest had a complete originalfailed receipt: exit1, empty stdout, stderr `adb: unable to connect for root: closed\n`. UID-before2000, UID-after not observed. All36casefiles and originalfailed receipts are preserved; ownedPIDs exited, guardian audits closed without secondaryerrors. This is a bootstrap blocker, not GPS/EKF evidence.

Within the user's continuing development authorization, allow one targeted S02 only, after source/mock/fresh candidate/admission. This is not a retry of S01 and no slot/lock or receipt is reset. Total actual slots for this investigation becomes two (s01 failed, s02 targeted), both180sdisarmed; no third automaticrun. Artifact9MiB remains exact; source/candidate6bfe and S01 are immutable.

Builder may repair only the active new Android bootstrap uncertainty path. A rootrequest is never sent twice. Keep the originalfailed command receipt and its UNKNOWN dispatch outcome. Only the exact durable/root/exit1/closed-output/capture-complete/no-secondary pattern may proceed to read-only postcondition checks within the same30sdeadline. Require actualUID0 and identical observed kernelbootUUID before/after, plus originalreceipt integrity and exactemulator5582ownedpreobserver context. No ACK inference, genericstderr whitelist, deadline extension or physicaldevice access. Every othererror, incompletecapture, corruption, wrongboot, notes, deadline or UID2000 remains failure. Versioned preparation evidence must distinguish originalrootrequestfailure from observed resultingUID0; no receipt rewrite or authorityrecovery.

Keep other safety/timing/physics/quotas exact; source graph and writer contracts must be regenerated and checked before newHOLD03. Root owns secondfreeze, liveadmission and autonomous physicaldisposal. If the secondprobe fails, preserve it and report remainingcause, without unmeasuredthirdattempts.
