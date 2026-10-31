# ADR076 — unavailable telemetry and supervisor lifetime

b2 connected but process exited on HOME_POSITION.q[0..3]=NaN in RX_DECODED journal serialization. Raw RX record867 was fsynced first; no upload/arm occurred. Original raw, process-exit evidence and b2 orphan closure are retained. Initial serial ASCII banner also requires bounded explicit handling in independent raw replay; no midstream noise is normalized away.

v3 canonical observation journal records nonfinite IEEE values as tagged {$number:NaN/Infinity/-Infinity} while preserving exact raw bytes; control/preflight consumes original typed values and keeps unknown/invalid checks. No null conversion or real-image claim. Receive/heartbeat boundaries close the link on genuine writer failure without killing the HTTP service. Capture fd closes even if final fsync fails.

Supervisor is detached into its own process group and detects parent loss before closing its exact owned container, so app exit need not orphan Docker. Mock parent-loss proves OS/process boundary only; full automatic Docker/app-crash recovery remains NOT_CHECKED until fault-tested.

Amend the self-imposed two-attempt engineering cap to three distinct retained attempts, because b1/b2 ended before any mission upload/arm and v3 fixes a newly observed telemetry contract error. This is a fresh candidate validation run, not retry/resume of either failed campaign. Keep the same21.25GiB admission,20GiB floor,256MiB forecast,64MiB AP-state/16MiB raw quotas and240s deadline. No change to frozen app/candidate/ENDURE, mission coordinates, profile, speedup or signing.
