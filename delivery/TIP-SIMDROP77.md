# SIMDROP77 — held-forward sensor loss and repeated controls

16/10/2026. Explicit new campaign authorized by owner; SIMSITL76 campaign stays closed. Single-agent SPEC/BUILD/VERIFY, no independent human reviewer claim.

## Scope / predeclared design

Four NEW independent internal-quad SITL flights. Counterbalanced control order AB, BA, BA, AB where A=AVOID_ENABLE0 and B=2. Every flight then approaches with avoidance2/valid sensors, holds RC2=1400/RC4=1500, cuts sensors without changing stick or mode, observes up to8guest seconds or centre x>12.3m, then explicitly neutralizes. Virtual plane north12m, reference sphere radius0.3m, margin2m, same inherited firmware/config/RC/geometry. No physical collision response. No Hera/SDK/HID/Fly/software signature or stable1× claim.

At most6actual containers (4planned +2diagnostic replacements), at most2attempts per replicate; starts must be explicit, never a retry loop. Failed trials retained in denominator and raw. Source versions archive before each start. Same source/config planned for all four; a mid-campaign executable change invalidates matched-source comparison unless separately qualified and reported.

## Acceptance

| ID | Required evidence / rule |
|---|---|
| R77-01 | Isolated pins, current resource gate, ownership/readiness, fresh typed preflight/GPS/EKF/Home, normal arm. Prior source/candidate/ENDURE and all76 receipts exactSHA. |
| R77-02 | Four qualified independent flights with predeclared balanced control order; baseline centre crosses12.3m; valid-sensor case approaches>7m, surface clearance≥1.2m and max|vx|last3s≤0.5m/s. Expected negative crossing is a successful control-test observation, not safe flight. |
| R77-03 | Loss case has stable valid-sensor approach, unchanged forward RC1400 before/during loss, AP RC echo, Loiter/armed, no mode/neutral intervention until observation endpoint. No sensor TX after committed cutoff; AP proximity expires. |
| R77-04 | Classify from raw trajectory: UNSAFE_VIRTUAL_CONTACT if min surface≤0; UNSAFE_CLEARANCE_LOSS if0<min<1.2; SAFE_STOP_OBSERVED only if full8guest seconds, clearance≥1.2 and tail|vx|≤0.5; otherwise INCONCLUSIVE. Unexpected unsafe behavior is a finding, never converted to safety PASS. |
| R77-05 | Explicit neutral intervention labelled after endpoint; restore sensors and observed proximity, LAND/disarm and owned-container closure. Do not attribute experimenter neutralization to AP failstop. |
| R77-06 | Durable wire chain / complete TX intent-return / raw CRC independently decoded; classification reproducible, adversarial cases refuse false-safe claims. Local hashes not authentication. |
| R77-07 | Bounded campaign resources, exact before/after preservation, completion report with outcomes/failures and limitations. Product/Hera acceptance remains NOT_CHECKED. |

Launch≥22GiB; agreedfloor20GiB; runtime stops at20.5GiB reserve. Total retained new artifact/state cap256MiB, host margin1.5GiB, rounded admission22GiB. Per run≤420host seconds, state≤32MiB, raw≤32MiB, Docker logs2×2MiB, CPU1/RAM256MiB/read-only root+16MiB tmpfs. No installs/builds/pulls/project copies; no evidence deletion. Internal AP physics / requested speedup1, not SIM32 external physics or a pacing optimization. Noise/seed defaults inherited and recorded; no matched real-Hera wind/load claim. Functional repeated comparison only, not statistical superiority.
