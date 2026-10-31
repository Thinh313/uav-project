# One FIELD01 delivery set

The receiver checks one accepted simulator flight raw handoff together with its
synthetic JPEG handoffs, then commits one durable overall receipt. This supplies
a complete data folder and one receiver command. It does not establish physical
images, physical flight, sensor exposure accuracy, camera identity or GNSS survey
quality. Hashes and context checks are transport integrity, not authentication.

The actual retained set `evidence/field01/delivery-set01` contains only:

* `index.json`
* `flight.tar`
* `capture-01.tar`
* `capture-02.tar`

Index SHA256:
`e34da4df45ecb7427d3a3567344e2bdeec060f0024a17e38d765d3869c9c2482`.
Total indexed bytes: 4589307. All three TARs are copied without byte changes.
This selected source uses the GUI-exported accepted SITL run
`sb5d91f31ba82446984dc`, RGB synthetic capture `capture-7b93d71a-1dac-4d8b-a6e1-5bd3ee55fbd6`
and thermal synthetic capture `capture-ee88b0dc-8b99-4dd9-ad2d-f4a29401d970`.

With the existing AERIS receiver bundle, Node and Python available, receive the
folder in one command. Save every member with its exact filename in one folder.
Use a stable state directory for that receiver and keep it across future runs:

```sh
python3 -B pilot/field01/evidence/receive-set.py evidence/field01/delivery-set01 \
  --index-sha256 e34da4df45ecb7427d3a3567344e2bdeec060f0024a17e38d765d3869c9c2482 \
  --state evidence/field01/destination-receiver-state \
  --receiver field01-evaluator --sender aeris-field01-synthetic
```

For a read-only check, replace `--state ...` with `--check-only`. Read-only mode
does not create state, acquire a receiver lock or write any replay ledger. An
index hash supplied through an untrusted channel is not proof of sender identity.

The first successful stateful receive returns `ACCEPTED_DURABLE_DELIVERY` after
journal and directory fsync. Repeating the set or renaming its delivery ID is
refused. Replay keys cover delivery ID, index hash, flight run, capture identity,
transfer ID and package ID. One flight run is receivable once per overall ledger;
incremental resends of that flight are outside this version. Do not discard or
replace receiver state to force replay. A present lock requires investigation;
the receiver never deletes stale locks automatically.

The standalone retained acceptance is in
`evidence/field01/evidence-delivery-set01-receipt.json`, with durable replay state
at `evidence/field01/delivery-set01-receiver`. That demo state has already accepted
this set and correctly refuses another receive.

The aggregate receiver performs these checks before writing any receiver ledger:

1. Exact flat file allowlist, expected index SHA, fixed relative filenames,
   regular files without symlinks, declared sizes and exact archive SHA256.
2. Every capture through the existing independent Python `validate_package`
   function in read-only form, with exact receiver/sender, JPEG structure,
   sidecar/file/manifest hashes, context, datum and uncertainty restrictions.
3. Flight through a separately invoked Node `receive-flight.mjs` CLI, including
   raw duplex chain/CRC, canonical command/readback/execution replay, immutable
   source manifest and accepted simulator execution. No archive is extracted.
4. Every capture's context and manifest link must match the accepted flight's
   run, boot, model SHA and plan SHA from document/session/review. Duplicate
   capture, transfer or package identities are refused within a set.
5. Each nearest host receipt reference must match the exact accepted raw position
   row's coordinates, MSL and relative-Home altitude, run, boot, model and plan,
   within 1500 ms of the declared host reference time. The receipt records raw
   row/hash and host reference delta. This is not physical sensor synchronization.

For the actual pair, matched raw rows are 4234 and 5670, with host reference
deltas about 30.46 ms and 33.58 ms. These numbers describe matching retained host
reference records. Physical exposure accuracy and sensor clock uncertainty remain
`UNKNOWN`, `qualifiedForSurvey` stays false, `actualImages` stays zero, and no
authority is restored. Mock-flight images paired with this SITL flight are refused.

The async exporter API is:

```js
import { exportDeliverySet } from './evidence/delivery-set.mjs';
const result = await exportDeliverySet({
  out: '/absolute/aeris/evidence/field01/new-delivery-folder',
  deliveryId: 'delivery-unique-id', // optional, random UUID by default
  flight: { archive: '/absolute/flight.tar', manifestSha256, expectedRun },
  captureArchives: ['/absolute/rgb.tar', '/absolute/thermal.tar'],
  receiverId: 'field01-evaluator', senderId: 'aeris-field01-synthetic'
});
// {out,indexPath,indexSha256,totalBytes,receipt,actualImages:0,authorityRestorable:false}
```

CLI equivalent: `node pilot/field01/evidence/delivery-set.mjs '<JSON options>'`.
The output directory must be new, under the owned FIELD01 evidence root with an
existing parent. The exporter reads bounded selected archives asynchronously,
creates exclusive immutable copies, fsyncs files and directories, and performs a
read-only aggregate receiver check before returning success. It never overwrites
an existing directory or automatically removes invalid/partial evidence.

Bounds are 32 MiB per flight TAR, 4 MiB per capture TAR, 16 captures, 128 KiB index
and 64 MiB total indexed bytes. Overall receiver state is bounded to 1024 receipts
and 4 MiB. Node flight verification has a 45 second deadline; the exporter check
has a 60 second subprocess deadline. Parent directories must be operator controlled;
static symlinks are refused but this is not concurrent malicious ancestor isolation.

Run Builder checks with
`node planning/field01/evidence-delivery-set-tests.mjs`. This uses retained actual
accepted simulator evidence and synthetic media, with no new SITL/media run. The
exporter and aggregate receiver have the same author; separate runtime/validator
paths do not constitute independent human review or producer authentication.
