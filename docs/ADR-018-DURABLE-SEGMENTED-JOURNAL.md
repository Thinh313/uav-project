# ADR-018 · bounded durable recorder

Accepted within owner request 2026-10-12. Appends acknowledge only after fsync; first files and atomic no-overwrite seal also sync directory. Record-v3 binds exact original spool and segment lineage; v1/v2 hashes remain historical. Capacity includes conservative reserve for closure/export; no automatic deletion. Queue overload latches a recorder gap rather than allowing later terminal observations to hide loss.

Restart reads bounded complete verified prefix, preserves raw bytes and publishes a conservative derivative with explicit recovery metadata. Existing closed/valid evidence is never rewritten. Pending valid envelopes may be published after validation; ambiguous stages remain visible. PID/unique-token exclusive writer refuses a concurrent owner and replaces only a dead writer lock. Local process-kill and replay tests do not certify physical power-loss/HeraHub.
