# AERIS product assessment

26/10/2026, Asia/Ho_Chi_Minh. **Engineering alpha; integrated beta NOT READY.**
This assessment combines retained milestone reports. It does not rerun Android,
SITL, video or field tests, and does not promote a component PASS to whole-product
acceptance. RAGAS is not the acceptance baseline; the target is the declared
premium UAV control, survey and inspection requirements.

## What an operator can already do

| Capability | Demonstrated | Remaining product gap |
|---|---|---|
| Mission planning | KML polygon/corridor, mission model/compiler, QGC subset and Home/altitude checks; Android/SITL results on named revisions | Finish the same final build across broad polygon/corridor corpus; native offline terrain/maps and achieved image quality |
| Flight | AUTO/HOLD/resume and fault observations in earlier isolated Android–SITL increments; full touch manual flight in SIM-STABILITY03/AP04 | One qualified integrated release covering manual, AUTO, video, payload, failures and restart; physical Hera not tested |
| Manual simulation | Actual APK → preflight → GUIDED takeoff → neutral LOITER claim → pitch/yaw → release → LAND/disarm → review → SAF | Long-capture recorder, closed timer, actual socket-loss/AP reboot and visual/audio performance still block full simulator acceptance |
| Safety/authority | Typed ArduPilot4.7.1 preflight/Home, stale/session/boot fences, bounded input leases, no automatic authority restoration | Validate complete supported configuration and hardware/HIL/field faults; no general safety certification |
| Camera/gimbal/multiple payloads | Discovery/routing/leases, dual-operator contracts and mock/SITL evidence in isolated increments | Real device/model/lens/firmware/SDK, independent operators and several payloads in the same qualified release; ACK is not exposure |
| Video | One bounded Android session measured29.997FPS, cold-start815.5ms and conservative maximum gap154.177ms | Full AUTO/video/payload workload and repeat runs; trace-sealing UI blocker; no real camera-to-photon measurement |
| Media/geolocation | Synthetic JPEG, telemetry-linked sidecars, review/receiver integrity | Real exposure timestamp/GNSS/time synchronization, original camera files, calibration and achieved mapping quality |
| Persistence/handoff | Android workspace/SAF/restart, durable review and cold receiver in named slices | End-to-end release-wide acceptance, target-device storage and external source identity |
| UX | RtR glass cockpit, themes/icons, native touch flows and scoped Android screenshots | Human operator/glove/day/night/hardware input QA, complete fault/popup states and frame/presentation latency |
| Deployment | Engineering APKs, bounded companion launchers and integrity metadata | Clean-machine installer, real controller/device qualification, official signing/update/security/support and continuous endurance |
| Advanced assistance | Deterministic planning and review foundations; mock training/coach exercises | No qualified autonomous AI flight, calibrated Hera digital twin or validated pilot training score |

An engineering APK can be installed on a compatible Android after its identity,
permissions and configuration are checked. The current evidence is mainly from
an emulator and simulator. **We cannot yet say that AERIS can be installed on a
Hera controller and safely replace its operational flight software.**

## Strongest recent evidence and its limits

SIM-STABILITY03/AP04 captured116,815 contiguous frames at1.000696× with UI and
actual ArduPilot SITL. WAL CRC/SHA and required AP stages were checked. Replaying
the same PWM through the immutable original Python model produced0 differing
sensor/modelAux bytes. This verifies deterministic agreement for this capture,
not Hera aerodynamics or sustained performance under every load.

The full SIM-STABILITY03 milestone has11 acceptance rows:8 scoped passes or
observations,1 failure,1 partial,1 not checked. That is not a product-completion
percentage. AP03/AP05 remain FAILED_INTERRUPTED. AP05's reverse-mapping removal
did not interrupt the established socket, so it did not qualify stale rendering
or audio mute. Active AudioFlinger output is not calibrated audible sound.

MissionBeta01 completed navigation in one polygon but failed the video maximum
gap (489.086ms against250ms);0/6 integrated nominal runs were qualified. Later
BETA-VIDEO03 passed one bounded video capture but retained a trace-sealing UI
blocker and unrun integrated scenarios. Those results cannot be combined into a
claim that a single final APK passed everything.

## Readiness by release gate

| Gate | Current judgment |
|---|---|
| Reviewable R&D prototype / engineering demo | Usable in declared simulator configurations, with explicit limitations |
| Repeatable integrated internal beta | NOT READY |
| HeraHub/controller bench release | NOT CHECKED: no hardware/SDK acceptance |
| Operational flight and commercial replacement | NOT READY |
| Certified/high-fidelity Hera training simulator | NOT ESTABLISHED |

There is no defensible single percentage for the total objective: source volume,
module counts and repeated test passes are not product maturity. The largest gap
is now integration and release repeatability, followed by hardware/payload/field
qualification. New feature breadth should not outrun these gates.

## Next milestone: one reproducible internal-beta release

1. Repair recorder capacity/closure-time accounting and the actual-page UI
   harness in a new isolated revision. Keep frames, fsync, speedup1, cap500ms and
   failed evidence intact.
2. Lock one APK/host/source/configuration. Qualify manual plus3 polygon and3
   corridor missions with video/payload, actual link loss/AP reboot, safe authority
   revocation, LAND/disarm, review, SAF receiver and cold persistence on that same
   version. State unsupported scenarios rather than combining old passes.
3. Package a reproducible host companion and install/run procedure, then obtain
   independent operator UX feedback. Keep simulator camera/physics/audio clearly
   distinct from real media and Hera calibration.
4. After the internal-beta gate, qualify Xiaomi/HeraHub/MCU/joystick/radio and one
   actual camera/gimbal chain, then expand Phase One/thermal/multiple payloads and
   field mapping/inspection. Physical hardware remains a separate gate.

## Traceable sources

- [Premium product baseline and48 requirement groups](../planning/product-standard01/BASELINE.md)
- [MissionBeta01 integration](../delivery/COMPLETION-MISSIONBETA01.md)
- [BETA-VIDEO03](../delivery/COMPLETION-BETA-VIDEO03.md)
- [SIM-STABILITY03](../delivery/COMPLETION-SIM-STABILITY03.md)
- [Isolated latest simulator source](../snapshots/simstability03/README.md)

Raw acceptance/manifest receipts remain on the engineering host. The repository
maintenance commit changes documentation, ignore policy and archival source
visibility; it does not alter flight behavior, retest the product, sign a release
or certify ENDURE.
