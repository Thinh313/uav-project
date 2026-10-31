# RESOURCE18 · Host operator runbook

Use the independently pinned external bootstrap published with evidence/resource18/artifact.json. Verify its entry SHA before executing Node; supply bootstrap descriptor pin and original engineering root anchor. This is local development authority, not official RtR release authorization.

`node <bootstrap>/secure-bootstrap.mjs --bootstrap <bootstrap> --expect-bootstrap <descriptorSHA> update start --directory <generation> --expect <planSHA> --port <loopbackPort>`

Managed candidate1.13+ on macOS: parent applies generated Seatbelt before Node, registers child PID durably, caps V8 old space256MiB and monitors Node RSS512MiB, disk20GiB+64MiB and heartbeat10s. Parent and child sample every500ms. Sampled RSS is not a hard memory/process-tree limit. macOS RAM estimate free+inactive+speculative is conservative policy observation, not allocation promise. API GET /api/resources/status shows current sample/managed context. Do not interpret development preview as isolated or historical test receipt as current host measurement.

When low resources: new mutations denied; parent stops on reserve/RSS/heartbeat/observation failure. SIGTERM then5s escalation. No auto restart, fallback, downgrade or deletion. Existing store validators must replay bytes on restart. Never publish partial files as accepted, synthesize missing receipts, or infer camera images from simulation commands.

Every managed run writes immutable UUID.begin.json and UUID.end.json in the update control directory (outside data). End binds begin digest plus PID, policy/isolation/manifest and exit cause/peak RSS. Parent killed before end => begin-only incomplete supervision; preserve raw begin and locks.

If only child fails and parent finishes: inspect end, resource cause and current data validity; explicit start takes new session. Dead legacy store lock takeover still requires valid PID and no live/ambiguous writer; replay validates all committed bytes. Never force unlock a live store.

If managed parent SIGKILL: child terminates on IPC disconnect, but control locks intentionally remain. Wait until both recorded PIDs are confirmed dead. Read exact ACTIVE phase digest and trust pending writer SHA. Then:

`... update recover-runtime --directory <generation> --expect <planSHA> --confirmation <ACTIVEeventSHA> --trust-confirmation <pendingTrustWriterSHA>`

Recovery refuses stale digest, live/unknown process, mismatched parent, changed root/release/schema/slot and pending authorization transaction. It preserves a digest-bound recovery intent before releasing confirmed dead trust lock, rechecks installed bytes/schema and only then removes the matching update lock. Interrupted recovery can continue from same immutable intent after trust lock release. No data cleanup, history change, automatic start or lowered sequence. Normal startup separately checks committed stores; corrupt evidence stays blocked. A new separately authorized forward software release is needed if code/schema is incompatible.

Unsupported OS managed isolation fails. Linux Docker sh/dd probes establish bounded kernel cgroup/tmpfs behavior only; no AERIS Linux deployment claim. SDK/Android/HeraHub, full host disk fill, physical power loss, process-tree/CPU hard isolation, target service ownership, official signer custody and independent security review remain NOT_CHECKED.
