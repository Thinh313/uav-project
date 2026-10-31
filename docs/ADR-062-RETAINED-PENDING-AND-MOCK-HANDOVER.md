# ADR062 · preserve incomplete generations; switch by explicit transaction

Accepted for isolated HERASWITCH49 host/mock15/10/2026.

Keep48 immutable. New49 owns groups/workspaces/switches under one local root. Reuse48 validation/staging and47 durable logical model/JVM journal unchanged. A failed generation remains evidence in its original location; recovery captures an exact tree and creates a new group, not an in-place HEAD promotion or retry. Invalid partial seed bytes are retained but never used as authority; recovery selects a verified original archive explicitly.

Group-ready evidence pins immutable48 seed and separate workspace identity/bootstrap. Only the latter journal may receive mock actions. Handover binds selection-chain token and both current journal heads. A single owner serializes mutations; an atomic SWITCH_PENDING directory excludes concurrent publication. Intent/commit are immutable files. Publishing the directory creates one selection-chain event; reads derive a unique chain, refusing forks. The publication head is not a caller-ACK/execution claim.

While SWITCH_PENDING exists, actions/new generations/switches block. Explicit recovery compares the complete tree SHA and current selection. A valid commit can be published after rechecking both journals; otherwise retain/abort by moving the complete attempt into retained-switches with an append-only resolution receipt. Partial resolution files stay in the tree and require a new explicit digest-bound plan. No automatic replay, retry, lock removal or evidence deletion. Restart reopens the selected journal as historical evidence and creates a fresh disconnected RAMsession; no calibration/preview/input authority restores.

Global quotas include all incomplete groups/workspaces/attempts and retained receipts. New recovery consumes a group slot; it does not reclaim one. Failed switch attempts consume the16-attempt budget even when retained. Single-owner/normal-host assumptions are explicit; this is not an adversarial filesystem or physical-powerloss certification. Existing46–48 preview processes remain untouched.

Recovered publication uses switches/r-UUID, while direct publication uses s-UUID. The former requires a valid resolution receipt covering the exact previous tree on every selection read. Corrupt/missing proof cannot be mistaken for a normal event. Event intent/commit bytes remain unchanged across the move. This is a deterministic integrity check, not producer authentication.
