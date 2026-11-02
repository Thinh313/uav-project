# Native journal lifecycle: proposed prerequisite for the next simulator run

Status: PROPOSAL ONLY. No native source/APK/data migration implemented or authorized by this document. Artifact11MiB approval remains effective; all other guards remain as implemented.

## Measured blocker

MISSIONINTEGRATED16 s01 stopped before AP startup with `PRODUCT_NATIVE_DTO_SIGNED_NATIVE_PRODUCER_SCOPE`. The original nonce/PID/SHA-bound Android DTO has `actorCreated=false`, no producer key/signature scope and an empty geometry. It is the application's explicit actor-absent failure DTO, not a valid producer that may be admitted.

The original prestart backup contains eight `files/product-input01/*.aj02` files. The retained selected APK source's InputJournal constructor refuses directory membership >=8 with `INPUT_JOURNAL_GENERATION_QUOTA` before creating a ninth generation. Original byte references and the conditional source-path proof are retained separately; the actual exception string was not captured from a screen/logcat. Increasing startup wait or retrying STATUS cannot remove the eight retained files. Do not spend s02 on an unmeasured timing workaround.

## Smallest product repair worth implementing

Add a native lifecycle with explicit `UNUSED`, `CLOSED_VERIFIED`, `UNRESOLVED`, `ARCHIVED_VERIFIED` dispositions. Keep at most eight live journal files; bound archives and total retained bytes separately under the original native/disk/metadata/export quotas. Monotonic lifetime generation/write/request counters must include archived generations and cannot reset or refund credits. Do not silently reinterpret the old all-history-eight-file guard as already allowing this: changing its accounting domain requires a user decision.

Before rotation, prove cold absence of every producer for the selected package, no current grant/configured input/pending IO, and exact original journal bytes. Header-only is classified UNUSED only by a strict decoder and original lifecycle observations; absence of a terminal marker must never become a fabricated completed input history. Any unknown/truncated/unresolved source remains protected and blocks rotation.

Export an immutable bundle containing every original journal, byte count, source/APK/process/generation identities, SHA and a journal-to-original-path index. Verify full-byte import at an independent receiver before accepting an archive. Moving to the archive is an explicit transaction with preflight capacity reservation, fsynced manifest/data/parent directories, committed pointer and restart recovery. Preserve all original bytes. Do not automatically delete, clear app data, create a replacement package/AVD, drop old counters or grant authority. If archive/byte quotas fill, refuse and require a separate explicit retention decision.

Create an isolated native source tree and development APK using the existing development trust boundary; do not modify the old APK/native source or any old run. Upgrading the same Android package must first preserve and verify the entire old private-data backup; candidate/source/native signature and old/new schema bindings are explicit. Startup failures must expose an actionable source-backed reason instead of presenting actor-absent as only a missing-key error. This diagnostic change does not permit missing-key DTOs to pass strict validation.

## Acceptance before another real run

1. Mock/replay: eight retained unused/closed generations, ninth startup refused before authorized rotation; unresolved/truncated/forged archive/receiver mismatch/no-space/fsync/rename faults refuse without data loss or restored authority.
2. Power/process crash injection across export/verify/archive/commit/restart; either old or new committed view is complete, no invented closure, no discarded original bytes.
3. Exact old-data SHA/preservation and monotonic counters after rotation; archive limits and all original numeric quotas remain enforced. Explicitly report the new active-versus-archived accounting rule.
4. Development APK integrity/signature and source/manifest migration checks; no production signing or real hardware.
5. Only after native lifecycle admission passes: a fresh source/candidate/admission and short Android–SITL mission. The already failed s01 remains immutable; ten-minute acceptance still requires a genuinely completed same-candidate short run.

## Decision needed

Authorize development and testing of controlled native journal archival/rotation, including an isolated development APK, while retaining all original journal bytes and all other guards. This changes the current lifetime-eight-file behavior into an explicitly bounded live/archive model. It does not authorize deleting evidence, increasing byte/clock/flight quotas, signing production or restoring input rights.
