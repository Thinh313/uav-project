# TIP-HERA03 / v0.6 · Native diagnostic foundation

Owner authorizes the most reasonable complete next increment on2026-10-12. Current GCS geographic/SITL slice is complete; native HeraHub observation is the next dependency. Host read-only scan found an existing Android SDK37.0, build-tools36, platform-tools and Homebrew JDK26; adb inventory shows zero devices. Use existing tools, no installs. Single agent switches Contractor/Builder/Verify, no independent-review claim.

Deliverable: an installable development-signed Android diagnostic APK using public native APIs, explicit device identity declaration, bounded input/lifecycle traces and local JSON export. A versioned import validator and GCS evidence view consume that report without granting flight authority or silently promoting hardware facts. Proprietary radio/video SDK transport remains unknown. Production native GCS stack is not fixed by a disposable diagnostic module.

AC01: ADR010/current roadmap/SOT owner authorization and scoped native contract.
AC02: read-only Android inventory: OS/build/API/ABI, current window density/insets/rotation, input devices/motion ranges, H264/H265 decoder enumeration. Failures remain unknown, codec count is not concurrent decode performance.
AC03: bounded input capture only after explicit toggle, raw joystick/key observations with source/device/time, hotplug/focus/lifecycle gaps; no flight bindings, external listeners or key text capture.
AC04: process/session boundary, app-private checkpoint and bounded lifecycle history; restore old snapshot only as previous-session evidence, no current device state restoration.
AC05: SAF user-selected JSON export, package/build/time/session/provenance/unknowns included; no network/Bluetooth/location/phone/storage permissions and no telemetry/flight transport.
AC06: existing-toolchain build, dev signature verification, manifest/dex/APK/source hashes, deterministic report-model host tests; development key private/local excluded from export/manifest.
AC07: browser import schema/time/size/build/bounds/unknown/provenance gates; atomic failed-import handling, replay/physical-unattested separation; no automatic SOT promotion or flight enablement.
AC08: GCS Review can access native intake, inspect/export/remove local reports, show observed-reported versus unknown and APK/runbook; responsive UI/no external fetch.
AC09: regression/SOT/Refinery/source gates, coverage/completion and cleanup. Native install/start/SAF/hotplug/process-death/HIL are NOT_CHECKED until a real authorized device is present; do not count host tests as Android execution.

Scope decision: public Android APIs are sufficient to deliver a diagnostic APK without proprietary SDK. Do not invent native vehicle/video integration or install on a device without a recorded target. No emulator/system-image download is needed to mask the missing real controller gate. Existing browser/SITL control remains unchanged.

VERIFY deviation: external original BOM locator is missing in this later session. Keep strict default original check; explicit canonical-only check establishes archived source/lineage integrity and marks current-original comparison NOT_CHECKED. Do not restore/change source bytes or choose another workbook.
