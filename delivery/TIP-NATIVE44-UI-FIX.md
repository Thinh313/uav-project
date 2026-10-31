# NATIVE44 UI closure · 2026-10-14

Authorized: user requests disk check, checkbox fix and final native44 UI checks above 20 GiB. Existing TIP-NATIVE44 applies. Single agent sequential specification/build/verify, no independent-review claim. Source/candidate/SOT/trust/ENDURE and earlier receipts unchanged; no APK, signature, emulator, SITL or install. New test stores are bounded, owned and removed after retaining evidence.

AC-UI1: Home/datum remain selected while asynchronous save is pending, including periodic renders; controls remain disabled, start remains unavailable until exact commit. Success derives authority only from committed model. Failure rolls back display and blocks storage/start, without retry or deleted evidence.
AC-UI2: Actual Chromium + existing host JVM journey survey → preflight → Fly mock → review, restart, ACK≠execution, export/recipient replay, lost reply, 1280/1024/360 layout, WebCrypto and no external requests.
AC-UI3: model regressions and old readonly firmware/parity source checks, protected13889 and ENDURE5051 unchanged, disk≥20GiB, namespace<32MiB, owned writers closed, scratch removed, fingerprints/completion. Android/Hera NOT_CHECKED.

Root cause observed in browser-failure4: onchange captures selection, then busy render replaces checkbox from pre-commit model before writer returns. Fix is display-only pending selection with aria-busy, discarded at completion; it never grants readiness. Keep previous failures intact. Use append-only browser5 evidence. Existing authorization covers implementation and host QA; no extra approval.

Refinement after browser5: pending checkbox passed, start safely refused due SOURCE_STALE/MOCK_START_INTERRUPTED_AFTER_SAVE. UI timer paused mock RX while storage busy. Keep guard thresholds and ticket lifespan unchanged; allow mock producer ticks while writer busy until volatile grant is handed off, and inspect return assesses completion clock supplied by UI (snapshot still captures original clock). No firmware logic change. Preserve browser5 failure/store. Final UI evidence browser6 or later.
