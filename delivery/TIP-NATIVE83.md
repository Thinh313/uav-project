# NATIVE83 · Android workspace and owned SITL

User authorization 2026-10-17: implement Android export/import, readonly native SITL, then full simulated mission. Existing development-signing authorization applies to isolated development APK; no production signing/candidate promotion. Same agent sequential specification/build/verify, not independent QA.

## Requirements / gates
- R83-01 preserve all previous protected SHA and ENDURE; isolated native/native83 and evidence/native83, no source/candidate/SOT edits. Floor20GiB; runtime admission32GiB, stop21GiB; bounded evidence/owned process cleanup.
- R83-02 Android SAF export whole immutable revision chain with head/digest manifest, provider readback; cancel/failure never success. Import bounded archive, reject traversal/duplicates/tamper/pending/invalid capsule; stage then explicit activate new workspace. Retain old workspace; no deletion, no authority restoration. New workspace requires current-head verified export.
- R83-03 actual Android SAF export/import and restart; independently compare exported chain/body SHA and semantic replay. Preserve prior failures.
- R83-04 separate loopback host bridge via scoped adb reverse, fixed owned simulator identity/binary/firmware/sysid42/compid1/session/boot. Native WebView offline, Java network destination fixed, bearer bound to process not persisted. Readonly connect/discovery/typed preflight first; no automatic commands/reconnect.
- R83-05 same Android cockpit KML planning -> explicit Home/datum confirmation -> fresh preflight -> upload/independent readback -> explicit development-SITL grant/arm -> observed post-arm Home/readback and explicit confirmation -> AUTO -> observed waypoints/land/disarm -> durable review. ACK never completion; zero real images. speedup1 internal quad not Hera calibrated physics.
- R83-06 loss/background/boot/process restart revoke volatile grants and invalidate command path; no imported journal authority/automatic mission resume. Mock adversarial tests before live; actual closure/restart evidence.
- R83-07 regression, cold raw replay and fingerprints/completion with coverage and NOT_CHECKED explicit.

## Architecture decisions
Reuse copied reviewed82 assets and pure Java DraftStore, import frozen qualified43 and63 modules read-only from host adapter. New separate package native83. SAF is native Activity results, not injected test JS. New narrow API on127.0.0.1 only; no hardware IP/configurable transport. Android INTERNET permission is solely for fixed127.0.0.1 bridge. ADB reverse maps to owned host; token passed explicitly on Activity launch, not saved; restart requires explicit reconnection. Controller abort stops owned simulator rather than issuing physical flight commands. Source clock, altitude datum and observed mission identity remain explicit.

Build/Verify may refine implementation within these gates; failures preserved and scope remains PARTIAL until actual Android and actual SITL gates pass. UI stays blur glass; added workspace/SITL panels explicitly labeled.
