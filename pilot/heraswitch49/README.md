# HERASWITCH49 · retained recovery / controlled mock workspace handover

Run from project root with≥20GiB plus reserve: `node pilot/heraswitch49/server.mjs`, localhost8803. Persistent product root `.local/heraswitch49/operator`. No SDK/install/build/APK/signature/SITL/emulator. Existing46–48 previews and stores are separate and remain unchanged. Reuses frozen48 parsing/staging,47 durable model and44 host JVM JAR; no physical transport or Fly integration.

## Recover an incomplete generation

Load a static actual48 process-crash PENDING fixture, an exported49 tree, or an incomplete49 group. A tree captures exact bytes/relative paths/empty directories, with16MiB logical/24MiB encoded bounds. Compare optional expectedSHA from a separate source. Choose an archive and candidate explicitly, review and check retention confirmation. No default candidate.

Recovery retains the complete source tree in a fresh group; the original is not changed or deleted. Rebuild only the selected saved draft, via validated original archive and48 plan, into an immutable48 seed plus a separate49 mutable runtime journal. Partial old seed bytes and pending intents are retained, never treated as executed/applied authority. Even an original ready.json left before directory publication does not automatically activate. If no valid archive remains, status is RETAIN_ONLY_NO_USABLE_ARCHIVE; software cannot reconstruct missing evidence. Export/retain it and obtain an independently preserved archive.

Group ready pins its tree, recovery plan, immutable48 seed and workspace identity/bootstrap. Every active journal must replay semantically, match the original bootstrap prefix and descend from its pinned raw record. Orphans, pending head, broken hashes or unknown storage block use. A ready file truncated during writing stays incomplete; the group's full tree can be inspected for a new explicit recovery. A complete ready group with a lost response is discovered by read-only reconcile, not recreated automatically.

## Switch workspace

Select a ready workspace and review a separate switch plan. The plan binds current selection token and both exact journal heads/digests/identities. It states the historical source state, including unfinished calibration. Confirm interruption of the source session and fresh disconnected target. The old draft/history remains in its own journal; no calibration, preview or input authority carries across.

The owner writes SWITCH_PENDING/intent.json then a commit describing a newly created disconnected target RAMsession. Validate source/target again before atomically publishing the whole directory into switches/s-UUID. This makes one selection-chain event; it is not a caller-ACK or command execution assertion. Directory sync/readback is host evidence, not device power-loss certification. Concurrent owner calls, stale plans, stale workspace/session/UI revision and selection forks are refused.

Every mock action supplies selectionToken +workspaceId +session +revision. This prevents a stale tab command reaching another workspace even when revisions happen to match. Available actions are logical mock diagnostics/calibration and saved-draft editing only. The UI requires a fresh mock handshake before editing. A saveDraft is not physical apply/SAVE/readback.

Restart preserves selected workspace identity, all committed history and saved draft. It opens a new disconnected RAMsession without appending until the next explicit action. Old logical evidence may say CALIBRATING; it remains history and does not resume. Read-only GET does not send commands. Explicit **Đọc lại và mở phiên an toàn** also discards uncertain volatile session authority without replaying actions.

## Resolve an interrupted switch

SWITCH_PENDING blocks new generations, switches and actions. Export its raw tree, then explicitly select one of:

- PUBLISH_VERIFIED: only when complete intent/commit/selection/source/target still match; start a fresh disconnected target and publish as switches/r-UUID. This is a different directory class requiring a digest-bound resolution receipt, so deleting a receipt cannot make recovered publication look normal.
- RETAIN_ABORTED: append a resolution receipt and move the complete attempt into retained-switches. The previous selection remains; its session is freshly disconnected.

Plans bind complete tree SHA and current selection. Old files are never overwritten or removed. Partial resolution files remain in the tree; a new explicit plan must bind them before another attempt. No auto retry/resume, LOCK removal or silent HEAD choice. On every selection read, recovered publication must contain a valid resolution receipt covering the exact prior tree; corrupt/missing evidence fails closed. Unkeyed hashes do not authenticate the producer or certify resistance to a malicious external filesystem owner.

## Quota / limits

Aggregate64MiB allocated-byte budget including incomplete groups/workspaces/attempts;4 groups including failed originals;16 switch attempts including retained/unfinished ones. Existing47 journal16MiB/capsule256KiB/8epochs limits remain. Admission reserves projected growth plus16MiB while preserving host20GiB free floor. A recovery consumes a new group slot, not a reclaimed slot. Per-write and per-action admission failures retain all bytes; no delete endpoint or automated cleanup. If full, export/verify retention and arrange separately authorized cleanup. Download alone does not prove off-host retention.

Single owner per root. Atomic SWITCH_PENDING creation and JVM CAS/OS lock protect normal host writes; snapshots comparing two inventories are not live OS writer leases. Do not run competing external owners or modify the store. Production/Android/HeraHub/real MCU, malicious host writer, sudden host powerloss and full-volume ENOSPC remain NOT_CHECKED (boundary errors injected instead of filling disk).

See delivery/COMPLETION-HERASWITCH49.md for final accepted receipt IDs/counts, correction history, resource/preservation checks and owned scratch cleanup. Raw negative-test stores are evidence of deliberately injected faults, not healthy operator stores. No ENDURE restart, historical rewrite, new24h acceptance or new software signature.
