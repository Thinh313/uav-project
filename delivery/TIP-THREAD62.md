# THREAD62 — per-thread host observation / filesystem attribution

Authorized: mock then at most two bounded ArduPilot 4.7.1 SITL captures with the existing 1920×1080 UI. Single agent separates specify/build/verify roles; no independent human review claim.

- REQ1: Read exact backend main thread via Darwin proc_pidinfo(PROC_PIDTHREADID64INFO=15); capture target PID, unique native thread ID, observer PID, SDK ABI pins. External child avoids target Python GIL sampling dependence. Sample every5ms, bounded32010rows; missed deadlines explicit, no synthetic samples. CPU counters in ns with kernel microsecond quantization. Return-size/errors fail closed.
- REQ2: Correlate query brackets with full syscall intervals and admitted frame spans, including CPU and wall. Sample counts are not durations. RUNNING includes runnable and does not identify exact runqueue delay; WAITING/UNINTERRUPTIBLE does not prove filesystem cause. No subtracting sampled CPU across clocks as exact one-way transport.
- REQ3: Mock identity, blocking/CPU states, observer lifetime, bounds, syscall faults, original oracle and fsync-before-sensor. Actual physics remains Darwin byte-exact reference, rate1200 speedup1/cap500ms; no drop, burst sensor replay or implicit tuning.
- REQ4: Both actual attempts use AP trace tmpfs and physical WAL; same source. Full UI trace saved as opaque JSON chunks500rows with SHA/count. No causal A/B claim against previous observer versions. Stable1× requires whole RTF≥1, every complete5s window≥1, zero cap clipping, conservation and raw original oracle.
- REQ5: Fresh admission22.5GiB, floor20GiB, retained quota2.25GiB/forecast1GiB per attempt; interrupt headroom20GiB+768MiB. No evidence deletion. Max two attempt reservations; no HTTP mutation retry. Close AP writer, verify export before owned container stops; final preservation verifies cumulative frozen hashes.

Existing ENDURE/source/candidate/trust/SOT remain read-only. Outputs only pilot/thread62, evidence/thread62, this TIP, ADR073 and completion report. Unrun checks NOT_CHECKED; diagnostics can pass while stable1× remains partial.
