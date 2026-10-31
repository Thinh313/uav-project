# ADR110 — move control stack into APK; keep simulator host passive

18/10/2026, engineering accepted.

Keep shared model92/offline94 compiler and cockpit. Port the existing SitlLink/MissionLink/preflight43/full dialect algorithms via explicit adapters for EventEmitter, UUID, hash, timers, raw socket and byte encoding. Do not use an HTTP server or a host-side GCS controller. Java socket connects only from the owned Android emulator to the fixed published ArduPilot TCP serial0 endpoint; launch context is explicit and volatile.

Native transport owns socket lifecycle, bounded durable raw journal, per-generation callbacks and independent outbound wire whitelist/target/compiled mission binding. Foreground loss closes socket and revokes native grant. A native successful write receipt is not an ACK or execution. Browser mission engine retains independent preflight/session/boot/parameter/Home/readback/execution guards and emits review only after observed terminal state.

A second read-only ArduPilot serial channel provides independent passive host observation. It must transmit zero bytes and never maintain GCS failsafe heartbeat. Both streams have separate clocks; receiver validates each in its own time domain. Native launch metadata is not hardware authentication. No unfreeze or promotion of candidate/ENDURE follows from this experiment.
