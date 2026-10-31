# FIRMWARE38 roadmap supplement

14/10/2026. Supplement only; frozen canonical roadmap/SOT/source/candidate/ENDURE unchanged.

| Area | Current preparation gate | Next gate |
|---|---|---|
| Firmware/discovery | Source-bound version/capability mock contract; legacy exception explicit | Frame adapter and actual named binary association; fresh announcement, UID/context/clock/capability observation |
| Typed parameters | Read-only C-cast/bytewise decoding and named index65535, bounded live witness | Actual AP parameter types/casting/count/change/read duration; no automatic writes or weakening of precision bounds |
| Failsafe/preflight | Rich Copter action/options/context graphs, no Wh fiction or execution claims | AP-side receipt/latch/RC/EKF/battery state adapter; actual pinned SITL branch and priority/cause verification |
| Altitude/geofence | Reviewed datum/Home/Origin/Terrain/mixed frame bands and active-mask separation | Actual altitude reference/activation/geometry/cause readback and fence enforcement; terrain/geoid data acceptance |

Actual SITL, Android/native, Hera hardware/SDK, calibration and release/endurance acceptance remain separate. No SDK or hardware is required to review this mock contract. No build/runtime/signing permission is implied by free disk space or a passing mock gate. Keep 20GiB floor and old evidence immutable in the next task too.
