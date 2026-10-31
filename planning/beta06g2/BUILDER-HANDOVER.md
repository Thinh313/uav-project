# BETA06 generation02 Builder handover

This is source/mock preparation only. Actual original failure cause remains unknown. Generation01 request s220913d46e964ec6af94 remains a counted failed preparation, never a successful nominal or deliberate fault. Its265-source manifest, evidence and all older source/candidate/ENDURE/native files stay unchanged.

New source lives only under pilot/beta06g2. New output and AP paths are evidence/beta06/generation02, with a common exact data fork workspace01. Stage is reused read-only from pilot/beta06/.stage; no large copy/build/install/download occurred.

Actual launch is only through the persistent Root controller's direct Node child. The child command is:

```sh
node pilot/beta06g2/app.mjs evidence/beta06/generation02/host-app02 --allow-sitl '--workspace=/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation02/workspace01'
```

It requires BETA06_ROOT_CONTROLLER_PID equal to the actual Node parent PID and BETA06_PARENT_HOST_REMAINING_MS as an integer1..1800000. A manual invocation without these is rejected. The same parent owns the original30-minute window; the Node remaining-duration timer is a secondary earlier bound, not a new clock anchor. One explicit managed restart uses output host-app02-restart and the same workspace, inside that unchanged window. Watch250ms closes on parent loss.

The final explicit supported AP profile is beta06-native-arm64-4.7.1: existing archived static aarch64 binary SHA1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41 in cached image e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84. The compiled observer is explicitly disabled, no entry shim/clockprobe/preload runs. Archived Aircraft/JSON source minus observer hooks matches base dbe79216 (terminal newline aside), retaining stock100ms debt. This is a different qualified engineering binary, not an assertion of equal build bytes or a proven performance improvement. Before control, actual binary hash/image/process/config/read-only mount/CPU1/memory256MiB/no-extra-privileges are checked. The old x86 and pacer-v2 binaries are refused. Canonical CRC/raw/mission/closure verification is unchanged, with an additional exact native-profile precheck.

The new adapter preserves command, parameter, physics, speedup1, AP540s, Home, lease and strict canonical receiver semantics. Its own4-request counter refuses request5 before any allocation. The exclusive manifest must bind11 original requests plus1 prior Beta request. Original caps are not modified.

New behavior is limited to1000ms whole lifecycle request/body bounds, no late commit, redacted diagnostic sampling, new namespace wrappers and declared capacity adjustments: own overlap journal6144 rows/8MiB and media cumulative processed body1GiB. Single-body/frame/queue/decoded/report/control/retained-media limits and the aggregate256MiB/early200MiB storage budget remain unchanged. Clock5 probes/20ms/60000ms, heartbeat750ms and hostTTL3000ms remain unchanged.

GET /api/media-diagnostics exposes redacted media quota/session/clock counters. GET /api/transport-diagnostics exposes bounded metadata and original-record call durations, which include hashing/write/fsync and do not isolate pure filesystem or guest CPU. Original record calls/returns/errors remain intact. Close-event diagnostics read the already-invalidated preflight reason only after RX_CONTEXT_OR_CLOCK. Compact browser lifecycle, media readiness and Node loop observations are retained in the existing1Hz observation journal; full bounded latest diagnostics are readable and saved on closure. These are observations, not authority or causal proof.

Source/VM tests:

- node planning/beta06g2/builder-host-tests.mjs:7 groups PASS, latest builder-host-mock06.json. Normalized methods, new4/5 admission, unchanged runtime/control/receiver semantics, processed-byte fake exact boundary, original-record observation invariance and diagnostic bounds.
- node planning/beta06g2/builder-http-tests.mjs:10 groups PASS, builder-http-handler05.json. Real request handlers in-process, no listening socket/AP; exact bootstrap route, read-only diagnostics, strict media future-clock rejection and clean evidence closure.
- Native qualification:6 groups PASS in builder-native-profile02.json; exact profile/import normalization and old-SHA/pacer-v2/wrong-ABI negatives. Actual JS live-identity predicate1 positive+15 negatives PASS in builder-live-identity02.json; actual Python runtime identity AST predicate1 positive+6 negatives PASS in builder-runtime-identity01.json. No Docker/AP was executed.
- Pure launcher cases:4 groups PASS in builder-launcher01.json; parent/remaining/env negatives, no process or socket actuation.
- Frozen publisher diagnostic session normalization:4 groups PASS in builder-clock-diagnostics01.json. Only the authenticated exact six-key session with matching routing viewerId drops that one routing field before the frozen validator; input-session object SHA/shape/target proof are journaled. Exact five-key sessions are unchanged; wrong viewer/extra fields/role are rejected. This fixes diagnostic serialization, not the historical latency cause.
- Bootstrap/helper VM and independent QA results are separate artifacts and must be bound to their final exact source hashes before pins are emitted.

Before any AP allocation Root must pass75seconds of uninterrupted current foreground client/session and current source/viewer configuration, including successful actual publisher/viewer clock renewal under unchanged bounds. A diagnostic field alone does not certify this gate. Actual pixels, N1/N2, airborne synthetic capture/gimbal, video metrics, cut/reboot, persistence and SAF remain pending. URI dispatch acknowledgment never certifies native/provider completion. No physical Hera, real camera or production acceptance is claimed.

No runtime, AP, emulator, browser, ADB, signing or installation was performed by this Builder.
