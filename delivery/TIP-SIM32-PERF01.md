# SIM32-PERF01 — >=1x UI/SITL, correctness first

Owner authorized optimization on13/10/2026. Sequential Contractor/Builder/Verify, no independent audit, no additional ship approval needed for this local increment. Frozen app/services/candidate/trust/ENDURE and prior receipts stay exact. Current SIM32 module may change; exact previous24source files remain in source-final.

REQ-P01: fix current analytic validator regression and retain failed baseline receipt; all20analytic/convergence and validation tests must pass. Zero resistance/damping are valid ideal reference cases; negative/nonfinite values remain refused.

REQ-P02: remove redundant physics computation without changing timestep/RK4/model/domain/profile. Replay entire6accepted old traces against optimized output and pinned reference, exact numeric equality required for supported profiles; benchmark paired identical inputs. No frame drops/precision reduction/model time scaling to make RTF pass.

REQ-P03: bound journal offload with explicit queue overflow/write error failure, drain/seal on shutdown and no false complete evidence. Full trace/hash/count stays mandatory. Measure stage latencies, queue/RSS and active-wire `(N-1)/rate/wall`, plus wall mission/flight segment. Stop on20GiB floor/headroom.

REQ-P04: run actual UI+SITL, reference empty/central/offset loads and winds; completed/disarmed/ground and raw integrity required. >=1x actual measured model/wall, not assigned clock or backend throughput alone. Declared AP pacing setting is part of configuration. Default AP speedup1 baseline and optimized runs compared; any explicit modest pacing headroom must be tested as separate configuration with matched baseline and disclosed, never credited to algorithm speedup. No no-lockstep/sensor extrapolation/automatic time resets.

REQ-P05: retain all failed attempts, protected before/after, source archives, baseline correction, operator/report/contract extension. No signing/SDK/AVD/Hera/Fly integration or ENDURE launch; cleanup only owned simulator state/container/cache. Current preview closed cleanly before code changes, then reused on8796.
