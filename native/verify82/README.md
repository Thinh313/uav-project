# COCKPIT82 emulator completion overlay

Existing signed development02 is the target; no new APK build, signature, app edits or production operations.

- Evidence: `evidence/cockpit82-emulator04`, prior COCKPIT82 report and fingerprints remain immutable.
- Same AVD aeris-cockpit82, serial emulator-5582, API33 ARM64; no wipe/copy of project or AVD.
- First controlled environment change: headless host GPU with explicit working hardware acceleration. Any later change gets separate runtime receipt.
- ADB/UIAutomator and adb root were explicitly authorized by user for the owned emulator-5582. No physical-device control or WebView debugging/JS injection.
- Readiness: real UI loaded, explicit authority, live preflight gates. No fixed sleep alone may count as readiness. Screenshots/XML/actual app-private journal + separate semantic replay form evidence.
- Required flow: survey save/compile → Home/datum/route confirmations → Fly mock → ACK no progress → points/landing → actual journal-backed review. Force-stop/cold reboot preserve exact HEAD for completed record and never restore authority. Active interruption audit should be verified if resource budget permits.
-20GiB hard floor,21GiB monitor stop,30GiB launch admission; cleanup SDK/ZIP/python cache after all owned processes close, preserve AVD and all evidence.
