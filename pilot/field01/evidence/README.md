# FIELD01 evidence boundary

This module stores synthetic JPEG bytes and metadata supplied by the host gateway.
It does not invent coordinates, inspect physical exposure time, sign camera output,
restore authority, or certify survey quality. Every receipt has `actualImages: 0`
and `authenticity: NOT_ATTESTED`. Stored hashes establish byte/context integrity.

```js
import { Store01 } from './evidence/store01.mjs';
const store = await Store01({ root: '/operator-owned/field01/workspace' });
const row = await store.append('WORKSPACE_SAVED', { document }, { expectedHead });
const receipt = await store.commit(captureId, {
  originalBytes, sidecar, link,
  guard: () => { /* synchronously throw if authority/frame was revoked */ }
});
const { originalBytes: untouched, sidecar: saved } = await store.read(captureId);
const { rows, snapshot } = await store.review();
const { bytes, manifest, receipt: exportReceipt } = await store.handoff(captureId, {
  transferId, senderId: 'aeris-field01-synthetic', receiverId: 'field01-evaluator'
});
await store.close();
```

`records()` and `snapshot()` are synchronous copied metadata views after awaited
initialization. They grant no authority. `review()` returns an object with `rows`,
not a plain array. Its rows distinguish `PENDING`, `COMMITTED`, and `QUARANTINE`.
All storage I/O, including file and directory fsync, uses `node:fs/promises`.
The JPEG marker gate reuses the pinned BIG02 pure function without editing it.
That gate is a bounded structure check, not a decoder or a safety certificate.

The journal is serialized, hash chained, and fsynced before each returned result.
Internal capture/handoff intents precede immutable file creation. File contents
and containing directories are fsynced before the result record is issued.
Capture originals are copied unchanged to exclusive files opened with mode 0400.
No pending data, capture, journal, archive, or stale lock is automatically deleted.
Limits can be tightened but cannot exceed 128 MiB, 16 captures, 16 handoffs, 2048
records, 4 MiB per original, and 128 KiB per bounded JSON value. Quota refusals
occur before intent when the transaction's conservative reservation cannot fit.

Use one writer per root. `writer.lock` uses exclusive creation; a present lock
opens the store for observation only. A crashed process leaves its lock retained.
`close()` releases only the lock inode and nonce owned by that instance. Investigate
a stale lock explicitly; this library has no stale-lock recovery/delete method.
Static symlinks are refused in ancestry, the root, and files. File opens use
`O_NOFOLLOW`. Operator control of parent directories remains required: Node lacks
an `openat` interface here, so this is not protection against a malicious account
renaming ancestors concurrently. File hardening does not authenticate producers.

Any uncertain write/sync poisons that writer. A failure after intent retains
`PENDING` data for review. No automatic retry of a capture or uncertain operation
occurs. A valid full result record can be observed after restart even when the
previous caller never received its receipt; that is storage evidence and grants
no flight/payload/session rights. Torn or corrupt journals remain observation-only.

The optional synchronous capture guard is called before intent and directly
before the final result record, after immutable files are synced. A guard failure
after intent retains pending files and poisons the transaction. Revocation during
an already issued final write/fsync cannot cancel that I/O: the gateway must check
authority again after `await commit`. The gateway records and returns ended
authority while retaining committed bytes in that case.

Sidecar schema version 1 has these exact top-level fields:

* `schemaVersion`, `kind: FIELD01_SYNTHETIC_CAPTURE`, `sourceKind: SYNTHETIC`,
  `actualImages: 0`, `captureId`, `frameId`, `context`, `position`, `timing`, `file`.
* `context` binds `gatewaySession`, `stationId`, `modelSha256`, `planSha256`,
  `flightRun`, `flightBoot`, `payloadId`, `sourceRun`, `sourceBoot`, `configId`, `feed`.
* `position` is null with a nonempty timing reason, or supplies latitude/longitude
  degrees, `altitudeMslM`, `relativeHomeM`, `datum: MSL`, `hostMonoMs`,
  `qualifiedForSurvey: false`, and `sensorTimeUncertaintyMs: null` (unknown).
  Method remains exactly the supplied `NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC`
  or `HOST_RECEIPT_BRACKET_REFERENCE_ONLY`; this store never upgrades one to the
  other. Optional `observationBefore`/`observationAfter` are retained bounded JSON.
  Neither MSL nor relative-Home is labeled WGS84 ellipsoid altitude.
* `timing` has source timestamp in microseconds, host bounds/reference in
  milliseconds, `method: BOUND_SOURCE_CLOCK_TO_HOST_RECEIPT`, and
  `physicalExposureTime: UNKNOWN`. These are host/source reference bounds,
  never bounds on physical sensor exposure. Optional `reason` explains no position.
* `file` names `original.jpg`, MIME `image/jpeg`, exact byte count and SHA256.

`link` binds schema version, capture ID, model/plan SHA256, flight run/boot,
payload ID, synthetic source kind and zero actual images to the sidecar context.

Handoff is an immutable deterministic TAR with precisely three regular members,
in order: `original.jpg`, `sidecar.json`, `manifest.json`. The manifest binds the
two content hashes/sizes, context/link, frame/capture, sender/receiver and transfer.
Export returns only after the archive and a handoff receipt have been synced.
The package ID and receipt hashes are not authentication or signing.

The separate Python stdlib receiver parses raw ustar headers without extraction,
enforces the three-member allowlist, bounds, regular files, checksum, padding,
hashes, JPEG structure, exact schema, synthetic provenance, context, sender and
receiver. Its own hash-chain receipt journal rejects transfer and capture replay
across process restarts. A receiver lock also has no automatic stale deletion.
Receipt fields preserve the reference method and explicitly report sensor
exposure accuracy and sensor clock uncertainty as `UNKNOWN`, survey qualification
false, and restored authority `NONE`.

```sh
python3 pilot/field01/evidence/receiver.py package.tar \
  --state evidence/field01/receiver-owned-run \
  --receiver field01-evaluator --sender aeris-field01-synthetic
node planning/field01/evidence-tests.mjs
node planning/field01/gateway-tests.mjs
```

Tests retain uniquely named evidence directories, including intentionally crashed
writer locks. Normal test stores call `close()` to release only their own locks.
No project copy, dependency install, build folder, camera, Android, CUA or SITL is
used by these tests. The evidence tests are Builder self-checks. Gateway tests are
delegated checks of another author's gateway, but use storage by this same Builder;
neither is an independent human review or physical field acceptance.
