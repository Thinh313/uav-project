# TIP-FLIGHT01 · independent GCS / ArduPilot integration

Owner authorization: 2026-10-12 user excludes RAGAS application source, requests an independent build for A/B testing with AI-native development support and implementation of the next step. Supersedes RAGAS source-reuse prerequisite. Single agent switches Contractor → Builder → Verify; no independent review claim.

Deliverable: a loopback-only ArduPilot SITL integration alongside the existing workbench. Pure mission compiler, MAVLink framing/telemetry, bounded mission transactions with readback, observed command outcomes, connected UI and reproducible simulator/QA receipts. No physical aircraft endpoints. AI-native here means inspectable contracts, deterministic core and machine-executable evaluation seams; no deployed LLM/autonomous command authority is claimed.

AC-01 Owner intent in canonical SOT, regenerated/reviewed registry, current baseline/check/bites/gate.
AC-02 Independent architecture/roadmap and A/B protocol; RAGAS reuse gate removed.
AC-03 Official MAVLink definitions captured/pinned; CRC/framing rejects corruption, unsupported/signature frames, respects streaming and identities.
AC-04 Compiler rejects unresolved datums; explicit flat-world SITL manifest required; camera start/stop per transect, speed/takeoff/RTL retained; canonical readback tolerances documented.
AC-05 Connect real version-recorded ArduPilot SITL; heartbeat/position/health freshness; disconnect clears session/transaction readiness.
AC-06 Mission upload handles requests/duplicates, rejection, timeout and download/readback; accepted ACK alone never permits execution.
AC-07 Simulator command acceptance and post-send observed state kept distinct; no retry of ambiguous actuation; busy/unknown timeout disallows another ambiguous command.
AC-08 UI explicitly separates rehearsal and ArduPilot SITL; no stale/synthetic telemetry shown as connected measurement; journal export.
AC-09 Actual SITL upload/readback/start/progress/RTL or completion trace plus negative-path/unit/browser regression receipts.
AC-10 Repeatable A/B scenario packet (same version/config/mission), measured AERIS result only; RAGAS run NOT_CHECKED until supplied/operator executed.

Scope limit: local TCP simulator adapter is a dev adapter, not final Android SDK/APK. No device certificates, QGC complex-item parity, basemap/DEM, video/hardware input, real camera imaging or physical flight. Survey flat reference cannot silently become an operational altitude. Build runtime in current project, ≤20GB stop rule, fixed Docker tag, remove only task-owned container and prune dangling images after use; no volumes/other containers touched.
