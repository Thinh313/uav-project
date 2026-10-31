# AERIS SIM-STABILITY03: NOT READY

Engineering handoff for the declared macOS ARM host and the unchanged development APK. This is reference-quad simulation, not calibrated Hera performance or authorization to control a physical aircraft. The current qualification is `QUALIFICATION-SIM-STABILITY03.json`; retained older NOT_READY notes/qualification/source IDs describe lineage only and do not override it. No production signature or private signing key is included.

## Verified outcomes within the declared scope
- Actual engineering APK on owned emulator5582 completed typed preflight/Home, GUIDED takeoff, neutral LOITER claim, bounded pitch and yaw, GUIDED release, LAND/ground/disarm, durable review and native SAF export/import in AP04.
- AP04 captured116815 contiguous frames over97.2773 receive wall seconds, RTF1.000696. WAL CRC/SHA chain and AP required frame stages checked with0 missing/duplicate required records. fsync-before-sensor, speedup1 and500ms cap retained.
- Independent replay of the same116815 captured PWM frames through the immutable original pure-Python model matched all sensor UTF8 and modelAux bytes exactly.
- Failed runs retained FAILED_INTERRUPTED with no successful-flight inference. Cold host restart restored history only, never session/boot/input lease. Native background revocation observed separately in AP03.
- Actual public SAF manual04 package SHA b34b341260663d84c1a0b40f1d8981d7807b64de3f98f35559f177ce81126394 verified and tampering rejected. External raw remains on original host and is not embedded.
- 17117 protected legacy identities and650 predecessor entries unchanged relative to retained baselines.165 previously missing paths remain recorded. ENDURE history not rewritten; no ENDURE acceptance inferred.

## Remaining gates and unsupported capabilities
- NOT READY overall. Immutable AP recorder capacity did not support full300s captures in AP03/AP05; a separate bounded capture-capacity solution and actual recheck are required without dropping frames or changing firmware silently.
- Closed-session activeAPSeconds still advances in public state; freeze elapsed time at exact closure and regression-check late callbacks in a new isolated revision.
- Native UI harness must select the actual current page before review navigation; AP05 LAND succeeded, next template mismatch halted driver, then the unclosed session exhausted trace capacity.
- Actual scene-loss/audio mute/freeze, final AP reboot and measured visual FPS/photon latency remain unverified. Removing ADB reverse did not prove an established socket outage. Active AudioFlinger track is not measured audible or calibrated Hera sound.
- Physical Xiaomi/Hera/HeraHub, real gimbal/camera/payload, projector display, Hera mass/aerodynamics/acoustics/environment calibration, AUTO, SDK and production release are outside this slice or NOT_CHECKED.
- Client HTTP input sequence/clock/axes are validated by code/mocks but not directly embedded in raw; wire sequence is a different evidence layer. Generic DJI superiority or training certification is not claimed.

Physical Xiaomi/Hera/HeraHub/payload/SDK acceptance is NOT_CHECKED. AUTO mission capability is unsupported in this slice. The PBR scene is a licensed visual representation driven by reference physics; synthesized RPM audio is not calibrated Hera acoustics. No unmeasured photon latency, general training validity, zero frame loss, full source-image delivery or broader environmental accuracy is asserted. Large raw captures are retained on the original evidence host and are NOT embedded in exported SAF metadata packages or this engineering archive.

## Host prerequisites and installation

Use macOS ARM with the cached Python3.14.6, declared Node runtime and existing Docker image digest from the manifest. These prerequisites are external; no download, native rebuild or Windows/Linux compatibility is implied. Check the archive SHA, exact 65-byte `bundle-manifest.sha256` (64 lowercase hex characters and LF), payload manifest and dependency closure before following `planning/simhand01/README.md`. Extract only into a new empty directory. The empty regular `runtime/sitl/arducopter` is a structural Docker bind target; the actual AP binary remains at the pinned runtime build path.

Keep admission20GiB and runtime10GiB plus256MiB reserve guards. The recipient policy remains2GiB; internal engineering runtime accounting does not change recipient guards. AP300s is a wall upper bound, not proof that the immutable AP recorder supports an accepted300s capture. Land and close bounded tests before recorder exhaustion.

The engineering APK is unchanged (SHA256 `8f1767933059b719d0bfb260df751678d24bd6d0a345397a5d52815cf7f2aec1`). Select an explicit USB serial for every Android action; never select an arbitrary attached device, root a physical phone, or treat an emulator result as Xiaomi/Hera acceptance. Native SAF imports are historical records only and never restore authority. Restart requires explicit new session, preflight and neutral acquisition. A doctor, archive hash or clean process exit alone does not prove a successful flight.
