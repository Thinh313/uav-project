# RESUME11 · durable handoff checkpoints

Owner-authorized hardware-free increment. Single-agent Contractor → Builder → Verify. Legacy v2 wire bytes and v1 recipient receipts remain compatible. Hash proves bytes, not sender identity or physical capture.

| REQ/AC | Gate |
|---|---|
| R11-1 | Immutable 1 MiB wire chunks, fsync/no-overwrite checkpoints chained to exact raw header, manifest/record digest and total length. Only checkpoint-referenced bytes are acknowledged. Unacknowledged pending/orphan bytes retained and quota-counted. |
| R11-2 | Explicit continuation after connection loss/process restart revalidates checkpoint chain and every retained byte, exact offset and prefix SHA. Stale/duplicate/mismatched/corrupt cursors refused; exclusive writer. |
| R11-3 | Complete receiver replays bounded chunks, validates header, each file/container and whole-package SHA/footer/EOF before atomic receipt. Partial/corrupt stages never VERIFIED or downloadable as accepted packages. No second full dataset copy. |
| R11-4 | Sender suffix export verifies skipped prefix SHA while scanning unchanged source; preserves deterministic wire/footer and backpressure. Local file/CLI resumes from receiver checkpoint with exact prefix match. |
| R11-5 | UI exposes real durable offset and explicit continue-file action across refresh/restart. No file-sized JS buffers; pending checkpoint never presented as receipt. Offline state cannot authorize acceptance. |
| R11-6 | Actual transport interruption and process-kill/restart, ≥512 MiB synthetic resume/roundtrip, adversarial integrity/EOF/quota/cursor tests, browser/control and legacy tests. Original closed SITL record stays immutable, zero flight writes. |
| R11-7 | Current source/evidence/SOT gates, scoped report and cleanup. Missing SDK/device/power-loss/remote authentication remain NOT_CHECKED. |

Storage: sender 8 GiB; receiver 12 GiB including chunks, metadata and failed stages; 20 GiB host free-space reserve. Existing 2 GiB/file, 8 GiB/dataset, 512-file limits apply. 1 MiB checkpoint boundary (last chunk may be smaller only at known total). Chunk writes are durable before checkpoint publication; crash between them leaves an unacknowledged orphan, never reused. Metadata/pending files are retained, no automatic deletion. Receiver chunks are canonical accepted wire storage, individual files are streamed as ranges after full verification, avoiding dataset duplication. Restart/host fsync is tested; physical power failure is not. Transfer UI remains local host, not a deployed remote security protocol. SHA/chains are unsigned.
