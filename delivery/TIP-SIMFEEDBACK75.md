# SIMFEEDBACK75 — feedback → acceptance → mock/replay corpus

Owner authorization: 16/10/2026, normalize feedback and implement pitch+yaw, obstacle/collision mocks. Dependencies: read-only SIM32, SIMTRAIN52, AERIS57, THREAD62 and supplied feedback. One agent separates SPEC / BUILD / VERIFY; no independent reviewer claim.

## Specification

New namespace `pilot/simfeedback75`, `evidence/simfeedback75`; no changes to prior modules, canonical SOT, frozen source/candidate, trust or ENDURE. No SDK, device, network/flight transport, SITL/emulator, APK or software signature. No installation or project copy. New artifacts budget32MiB, actual free-space floor20GiB checked before writes/runs. No deletion of evidence.

| REQ / AC | Observable acceptance for this increment |
|---|---|
| R75-01 | Every substantive feedback theme has source locator, uncertainty, required behavior, test data, comparison method, PASS/FAIL rule and next-level gate. No uncertain claim promoted to Hera fact. |
| R75-02 | Pitch+yaw corpus covers both signs, sequential and simultaneous inputs, empty/central/offset loads and calm/gust. Read-only SIM32 native path vs Python derivative and dt/2 convergence; explicit open-loop PWM label, not AP control validation. Analytic rotation fixtures detect axes/order/sign mistakes. |
| R75-03 | Synthetic avoidance envelope has declared margin/deceleration/timestep/TTL/mode and rejects stale/future/wrong target/session/boot/frame. No universal10m or ArduPilot-behavior claim; policy output is not physical braking evidence. |
| R75-04 | Continuous swept-sphere contact tests detect wall/ground/slope/sphere crossing and tunnelling, including tangency and initial overlap. Unsupported shapes fail loudly. Detection only, no impact response or complete 3D mesh fidelity. |
| R75-05 | Replay header pins model/profile/scene identity, SI/NED/FRD, virtual-Home datum and mock clock. Sequence, SHA chain, expected digest, quaternion/finite checks detect missing/reordered/tampered frames and ACK-only evidence. |
| R75-06 | A second mathematical path checks geometry and orientation; deliberate wrong outputs must fail. Frozen-model numerical agreement is not independent Hera calibration. |
| R75-07 | Missing-Hera registry states fields, units, source/capture needed and blocked gates for each theme; no invented tolerance or data. |
| R75-08 | Before/after exact SHA preservation, source pins, bounded evidence, quantitative verification and completion report. All deferred SITL/Hera/HID/graphics/performance checks NOT_CHECKED. |

## Decisions

Existing user authorization covers the isolated harness; no additional blueprint approval needed. Mock policies and numerical thresholds are fixture engineering criteria, not approved Hera performance tolerances. Reuse frozen physics read-only instead of inventing a replacement flight model. Physics run is open-loop PWM, not pilot pitch/yaw through autopilot. Collision scene is analytic primitives in metres, independent of the existing photographic renderer. Mock contact failures are expected test stimuli, never demonstration pilot guidance. No new UI needed for this data/verification increment.
