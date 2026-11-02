# BETA-RC01 native archive boundary

This isolated code preserves Native17 and all previous source/candidates. No APK
change, quota increase, evidence deletion or rights restoration is implemented.
Root owns every actual Android/AP/maintenance process and independent acceptance.

## Live APIs

- `archive_rc01.verify_storage(backup_path, backup_sha, expected_head, *, source_candidate, archive_receivers, approved_sources, node, require_selected_closed=())`: strict complete TAR/index/receipts/manifest replay. `archive_receivers` is a list of exact `{path,bytes,sha256}` originals or already retained exact byte reports keyed by SHA. `approved_sources` is the list of separately Root-approved capsule refs. No subprocess is created by this live verification path.
- `receiver_rc01.receive(backup, cold_proof_path, cold_proof_sha, new_source, expected_head, *, approved_sources, node)`: returns original receiver bytes and the unchanged native17 text plan. All direct active generations are required. Used bytes must match a replayed prior closed source exactly; unresolved/unknown generations refuse. UNUSED is exact MAGIC only.
- `maintenance_rc01.perform(owner, case, anchor_path, anchor_sha, node, *, deadline_ns)`: one explicit PREVIEW/APPLY with current cold APK/full-private backup, independent receiver, post-copy/index replay and full original conservation. Enrolled PREVIEW has its own durable receipt handling; it does not reuse the frozen initial unenrolled preview. No Activity, input producer or AP starts. Every uncertain operation is attempted at most once.
- `root_maintenance_rc01.py`: source-held executable adapter using the existing WorkbenchRuntime, fixed `m101/m102/m201/m202` slots and the existing 180-second admission/guards. It calls normal administrative closure. Root must inspect source, freeze the complete release and independently admit it first.

The native Java protocol/limits remain unchanged: at most8 direct generations,
8 archive batches of at most8 generations, 64MiB total input/archive/index/control,
32 administrative requests, no automatic deletion/recovery. Every active direct
generation must be included in a plan. Failed/unresolved generation cannot rotate.

## Offline original verification and explicit Root approval

Full prior-source P256/native STATUS/ACK/RC/clock replay happens **after the prior
case has physically closed and before any new runtime actors**. It is never run
as an unbudgeted nested child in a live pipeline. Only the standalone offline
`source_replay.py` imports a prior candidate and starts a bounded Node verifier.
Its child captures finite stdin/stdout/stderr, EOF, deadline and owned-group cleanup;
failures return retained capture diagnostics and never approval.

Root first writes an unverified request and exact replay options from original
case material. Request schema1 has exactly:

```json
{"format":"aeris-betarc01-native-cold-replay-request","version":1,"status":"UNVERIFIED_REPLAY_REQUEST_NOT_AUTHORITY","authorityRestorable":false,"candidatePath":"ABSOLUTE_E17_CANDIDATE","candidateSHA256":"SHA256","caseRoot":"ABSOLUTE_CASE","androidEvidenceRoot":"ABSOLUTE_CASE/sessions/RUN/android-api","productRoot":"ABSOLUTE_CASE/sessions/RUN/product","optionsRef":{"path":"ABSOLUTE_CASE/OPTIONS.json","bytes":1,"sha256":"SHA256"}}
```

The options document contains exactly `{reference,descriptor,productRoot,sourceSeal,reviews}`.
They are the original closed-native descriptor reference, original product descriptor,
actual `SEAL_PRODUCT.result.product`, and reviews from the original workspace WAL.
The verifier independently checks all original OnceStore commands/ACKs/snapshots,
Root registrations, installed candidate/source origin, true P256 envelopes,
AJ02 pairs/heads, original semantic journals, RC transactions and clock brackets.
The original companion launch/PID/seal and workspace row/close chains are also joined.

```sh
python3 -B planning/betarc01/archive/source_replay.py \
  --capsule ABSOLUTE_REQUEST --capsule-sha REQUEST_SHA \
  --capsule-bytes REQUEST_BYTES --node /usr/local/bin/node
```

Root retains the complete command output, `replay`, `inventory` and raw Node output
as exclusive evidence. Canonical stored `replay` and `inventory` bytes are sorted-key
compact JSON plus one LF. Only after independent review does Root create and approve
capsule schema2 with exactly:

```json
{"format":"aeris-betarc01-root-approved-closed-native-source","version":2,"status":"ROOT_COLD_VERIFIED_NATIVE_SIGNED_SOURCE_NOT_FLIGHT_CERTIFICATION","authorityRestorable":false,"requestRef":{"path":"ABSOLUTE_REQUEST","bytes":1,"sha256":"SHA256"},"replayRef":{"path":"ABSOLUTE_REPLAY","bytes":1,"sha256":"SHA256"},"inventoryRef":{"path":"ABSOLUTE_INVENTORY","bytes":1,"sha256":"SHA256"}}
```

The **externally supplied Root-approved capsule SHA** is administrative trust,
not cryptographic external identity. A bundle's own claimed SHA/closed status is
never its approval. Schema1 requests are refused by live schema2 readers. Live
verification rehashes every original inventory file (size/mode/SHA), checks the
original offline result bytes/capture and joins current cold AJ02 bytes. No live
crypto subprocess, new child slot or arbitrary trusted JSON fallback exists.

## Checks and limits

```sh
node planning/betarc01/archive/test_used_crypto.mjs
python3 -B planning/betarc01/archive/test_archive_rc01.py
```

The15 crypto cases use actual generated P256 signatures, Root-reference fixtures,
AJ02/AJZ codecs, original clock brackets and an RC transaction. The14 Python methods
check strict registry/used-proof joins, byte conservation, live-path AST and bounded
offline child setup/timeout/overflow cleanup. They are synthetic/component tests,
not an Android OnceStore or actual used-archive acceptance. Root's actual G2 closed
source capsule and real maintenance acceptance remain required. No counts certify Beta.

The first crypto fixture run failed due to an incorrectly nested fixture-array
spread; the fixture was corrected and all15 cases then passed. No protocol guard
was changed to make it pass. Both report types keep `flightAcceptance=false`.
