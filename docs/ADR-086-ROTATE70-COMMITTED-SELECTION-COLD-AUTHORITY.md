# ADR-086 — committed selection with cold authority

Accepted 16/10/2026 for isolated mock adapter. Preserve source/candidate/JOURNAL68/ARCHIVE69/ENDURE. JOURNAL68 append-only catalog is reused unchanged within ROTATE70-owned stores.

A root OS lock and canonical hash-chained exclusive control receipts encode BEGIN → FREEZE old store → STAGE validated cold seed → SELECT. SELECT is the durable commit point, not metadata plan or elapsed time. New live engine has fresh boot and no restored authority. Closed stores retain full byte manifest + semantic inspection; selection verifies frozen data and seed again. Startup with pending BEGIN stays HOLD. Startup after valid SELECT opens only its committed target, cold; invalid ledger/data stays HOLD. File/directory fsync and process crash are host evidence only, not hardware powercut certification.

Rollback uses explicit current-byte/ledger-bound one-use confirmation and creates a fresh writer with previous known baseline lineage. It retains all committed history and any abandoned partial candidate. No command undo, previous token/lease/pending restoration, automatic retry/cleanup or schema/software downgrade. Source/schema compatibility stays pinned; unsupported data requires a separate migration gate. Disk reservations and retained generations are counted; no false claim of reclaimed storage.
