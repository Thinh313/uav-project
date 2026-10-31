# COCKPIT05 UI qualification contract

Selected APK: `native/betaintegrated01/cockpit05/dist/aeris-cockpit05-development.apk`.
Package/activity: `vn.rtr.aeris.cockpit05/.CockpitActivity`, versionCode501, label `AERIS Cockpit UI`. Cached development certificate only. Root alone owns emulator5582/ADB/UIAutomator and private fixture seeding.

No operational connection is authorized in this task: do not stage a launch binding, tap CONNECT, start AP/SITL, send flight commands or grant input. Initial native state remains NO_SESSION/ownerfalse/bindingnull. No synthetic fixture, mock bridge, mock HTML/CSS, fake telemetry or fake camera source is packaged.

Root may seed its own compatible UI-only JSON into this NEW package private `files/workspace03/` via run-as. Use explicit MOCK names, contiguous draft revision generations beginning1, canonical byte SHA filenames (`draft-000001-<sha>.json`, `review-<run>-<sha>.json`). Review records must remain FAILED/UNKNOWN/PENDING, actualImages0, authorityRestorablefalse, completionClaimfalse. This seed is external UI-test evidence and must not be mistaken for flight/native journal acceptance.

Existing read-only probes remain unchanged: `files/workspace-state.json` and `files/native-controls-layout.json` (view/presentedView/viewReady, ownerActive, bindingStagedSHA256). No new probe, intent or bridge API was added. Ordinary launch is enough; existing two-render-frame acknowledgement gates overlays.

WebView UI selectors: survey/preflight/Fly/review navigation keeps existing accessible names. Review rows now use `Mở hồ sơ <run>` for unselected and `Đang xem hồ sơ <run>` for selected, with aria-current and a trailing check. Theme button uses existing light/dark accessible action name and sun/moon. Preflight notice uses a neutral information icon. Native control selectors remain `control01-*`, but remain unconnected and ungranted in this task.

Root should inspect both themes, selection changes between MOCK review rows, aligned title/metadata/check, no gold leading inset or notice border, centered short navigation underline, unchanged glass, and no clipped/overlapping native/WebView layers. Browser/DOM checks are not Android pixel proof. This Builder did not start Android, AP, services or install the APK.

Source adaptation is only Activity/ClosedReview package04→05. Config/Owner160/core and helpers reference frozen accepted sources. APK UI assets are byte-exact `planning/betaintegrated01/cockpit05-ui/assets/`, excluding all standalone preview/mock files. Existing cockpit04 package/private data, source/candidate and ENDURE remain untouched.
