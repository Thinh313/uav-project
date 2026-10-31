# SIMFEEDBACK75 — offline mock acceptance

Start with [ACCEPTANCE-MATRIX.md](ACCEPTANCE-MATRIX.md), `contract.json` and `hera-data-gaps.json`. The12 feedback themes remain distinct from8 implementation requirements for this increment. Priorities are local to this harness, not a rewrite of the frozen roadmap/SOT.

Read-only SIM32 reference quad:30 open-loop PWM experiments,4 coupled pitch/yaw sign combinations plus sequential pitch→yaw,3 load profiles and2 wind profiles. Motor fixture mixes normalized thrust then maps through sqrt to PWM; independent signed wrench checks prevent roll being mistaken for pitch.30×200=6000 physics frames; native derivative vs Python expression, dt/2 comparison and exact cold replay. No autopilot input/response is tested here.

8 quaternion/Rodrigues rotation cases,14 declared contact cases,100 seeded sphere comparisons,12 avoidance faults/boundaries and300-frame constant-push kinematic trace. Replay adversaries include missing/duplicate/reordered/tampered/re-sealed frames, wrong identity/clock/frame/datum, zero quaternion, ACK-only and nonfinite data. `MOCK_LIMIT` is an output from a synthetic policy, never proof an aircraft slowed/stopped. `UNAVAILABLE` has no fabricated speed. The single approach ray does not prove safe retreat or full sensor coverage.

Contact is swept sphere vs sphere/infinite plane only. It detects tunnelling, initial overlap and tangency. There is no collision response, finite wall/mesh, rotor envelope, terrain service, renderer or physical aircraft calibration. Matrix lists these next gates explicitly.1m margin/2m·s⁻² and numerical tolerances are fixture assumptions, not Hera settings or ArduPilot guarantees.

## Reproduce

From `/Users/os/Downloads/AI technique/aeris`, check actual free disk first. Maintain20GiB floor +32MiB admission/budget. Use a new output name; runners refuse overwrites. No dependencies/build/install required; existing Python3.14 and SIM32 native extension must match their pins.

```sh
df -h /
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s pilot/simfeedback75 -p tests.py -v
PYTHONDONTWRITEBYTECODE=1 python3 pilot/simfeedback75/qa.py --out evidence/simfeedback75/mock-NEW
PYTHONDONTWRITEBYTECODE=1 python3 pilot/simfeedback75/verify.py evidence/simfeedback75/mock-NEW --out evidence/simfeedback75/cold-NEW.json
```

Only run cold verification after successful corpus generation. Preserve every failure directory. Latest accepted scope is `mock-r03` and `cold-readback-r03.json`. `mock-r01` originally reported67passes but is superseded: it exercised dominant roll+yaw because rotor mapping/fixture checks were insufficient. `mock-r02` failed the stronger zero-roll wrench gate; linear PWM mixing creates cross terms in quadratic thrust. Fixture now mixes thrust. The first unit attempt expected exactly zero pitch for the old wrong mix, overlooking its small cross term; repaired test detects dominant wrong-axis moment. All receipts are retained; they are not accumulated into final test counts. Old module source versions were not archived, so exact full-source reconstruction of these early attempts is not claimed.

SHA chains/expected heads prove consistency against a pinned manifest; whoever can replace the manifest and all local trust data can replace history. They are not signatures. Single-agent specification/build/review with a second mathematical path is not independent human review. No existing source/candidate/ENDURE changes, transport/SITL/HIL/device connection, signing or authority restoration.
