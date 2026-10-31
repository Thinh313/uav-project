# SIMSITL76 — actual AP pitch+yaw / virtual proximity

16/10/2026, owner-authorized real isolated SITL after resource gate. Dependencies: SIMFEEDBACK75, read-only APSTREAM40/FIRMWARE4.7.1/FLIGHTSAFETY42. Single-agent SPEC→BUILD→VERIFY; no independent assessor claim.

Use ArduPilot INTERNAL quad physics to test autopilot RC and proximity paths. It is a different physics model from SIM32 and is not a calibrated Hera. No claim of numerical parity with SIM32, full simulator acceptance, physical contact, real sensors, HID or1× UI pacing. No physical endpoint, SDK/HeraHub, Fly integration, APK or signature.

## AC

| ID | Acceptance |
|---|---|
| R76-01 | Pin binary/image/config/source/protocol; verify firmware/discovery/typed readbacks/GPS/EKF/Home and fresh armed/landed telemetry; normal arm only. |
| R76-02 | Four signed pitch+yaw RC cases through AP in Loiter; actual RC echo +signed attitude/yaw-rate response, bounded attitude/height and ground/disarm closure. No inference from ACK alone. |
| R76-03 | Ray-derived8sector DISTANCE_SENSOR through MAVLink; AP proximity output confirms ingestion. Compare baseline avoidance0 vs2 with virtual wall12m; enabled case surface clearance≥1.2m and last3s forward speed≤0.5m/s; baseline actually reaches/crosses virtual wall. Fixture criteria, not Hera tolerances. |
| R76-04 | While neutral/holding, sensor TX dropout; inspect fresh AP sensor outputs/timeouts, then explicit restore. Adapter rejects wrong target/session/boot/frame/stale/invalid payload in mocks. No claim AP authenticates targetless DISTANCE_SENSOR. |
| R76-05 | Durable TX intent before socket write, complete bounded raw RX/TX log with chain/sequence; second decoder raw replay and negative mutations; observe commands vs actual vehicle response. |
| R76-06 | Mock gates before actual runtime; all failed starts/source versions retained; bounded lifecycle closes owned container on disk/parent/driver/deadline fault; no auto retry/reconnect/force arm. |
| R76-07 | ≥22GiB actual launch gate,20GiB floor,256MiB campaign budget and1.5GiB host margin (rounded up). Monitor≥20.5GiB during run. Readonly prior modules/source/candidate/ENDURE, exact before/after SHA; no deletion. |

At most2explicit attempts after diagnosing failures; no automatic reruns. Per run≤420host seconds, raw≤32MiB, state≤64MiB, Docker log2×2MiB, CPU1/RAM256MiB; fixed local port5896, fixed image already present, no pull/build/install. AP onboard logs disabled to bound state; full MAVLink wire is retained, not the1200Hz SIM32 external sensor WAL. This is intentionally not a repeat of its durability/pacing benchmark.

Control trials: pitch RC2=1500±50; yaw RC4=1500±80,1.5s each; preserve timestamps and all samples. Reaction criterion signed peak attitude delta>0.01rad and signed yaw rate>0.03rad/s; |roll|/|pitch|<0.6rad, relative altitude3..7m. Quantifies fixture response, not acceptable Hera maneuver accuracy. Virtual wall has no physical force/collision response in built-in world. Baseline crossing is a deliberate software negative test; do not present it as training behavior.
