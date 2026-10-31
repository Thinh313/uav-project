# FIELD02 Android Builder report

22/10/2026. Scope is a development Android WebView host-companion, not standalone native MAVLink, Xiaomi/Hera or production acceptance. Contractor performs runtime/UI verification separately.

## Implemented

- New package `vn.rtr.aeris.field02`, loopback control8872/media8873 only; main-frame custom URI for SAF, no callable JavaScript interface across frames. Native HTTP has no redirects and only fixed host routes.
- A native UUID is shared by initial URL and environment injection. Actual foreground state determines `onPageFinished` lifecycle. Background sends a native HTTP fence in addition to best-effort JS; host heartbeat expiry remains required. No reconnect, authority grant or AUTO originates in native code.
- Native SAF export stages immutable verified bytes before picker, provider readback must match SHA. Artifact downloads require fixed path, expected SHA, safe filename and bounded body; redirects refused. Browser blob downloads are not represented as SAF success.
- Workspace export wraps exact committed body bytes and model SHA; import checks wrapper SHA/schema/authority flag, pre-picker committed head, host idle/CAS and model readback. No permission is imported. Native mirror is an immutable byte artifact; semantic schema validation remains host-owned.
- Durable bounded SHA-chain operation journal, fsync-before-picker, UNKNOWN recovery after restart, no auto retry or cleanup. 16 operations,128MiB quota,128MiB local reserve; pending tail fails readonly. KML/QGC picker uses ACTION_OPEN_DOCUMENT.
- Read-only WebCodecs capability probe emitted as `FIELD02_CAPABILITY` in Android logs, with user-agent and viewport. No Android video performance is claimed before actual run.

## Evidence

- `evidence/field02/android-pure-java-check02.json`:28 deterministic byte/path checks PASS, including origin/path/digest/bounds/immutable publish/symlink rejection. These are host JVM checks, not ART/UI.
- Build01 failed before APK because cached Android API does not expose `OsConstants.O_DIRECTORY`; retained log. Fix uses no-follow validated directory, `Os.open(O_RDONLY)` and `fsync`.
- Build02 PASS: `native/field02/dist/aeris-field02-development02.apk`,41,363bytes, SHA256 `df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d`.
- SourceID `30d6c941b1f6dc2fb38411ecc56cf2e9372b937eaad96f29a371e09d2e2240a8`. Exact source manifest and stable build resource samples are in `android-source-freeze02.json`.
- Signature v2/v3 verified with retained engineering-only certificate; permission INTERNET only; unsigned payload bytes identical. No production signing or SDK download.
- Own new AVD prepared under `.local/field02/avd`, references existing API33arm64 system image without altering old AVD. Runtime launch/install belongs to Contractor.
- Build stage `.build` and pure-Java class cache removed. Test artifacts and both failed/successful build logs retained.

## Not yet demonstrated by Builder

Android ART startup, touch/SITL end-to-end, WebCodecs support/performance, SAF provider success/readback, actual process restart and cross-frame malicious navigation require Contractor runtime tests. This report is not FIELD02 READY.

Build budget2/2 consumed. No further APK build without Contractor scope/budget decision and new evidence.

## Later retained-runtime countercheck and source-frozen mock phase

After Contractor collected actual Android SAF artifacts, Builder independently re-read their bytes without using ADB or emulator UI. `android-builder-final-check01.json` checks10 native journal records, SHA-chain, two exact exported provider artifacts (workspace20,603bytes and aborted SITL raw7,472,640bytes) and one import receipt. The workspace/raw hashes match the retained native readback records. The raw export is explicitly an aborted run, not nominal mission acceptance. Separate QA `qa-saf-independent01.json` also checked host canonical workspace import.

Additional source-frozen tests:

- `android-quota-jvm01.json`:7 checks call the exact frozen private `admission` method via reflection, with a mocked free-space File. It refuses operation16, insufficient reserve, oversized byte forecast and preserves the original file; not ART or filesystem-durability evidence.
- `android-recovery-jvm01.json`:16 checks call the exact frozen private `recover` method with captured Android journal bytes. Completed journal stays identical; pending export becomes UNKNOWN_AFTER_RESTART exactly once; restart is idempotent; torn tail, changed body, reordered chain and over1MiB journal refuse without rewriting input. Gson/time/fsync adapters are test-only, so this is host JVM contract evidence, not Android fsync/power-loss qualification. The first harness compile lacked unrelated JSONObject adapter methods and was corrected; production sources were unchanged.
- Runtime pending-force-stop, cancel, tampered import and changed-head picker race remain NOT_CHECKED by Builder. Exact post-mission steps are in `android-pending-restart-runbook.md`; the Contractor owns these actual UI tests.

The7 frozen source files remain exact; APK unchanged; no build3, no ADB/UI contention and no source/candidate/ENDURE writes. Own test `.classes` cache was removed; all evidence fixtures retained. No grand-total quality percentage or whole FIELD02 READY claim follows from these checks.
