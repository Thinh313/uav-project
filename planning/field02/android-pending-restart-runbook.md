# FIELD02 pending/cancel/restart runtime check

Contractor executes only after the active SITL mission has closed. Builder has not used ADB or emulator UI in this phase. This procedure uses the existing signed development02 APK, never a rebuild, clear-data, lock deletion or automatic retry.

## Admission and baseline

1. Confirm host `/api/state` has `flight.run = null`, no flight authority, and payload leases revoked. Record model/plan/raw KML hashes, captures/reviews and current native journal prefix. Keep all previously collected SAF documents.
2. Use only owned `emulator-5582`, package `vn.rtr.aeris.field02`. Check runtime guard/floor and evidence budget remain admitted. The UI should display Android host-companion simulation honestly.
3. Check current native journal operations remain below16. All export/import/cancel/unknown operations count; do not reset the app to make room. Quota boundary itself has exact frozen-method host JVM evidence, not16 destructive UI repetitions.

## Pending export interrupted before Save

1. On Android Review/workspace action, tap **Xuất workspace**. Wait for actual Android CREATE_DOCUMENT picker. Do not tap Save.
2. Capture picker screenshot. Through authorized readonly collection, snapshot `/data/user/0/vn.rtr.aeris.field02/files/field02/journal.jsonl` and the staged `<operationUUID>.artifact`. Last record must be PICKER_PENDING/export with expected bytes/SHA. Record operation UUID, artifact SHA and entire prefix SHA before interruption.
3. Explicitly force-stop only this package: `adb -s emulator-5582 shell am force-stop vn.rtr.aeris.field02`. This is intentional process termination, not an Android crash or an AP reboot. Do not force-stop the host companion, emulator or SITL.
4. Relaunch existing APK component through launcher/UI or `adb ... shell am start -n vn.rtr.aeris.field02/.ShellActivity`. Do not reinstall or clear data. Observe actual resumed cockpit.
5. Collect a new native journal snapshot under a new evidence filename. Validate original prefix bytes unchanged; exactly one UNKNOWN_AFTER_RESTART for the pending UUID, reason NO_AUTOMATIC_RETRY_OR_AUTHORITY_RESTORE. There must be no EXPORTED_READBACK_VERIFIED for that UUID and no new picker. Staged artifact bytes remain equal to pre-stop SHA.
6. Record host fresh client instance/epoch and no flight authority/payload lease. Do not equate foreground activation with a grant. Model/plan/KML/capture/review identity must survive. Relaunch once more only if required to prove UNKNOWN is not appended repeatedly; the same UUID should not receive another recovery transition.
7. If journal or stage cannot be collected or invariants differ, mark FAIL/NOT_CHECKED. Never rewrite the native journal or synthesize a successful receipt.

## Explicit cancellation

1. Start a separate workspace export in actual UI; note pending UUID/SHA.
2. Tap Android Back/Cancel on picker. Expect CANCELLED(stageRetained=true), no success message or exported receipt, original stage hash unchanged. No automatic re-open.
3. Verify authority remains absent. A picker cancellation is not a successful provider write, and provider files are not removed automatically.

## Import tamper and changed-head refusal

Use separately named fixture documents; never alter the original verified exported document.

- Tamper fixture: change one byte inside bodyBase64 while retaining declared SHA. Choose it in actual Android import picker. Expect operation UNKNOWN with SHA256_MISMATCH (not import success), host committed head/model unchanged.
- CAS fixture: start Android Import to capture head H; while picker is open, use a second authorized host UI to explicitly save a distinct valid idle mission (H2). Return to Android and select the original verified wrapper. Expect WORKSPACE_CHANGED_WHILE_PICKER_OPEN, no additional WORKSPACE_SAVED by this operation, no authority restoration. Restoring the original mission afterward requires another explicit valid UI action and consumes another operation.
- Truncation fixture: cut a copy before closing JSON/body. Import must refuse before host save; retained original and host model stay valid.

These runtime checks complement frozen source and JVM mock evidence. They do not prove device power-loss durability, malicious provider behavior, physical media, Xiaomi or production readiness.

## Runtime entrypoint qualification

Actual QA found that a force-stopped app with a DocumentsUI picker child could return that old external-picker task on an ordinary component start, leaving no FIELD02 PID and no journal transition. Preserve that attempt as **NOT_EXERCISED_RECOVER**. For the bounded owned-task test, explicit NEW_TASK|CLEAR_TASK (`0x10008000`) makes ShellActivity a new root without clearing app/provider data. Require actual new PID plus foreground ShellActivity before judging recovery; see `android-task-restore-assessment.md`. This is an explicit QA recovery entrypoint, not proof that every ordinary launcher/recents path already has polished recovery UX.
