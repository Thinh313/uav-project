# Selected engineering artifact and evidence

Current selection for this task is APK03, not the earlier APK01 path in the
Builder's initial RUNNER.md:

- `native/betaintegrated01/cockpit03/dist/aeris-cockpit03-development-03.apk`
- SHA256 `3086cc4c4f503c34f5fd336e2b7450df135781a512858faa6a91af9e15860114`
- Source digest `4c93a9f0db63bb6f9db58641109ab9bb0ea0c6855d6a8a26b8d716b5fbd14397`
- Build/tool/certificate/input snapshot: `evidence/betaintegrated01-m1cockpit03/native/build-03.json`
- Scoped acceptance: `evidence/betaintegrated01-m1cockpit03/qa/FINAL-QA.json`
- Detailed report: `delivery/COMPLETION-BETA-CAMPAIGN01-M1-COCKPIT03.html`

This is the owned API33/ranchu Android emulator engineering profile, not a
production phone/HeraHub/real aircraft release. APK03 uses the same glass UI
assets02 and accepted Owner03/Flight02; only a nonflight intent adapter fixes the
STAGE_BINDING seam. The immutable shared PendingExplicitAction does not itself
accept STAGE_BINDING. The new wrapper keeps its replay/TTL/foreground fence and
admits STAGE/CLOSE/STATUS only. All flight actions remain native touchscreen.

Fresh explicit staging must first prove the exact private binding SHA, a saved
survey, settled preflight view and ownerActive=false BEFORE starting host/AP.
Stage opens no socket. After actual AP identity/passive heartbeat validation,
visible native CONNECT alone opens the writer. Root's accepted run is
actual-nominal02. Its raw/metadata/native archives and root parent anchors stay
immutable; running an old attempt again must refuse rather than overwrite.

The test controller is not an end-user launcher. No automatic rerun/resume or
flight retry is authorized by this file. A future authorized test needs a new
explicit case, current admission and source pins. Keep entry20/livefloor10GiB
plus256MiB and the real15s runtime guards, speedup1/cap500ms and fsync-before-sensor.

Native target bounds/readiness are current Android measured layout, not cached
WebView click authority. Presentation overlays wait for the current-view two-RAF
ACK. Header/day-night navigation and read-only workspace bridge cannot grant
control. Review card click loads the bounded detail. Summary is not the complete
trajectory; no visible spatial review map or automatic detail load is certified.

Ordinary Activity restart restores saved drafts/reviews only. The accepted
restart left16 journal/workspace/link files exactly unchanged, NO_SESSION,
ownerActive=false and bindingStagedSHA256=null. All owned processes are now
closed. Raw, workspace and AVD are kept; only enumerated transfer/XML scratch and
build scratch were removed.
