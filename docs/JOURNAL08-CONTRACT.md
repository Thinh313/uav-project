# JOURNAL08 · durable bounded execution journal

Owner authorizes long-duration recording, storage limits and recovery after restart without SDK/HeraHub. Single agent Contractor→Builder→Verify; no independent audit claim. No installed hardware or physical power-loss assurance.

| REQ / AC | Acceptance |
|---|---|
| J08-1 | Every acknowledged append flushes data to the host filesystem. Seal publishes without overwriting, with directory sync; record-v3 binds exact original spool hash/bytes. Legacy v1/v2 remain readable. |
| J08-2 | Long attempts roll to bounded linked segments before row/record limits. Logical attempt, previous record/hash, source/session/profile remain bound. Each incomplete/segmented record remains UNKNOWN; no unobserved whole-mission completion. |
| J08-3 | Disk allowance reserves space for gap/closure/export. Queue bounded; saturation/storage/I/O faults latch degradation, stop recording the affected attempt and retain durable prefix. No automatic evidence deletion. New upload/ARM/AUTO blocked when archive cannot record; HOLD/RTL/read-only operations retain their existing checks. |
| J08-4 | Actual child process SIGKILL/restart recovers open spool conservatively; unchanged original bytes kept. Torn UTF-8 tail and corrupt middle preserve raw bytes, recover verified prefix with visible gap or CORRUPT. A durable terminal close before kill may preserve its proven outcome. |
| J08-5 | Pending seal, repeated restart and missing/damaged/spool-swapped data cannot overwrite an existing record or fabricate saved/completed evidence. Exclusive writer lock prevents a second writer closing a live attempt. Dead child locks recover; live locks refuse mutation. |
| J08-6 | Paginated inventory exposes old records and unresolved spools, storage/queue/recovery status. Review/import/export retains v3 integrity and surfaces segment/gap scope. Offline review retains historical status, zero flight writes. |
| J08-7 | Measured ≥600 seconds real wall-clock disarmed loopback SITL recording at 1 Hz, explicit profile rereads, clean segments/restart; separate synthetic replay covers 24 h logical time at 1 Hz. Replay is not 24 h hardware/endurance measurement. RSS/queue/disk observations and counts retained. |
| J08-8 | Existing completed/interrupted mission correctness and historic BENCH06/RECOVERY07 remain valid; actual bounded SITL flight regression, unit/API/fault injections, browser/control and SOT/source-byte checks pass. |

Host fsync/SIGKILL tests cover the documented local filesystem boundary, not Android/HeraHub sudden power removal, drive firmware or signed origin authenticity. Writes not acknowledged as durable at kill can be incomplete; no silent promotion. Capacity faults require explicit investigation/export/storage provisioning; no automatic delete/resume/parameter changes. Long-duration pilot remains disarmed. Scope uses fixed normal ArduCopter4.7.1 loopback speedup5 and exact BENCH06 requests/profile1.0.0.
