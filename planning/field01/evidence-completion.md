# FIELD01 evidence Builder completion

Implemented an isolated asynchronous durable store, immutable synthetic capture
and TAR3 handoff, and a separate Python stdlib receiver. Root-authored gateway
received one announced narrow repair: late-revocation journal kind changed to
`PAYLOAD_CAPTURE_AUTHORITY_ENDED_AFTER_COMMIT`, because external `CAPTURE_*` kinds
are reserved for the store state machine.

User outcome: the host gateway can await durable intent/result ordering, retain
unchanged synthetic JPEGs with exact mission/source context, review saved or
pending evidence, and transfer a bounded package whose receiver independently
checks byte/context integrity and persisted replay state. Restart grants no rights.

AC5 evidence slice: implemented async serialized fsync-before-return WAL, poisoned
uncertainty, expected-head CAS, exclusive writer ownership, pending retention,
conservative quota, original/sidecar/link integrity, immutable archive, datum and
time uncertainty labels, independent receiver gate, restart replay refusal and
no authority restoration. AC4 gateway policy was exercised with fake flight/media
and actual Store01. Browser/SITL/physical exposure acceptance is outside this slice.

Verification:

| Scope | Result | Retained output |
|---|---:|---|
| Store and independent receiver Builder checks after nearest method update | 14 pass, 0 fail | `evidence/field01/evidence-tests-2026-10-21T12-16-05-371Z/results.json` |
| Delegated root gateway integration, actual store plus fake Flight/media/clock | 10 pass, 0 fail | `evidence/field01/evidence-gateway-tests-2026-10-21T12-17-35-624Z/results.json` |

The store check includes a 180 ms injected async fsync pause during which the host
health interval continues ticking; receipts remain pending until the pause is
released. Other retained cases include fsync error poisoning, two child-process
crashes leaving locks, pending file/guard failures, quotas, static symlinks,
corrupt/torn journals, receiver process restart replay, and byte/hash/context/TAR
faults. Validly rehashed false survey, datum, sensor time and physical image claims
are rejected independently by Python. The gateway suite tests timeout without
retry, identity/lease gates, wrong-target/absent evidence, disconnect/reboot,
unknown position, exact capture linkage and both async revocation windows.

These are synthetic fault/protocol checks, not empirical sensor quality, camera
authenticity, browser speed or flash-power-loss durability certification. Actual
images remain zero. Position is a host receipt reference with MSL and relative
Home quantities; physical exposure time, accuracy and sensor-clock uncertainty
remain unknown. JPEG markers do not establish decoder safety. Hashes do not sign
the producer. Parent directories must be operator controlled because Node has no
openat protection against concurrent ancestor replacement.

Value evidence: deterministic policy/storage has no LLM runtime baseline. Operator
effort and end-to-end workflow advantage were not measured here. The tests author
also implemented Store01, so its storage assessment is not independent. The Python
receiver uses a separate implementation/language and no JavaScript validator,
but does not constitute independent human review.

No install, whole project copy, Docker build, CUA, APK, or SITL process was created.
Normal stores released their own locks through `close()`. Intentionally crashed
locks and all evidence are retained for inspection; no data was automatically
deleted and no scratch dependency directories required removal.

Slice status: READY for host integration within these checked protocol/storage
conditions. Physical camera/GNSS/RF/Android and complete FIELD01 acceptance remain
NOT_CHECKED by this Builder slice.
