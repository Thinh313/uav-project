# ROTATE70 — controlled JOURNAL68 writer rotation

16/10/2026 · [Local mock UI](http://127.0.0.1:8825/). New root-owned active JOURNAL68 stores; original68/ARCHIVE69/source/candidate/SOT/ENDURE are read-only and not migrated.

Run from aeris. First creation only: `node native/rotate70/server.mjs --initialize`. Preview `.local/rotate70/preview01` already exists; use `node native/rotate70/server.mjs` for subsequent starts. No SDK/install/build required. SIGTERM/SIGINT close the current mock run cleanly. Do not delete locks, modify receipts or initialize existing roots. Server listens loopback8825; no operational transport or flight commands.

Operator flow:

1. Optionally connect payload mock, claim camera and capture mock. Capture/ACK are synthetic: no actual image/exposure proof.
2. View rotation plan. It binds current root boot, committed selection/control head and all generation bytes. Read the source/baseline, acknowledge that current grants and pending handover will be dropped, then type the exact displayed phrase. Plan expires after60 seconds and is one-use; any current-WAL mutation makes it stale.
3. Root serializes admission, fsyncs BEGIN, closes current session (CLOSE/OUTCOME/SEAL), verifies catalog/frames/semantic replay, then records FREEZE. It creates a cold sealed seed store, validates it, fsyncs STAGE and commits SELECT. Only the committed target receives a new cold writer with fresh boot, no session/grants/pending/transactions.
4. View rollback if there is a prior baseline or a pending rotation. Explicit confirmation creates a new physical writer using previous baseline lineage. It never reopens a frozen old writer, rewinds evidence, undoes a camera command, downgrades software/schema or restores rights. Old and failed candidate directories remain.

Control receipts use exclusive canonical files, SHA chain and file/directory fsync, bounded32KiB/record and512KiB/control ledger. Root uses existing OS flock bridge; root lock loss fences/revokes in-memory grants and releases its current store. Every generation also uses unchanged JOURNAL68 writer lock and WAL. No cleanup endpoint, automatic retry, tail repair, pointer rewrite/rename or auto rollback.

Restart before SELECT with pending intent stays HOLD. Nothing is automatically selected or replayed into a live engine; valid pending evidence needs a new explicit rollback plan. Restart after a valid SELECT opens that selection cold if source/schema/seed/frozen data pass gates. Corrupt/unknown/missing/aliased data or control stays HOLD; do not bypass with reinitialization. Failed old SEAL is not reported clean. An explicit rollback can preserve a verified uncertain prefix, clearly labeled; it never executes pending commands. Invalid semantic data requires investigation rather than a forced rollback.

Quota defaults32MiB/root, at most32 generation directories,8MiB logical reservation before transitions/activation, plus control headroom. Physical floor is20GiB+32MiB+required reserve. All retained stores count; full quota blocks instead of evicting. Export is allowed only for frozen generations, using ARCHIVE69 package/receiver verification. It does not remove root data or change69 quota. Live retention/tombstones need a separate design gate because root manifests reference every frozen generation.

The local mock HTTP driver advances logical event time by1ms per explicit action; no background heartbeats are generated and no timing/real-link qualification is claimed. Core policy itself is unchanged. UI buttons are diagnostic mock controls, not hardware authentication. Administrative API tokens and plan tickets are process-local and not persisted. Prior writer boot is fenced on mock actions.

Tests, using new run names without overwriting evidence:

```sh
R70_TEST_RUN=next01 node --test native/rotate70/tests.mjs
R70_CORPUS_RUN=next01 node native/rotate70/corpus-qa.mjs
R70_CRASH_RUN=next01 node native/rotate70/crash-qa.mjs
R70_HTTP_RUN=next01 node native/rotate70/http-qa.mjs
```

`verify-control.py <root...> --output <new-receipt.json>` là bộ kiểm Python chỉ đọc cho canonical/SHA/selection bindings và frozen/seed byte anchors, có đối chiếu source pins68. Nó không thay semantic replay, chữ ký hay kiểm định viên độc lập. Receipt output phải mới, không ghi đè.

HTTP QA requires8825 free: stop only your own ROTATE70 preview cleanly first; keep originals/ENDURE/other previews intact. Cleanup is never called; fixture confirmations are explicit. Small fixture stores and receipts are intentional evidence, not whole-project copies. Task budget48MiB; check disk before new work.

Scope: host mock/replay; fsync/SIGKILL are not physical powercut/F_FULLFSYNC/Android qualification. Same pinned JOURNAL68 source/schema throughout, no schema/software rollback proved. Internal hash consistency is not a signature, trusted identity or external anti-rollback anchor. No production operator auth, hardware flight, SDK/HeraHub or endurance acceptance is implied.
