# COCKPIT85

Isolated, browser-verified UI overlay derived from immutable NATIVE84 assets. No Android APK85 or flight qualification is asserted. Latest accepted APK remains NATIVE84 development10.

Preview: `node native/cockpit85/server.mjs`, loopback 127.0.0.1:8848 only. `/mock.html` runs the native mock journey against a separate host JVM journal at `.local/cockpit85/journal`. `/` uses the disconnected real-source presentation and an explicitly labelled read-only exact-SHA archive of the five NATIVE84 SITL reviews. No telemetry fixture is injected into live state. No flight transport exists in this server. Do not replace the accepted native84 files.

`assets/layout85.css` owns viewport gutters, work-surface bounds, content scrolling and lower-instrument columns after inherited styles. `layout85.mjs` coordinates panels and focus only. App assets are listed in asset-list.json; negative-control styles are excluded from Android packaging. A future native integration must retain the Java bridge whitelist, origin, permissions and acceptance gates and repeat Android/IME/SAF checks.

QA uses CUA documented locators and read-only DOM evaluations. `browser-audit.mjs` exports createAudit85; `text-containers85.mjs` checks visible button child/container bounds, not glyph rasterization. Top/bottom sheet checks and screenshots complement those measurements. Earlier failing captures are retained; only explicitly selected passing receipts enter verification-ui.json. Two deliberate geometry faults must fail. A second source-pin set records the video-loss correction; the previous popup/panel/return matrix is reused only under its exact one-file CSS diff and full main/alert/history rechecks.

Audit commands create receipt paths; do not overwrite prior runs. `verify-ui85.mjs` currently writes verification-ui.json exclusively. For future work use a new evidence namespace/run id rather than deleting or replacing evidence. No project scratch/dependency/cache installation was created by this task.
