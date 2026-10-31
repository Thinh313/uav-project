# ADR-040 — isolated development installation for NATIVE30

Decision: derive a separately signed, debuggable engineering APK from the existing N30 source/assets in native/runtime31. Preserve every existing N30 file and prior failure receipt. Keep the software release/candidate and ENDURE immutable. A dedicated development key has no release/trust role.

Reason: PackageManager correctly requires signing; host-only checks could not close the ART and Activity/private-storage gates. The user explicitly authorized development signing. Actual emulator checks must identify API, ABI, image, WebView and certificate, and must never be promoted to Hera hardware acceptance.

Resource decision after measurement: retain the licensed AOSP Android13 ARM64 target, but block installation at current capacity. The sparse extraction attempt crossed the floor (19,783,680,000 bytes observed); the guard was insufficient to bound final allocation. It was stopped and its owned scratch removed. Future admission must budget the full uncompressed image, archive, AVD, emulator and host margin, with at least28GiB free. No unrelated data deletion or project copies. Host free space can change independently; do not assume zero-seeking alone establishes safe physical allocation. The user subsequently chose APK/host handoff at current capacity.

Derived code changes, if needed for Android runtime behavior, are recorded in build receipts alongside original and overlay hashes. Original N30 failure remains FAIL; the new attempt has a separate outcome. Debugging is local to the owned emulator and scoped engineering build. No operational command path exists.
