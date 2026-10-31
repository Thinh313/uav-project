# ADR044 — repeated pacing without changing the pacer

Measure the exact INSTRUMENT01 experimental ARM64 v2 build, not recompile or adjust speedup/debt/model. Repeated balanced workloads separate descriptive host-load response from one-run optimistic conclusions. All nine fly the same offset/gust7m compiled plan with existing UI at1280×800; CPU workers0/2/6 are an explicit injection, monitored rather than presumed load. No affinity or hard-real-time claim on macOS/Docker.

Bounded fixed trace storage and full raw/model oracle remain mandatory. Cap saturation discards time debt, not physics frames, and must be reported as loss of wall-time catch-up, not hidden speedup or uninterrupted1×. Jitter distributions and short-window RTF remain visible even if whole-run mean≥1.

Ground-only process suspension tests bracket500ms. Resume is a deliberate test injection on the same owned PID, not an allowed automatic recovery path. The3200ms probe additionally tests whether backend/control stale semantics detect process suspension; any gap is reported without silently changing the frozen implementation. Safety assertions derive actual state/command records, not ACK.

Keep protected baseline and prior experiment receipts. Single-agent sequential verification, no production or ENDURE acceptance claim. Repeat runs provide descriptive n=3 summaries only; longer/other-platform or calibration tests remain separate gates.
