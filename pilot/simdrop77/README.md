# SIMDROP77 — held-forward proximity loss

New campaign explicitly authorized16/10/2026; prior SIMSITL76 remains closed and unchanged. Read `delivery/TIP-SIMDROP77.md`, ADR093 and the completion report. No production/native/HeraHub deployment, hardware or software signature.

Four independent internal-quad SITL flights, AB/BA/BA/AB where A=AVOID_ENABLE0 and B=2. Each flight has two functional controls and a separate valid-sensor approach followed by committed sensor cutoff with forward RC2=1400 unchanged. Every sensor write already queued must drain before cutoff marker. Data collection ends at8guest seconds or centre north>12.3m; experimenter neutralization is logged **after** endpoint. Expiry of proximity output is evidence of unavailability, not proof the aircraft stopped.

The outcome can be `UNSAFE_VIRTUAL_CONTACT`, `UNSAFE_CLEARANCE_LOSS`, `SAFE_STOP_OBSERVED` or `INCONCLUSIVE`. Diagnostic observation acceptance and safety acceptance are separate. Virtual plane north12m/sphere0.3m has no contact force in built-in AP world. Do not portray a crossing as physical collision damage or a validated Hera behavior.

Source: existing ArduCopter4.7.1/dbe79216 binary/image and76 geometry/wire policies imported read-only. Small new client adaptation uses77 scope/port5897 and a drainable sensor gate. `source-pins-v2.json` fixes the initial operational files. Final run06 uses source-pins-v3 and a separately mocked RX-drain collector; unchanged AP/config/control-driver body is verified, but source-identical comparison is deferred. Cold audit/bites/summary added separately after first archive; they never execute flight commands. Per-run archives preserve exact files present at launch; differences in added analysis tools do not imply operational source changes.

## Read-only reproduction

From `/Users/os/Downloads/AI technique/aeris`, check free disk and choose new receipt names:

```sh
df -h /
node pilot/simdrop77/tests.mjs
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s pilot/simdrop77 -p runtime_tests.py -v
PYTHONDONTWRITEBYTECODE=1 python3 pilot/simdrop77/audit.py evidence/simdrop77/run01 --out evidence/simdrop77/cold-NEW.json
```

Do not feed duplicate-replication receipts to `summary.py`: it requires exactly four unique qualified replications and unchanged raw/source hashes. Existing `bites.py` and summary outputs use exclusive creation; never remove receipts to rerun them. Use a future explicitly authorized campaign/namespace for new runs. This completed design does not authorize changing firmware/candidate or bypassing an unsafe result.

Launch≥22GiB, agreedfloor20GiB, stopreserve20.5GiB; campaign256MiB logical quota includes retained evidence/state. CPU1/RAM256MiB/read-only root+16MiB tmpfs; bounded raw/state/log/deadline, loopback only. No dependency install, build, pull or project copy. Own container only; no unrelated containers/volumes removed. Raw captures every MAVLink byte with fsynced TX intent, not the1200Hz SIM32 external-sensor WAL.

## Limits

Four functional replicates do not establish statistical superiority, real-time performance, Hera-calibrated behavior or real sensor FOV/noise/dropout causality. The single wall/range fixture has known units/frames but no environmental/collision fidelity. Neutral intervention, sensor restore and LAND are experimenter actions, not autopilot failstop. No production sensor-loss mitigation is implemented by this diagnostic campaign. Existing SIM32 pacing and Hera/HID integration gates remain open.

## Final campaign ledger

Qualified replications: run01/rep01, run02/rep02, run03/rep03, run06/rep04 (AB/BA/BA/AB). Runs04/05 both retain FAIL at observer closure after observed LAND/disarm; raw behavior independently verifies but they are excluded from qualified counts. All six actual starts remain in the ledger. Closure addendum permitted final attempt with new collector, without changing RC/AP/sensor criteria or the1500ms age guard. `summary-v2.py` discloses collector revisions3+1; original strict same-source summary remains unchanged and is not used to claim source-matched acceptance. Current six-container budget is exhausted.
