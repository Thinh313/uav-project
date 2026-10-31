# ADR111 — Native evidence boundaries under link loss/reboot

Accepted for isolated NATIVE96 engineering work, 18/10/2026.

Reuse Native95 direct Java transport/wire gate and in-APK mission engine. Never reconnect, grant or resume automatically. A locally closed socket does not establish safe aircraft state. Interrupted review uses unknown aircraft outcome and cannot be accepted; a separate passive observer qualifies simulator failsafe externally.

Export only closed native raw generations. Build a bounded immutable ZIP with original raw bytes, byte-exact SHA and chain-prefix/tail metadata; optional review remains a claim cross-checked by receiver. Do not trim/repair torn source. SAF write outcome and provider readback use durable FileOps; ambiguous operations survive restart as UNKNOWN. A receiver receipt binds manifest/package/receiver/nonce and is integrity evidence only, not a signature or flight completion.

Native95 UI diagnostics hit persistent ~2MiB saturation and a character/UTF-8 mismatch. Native96 writes byte-bounded per-Activity generations with a total count/size reserve. No evidence is automatically deleted. UI reports remain self-observation; raw flight evidence and fresh screenshots are separate.

Actual admission uses owned emulator/AP container identities and fixed simulator endpoints. Host only runs AP/physics and passive observer. AP reboot gate is exercised on ground; it does not simulate an airborne controller reboot safely.
