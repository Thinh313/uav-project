# APROUTE28 · Actual AP serial routing, synthetic payloads

Isolated engineering harness, not Fly or an installed HeraHub adapter. ArduCopter4.7.1 existing binary is mounted read-only in an owned1CPU/256MiB container. GCS5774 connects only to AP SERIAL0; fixture process connects to AP SERIAL1/5775 and SERIAL2/5776. Cameras100/102/101 and manager154devices1/2 are synthetic configuration. The bridge has no direct peer socket or GCS injection API.

Reviewed immutable T25 context, fresh observed disarmed heartbeat/discovery, narrow unsigned payload command profile and one attempt. Camera zoom/focus/single capture, discovery and manager angle/authority commands only. No APcomponent1/broadcast/flight/mission/param command. Existing inner broker remains MOCK provenance. Outer raw receipts establish actual routing, never execution or actual image files. Shared-manager ACK key is serialized/fenced until explicit reconnect; wire ACK carries no transactionUUID. After reconnect, unsigned stale traffic cannot be authenticated as fresh merely from local generation; the late-ACK test protects historical records, not an absolute remote-freshness guarantee for new same-key commands.

Fresh AP startup: wait actual AP heartbeat and GCS advertisement before fixture catalog. Publish fixture metadata only on AP serial buses. Peer closure is inferred conservatively from absent forwarded component heartbeats (3s), not an AP-reported peer disconnect. Pending work can already be TIMED_OUT_UNCERTAIN when liveness expires. AP socket close/fresh boot and payload boot regression require explicit reconnect; no historical resend, automatic failover or retry.

Raw GCS/peer chunks and frame/SHA journals, command target/correct and opposite bus, response TX/GCSRX, immutable local generation, no-media/causality, exports checked by replay. Journals<=4096rows/2MiB; sockets<=4096queued bytes, connect3s, test deadlines bounded. Exhaustion freezes the session and marks incomplete evidence; the bounded scenario is not a complete capture. These are host functional deadlines, not hardware latency benchmarks. Signing unsupported/refused; no remote authentication claim.

Run from project root using unused evidence/state IDs only:

```
python3 -B pilot/aproute28/simulator.py start run06
node pilot/aproute28/network-qa.mjs attempt06 run06 run02
node pilot/aproute28/replay.mjs attempt06
python3 -B pilot/aproute28/simulator.py stop run02
node --test pilot/aproute28/bridge.test.mjs
```

The runner explicitly stops the initial owned simulator and starts a fresh state once for the reboot test. This is an authorized test action, not automatic recovery. If it fails, read qa.activeSimulatorRun/container identity and stop only the currently owned instance; do not erase or reuse failed state/receipts. Leave ENDURE launch/controller/candidate untouched. Current final corpus attempt05 uses run04→run05; owned instance/ports now stopped. No SDK, dependency install, whole-project copy, new image tag, app/native/compiler/signing/trust edit or browser acceptance required.

`delivery/COMPLETION-APROUTE28.md` and `evidence/aproute28/verification.json` record requirements/results/limits; `pilot/aproute28/verify.py` validates existing receipts and writes only A28 metadata/fingerprints. Do not rerun old release/campaign helpers. Raw sources include official routing/serial docs and GPL routing source at recorded firmware commit; these are captured claims, not an independent firmware rebuild.
