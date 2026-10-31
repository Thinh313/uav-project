# Closed flight evidence handoff

This is an additive FIELD01 host utility. It does not edit the frozen flight module or its 50-file source manifest, launch SITL, restore authority or contact hardware.

```js
import {exportFlight} from './handoff.mjs';
const result = await exportFlight({
  run: 'm711f0b2f20184c0bbb21',
  out: '/absolute/repo/evidence/field01/new-flight-handoff.tar'
});
```

The output must be a new, normalized absolute `.tar` filename under this repository's `evidence/field01`. Its parent must already exist. Runs are restricted to the owned `evidence/field01/flight/runs` directory. Symlinks, path traversal, absent or incomplete reviews, source file hash changes, altered documents, invalid raw chains or a mismatch between actual raw execution and the review are refused. Existing output is never overwritten. The exporter fsyncs the archive and parent directory and creates the archive with mode 0444. The 32 MiB limit applies to the full uncompressed TAR.

The archive contains byte-exact `document92.json`, `plan.json`, `review.json`, `raw.jsonl`, `request.json` and `session.json`; it also contains per-run `source-pins.json`, `launch.json`, `closure.json` and `admission.json` when present. SITL archives require launch, closure and admission. The first failed real run predates per-run source-pin snapshots, so its manifest explicitly records that the snapshot is absent. The exporter validates every original file hash declared by the review before export. AP state and other bulky source files are deliberately omitted, with the omitted paths listed in the manifest. A receiver cannot verify omitted bytes from this archive.

`canonical-replay.json` is newly derived from actual duplex raw bytes, not copied from an old verification result. The reused canonical decoder checks CRCs, frame/command/target allowlists, exact mission items, pre/post-arm readbacks, explicit Home review and grant, AUTO/navigation/terminal/ground/disarm when accepted, raw chain, exact document/model/plan binding and reference-position metadata. Accepted execution must match the closed review. A failed or aborted simulator review stays unaccepted after transfer.

`manifest.json` binds every member's name, byte size and SHA-256. The exporter returns `path`, `run`, `bytes`, `archiveSha256`, `manifestSha256`, `receiverId`, `accepted` and `authorityRestorable:false`. Keep both digests outside the archive for the receiver.

Run the separate receiver process with one JSON argument:

```sh
node pilot/field01/flight/receive-flight.mjs '{"archive":"/absolute/new-flight-handoff.tar","manifestSha256":"...","archiveSha256":"...","receiverId":"FIELD01_FLIGHT_RECEIVER_V1","expectedRun":"m711f0b2f20184c0bbb21"}'
```

The receiver parses TAR independently of the exporter and never extracts files. It rejects symlinks, non-regular members, unsafe or duplicate names, unexpected trailing data, incorrect TAR checksums/padding, oversized archives and any digest/member-set/receiver/run mismatch. It then reruns the canonical raw decoder and compares the result against the handoff manifest and review. This is a separate-process receiver using the same canonical wire decoder, not an independently authored second wire decoder or human review.

A receipt states `PASS_TRANSPORT_AND_RAW_REPLAY`, with `authenticityProven:false`, `physicalFlightProven:false` and `authorityRestorable:false`. The fixed receiver ID is a protocol target check. SHA-256 demonstrates byte integrity against the externally supplied hashes; it does not authenticate the sender or authorize commands.

Tests: `node planning/field01/flight-handoff-test.mjs NEW_SUFFIX`. Each suffix creates a new bounded evidence directory and retains failed/corrupted archive fixtures. No simulator is started. The sparse over-limit fixture is removed after its rejection is recorded.
