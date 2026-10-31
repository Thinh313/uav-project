# TIP-FLIGHTADAPTER39 — isolated readonly flight-operations composition

2026-10-14. User authorized APFLIGHT36–MAVFLIGHT37–FIRMWARE38 composition with mock/replay only. P0; dependencies are their accepted immutable sources/receipts. One agent switches specification, build and verification roles; this is not independent review. No further scope approval needed.

## Scan and decisions

M37's decoder does not recognize AUTOPILOT_VERSION148 and its fence transaction expects REAL32 parameters. F38 requires whole frames and source-bound typed parameters. Reuse M37 wire codecs/telemetry, F38 typed reader/policy/altitude, A36 preflight through M37; add a bounded union framer and central session gate. Do not fabricate typed-to-Wh policy conversion or weaken the old fence reader. Geometry/fence upload is deferred; this composition is readonly observation/preflight inspection, not a fence uploader or flight-command broker.

## Requirements and observable acceptance

| ID | Requirement / acceptance |
|---|---|
| R39-01 | Union framer covers 18 M37 messages + unsigned v2 version148, v1/v2 lengths/CRC; every split/coalescence retains exact bytes and first/last receipt. Bound input, pending, noise and frame count; corrupt/signed/unknown frames invalidate rather than hide changes. |
| R39-02 | One central target/session/boot/link/epoch, ordered local receipt/now clocks, wrapping sequence and per-message boot clocks. Duplicate/reorder/foreign sender quarantined; regression/ambiguous sequence/foreign context/stale/suspension require a new explicit instance. |
| R39-03 | Fresh reviewed announcement starts one-pass F38 typed readonly read; first-byte freshness used; changed announcement/typed values/count/type/index or unavailable journal revokes all composed witnesses. No implicit refresh/retry/reconnect. |
| R39-04 | M37 telemetry + A36 preflight and F38 policy/altitude are separately scoped in one inspection. Missing supplements/references remain UNKNOWN; no normalized policy/Wh/active enforcement/physical execution/authentication invented. |
| R39-05 | Process-local inspection capability, not flight authority. Disconnect, owner/focus loss, timeout, partial frame expiry, concurrency and revoke-during-commit block publication. Serialized/tampered/restarted snapshots cannot restore capability. |
| R39-06 | Bounded journal audit and mock PARAM_REQUEST_READ output only; intent persisted before publication, journal is injected mock storage. Capture source-bound replay corpus, negative/tamper tests, cold replay and exact old36/37/38 regressions without old writes. |
| R39-07 | Fingerprints before/after including newest38 and ENDURE inventories; floor20GiB, namespace budget16MiB+64MiB reserve; no dependency/build/runtime/signature/source/candidate/SOT/trust edits. |

## Test/verification plan

Mechanical framer split/coalescence matrix; adversarial session/clock/sequence/boot cases; typed C-cast and bytewise mock dialogues; shared revocation and journal fault/race cases; inspect wire-only vs explicit mock state; independent cold replay invocation and old corpus exact comparison. Receipts append with exclusive filenames, failures retained. Runtime/AP firmware association/Android/Hera/live transport are NOT_CHECKED. Passing offline tests never closes ENDURE24h or allows integration/signing.

## Outputs

`pilot/flightadapter39`, `evidence/flightadapter39`, ADR052, completion and roadmap supplement. Frozen canonical roadmap/SOT unchanged. No UI or browser acceptance in this task. Use existing Node/Python stdlib. No scratch project, install or ephemeral build directory.
