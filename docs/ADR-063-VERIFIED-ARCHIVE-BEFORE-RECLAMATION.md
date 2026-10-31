# ADR063 · retained archive + independently read-back receiver before hot cleanup

Accepted for HERASTORE50 host/mock15/10/2026. Keep49 source and live store unchanged;50 wraps49 in its own root.

Separate hot49 quota from cold retained evidence and host free space. Cold copies stay on the host in this scope, so hot quota reclamation is not a host-disk savings claim. Group cleanup includes all attributable journals; active workspace, published selection-chain events, SWITCH_PENDING and ambiguous orphan associations are ineligible. Retained-aborted switches may be archived independently; immutable published chain stays intact.

Use a streaming line-framed archive with a canonical typed manifest,256KiB chunks, per-file/chunk hashes and externally supplied whole-file SHA for receiver verification. Bound64MiB logical/96MiB package/4096files. Receiver reconstructs only allowlisted relative unit paths in a new directory, verifies readback, and runs existing49/47 replay where applicable. Partial/corrupt source evidence is retained as raw and labelled quarantined; no execution/physical authority is inferred.

Cleanup requires server-owned export/import receipts, current raw archive and receiver validation, exact source and selection binding, typed unit ID and explicit acknowledgement. Move the authorized hot roots into CLEANUP_PENDING/trash before unlinking. An immutable authorization and per-file delete intent precede every unlink; results/audit remain. Count pending trash as hot occupancy until a completed receipt. A crash cannot automatically resume or free quota. Explicit continuation rechecks retained copies; rollback is available before any delete intent. Missing data without a bound delete intent is an error, not evidence of successful cleanup. No product rm-rf or background cleanup.

Cold/audit capacity has its own cap and reserve. Unknown outcome stops; no automated POST retry, flight/MCU commands, trust selection or signing. OS/physical powerloss, malicious external writer and actual off-host storage are outside host acceptance. Every hash here is integrity, not producer authentication.
