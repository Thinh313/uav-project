# Independent M1 mock adversarial review

Scope: new isolated source only, public APIs and actual small filesystem records.
No AP/Android/socket runtime, physical device, native/AP/APK artifact or signing.
The reviewer did not author production modules or builder tests. Agent review is
not independent human flight review and cannot qualify the later integration.

## Evidence priority

Inspect raw bytes, durable ordering and cold reconstruction rather than accepting
builder summary PASS fields. Record source SHA for each run; if a source changes,
retain the prior finding and test result under a separate exclusive receipt.

## Adversarial families

1. Journal chronology: successful frame group requires RX/INTENT/durable barrier
   before the observed send callback, then local-send outcome. Sender failure or
   short return must not become SENT. Segment seal is not session completion.
2. Membership and binding: missing/extra/renamed/duplicate/reordered segments,
   foreign run/epoch/sequence, mutated payload/length/hash/status, symlink files
   and directories, traversal or a manifest pointing outside expected root.
3. Fault publication: partial write, EIO/ENOSPC, file sync and directory sync
   failure, precreate/rotate/seal failure; no false session CLOSE. Preserve valid
   prefix and unknown outcomes, no append after seal, no silent repair/delete.
4. Admission: booleans/float/NaN/Infinity/negative/overflow/undefined upper bounds,
   copies/export reserve, decline forecast and floor exact boundaries; no physical
   host disk fill is needed.
5. Clock: more than1024 requests with bounded pending/tombstones, expired/evicted/
   late/duplicate/unknown IDs, peer/epoch/boot mismatch, impossible brackets,
   monotonic regression and suspend. Exact raw events stream before state publish;
   failing sink poisons state and cannot freshen calibration.
6. Lifecycle/provider: expected/observed identity mismatch, mutable aliases,
   nullable candidate hashes, generation/context mismatch, expired/revoked lease,
   repeated close, resources-closed versus review-committed, restart and old
   callback against a new run. Elapsed closes once; timing never means LAND.
7. Composition: connect clock durable sink to journal event API where possible;
   verify state cannot advance across journal failure and receiver sees all exact
   clock events without conflating event sequence with frame sequence.

Tests remain bounded (<32MiB/<500files); shared guard20GiB entry and10GiB+256MiB
floor with forecast15s remain unchanged. Pure Java classes may be compiled using
the pinned JDK --release8 in the QA-owned subtree of native/.build, then removed.
No test may import or execute a legacy launcher as a convenience fixture.

Findings report severity, exact reproduction, expected versus observed behavior,
source SHA and acceptance implication. A test-design error is distinguished from
a product bug. Required untested scope remains NOT_CHECKED.
