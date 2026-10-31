# PROTOCOL22 · offline camera/gimbal discovery and correlation

Bounded14 reference-C vectors /37 ordered synthetic protocol scenarios. Thirteen pinned MAVLink messages; original XML and selected reference-C headers from commit8c63a49fe35aead7f9ef14031381c5e076ff743a. Original sources/hashes and retained generated-output license notice under reference/protocol22. Official C code is a QA oracle, not an application dependency or Hera SDK. New codec/controller ES modules use no Node/socket API and no aircraft transport. No RAGAS source.

From aeris, no installation:

```sh
node --test pilot/protocol22/protocol.test.mjs pilot/protocol22/gate.test.mjs
node pilot/protocol22/browser-qa.mjs
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B pilot/protocol22/verify.py
node pilot/protocol22/integration-gate.mjs
node pilot/protocol22/server.mjs
# http://127.0.0.1:8790
```

To regenerate the oracle/corpus, run generate.py, compile oracle.c with `clang -Ireference/protocol22/c` to pilot/protocol22/.oracle, then build-corpus.mjs. Remove .oracle after QA; keep original packets/corpus/pins. Check hashes against retained corpus-pins.json before adopting changes. Regeneration requires updating pins.mjs corpus SHA and browser contract count if the reviewed corpus changes. Oracle and XML/header disagreement must fail; do not silently mix schemas. Existing candidate dialect is not regenerated.

Discovery requires heartbeat plus information; autopilot role is separate from airframe type. The bounded corpus handles fixedwing/quad/coaxial/heli/hexa/octo/tri autopilot kinds at component1 and cameras/gimbals separately; unsupported roles remain unavailable. Advertisement is not authenticated installed capability. Proxy camera IDs explicit; camera definitions/URIs are retained as metadata and never fetched. Stream running metadata is not decoded video. Manager status is the source of primary authority; configure ACK cannot grant it. Secondary/mission authority is distinct.

Requests queue **offline bytes only**. One unresolved responder/command ACK key; proxy result_param2 and optional GCS recipient checked. Modern REQUEST_MESSAGE512 has no requested-message ID in its ACK, so requests serialize. Legacy521 supported in corpus. ACK-only/in-progress has an absolute fixture deadline2s, no automatic resend. Timeout/invalidated keys quarantined; explicit new transport epoch discards parser/decoder state, does not resume transactions. Epoch context is caller-supplied local provenance, not cryptographic wire/session authentication; signatures unsupported and refused. CRC/sequence/boot checks do not authenticate a remote sender or prove fresh timing across a physical reconnect.

Camera zoom/focus uses0..100percent, not factor/meters. Absent/NaN legacy extensions remain unknown. Single-capture index/time baselines separate capture metadata from file bytes; CAMERA_IMAGE_CAPTURED does not echo the local request ID. Gimbal limits radians, command1000 angles degree, message287 radians, attitude quaternion; require vehicle yaw frame, valid norm, fresh primary status and no failure flags. Accepted ACK plus matching later settings/attitude/image metadata is OBSERVATION_CONSISTENT_UNATTRIBUTED, never proof of request causality or physical media. Current controller covers selected camera actions/gimbal angle, not all protocol modes/commands.

UI is an offline corpus inspector. Review exports preserve raw hex, local session/generation, request bytes and expected-result scope; NaN serializes as null in JSON, original rawHex is authoritative. Bounded256-entry history visibly becomes incomplete after eviction. It is not an official durable mission record or signed handoff. Static GET-only server8790 is separate from frozen8788 and PAYLOAD21 on8789. Stop only its recorded PID/session. Current Fly/signature integration is pending accepted ENDURE20 per delivery/TIP-PROTOCOL22-FLY-INTEGRATION.md; gate is metadata prerequisite, not independent trust attestation/signing approval. Real/native/SDK/video/media/SITLpayload/HIL/flight/A/B remain NOT_CHECKED.
