# NOT_READY: diagnostic engineering handoff

This archive is a diagnostic source/dependency handoff. It is not a qualified flight simulator release, Beta acceptance, production APK or Hera flight-control release. Do not use it to control a physical aircraft.

The payload preserves the exact receiver04 manifest closure and existing engineering APK, with these packaging-only additions: an empty regular `runtime/sitl/arducopter` Docker mountpoint, lineage manifest, this notice and qualification metadata. The empty file is a structural bind-mount target, not firmware and not an executable replacement. The actual pinned AP artifact remains at its existing runtime build path. No runtime was started to qualify this new archive.

Unresolved acceptance gates:

- A usable, fresh simulator/AP control link and recovery after a dead link remain unqualified.
- A complete manual takeoff, neutral acquisition, bounded pitch/yaw, release/background/stale revocation, LAND and observed ground/disarm sequence did not pass end to end.
- Real-time factor, clock/frame correctness and sustained behavior under the operator/UI load have not been accepted for this recipient build.
- Durable closed review and full raw evidence reconstruction have not been accepted. Metadata or externally referenced raw paths do not establish full raw verification.
- Android public SAF export/import, restart persistence and receiver roundtrip have not been accepted. Import never restores control authority.
- RPM-based synthesized audio is not Hera acoustic calibration; audible output and stale/end mute acceptance remain unverified.
- Physical Xiaomi/Hera/HeraHub/SDK acceptance, AUTO missions and broader weather/collision/training validity are not established. Features marked unsupported remain unsupported.

The included 3D assets and input/audio code do not prove functional readiness or subjective visual/training quality. Structural archive verification proves byte/membership integrity only. Existing `sourceIDs` describe lineage, not a certification or software signature.

The engineering APK is unchanged. Use only an explicitly selected Android USB serial; never root a physical phone, choose an arbitrary connected device or use another app's data. The supported host is the declared macOS/ARM dependency set, not an asserted Windows/Linux port. Existing 20 GiB admission and 10 GiB plus reserve runtime guards remain in the source. Start/doctor scripts do not override this NOT_READY qualification.

Before any authorized future test: extract into a new empty directory, verify the archive SHA and manifest, inspect `QUALIFICATION-NOT-READY.json`, then follow `planning/simhand01/README.md`. A doctor or clean process exit is not functional acceptance.
