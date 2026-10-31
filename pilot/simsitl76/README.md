# SIMSITL76 — actual internal-quad behavioral gate

Accepted run: `evidence/simsitl76/run03`, `cold-readback-run03.json`, `bites-run03-v2.json`. See delivery/COMPLETION-SIMSITL76.md for the full scope/ledger. This module does not modify the frozen application or make it ready for HeraHub/physical flight.

ArduCopter4.7.1/dbe79216 internal quad at requested speedup1; existing binary/image, no build/install. This tests RC pilot inputs and virtual proximity through real AP. It does **not** use SIM32 external physics, prove Hera dynamics, close its stable1× pacing gate, or add physical collision response. Wall is an analytic infinite plane NED x=12m; sensor-origin ranges and a separate provisional0.3m aircraft sphere are explicit fixture geometry.

Four1.5second signed pitch+yaw cases in Loiter, RC echo plus attitude/yaw-rate observations. Explicit Guided return-to-origin between cases is logged; it is not hidden pose reset. Same single flight then disables proximity avoidance for a deliberate virtual-wall crossing, returns to origin, enables it and repeats approach. This ordered one-run comparison is functional evidence, not counterbalanced statistics. Sensor dropout runs with neutral controls; expiry of outgoing proximity data does not prove failstop or safe continued stick input. LAND/disarm is observed before container closure.

## Read-only verification

From the aeris root, check free disk and use a new receipt name:

```sh
df -h /
PYTHONDONTWRITEBYTECODE=1 python3 pilot/simsitl76/verify.py evidence/simsitl76/run03 --out evidence/simsitl76/cold-NEW.json
node pilot/simsitl76/tests.mjs
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s pilot/simsitl76 -p runtime_tests.py -v
```

`runtime.py` is not a preview/server. It needs an explicit new campaign authorization after the two actual-container budget has been used. It will refuse an occupied name, existing run, wrong pins, insufficient disk, unverified mock gate or exhausted budget. It does not retry/reconnect/resume. Port5896 only; recorded CID/label/image, normal arm and output whitelist. Current campaign is closed. Do not delete receipts/locks/containers to bypass its gate.

Launch≥22GiB (20GiB floor +256MiB campaign forecast +1.5GiB host margin, rounded upward); supervisor monitors20.5GiB reserve, state64MiB/campaign256MiB, CPU1/RAM256MiB and420s deadline. Full MAVLink wire RX/TX is retained with fsynced intent before send, not the1200Hz external SIM32 sensor WAL. Original source/candidate/ENDURE kept read-only; no physical endpoint, SDK/HID, Fly integration or signing.

Cold decoder implements its own frame parsing and bitwise CRC from the pinned dialect metadata. It records a narrow known boot exception:12ASCII bytes `Init Gyro**\n` interleaved during startup, before ARM. Other ASCII or late startup text fails. SHA chains require trusted expected manifests to resist history replacement and are not signatures. Single author / second mathematical implementation, no independent human review.

## Retained failures

- run01 reservation failed before Docker creation: lowercase `no such object` did not match original case-sensitive gate. Old runtime source and diagnostic retained.
- run02 actual container closed before client/arm: console-based readiness required absent SERIAL0 text. Final readiness uses passive kernel socket LISTEN5760 in the attested guest, not a TCP probe. Source archive and closure retained.
- First mock attempted legacy service decoder message70 absent from that limited dialect. Replaced with byte-offset/bitwise-CRC checks and complete-dialect cold parser; no legacy edits.
- First cold parser rejected startup ASCII interleaved after MAVLink began. It was not a corrupted raw frame; bounded exact boot text exception added with before-ARM timing requirement. Old parser/incident retained.
- Initial wrong-parameter bite was caught at TX-return mismatch before its intended semantic gate. Final bite updates paired return, requires raw integrity PASS, then confirms behavior gate refuses it. Both receipts retained; final counts are not a sum of attempts.

Hera airframe/mass/CG/inertia/actuator/sensor/FOV/latency/calibration/HID gaps remain in SIMFEEDBACK75. Loaded/gust/external-backend cases, sustained/complex turns, physical collision/terrain meshes, dropout with continued forward input, statistically repeated A/B, renderer/audio and actual Hera acceptance are NOT_CHECKED here.
