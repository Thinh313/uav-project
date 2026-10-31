# FLIGHTADAPTER39 — isolated readonly AP-FLIGHTOPS composition

New namespace. Frozen app/source/candidate/trust/SOT/ENDURE and old module/receipt bytes are not edited. No socket, server, network, SDK, APK, SITL/emulator, flight command or signing. Incoming data and AP state are MOCK_REPLAY/SYNTHETIC. Injected journal persistence is a mock contract, not a tested production disk implementation.

`UnionFramer` covers M37's18 messages plus F38 AUTOPILOT_VERSION148 unsigned v2. MAVLink1 supported for M37 definitions with exact base length; v2 zero truncation follows pinned schemas. CRC and sender/length checked before publication. Whole frames retain exact raw hex and first/last byte local receipt timestamps. Bound4096-byte chunk,267 pending bytes,64 frames/batch,64 total noise bytes. Corrupt, signed/incompatible or unsupported message closes the session: this strict19-message subset is not a general full ArduPilot stream.

`FlightAdapter39` centralizes reviewed target/system/component/session/boot/link and local clock epoch. Context/host receipt/now regressions, stale1500ms, partial-frame expiry, sequence half-range ambiguity and accepted per-message boot-ms regression revoke the instance. Sequence wraps are admitted; duplicate/reordered packets are quarantined, never refresh witnesses. Foreign components never advance AP sequence. Conflicting same-target firmware or an already observed parameter revokes even if sequence is duplicate/reordered. Unsigned CRC/UID/outer metadata do not authenticate a remote sender or prove a reboot; Unix-vs-boot time_usec is not guessed. Sequence gaps cannot uniquely distinguish packet loss from reorder/reset.

One fresh reviewed version binds F38, then28 named typed read requests. C-cast/bytewise semantics, unknown index65535, type/count/range/precision and full process-local readback checks are retained. All output is MOCK_BUFFER_ONLY ID20 PARAM_REQUEST_READ, networkSent:false, after injected journal intent. No parameter writes, upload/clear, ARM, mode/takeoff/landing or generic command capability. Identical version announcements do not renew binding; changed firmware/configuration, session/owner/focus loss, writer uncertainty, concurrent receive/inspection and revoke-during-commit block subsequent publication. Buffers already returned remain mock historical observations; no automatic retry or cancellation/execution claim.

M37 telemetry feeds A36 preflight; F38 typed policy/failsafe/altitude remains separate in one `inspect` result. Wire-only preflight is UNKNOWN because fence readback, normalized policy, independent RC/AP receipt and remainingWh are not established. Explicit AP-side/altitude snapshots must be SYNTHETIC, current and context-bound. No mAh/V-to-Wh or rich-policy-to-old-enum substitution. Legacy fence upload/completion is deliberately not composed: its REAL32 parameter proof cannot be borrowed for this typed reader. Active enforcement and physical execution remain false. Missing AP state/Home/terrain remains UNKNOWN.

Inspection proofs are WeakMap-issued in one process and are readonly; flightAuthority is always false. Serialized/tampered snapshots do not restore witnesses, and a new constructor requires a reviewed contract, not a snapshot. A newly created instance starts WAITING_FIRMWARE. Restart/reconnect is explicit future work, never automatic.

Session audit journals hold admitted/quarantined complete frames and byte lineage; F38 retains typed readback intents/observations. Loss leaves prefixes intact and terminal state/reason in snapshot/replay. Partial chunk intent is preserved in corpus, not falsely claimed as a committed complete frame. In-memory default persist is not power-loss durability.

Tests use185 previously accepted upstream oracle vectors,5671 split positions, union/coalescence/clock/context/configuration/owner/writer adversarial cases,40 source-bound replay scenarios and9 semantic/hash bites. Cold verification replays old36/37/38 receipts without writing them. All receipts append; logic1/replay1 failures remain. Official schema/source provenance is inherited read-only from ../mavflight37/REFERENCES.md and ../firmware38/REFERENCES.md; no new external fact or hardware capability is inferred.

Commands (append new receipts; never overwrite existing ones):

```
node pilot/flightadapter39/tests.mjs
node pilot/flightadapter39/replay.mjs
python3 -B pilot/flightadapter39/verify.py
```

`verify.py` binds the accepted logic4/replay4/corpus4 set; it never silently accepts a changed source/newest attempt. A generic bytewise profile does not inherit Copter telemetry interpretation. Actual firmware/binary association, full-stream policies, production persistence, flight/enforcement, Android/Hera/SDK and ENDURE acceptance remain separate NOT_CHECKED gates.
