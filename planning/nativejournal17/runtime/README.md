# Native17: source and mock handoff

Current scope: **code/mock only**. Do not launch Android, emulator, SITL, ADB, install, signing, candidate freeze or admission from this handoff. The latest user instruction defers all actual device/runtime work.

## What changed

N01 failed because its readiness check reached an unstarted ProductWriter. The preserved original entry reproduces that exact guard failure in the coupled mock. Revision r02 starts the unchanged host writer and static descriptor before device readiness; the companion still starts after verified cold migration.

N02 reached the install call but its command receipt failed to serialize: the allowlist and receipt used different authorization attributes. N02's installation outcome remains **UNCONFIRMED_COMMAND_RECEIPT_NOT_PERSISTED**. Captured SDK text does not replace a durable installation receipt. No retry or reinstall has run.

The canonical future install path now uses one durable authorization for both predispatch checks and the version9 command receipt. It refuses missing, foreign or consumed authorization before Popen, retains failed captures and never resends. A separate typed install17 reader checks the exact command/authorization/source/APK/receiver bindings. The generic STATUS version3 reader stays strict. Only these exact successful SDK outputs qualify: `Success\n` and `Performing Streamed Install\nSuccess\n`.

The future `root-owner-native17-adopt03.py` entry contains no install call. It may proceed only after fresh cold observations show the already-reviewed Native17 APK and a complete original private-files TAR matches retained N02 files **and directories** exactly. Old/foreign APK, changed data, an empty new registry directory, missing EOA or hidden TAR bytes must stop. The original N02 receiver and plan remain unchanged. The unknown old installation is never relabeled successful.

After that future prerequisite, the retained native-only workflow would explicitly APPLY, verify the complete registry/TAR, create and save a mission through the public UI, close UNUSED producer1, cold-check it, restart with a different PID/epoch/key, verify persistence without restored rights, close UNUSED producer2 and cold-check all originals. This is not flight, video, payload, physical-HID or beta acceptance.

## Run only these mock checks

From the AERIS repository root:

```sh
python3 -B planning/nativejournal17/runtime/test-runtime17.py
python3 -B planning/nativejournal17/runtime/test-writer-order02.py
python3 -B planning/nativejournal17/runtime/test-adoption03.py
python3 -B planning/nativejournal17/runtime/test-tar-shape03.py
```

These use disposable mock-budget fixtures, original-byte readers and no-child fake Popen pipe transports. No external Android/AP process starts. Temporary fixture directories are removed on completion. The directory/framing tests include a generic post-APPLY archive namespace positive; its placeholder registry content is structural test data, not valid lifecycle evidence.

Inspect the held source graph without writing or actors:

```sh
python3 -B planning/nativejournal17/runtime/prepare-source-gate03.py --node /usr/local/bin/node
```

`--write` is a Builder preparation command that updates two active source assets. Do not run it after HOLD unless a new source revision is explicitly being prepared.

## Preserved boundaries and deferred work

The original entries, HOLD01/HOLD02, N01/N02 raw evidence, all frozen candidates, old source, development APK/native source, ENDURE and public handoff remain preserved. Disk floor10GiB, reserve256MiB, artifact11MiB, metadata64MiB, native journal64MiB and export192MiB remain unchanged, as do HostHealth100ms, writer200ms, freshness250ms and input lease200ms. The new qualified n03 slot remains180 seconds; it grants no automatic launch permission.

Before any later actual run, Root must independently verify the final source and preserved evidence, obtain fresh resource admission and explicit runtime authorization, and review fresh installed-APK/private-byte observations. Actual adoption, APPLY, Android startup/restart, persistence and final physical actor closure have **not** been accepted by these mocks. No production signing, SDK, HeraHub or drone operation is included.
