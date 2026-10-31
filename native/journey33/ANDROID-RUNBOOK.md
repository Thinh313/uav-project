# Actual Android acceptance — not executed yet

This is a preparation checklist, not runtime evidence. Host tests cannot close these gates. The latest task currently has no installed system image/emulator/AVD and <28GiB headroom. No download, launch, installation or reboot has been performed.

## Admission / ownership

Before any runtime download/install, observe real free space ≥28GiB and budget full archive + fully allocated uncompressed image + emulator + AVD + host margin, preserving20GiB. Do not rely on sparse extraction. Use the verified official API33 ARM64 AOSP archive identity from `evidence/native31/system-download.json` and an owned emulator. Installed SDK/JDK tools stay read-only. No new license acceptance, device fallback or existing-device control.

Create owned runtime scratch inside this module only, record absolute paths/PID/process command/explicit serial/AVD identity before testing. Reserve continuous headroom; if threatened, stop that owned emulator and remove its scratch after collecting small evidence. Never delete unrelated files, frozen data or locks. No current task launch is permitted while admission remains unmet.

## Acceptance sequence

1. Verify selected development APK SHA/build receipt/certificate, zero permissions and min/targetSDK. Boot an owned API33 ARM64 emulator,1280×800/density160; record qemu identity, firmware/WebView and display versions.
2. Execute APK-contained `vn.rtr.aeris.journey33.AndroidProbe test` through actual ART with a fresh owned test directory. Verify31 journal assertions; do not reuse/overwrite the old N30 ART FAIL.
3. Execute the three owned `AndroidProbe crash` boundaries: RECORD_PUBLISHED, HEAD_PENDING, HEAD_COMMITTED. SIGKILL only the exact marker PID after checking `/proc/<pid>/cmdline`. Keep two revision records; recover old/old/new exact capsule respectively, disclose pending and block automatic publish. Preserve raw receipts.
4. Install only package `vn.rtr.aeris.journey33` on that explicit owned serial. Verify installed APK bytes. Start Activity, verify offline assets, bridge and native private storage; record logs and screenshots.
5. Edit a valid polygon/name/altitude/speed. Save draft; force-stop only this package and relaunch. Compare private journal head/body and form; require DRAFT/no gates. Repeat for an invalid editable draft; it must not compile/start.
6. Compile current input, inspect, explicitly confirm Home and datum. Starting without either confirmation/stale observation must fail. Start Fly mock; ACK leaves cursor unchanged, early landing fails, editor is locked. Check that each accepted point is committed in private storage.
7. Force-stop mid-run and relaunch. Match exact saved event prefix/cursor, append INTERRUPTED_RESTART, never advance/resend/restore gates. Compile/preflight anew; finish all points then explicit landing. Review must report COMPLETED_MOCK, no physical execution/media, correct mission lineage and prior interrupted history.
8. Force-stop/relaunch after completion and reboot the owned emulator. Verify identical committed completed report/draft; zero restored compile/preflight/input authority. Distinguish an explicitly interrupted restart from unchanged completed history.
9. Background/resume, Activity recreation, keyboard/window resize and focus during admitted save. Inspect pending/unknown states and the prepared-background race; no automatic retry. Test SAF export/cancel/provider failure/import and verifier replay. Do not claim provider completion from picker-open ACK.
10. Collect app-private journal hashes/reports, actual Android screenshots/logs and power/resource observations before stopping/removing only owned runtime/AVD scratch. Record all PASS/FAIL/NOT_CHECKED and rerun protected fingerprints. Actual Android/Hera hardware/video/input gates remain separate.

No SDK/HeraHub, aircraft commands, software-release signature/selection, Fly candidate integration, ENDURE relaunch or external publication.
