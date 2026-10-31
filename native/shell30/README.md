# NATIVE30 · Editable offline survey / versioned drafts

Status: host editor/persistence preparation verified; actual Android runtime task **PARTIAL**. APK is unsigned; new Activity/WebView execution, provider/SAF and app-private persistence are NOT_CHECKED. AOSP Android13 arm64 emulator did boot and start N30 DEX under ART shell. The first save failed on Android's unsupported `Files.getFileStore`, fixed with `File.getUsableSpace`; fixed code has not been rerun on Android. Owned emulator was stopped and all temporary SDK/AVD files removed after free space fell below20GiB. Raw log/diagnosis retained. No SDK/HeraHub/flight/new signature/ENDURE changes.

Editor: WGS84 polygon3–64vertices, map-add/remove-last, name, altitude5–120m, speed0.5–20m/s, heading0–179.9°, overlaps0–95%. Same exact frozen survey/compiler files are packaged read-only. Scope remains≤500m around flat simulator Home, camera template uncalibrated. Invalid/self-intersecting/unsupported-datum/unfeasible inputs cannot retain old routes/gates. No terrain, arbitrary global flight or measured coverage claim.

Draft persistence: exact form text (including invalid drafts), source SHA and compiled raw mission bytes are stored as immutable revisions under an atomic committed head. Cross-process lock/expected-head protects against stale tabs/writers. Revisions/hash chain/pending/orphans are retained; limits64records/128KiBbody/8MiBtotal/16MiBreserve are engineering policies. Draft and review histories use separate stores. Read-only historical review validates canonical event/mission SHA and completion evidence; reading a completed mock review never resumes it. Restart restores form only and requires fresh compile/preflight. UI mock progress/ACK/landing is not drone execution. No automatic persistence of every keystroke or unacknowledged save claim; use explicit Save. Dirty/unsaved status remains visible.

Native prototype: Android Activity owns offline WebView, allowlisted local synthetic HTTPS assets, no network permission, single-worker bounded Java bridge, explicit SAF import/export and lifecycle revocation. This preserves one geometry implementation, not a final production-stack selection. Browser and APK package the same editor. Java storage runs on host JVM for browser reference; it does not establish Android private filesystem/power-loss durability.

From the project root:

```sh
python3 native/shell30/build.py
node --test native/shell30/editor.test.mjs
node native/shell30/browser-qa.mjs
python3 native/shell30/crash-qa.py
python3 native/shell30/verify.py
node --max-old-space-size=64 native/shell30/server.mjs
```

Preview localhost8795 writes only `.local/native30/drafts` and its separate review journal via Java. It has no flight/device API, rejects cross-origin writes, uses exact expected-head tokens and does not retry failed writes. Quota/timeout/partial state is surfaced. `.local/native30` contains user-created preview drafts/reviews and is intentionally retained; never treat it as disposable build scratch.

Android continuation needs a scoped owned emulator with enough space for SDK/image/AVD **and**20GiB reserve. Do not relaunch a stopped runtime by guessing devices or signing keys. `runtime-qa.py` explicitly targets emulator5580 for future ART/legacy probes; expected tests are prepared but the current receipt is FAIL, not acceptance. Unchanged N24 installation/video and unsigned N30 installation-refusal probes were not reached. Installing new N30 UI needs an authorized development signature; this task expressly did not create one or bypass PackageManager. Android boot/ART shell is not installed GCS/Hera support.

Small APK revision aliases and logs are evidence. Build/test/browser scratch is removed, SDK/AVD/emulator stopped/removed, no whole-project copy/dependency cache or OS power-setting changes. See `delivery/COMPLETION-NATIVE30.md` and `evidence/native30/verification.json`.
