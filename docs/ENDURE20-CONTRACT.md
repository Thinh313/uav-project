# ENDURE20 · Progress-bound bulk transfers and 24-hour acceptance

Owner request 2026-10-13 authorizes this local hardware-free increment. v1.15.1 / candidate sequence9, selected7 until real acceptance. Single agent separates Contractor/Builder/Verify; no independent audit.

| REQ | Acceptance |
|---|---|
| E20-01 | Server-derived bulkRead1/bulkWrite1 separate from observe4/control1/read2/write1/static8; zero queue, explicit429, no automatic POST/flight repetition. |
| E20-02 | Bulk first/progress window60s: at least64KiB server-observed byte advancement per window resets deadline;6h absolute cap. All other requests retain30s. Node whole-body requestTimeout disabled in favor of owned deadlines;5s headers/keepalive remain. |
| E20-03 | Input progress counted only as application consumes source chunks, output after successful Node write callback; neither is receiver verification or durable commit. Small drips cannot renew windows. Joint handler/response release and storage finally/reserve retained. |
| E20-04 | Actual >30s slow export/upload, paused output timeout, stalled input timeout, overload before IO, explicit checkpoint resume and tamper rejection preserve sealed record/receipt; incomplete data never published. |
| E20-05 | Versioned policy/UI with seven rows, unknown/invalid/offline clearing and six viewport checks. Signed payload and pinned external bootstrap. |
| E20-06 | Actual continuous24h managed read-only mixed-load canary: ≥86400000ms monotonic AND wall clock, no progress gap>90s, heartbeat/RSS/storage admission, bounded client memory/logs and expected overload; no fabricated acceleration or resumed-duration stitching. |
| E20-07 | Pre/post664 source/copied files,156 baseline records and27 receiver package digests. Commit8 only after source/payload/canary/soak verification. Failed or incomplete run leaves7 selected, records failure, no auto restart/reselection. |
| E20-08 | Durable RUNNING_NOT_FINAL / FAILED / PASSED status, chained fsynced raw logs, intent-only SOT, report/fingerprints. Monitor ongoing run and finalize without counting checkpoints as PASS. |

Decisions: existing authorization covers design and local signed engineering candidate; no external ship gate. Three roles are sequential phases, no delegation. Machine awake assertion scoped to one caffeinate-bound test process. Operator/OS interruption terminates or invalidates the continuous campaign; restart begins a NEW explicit run, never joins samples. 24h PASS remains NOT_CHECKED until exact final gates. Existing layouts/schema/frame/Home/camera/acceptance and memory18/Seatbelt stay intact. This is host engineering, not HeraHub/native/HIL/flight/device/physical-power validation.

Primary references: [Node HTTP](https://nodejs.org/api/http.html) documents whole-body requestTimeout and headersTimeout; [Node streams](https://nodejs.org/api/stream.html) documents backpressure/pipeline error cleanup. Server write callback means Node transport advancement, not receiver commit.

ENDURE20 revision2: signed8/generation01 and first interrupted interval preserved in evidence/endure20-attempt01. Early response to any request carrying body framing disables keepalive (Connection:close), including host/path/auth/canary/overload rejection. This prevents post-response body drips after handler lease is legitimately released. New signed9/generation02 starts a fresh continuous24h; prior interval is not stitched.

Current campaign generation03 reuses exact signed9 bytes/bootstrap after generation02 pre-soak replay encountered expected singleton-pool429. Failed generation02 and receipts retained in evidence/endure20-attempt02. Package-replay controller waits and retries admission for GET only (bounded60 attempts/1s); never repeats POST. Both failed intervals excluded from real24h timing.

Current generation04 reuses signed9 after generation03 was stopped to correct external test-driver intentional AbortError cleanup classification. A real deliberate disconnect is required before long workers start; arbitrary/global errors still fail. Earlier intervals preserved in evidence/endure20-attempt01/02/03 and excluded from accepted duration.
