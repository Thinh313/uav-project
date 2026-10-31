# SIM-STABILITY03 exact source overlay

This archival overlay retains the exact changed source from isolated receiver03.
It is **NOT READY**, not a standalone installer and not automatically selected by
`npm start`. The original application, frozen candidates and ENDURE were not
modified. No runtime or flight command is executed by this snapshot.

Read `overlay.json` for paths, base-checkout digests and final source digests.
`source-bundle-manifest.json` pins the complete host-local parent closure,
including external artifacts which are intentionally not copied here. Nine
changed source/configuration files are stored under their original relative paths.
All unchanged code continues to live at the repository's original paths.

The authoritative full result is
[SIM-STABILITY03 completion](../../delivery/COMPLETION-SIM-STABILITY03.md).
One actual manual Android–SITL sequence passed. Long-capture recorder capacity,
closed timing and media/link/reboot acceptance remain open. Do not infer release
readiness from source hashes or copy this overlay into a live/frozen candidate.

AP firmware/native kernels, APK, raw captures and the engineering archive remain
host-local. Reproduction needs their exact recorded prerequisites. A fresh Git
clone alone cannot run the complete emulator/SITL environment.
