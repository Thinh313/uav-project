# Segmented host recording foundation, format 1

This package is isolated and **unwired**. It creates no sockets, autopilot,
Android process or flight authority. It is a new format, not a compatibility
implementation for any earlier WAL or native raw recorder.

## Public API

```python
from pilot.betaintegrated01.journal import (
    SegmentedJournal, Policy, FileIO, verify_journal, estimate_admission,
)

# An owning caller must have passed the real 20 GiB entry gate and declared
# duration/rate/original/copy/export capacity before starting a run.
j = SegmentedJournal(new_root, "run01", "epoch01", Policy())
j.record_frame(0, b"received-pwm", lambda rx: b"computed-sensor", send_callback)
j.append_stage(0, {"computeNs": 100, "fileSyncNs": 200})
j.append_event("CLOCK_EXCHANGE", {"clockId": "run01-clock01", "offsetNs": 5})
receipt = j.close()

# Retain this anchor OUTSIDE the journal using the owning caller's trusted
# context. Never reconstruct a trusted anchor from an imported directory.
anchor = receipt["commitAnchor"]
v = verify_journal(new_root, "run01", "epoch01", expected_commit=anchor)
assert not v["publicationAllowed"]  # This package never grants publication.
```

`root` must not exist, and its parent must already exist. Run/epoch IDs are
1–64 ASCII identifier characters. Frame numbering starts at zero and is
contiguous. `send_callback(intent)` must return exactly the byte length as a
Python `int`; raised exceptions, short sends, non-integer values or out-of-range
integers become an explicit `UNKNOWN` and fence the journal. There is no retry.
The callback's local return is not proof that ArduPilot received or executed it.

The class has a nonblocking single-writer lock. Concurrent or post-close calls
reject. An invalid admitted operation fences the run rather than silently
continuing. `abort(reason)` retains an incomplete prefix; it cannot upgrade it.

`FileIO` provides `open_exclusive`, `write`, `fsync`, `dirsync` and `close` fault
seams. Its optional hook receives `(operation, path_or_none, byte_count)` with
operation `open`, `write`, `fsync` or `dirsync`. A separate actual-host disk guard
is checked before writes/admission/send, so a mock FileIO cannot substitute
synthetic free space. It retains at most 64 samples, forecasts 15 seconds from
the available recent decline and preserves 10 GiB plus 256 MiB. This forecast is
an observed-rate refusal mechanism, not a guarantee against future host writes.

## Record and failure contract

Records use a global sequence, run/epoch/segment context, CRC32 and a SHA256
previous-record chain. A successor header binds the previous segment file hash.
An exclusive-created segment is synced and sealed, with directory sync, before
a successor is admitted. Rotation occurs only between frame groups.

The observed order is `RX → compute → INTENT → file fsync → callback → SENT`
or `UNKNOWN`; a bounded three-record group and termination reserve are checked
before RX. Segment sealing alone is not session completion. CLOSE, all seals and
the exact session receipt are needed for complete bytes. No append is allowed
after closure. Real receive-loop admission remains the future caller's duty:
this API accepts an already-owned byte object and does not attest an external
socket received every frame.

Ingress byte length is checked before base64. Event trees are checked before
JSON serialization: depth at most 8, 256 nodes, at most 64 entries per container,
bounded strings/total tree size and finite bounded numbers. Final serialized
records must also fit `max_record_bytes`. A caller-provided compute function
can allocate memory itself; that callback is outside these component bounds.
Stage rows retain exact fields in the stream; summaries contain only bounded
count/sum/max per field, at most 32 fields, without a growing timing array.

The cold verifier has its own format implementation and streams bounded lines.
It rejects mismatched context, missing or renamed segments, extra members,
static symlinks/hardlinks, tampering, forged receipts, appended sealed data and
illegal frame chronology. Leaf opens use NOFOLLOW/fstat. The root is a trusted,
quiescent caller-owned filesystem capability, not a hostile shared directory;
same-UID concurrent parent-directory replacement is not a supported security
boundary. There is no archive extraction or metadata-supplied path resolution.

## Honest cold verdicts

| Cold result | Meaning |
|---|---|
| `INCOMPLETE_RECORDING` | Valid retained prefix without a complete byte sequence. |
| `COMPLETE_BYTES_UNATTESTED` | Exact complete bytes; no external successful-close acknowledgment supplied. |
| `COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH` | Complete bytes match the caller-owned anchor returned after successful local sync acknowledgments. |
| Exception | Invalid format, corruption, context mismatch or supplied-anchor mismatch. |

Every result has `APExecutionAccepted=false` and `publicationAllowed=false`.
`writerCommitAttested` is true only for a matching external anchor. It is not
source authentication, physical power-loss durability or actual sensor-send
proof. Format hashes alone provide integrity/consistency, not signer identity.

In particular, a final directory sync can fail after `session.json` bytes exist
while writing `failure.json` also fails. The cold directory alone cannot reveal
the failed acknowledgment. It stays `COMPLETE_BYTES_UNATTESTED`, never an
authorized committed publication. Adding another in-directory commit file would
only move this ambiguity. No externally retained anchor is returned on failure.

## Admission arithmetic and evidence scope

`estimate_admission` is pure arithmetic. Every rate/size is a **caller-declared
upper bound**, not an empirical average. It accounts frame capacity, WAL/trace/
stage/video bounds, metadata, copies, export peak, entry 20 GiB and retained
10 GiB plus 256 MiB. Missing, boolean, negative, non-integer and overflowing
inputs reject. The caller must justify that its supplied bounds cover the
selected profile and every enabled stream; this helper cannot certify them.

Builder evidence is under `evidence/betaintegrated01-m1mock/journal/`:

- `tests01/report.json`: 25 original-source filesystem/fault/crash groups.
- `regression02/report.json`: targeted bounded-ingress and commit-verdict repair,
  plus retained-prefix cold replay, after the source changed.
- `send-return03/report.json`: explicit UNKNOWN for out-of-range callback return.
- `parity05.json`: exact-context replay of independent QA's schema-parity cases.
  `parity04.json` used the wrong expected context and is explicitly invalid for
  that schema claim; it is retained without rewriting history.

Independent QA has separate tests and receipts under the `m1mock/qa` paths. Test
counts are scoped checks, not proof of 30-minute operation, performance, actual
AP-stage coverage, native provider readiness or Hera calibration. M1 still needs
a separately admitted build/actual campaign with bound artifacts and runtime
closure. Nothing in this package authorizes that campaign automatically.
