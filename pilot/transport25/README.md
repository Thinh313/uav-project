# TRANSPORT25 · mock-only transport preparation

Contract/runtime broker and42 synthetic routing scenarios, isolated from frozen app/candidate. No Hera SDK/device, real/network transport, SITL write, compiler integration or new software signature. Working path is `pilot/transport25`; evidence is `evidence/transport25`. Default synthetic topology: three cameras (EO component, thermal autopilot proxy, fixed survey component), two gimbal devices behind one manager and two mock links. Two extra cases declare a fourth proxy camera for ambiguity tests. These are not installed Hera configurations or supported hardware capacity.

From repository root:

```
node --test pilot/transport25/transport.test.mjs
node pilot/transport25/browser-qa.mjs
node pilot/transport25/server.mjs
```

Current static inspector runs at127.0.0.1:8792. POST/body-framed requests405; no aircraft/data APIs. Browser replays original pinned JSON/raw frames; tamper/offline invalidates review/export. Existing PROTOCOL22 codec/session/definitions are read-only imports. Producer uses its JS serializer;14 prior C vectors/82 PROTOCOL22 tests are regression evidence, not independent C generation of these new42scenarios. `build-corpus.mjs` deliberately regenerates this isolated corpus/pin only; do not run old corpus helpers. The first40-scenario corpus was reconstructed byte-exact and hash-checked against its retained browser review, stored as corpus-revision01.json; final42 scenario receipts are separate.

Transport contract: `contract.d.ts` documents the interface; `config.mjs` runtime validators enforce supported fields/limits. Type declarations are not independently TypeScript-compiled. Configuration is cloned/deep-frozen, hashed and bound to local session/generation. Camera component/proxy IDs, optional gimbal manager/device, actor ID255/190 and selected link are explicit. A fixed camera has no inferred manager. Physical capability/primary authority still needs fresh advertised information. Configuration SHA/local context and CRC are not sender authentication.

Example mock call:

```
const port = new MockTransport();
const broker = new TransportBroker({ transport: port, now: () => fixtureClock });
await broker.connect(CONFIG, { activeLink: 'mock-a' });
// Inject declared raw fixture heartbeats/information, then review the current context.
broker.request({ bindingId: 'front', operation: 'zoom', value: 40,
                 context: broker.context() });
```

Construction accepts branded exact/frozen MockTransport only; real adapter creation refuses. This protects the supported API from accidental adapter substitution, not arbitrary code execution in the same process. Mock send admission is not ACK; ACK is not execution; consistent observations remain unattributed. Physical media always empty/false, live video/thermal quality/native/manual RC untested.

One pending operation per camera/gimbal target and one ACK key per responder/command; terminal ACK keys stay fenced until explicit new generation. This deliberately restrictive policy prevents a completed/late ACK from being mistaken for a new operation. It is not production continuous joystick/zoom control. Reconnect discards pending work, restarts discovery, never resends; local epoch cannot prove remote freshness if caller metadata is forged. Aircraft heartbeat loss freezes all commands; scoped camera/gimbal/video faults remain separate. Active-link loss requires explicit reconnect/choice, not auto failover. Per-link deframers cannot splice fragments; bounded exact-byte dedup does not assert universal redundancy/authentication support. Signed/unknown messages are refused for local inspection; no routing-forwarder claim.

Limits:2links/8bindings/64retained transactions; no send queue; receive chunk4096B/current-generation raw-byte cap256KiB,128journal/dedup entries. Admission refuses before dispatch when capacity exhausted. Journal/dedup/inherited history eviction is explicit via dropped/historyComplete:false; corpus original raw bytes remain immutable. Clock regression produces a historical cached conservative review and invalidates pending interpretation. Declared budgets are fixture policy, not measured Hera transport latency/throughput.

Mission draft is a separate pure target projection for zoom531/focus532/capture2000: direct camera component or autopilot-attached device maps into the mission camera-ID field. It is config/context/capability-bound and refuses broadcast0, unsupported/unknown target or hidden input fields. It does not encode/upload MISSION_ITEM, extend current QGC compiler or prove installed ArduPilot behavior. Raw COMMAND_LONG NaN fields remain authoritative in raw hex; JSON non-finite parameter copies alone are not the original wire representation.

Current188 canonical checks:75 core/corpus tests (42 raw scenarios plus33 targeted negative/bounds/schema tests),31 browser checks,82 prior protocol regression tests;0FAIL/0unit skips. Browser six-width geometry/keyboard/export/tamper/offline tests and actual screenshots are retained. No installer/build/dependency/scratch directory required. SDK/HeraHub/HIL/new SITL payload transport/physical media/real authentication/runtime A/B remain NOT_CHECKED. PROTOCOL22 post-ENDURE20 Fly integration still follows its approved offline-inspector TIP; this module is not automatically included.
