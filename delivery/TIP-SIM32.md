# SIM32 — closed-loop simulation quality baseline

Owner intent: high-fidelity Hera/general drone simulation controlled by AERIS; empty/loaded behavior, wind/environment/audio; strict competitive quality exceeding DJI. Confirmed strategic standard13/10/2026. Requirements baseline prepared now; runtime/physics/viewer not built or accepted by this document.

Follow docs/AERIS-PRODUCT-QUALITY-STANDARD.md, pilot/sim32/acceptance-contract.json and pilot/sim32/AGENTS.md. Sequential Contractor/Builder/Verify; do not claim independent audit.

## Implementation sequence and acceptance

| ID | Required implementation / acceptance |
|---|---|
| SIM32-01 | Versioned reference aircraft/payload/physics/environment profiles with SI units, frames, source hashes, seed and calibration status. Missing mass/inertia/actuator assumptions explicit. No generic “Hera validated” model. |
| SIM32-02 | AERIS workspace→isolated MAVLink adapter→pinned ArduPilot SITL→physics/sensors→telemetry. Raw causal trace from request through observed state, not replay/ACK completion. Verify supported model interface on actual pinned binary before selecting built-in or external JSON backend. |
| SIM32-03 | No-load/central-load/off-center-load models, wind/crosswind/gust, bounded actuators and battery model. Analytic/reference and numerical convergence checks, dt/clock/seed trace, no render-driven physics. Physical tolerances require calibrated references; unsupported effects explicit. |
| SIM32-04 | Plan/preflight/Home/datum/upload/readback/AUTO/landing/review operator journey through simulator; camera/gimbal identities and distinct streams/capture events/media provenance. Native APK current mock is not silently made operational. |
| SIM32-05 | Clock-synchronized3D telemetry viewer, terrain/obstacles with documented sources/metric scale, camera/gimbal views and optional audio tied to model. Screenshot/walkthrough plus traces; no3D or audio changes to vehicle state. No borrowed demonstration animation as evidence. |
| SIM32-06 | Flight/payload/video link loss, wrong target, late/duplicate ACK, process restart, stale sensor/clock, overload; authority gates, uncertain outcomes, zero unintended resends and preserved raw/review evidence. |
| SIM32-07 | Performance corpus and budgets by workload/hardware; p50/p95/p99/max/deadline misses/queue/memory/frame age with failed samples retained. Proposed60FPS/UI100ms goals must be labeled target. Safety/correctness gates before optimizations. |
| SIM32-08 | Prepared Ragas same-config comparison and DJI equivalent-system comparison protocol; named product/version/hardware, counterbalanced tasks, predeclared criteria/denominators/confounders. No superiority claim until actual comparative collection/analysis and hardware gates. |
| SIM32-09 | Before/after protected inventories,20GiB floor/peak admission, cleanup, source/evidence fingerprints, completion report. No SDK/HeraHub/ENDURE mutation/Fly integration/software release. |

## Deliverable and gate order

Profiles + interface capability proof → physics/oracle → control/mission/payload loop →3D/audio → integrated fault/performance verification. Dedicated local simulation workspace may reuse core through read-only imports/copies pinned by hash; no edits to app/services or original release path. A new flight/physics backend implementation requires an ADR describing units, conventions, lifecycle, rate/clock, resource budgets and isolation before code. A container/image install is not implied by this baseline; reuse existing bounded tooling first.

Simulation completion requires all applicable runtime gates and explicit handling of UNSUPPORTED items; no test-count percentage toward product readiness. Hera calibration, Android private-storage/runtime/input/video, hardware/HIL/controlled flight and comparative superiority remain separate later gates. This TIP does not change ENDURE acceptance or permit signing past its gate.

## Current state

REQUIREMENTS_BASELINED. All SIM32 runtime, physical calibration, render/audio and comparative measurements: NOT_CHECKED. Baseline quality targets: PROPOSED_NOT_MEASURED. Existing N31 resource incident and ENDURE failures retained. No new simulator process or large build launched by the requirements preparation.
