# NATIVE24 · Isolated native shell/input/local-video preparation

Owner authorization2026-10-13: build the native shell/input/video preparation without Hera SDK, outside frozen ENDURE20 source/candidate. Single agent specification → build → verify. Scope uses existing public Android SDK/JDK; no new dependency install, real transport, SITL/flight command, official release or selected-candidate change. RM-05/06 preparation only; no final production-stack commitment.

| REQ | Exit gate |
|---|---|
| N24-01 | Separate package/source/build/receipts; Android Views shell for Plan/Fly/Review, lifecycle revokes mock authority and playback; historical checkpoint never restores authority. |
| N24-02 | Pure-Java versioned mock calibration/input model: finite range/deadzone/inversion, exact session/device, neutral qualification, explicit deadman/owner, timeout/hotplug/focus/reorder invalidation. Bounded history with dropped count. Real raw Android input never acquires mock flight authority. |
| N24-03 | One local-video player, synthetic fixture/imported-unattested origin/hash, byte/dimension/duration bounds, stale player callbacks rejected, stop/release on lifecycle/surface/error; no camera image, live latency or continuous frame-age claim from MediaPlayer start event. |
| N24-04 | Native bounded SAF local intake/export and app-private historical checkpoint; no network permission, WebView bridge, SDK/vehicle endpoints, arbitrary path/network playback or persisted input authorization. |
| N24-05 | Existing host toolchain compilation/DEX/package/development signature and host model fault tests; no original diagnostic build helper invocation or frozen app/native pins edits. |
| N24-06 | Isolated browser walkthrough of host-Java replay and real encoded synthetic local-video fixture, responsive/aligned controls, offline/tamper/fault state/export; label browser decode separately from untested Android execution. |
| N24-07 | Before/after source/slot/controller/PAYLOAD21/PROTOCOL22/SOT/candidate identity match; live soak fresh/0errors, no restart/commands, disk>=20GiB before build and build scratch removed. |

No device/emulator was present in initial inventory; required Android runtime/device install/SAF/lifecycle/native decode/inputs remain NOT_CHECKED. Host replay and browser cannot close them. Touch floor native48dp, browser44CSSpx with shared aligned actions. Android min26/target33/build-platform37 are prototype choices, not measured installed HeraHub compatibility. APK dev signing reuses existing diagnostic development key read-only; not software-release/trust keys. Runtime modules remain isolated after ENDURE20 until their own future integration gate.
