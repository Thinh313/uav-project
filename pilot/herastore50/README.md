# HERASTORE50 · streaming archive / receiver verification / confirmed hot cleanup

Run `node pilot/herastore50/server.mjs` from the project root with≥20GiB free plus reserve. Preview8804. Product root `.local/herastore50/operator`; hot49 manager/data live under `hot49`, retained copies under `vault`, append-only audit under `operations`. Existing49 preview8803/store and completed source/candidate/ENDURE are untouched. No SDK/install/build/APK/signature/SITL/emulator.

## What can be reclaimed

An inactive49 group and all attributable workspace journals, or a retained-aborted switch. Never the active workspace or published selection-chain events. Published chain cannot be pruned within this design. Unknown workspace identity/orphan association is refused rather than guessed. SWITCH_PENDING and CLEANUP_PENDING block new writes.

The console starts empty. **Thêm workspace mock** explicitly creates synthetic data only in the50 root. It does not migrate or manage the live8803 store. Manager49 format is reused unchanged; root ownership/quiescence must be established separately before any future live integration.

## Operator flow

1. Select a unit and **Xuất gói lưu**. Export reads a bounded manifest, then streams256KiB chunks with per-chunk/per-file SHA, an end frame and whole-package SHA. Source is rechecked before export receipt. A package is64MiB logical/96MiB encoded max,4096files/1024directories; no compression or whole-payload buffering. Duplicate/traversal/unsafe paths, symlinks and hardlinks are rejected.
2. Download uses a native streaming browser download. Or explicitly import the retained host package. A user-uploaded `.aeris50` file is streamed to a new receiver; the expected whole-package SHA is mandatory. For an outside producer obtain that SHA through a separately trusted source. Unkeyed SHA is integrity, not producer authentication.
3. Receiver reconstructs regular files/empty directories only within the unit allowlist, verifies every byte again after writing, then runs49/47 mock semantic replay where valid. Fresh inspection state is disconnected with no commands/input/preview authority. Incomplete source is RAW_ONLY_QUARANTINED; a retained aborted attempt is raw evidence, not execution. Nothing is automatically activated in hot storage.
4. **Lập phương án dọn** checks both retained package copies, receiver data and semantic report again, plus current source bytes/stamp/selection. Review exact unit, byte count and receipt IDs; type the entire unit ID and check acknowledgement. Without this there is no removal.
5. Only the authorized hot replica moves into CLEANUP_PENDING/trash. Each unlink requires a bound intent, exact source SHA/identity, unchanged retained-package identity and exact corresponding receiver file. Final proofs precede the completed receipt. Old source/candidate/evidence outside this owned root cannot be targeted. No product rm-rf/background cleanup or POST retry.

**This frees hot quota/group or retained-attempt slots, not host disk space.** Export package, receiver package+data and all audit stay local. More disk can be consumed by retaining these copies. A local download/import is not off-host retention evidence. Arrange separately authorized off-host retention/cold cleanup when needed; this module does not automatically reclaim the vault.

## Interrupted cleanup

Quota remains charged for the complete pending unit even when parts moved or files were already unlinked. Normal writes block until a new explicit digest-bound recovery confirmation:

- CONTINUE_CONFIRMED_CLEANUP revalidates retained copies and all remaining bytes. An absent file is accepted only with its bound durable delete intent; outcome is labelled MISSING_AFTER_AUTHORIZED_INTENT, not a claim about exact cause/timing. Unexpected missing/changed/extra data blocks.
- RESTORE_BEFORE_DELETE moves the intact replica back only if no delete intent exists. Byte readback must match before the aborted receipt.
- RETAIN_UNSTARTED_METADATA preserves an early incomplete authorization transaction only if no moves/trash/delete intents exist. It never removes hot data.

After any delete intent, rollback in this module is unavailable. The independently verified receiver still holds the full archive-inspection copy, but no automatic hot reactivation is implemented. Lost response after publication is resolved read-only; never resend cleanup blindly. A pending state with unknown changed evidence stays blocked for investigation, not forced to PASS.

## Quota / assumptions

Hot manager49 remains64MiB/max4groups/max16attempts; incomplete/retained units count until confirmed completion. Root50 has a512MiB cap including hot, vault, incomplete uploads and audit,16exports/16imports/16completed-or-retained cleanup attempts. Projected writes and a16MiB reserve preserve host20GiB. Per-chunk host checks avoid rescanning all data; data are streamed with bounded buffers. Final cleanup reads the relevant receiver file and source identity before every unlink; full archive/replay verification occurs at operation boundaries.

One cooperating owner per root, no competing direct49 writer. OS malicious-writer resistance, physical powerloss, actual full-volume ENOSPC, Android/HeraHub/MCU and off-host storage NOT_CHECKED. Faults are injected without filling disk; owned Node processes are actually SIGKILLed. Imports/export/archive receipts are not software signatures or24h ENDURE acceptance.

Startup rejects malformed closing tags or missing recovery options; browser regression checks every recovery choice, typed confirmation and52px controls at1280/1024/360. Details/raw hashes are in collapsed review panels. See Completion for final accepted test IDs/counts, all retained negative-test stores, source fingerprints and owned scratch cleanup.
