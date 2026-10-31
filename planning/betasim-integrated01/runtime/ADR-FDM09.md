# FDM09: lossless physical compaction within existing quotas

R06 retained 267,583,522 physics-journal bytes for 103,484 complete frames.
That measured rate cannot fit all maximum source frames under the original
180/760-second quotas. Slower execution, fewer frames, a larger quota and a
larger export limit are not solutions in this release.

Root L2 authorized a new physical codec only for the selected MAIN `journal`
role. CLOCK and MAVLink transport journals remain plain, with the default cold
reader refusing a codec declaration. The main caller must explicitly select
FDM09 and the main namespace. Earlier candidates and every original file remain
unchanged.

Each accepted logical record is still the exact canonical journal-v2 envelope,
including every original raw byte, field, integer, CRC and logical hash. Typed
physical lines remove repeated context, JSON field names and derivable previous
hash/hash strings. The decoder restores these bytes from the pinned segment
context and sequential logical head. Segment physical SHA, seals, external
commit anchors, record physical CRC and the original logical CRC/hash chain all
remain checked. Unknown body keys, a non-integer/wrong version, original-byte
mismatch, unknown fields, booleans/None/floats in integer STAGE fields, overflow,
partial rows and noncanonical encodings are rejected rather than normalized.

RX stores its exact 40 bytes; INTENT stores its exact at-most-768 bytes; SENT
stores its exact bounded returned/expected counts. STAGE has a fixed source
dictionary, a 64-bit presence mask, and at most 32 actual uint63 fields. It may
use an exact changed-field mask plus canonical signed-varint deltas against the
previous STAGE. The first STAGE in every segment is absolute. A delta is chosen
only when physically smaller; this retains the absolute worst-case bound.
The original field presence and values are restored, not inferred away.

The original serializer rejects nonfinite values and oversized sensor JSON
before INTENT. The pinned model has exactly 22 binary64-or-literal-zero sensor
leaves. Its JSON scaffold including newlines is 160 bytes. A finite binary64
shortest JSON representation needs at most 24 characters, giving a static
688-byte model bound below the unchanged 768-byte runtime guard. FDM09 also
preserves arbitrary byte payloads up to the full 768-byte envelope bound.

The maximum physical complete-frame envelope is 1,644 bytes: RX 105, INTENT
1,077, SENT 57 and 32-field absolute STAGE 405. With conservative original
segment metadata and 4 KiB allocation rounding, all 216,000 short-case frames
fit below 402,653,184 bytes and all 912,000 long-case frames fit below
2,013,265,920 bytes. The original maximum segments are 64 and 320 respectively.
No resource owner, raw-data exclusion, duration, speedup or frame cap changes.

Scene selection is reserved privately by the single physics thread before the
STAGE encoding/fsync barrier, using the original 20 Hz sample-clock policy.
Reserved rows must be absolute. A later offer cannot select a delta because
time crossed a boundary during fsync. Skipping a visual sample does not skip a
physics frame. A standalone Scene prefix reader rejects a delta without state.
The private pipe supplies the preceding logical head and physical stage SHA;
Root verifies physical byte SHA/CRC and the restored logical head before
stripping private decode hints. The public validated frame retains byte-span
identity, path/prefix and logical head, with status
`LIVE_ROOT_VALIDATED_COLD_FULL_PREFIX_REQUIRED`. This avoids adding another
changing 64-hex field to every media-proof record. Full cold-prefix/model replay
is still required for acceptance.

The original RX -> compute -> INTENT fsync -> sensor -> SENT fsync -> STAGE fsync
ordering is unchanged. Partial write, fsync failure, unknown send and missing
state retain a failed/incomplete prefix. No dropped frame, replay, implicit
conversion file or live export fallback is permitted.

Capture capacity is a hard source bound. Export compression is a separate
measurement and an unchanged hard runtime guard. The virtual R06 all-file TAR
models are RAM-only size experiments, not valid closed export archives: original
segment metadata is not rewritten for the virtual physical layout. R06 also
lacks future airborne/manual/video and final native-closed-file entropy. Both
the raw bundle's 168 MiB limit and the shared/joint 192 MiB domains must be
considered; an uncompressed native TAR is counted as its actual bytes, once.
No 10-minute run is justified by an already-over-limit projection, and no beta
acceptance follows from these source/mock results.

## Final approved code5/code6 and AP role

MAIN INTENT code5 is an absolute fixed22-scalar representation, with a type bit distinguishing literal integer0 from finite IEEE64 float, including negative zero. The fixed Model.sensors scaffold, object ordering, list lengths and leading/trailing newlines are reconstructed, and the entire original sensor byte string must match before the encoder chooses the mode. Unknown values/scaffolds remain unchanged RAW. Code6 stores a current type mask plus changed float-bit mask and canonical nonzero U64 XOR varints against the previous actual sensor bits. It is chosen only when smaller than absolute code5; first sensor per segment is absolute, and unsupported RAW clears sensor state. Every reader rejects missing state, unknown masks, malformed lengths, noncanonical values, nonfinite bits and trailing bytes. Generic RAW768 remains operationally supported, so the original generic1644B/frame forecast is retained; no selected860-only admission guard was implemented.

AP stage is a separate version2 physical role APSTAGE09_EXACT64_BLOCK128_DELTA. Its original C++ pipe producer and exact nine-field64-byte events do not change. At most128 original events are buffered; integer delta/time-basis residuals are bijective, including exact uint64 two's-complement argument bits. A compact block has its own CRC and is admitted by the cold reader only after the complete bounded block CRC. If compact header+payload would grow, the source writes the original plain64-byte records instead. This preserves64B/event as an absolute physical bound. Physical segment SHA/seals and a separate original-event SHA cover all bytes. First event per segment is absolute. Normal EOF flushes a partial block with its actual count; exceptional close flushes it when no write began. Unknown/partial writes are never retried; pending exact original bytes and the original pipe tail are retained as failed evidence when storage permits, without a completion claim.

R06 virtual sizing is not a valid newly sealed archive: original headers/seals were retained for the size experiment. The latest model08 roundtrips every original MAIN logical row and every AP event, but R06 had zero ARM and old STAGE fields. It cannot prove current airborne entropy, new Scope9 timing entropy, actual IO/pacing or future compression ratios. Cumulative MAX-short+MAX-long Native SAF projection remains over192MiB before other private files; the release disposition is short-only. Actual accepted short bytes and phase-specific airborne measurements are required before any future long admission.
