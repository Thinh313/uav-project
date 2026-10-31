# Native98 delivery diagnosis

APK03 failure before ARM: journal JS_TRANSPORT_FAILURE98 reports RX_DELIVERY lag1959ms versus1500ms. Root cause remains unknown; no frame loss or CRC failure inferred. Keep guard and all raw.

Isolated development04: replace per-byte String.format hex encoder by fixed two-char lookup; exact legacy reference/roundtrip across all byte values and seeded unseen buffers. Add monotonic timing fields on the same delivered RX envelope (receipt, WAL done, apply done, state done, encoded), no additional hot-path journal fsync. Raw still durable before consumers and delivery, TX still fsync before socket. Existing pending/authority/freshness bounds unchanged. Timing fields are diagnostics, not hardware attestation. New APK/dev source version preserved separately; Java delta limited to helper and RX instrumentation.

This is targeted repair inside authorized acceptance scope, not a flight architecture or operational target change. No claim hex was the root cause until measured evidence.
