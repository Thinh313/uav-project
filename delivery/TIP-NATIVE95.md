# NATIVE95 — Android direct MAVLink / owned ArduPilot SITL

18/10/2026. User authorized tiếp tục ưu tiên transport native; development signing/emulator/ADB scope inherited. SPEC→BUILD→VERIFY by one agent, no claim of independent human/team review.

- R95-1: no HTTP GCS/control bridge. Java-owned raw TCP from owned emulator to fixed 10.0.2.2:5907, direct ArduPilot serial0. No arbitrary endpoints or hardware access.
- R95-2: port existing qualified mission/preflight/wire algorithms into APK with documented adaptations; unchanged model92 and offline94 compiler. Mock differential wire/semantic, stale/CRC/foreign target/reboot/lifecycle/expired authority tests before SITL.
- R95-3: native bounded raw journal fsync before TX and RX delivery, generation/clock/queue/storage guards; no reconnect/retry/resume/grant restoration. Java outbound whitelist and compiled-item binding independent of UI. Read-only connection before explicit scoped grant.
- R95-4: actual APK/emulator discovery pinned4.7.1 + typed parameters/read-only preflight, then explicit grant/upload/readback/Home after arm/AUTO/ground-disarm/review only after read-only gates. ACK alone never execution. Host only runs AP simulator and passive observer, sends no flight/GCS commands.
- R95-5: Android review/persistence/restart; raw export/pull and receiver replay in separate host implementation. Distinguish native receipt clock from host observer clock; do not compare them as same clock. Unknown outcome is retained, no false PASS.
- R95-6: preserve all prior source/candidate/ENDURE and receipts through94; floor20GiB; cleanup only owned transient build/runtime. Do not integrate frozen candidate, production-sign, or claim Hera hardware readiness.

Mandatory unrun checks are NOT_CHECKED. If read-only qualification fails, do not unlock control. Simulation host identity supplied as an engineering launch assertion, not authenticated physical aircraft identity. ArduPilot internal quad is not a calibrated Hera physics model. Native TCP scope first; no SDK/HeraHub required.
