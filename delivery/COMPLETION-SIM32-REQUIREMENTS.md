# SIM32 — quality requirements baseline

STATUS: REQUIREMENTS_BASELINED_ONLY. Owner13/10/2026 requires strict algorithm/performance/graphics/simulation quality and a competitive product aiming to exceed DJI. Persistent working standard and scoped acceptance plan are saved outside frozen source/SOT/candidate.

Delivered:
- docs/AERIS-PRODUCT-QUALITY-STANDARD.md:10 mandatory principles, workload-based performance targets, physics/graphics/audio/authority/resource gates, and competitive measurement rules.
- pilot/sim32/AGENTS.md: requires future work in this module to read the standard and TIP first.
- delivery/TIP-SIM32.md:9 requirement IDs and implementation/gate order.
- pilot/sim32/acceptance-contract.json: versioned targets distinguished from measurements, all runtime requirements NOT_CHECKED, no comparative winner or unsupported readiness claims.

Verification here covers document/contract consistency, hashes, isolation constraints and existing protected bytes only. It does not validate a simulator, physics fidelity, FPS, UI latency, Android runtime, Hera configuration or competitive performance. See evidence/sim32/verification.json and fingerprints for exact quantitative document checks and preservation count.

Next implementation sequence: versioned profiles and pinned SITL interface capability → physics/reference/convergence checks → AERIS closed-loop mission/payload workflow →3D/audio tied to physics → integrated faults/resource/performance tests. A scoped ADR is required before flight/physics backend code. Engineering60FPS/local UI100ms targets are proposed, not measured results or numerical owner approval. Hardware calibration and matched Ragas/DJI comparisons have separate gates.

No simulator started, dependencies installed, large build run, software package signed, frozen source/candidate/trust/ENDURE modified, or full-project/scratch copy created. No task cleanup needed beyond normal retained small documents/metadata. Prior N31 resource violation and ENDURE failures remain unchanged; current capacity choice remains in effect.

Single-agent sequential requirements preparation/verification; no independent audit claimed.
