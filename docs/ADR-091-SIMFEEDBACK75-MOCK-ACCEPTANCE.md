# ADR091 — Isolated SIM feedback acceptance harness

Status: accepted within owner's mock/replay scope,16/10/2026. Existing aircraft source, candidate and ENDURE remain frozen.

Feedback combines operator workflow, autopilot policy, physical dynamics and visual scene behavior. A single simulator PASS would collapse those boundaries. Use separate statuses: PASS_MOCK_SCOPE, NOT_CHECKED_SITL, NOT_CHECKED_HERA, UNKNOWN_DATA and UNSUPPORTED_MODEL.

Pitch+yaw checks reuse SIM32 reference rigid-body model with synthetic motor inputs. Its native derivative is compared with the existing Python expression and a finer timestep; this checks implementation consistency, not independent identification of real aircraft dynamics. Additional constant-rate rotations use a Rodrigues-matrix oracle. Avoidance uses a deliberately synthetic stopping-distance policy, not a reimplementation or certification of ArduPilot. Continuous sphere/plane and sphere/sphere collision checks have analytic test references and an independent sampled distance oracle. Visual meshes, finite walls, propeller contacts, mesh terrain and physical restitution are not represented.

All replay evidence has metric frames, virtual Home, model/profile/scene hashes, target/session/boot and local simulated timestamps. A SHA chain detects modification only with an externally pinned expected digest; it provides no signature/authentication. Reports retain negative outcomes and never promote ACK or synthetic velocity to actual flight execution. No output endpoint exists, so the harness cannot command a vehicle.

Later gate: record exact Hera airframe/firmware/config/sensor/HID/flight logs; establish tolerances from separate calibration/validation data; then scoped SITL, HIL and hardware acceptance. Stable1× pacing remains an existing open gate and is not addressed by offline test speed.
