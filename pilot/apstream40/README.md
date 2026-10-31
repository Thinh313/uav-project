# APSTREAM40 — full pinned ArduPilot dialect, restricted mock discovery

Separate namespace. No frozen app/candidate/source/trust/SOT/ENDURE or old module/receipt writes. No socket, HTTP server, APK, dependency install, actual ArduPilot/SITL/emulator, signing or aircraft/payload output. Buffers are MOCK_BUFFER_ONLY and networkSent:false. All input/context/AP-side state is synthetic mock/replay.

## Full-stream scope

`definitions.mjs` derives the entire local upstream ardUpilotMega include closure:299 messages,9 XML files,188 v1-addressable IDs, full24-bit v2 IDs. All layouts/CRC_EXTRA match upstream mavparse. Runtime-tree XML differs from the older captured M37 XML; `overlap1.json` retains differences and18 base layout/CRC matches, with exact25-byte PARAM_VALUE22 and78-byte AUTOPILOT_VERSION148 bounds. No merged snapshots or old schema edit. This is the pinned dialect, not every future/custom dialect or semantic support for299 message types.

`wire.mjs` implements native-size ordering/arrays/little endian/signed and unsigned integer types;64-bit values remain decimal strings; v2 zero truncation/extensions and v1 base lengths. Char fields preserve raw hex and disclose invalid text. FullFramer bounds16384-byte chunks,64 frames per batch,280 pending bytes and64 cumulative noise bytes. Whole frames preserve exact raw bytes plus first/last local receipt time. Known CRC corruption closes the instance. Opaque unknown IDs retain bounded framing/raw bytes with crcVerified:false; no guessed CRC or semantic meaning.

Signed known frames retain the complete13-byte trailer and checked CRC, but authentication is SIGNED_UNVERIFIED. Test trailers are fabricated bytes, not cryptographic signatures. Unknown incompatible flags fail closed. Selected-AP signed/opaque frames during discovery/readback make the witness uncertain and invalidate it; foreign frames are quarantined and never alter selected AP sequence. No authentication/signing implementation or radio security acceptance is claimed.

## Discovery and semantic dispatch

APStream40 requires an explicitly reviewed F38 SYNTHETIC contract and a fresh unsigned selected-target heartbeat(type2/autopilot3). Discovery starts only with explicit `startDiscovery`. One REQUEST_MESSAGE512/param1=148 is journaled before its buffer. This is the only COMMAND_LONG output; param2..7/confirmation are zero, exact target is required. The seed GCS sequence255 then readonly parameter sequence0..27 preserves ordering across the seam. No arbitrary command, mode, ARM, fence upload/clear or parameter-write API.

Discovery has one1500ms window. ACK512 is diagnostic only and requires the exact AP sender plus v2 GCS255/190 recipient; accepted/in-progress ACK does not bind firmware or extend the deadline. Version148 is required; unsolicited, wrongtarget, late, pre-request first-byte, signed or mismatching source/capability/version/UID responses cannot create a binding. Same wire-key replies have no request nonce, so matching does not prove causal response or authentication. No automatic retry/reconnect/renewal.

Validated auxiliary AP packets advance the outer sequence and legacy reader/link sequence without re-encoding raw input. The legacy telemetry cache receives validated decoded frames rather than reparsing a different XML snapshot. Only reviewed base-compatible telemetry semantics feed M37→A36 preflight. F38 typed reader receives actual unchanged PARAM_VALUE bytes. Generic bytewise profiles cannot inherit Copter telemetry/policy interpretation. Source/binary association and actual firmware identity remain NOT_CHECKED; fixture identities still contain MOCK0038 and arbitrary UID/board values.

Context(session/boot/link/epoch), receipt/now regression, age/partial expiry, accepted per-message AP boot regression, sequence half-range uncertainty, incompatible heartbeat, firmware/config conflict, owner/loss/writer/concurrency invalidate all process-local witnesses. Boot-ms wrap is allowed; time_usec is not guessed as guest/host time. Duplicate/reordered frames never refresh discovery/readback; conflicting already-read config/identity revokes even under old sequence. All reboots are not detectable from sequence alone; explicitly changed context requires a new instance/discovery/full readback.

Preflight wire-only remains UNKNOWN; rich policy/failsafe/altitude results are separate. No mAh/V→Wh, normalized-policy equivalence, active geofence enforcement, execution/capture or physical firmware claim. Explicit AP-side and reviewed altitude mocks remain labeled synthetic. Proofs use WeakMap issuance, canonical tamper checks and live owners; snapshots/clones do not restore authority. flightAuthority/operationalAllowed/authenticated/executionProven are always false.

## Audit and checks

Incoming bytes/context are cloned before any await. MockJournal records raw chunk intent and each accepted/quarantined/rejected complete frame;8192 rows/4MiB are explicit limits, no silent pruning. F38 typed journal is unchanged. Writer faults retain prefixes and unknown terminal state; revoked async commits cannot publish buffers. Persistence is injected mock storage, not proven production durability or power-loss recovery. Partial/raw receipts are not turned into complete protocol success.

Current accepted receipts: logic2/replay2/corpus2, oracle-check1 and verification1.1015 logic checks include974 upstream vectors(all299 IDs, v1/v2 patterns) and37166 split positions.44 replay scenarios and9 falsification bites; cold replay validates88 journal chains and exactly reproduces old36/37/38/39 corpora. Counts overlap, not flight trials.

Commands append receipts without replacing old files:

```
node pilot/apstream40/tests.mjs
node pilot/apstream40/replay.mjs
python3 -B pilot/apstream40/oracle-check.py evidence/apstream40/js-vectors2.json
python3 -B pilot/apstream40/verify.py
```

Verifier binds accepted filenames/source hashes; it does not automatically select changed source/newest runs. Generated Python upstream GPL-3.0-or-later serializers are test-only; XML/license source remains pinned. Existing parser warns about two enum bitmask entries; no source correction was made, and299 message layout/CRC checks pass. Build/typecheck/lint/live traffic performance/binary association/Android/Hera/SDK/A-B/release/ENDURE acceptance are separate NOT_CHECKED gates.
