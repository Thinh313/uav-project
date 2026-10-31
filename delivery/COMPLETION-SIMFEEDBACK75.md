# SIMFEEDBACK75 — bàn giao ma trận và corpus mock

16/10/2026. **DONE / READY trong phạm vi mock; chưa nghiệm thu Hera hoặc simulator hoàn chỉnh.** Một agent tách SPEC/BUILD/VERIFY; second mathematical path và cold process không là reviewer độc lập.

Đã chuẩn hóa12 chủ đề từ transcript và ảnh feedback thành ma trận có nguồn, uncertainty, hành vi cần đạt, corpus, metrics và PASS/FAIL.15 nhóm dữ liệu Hera còn UNKNOWN. Không nâng các claim10m/creep, tự hạ khi mất motor, điện áp80% khi SOC10%,4RPM hay AUTO tránh núi thành sự thật đã kiểm. Ma trận/source snapshots nằm trong `pilot/simfeedback75` / `evidence/simfeedback75`; không cập nhật canonical SOT hoặc roadmap đóng băng.

## Kết quả nghiệm thu increment

| REQ | Kết quả / bằng chứng |
|---|---|
| R75-01 matrix/provenance | PASS scope:12themes +2user source snapshots/SHA; contract-audit.json |
| R75-02 pitch+yaw | PASS reference:30cases,6000frames,4coupled sign combinations +sequential,3load×2wind;8rotation cases; signed wrench and wrong-axis bite. Open-loop PWM, không AP pilot control. |
| R75-03 avoidance mock | PASS:12fault/boundary cases +300frame constant push; fixture1m/2m·s⁻², no10m/ArduPilot claim. UNAVAILABLE không là đã dừng. |
| R75-04 collision | PASS detection:14analytic cases +100seeded second-path sphere comparisons. Swept sphere/infinite plane/sphere; no response/mesh/real terrain. |
| R75-05 replay | PASS: sequence/header/frame/datum/identity/SHA chain +external expected head;12tamper/reseal/ACK/finite negatives;6300frames cold readback. |
| R75-06 mathematical cross-check | PASS numerical scope: quaternion vs Rodrigues; contact vs closest-distance/bisection; native vs Python derivative and dt/2; wrong rotation order/endpoint-only detected. Not independent calibration. |
| R75-07 missing Hera data | PASS registry:15groups with fields/units/source/blocked gates; all UNKNOWN. |
| R75-08 preservation/handoff | PASS endpoint SHA:43,719protected paths,0issues; floor observed before writes/runs/final; pins/completion/final receipt. No continuous-presence or ENDURE PASS claim. |

Final unit **24/24**, corpus **80/80**, scoped contract audit **28/28**. These counts are separate suites, not a software completion percentage; earlier attempts are excluded. Cold process reads31traces/6300frames and reproduces6000physics frames exactly. Native/Python full-state max abs error=0.0; worst dt/2 discrepancy=0.000917806771632 against declared0.002 engineering component criterion. Quaternion/RK4 consistency does not prove physical stability or real Hera fidelity. Each physics case is0.5s atdt0.0025s; timing was not benchmarked, no1× claim.

## Issues retained / deviations

mock-r01 originally said67PASS but dominant roll+yaw motor mix did not meet intended pitch+yaw coverage. Stronger signed wrench checks caught fixture mapping and nonlinear PWM cross-term issues. mock-r02 fails zero-roll gate before physics traces; mixing thrust then sqrt-to-PWM fixes fixture without changing SIM32 or tolerance. First unit attempt incorrectly expected the old mix to have exactly zero pitch; updated criterion checks dominant wrong-axis moment. All original receipts/failed artifacts remain. Early complete module source versions were not archived, so exact reconstruction is NOT_CLAIMED. `fixture-axis-incident.json`, `fixture-wrench-incident-r02.json`, `unit-final.json` preserve these facts; accepted runs are `unit-r02`, `mock-r03`, `cold-readback-r03`. No old result rewritten.

No UI/browser work required for this matrix/harness increment. Build/APK/typechecker/linter not applicable;6Python files AST-valid,2JSON files parsed. No dependencies installed, SDK, SITL/emulator, flight transport, Fly retrofit, software signature or authority restoration. Existing flight source/candidate/trust/ENDURE/history unchanged at point checks. No new runtime left active.

## Limits and next gates

G1 later: pin real Hera firmware/config and inject valid/faulty proximity stream through SITL; actual pitch+yaw operator input→AP→physics→sensors, observing trajectories/motor margins and failures. G2: calibrated Hera profile and separate validation dataset with expert-approved tolerances. G3: stable1× pacing, actual HID/UI, full contact/environment/instructor and training acceptance. Missing flight logs, geometry/inertia/propulsion, sensor/FOV/latency, battery, sling, fault behavior and HID cannot be replaced by guessed constants. Full terrain/impact/sling/VRS remain unsupported/unrun. Existing THREAD62 pacing and AUTO63 incomplete gates remain unchanged.

Resource observations: initial free28.381GiB; final21.095GiB. External host activity lowered free space; module artifacts before final receipts approximately9.77MiB of32MiB budget. Samples do not prove continuous disk behavior. No evidence/user files deleted; no scratch/project copies/build folders/install/Docker runs created, so no cleanup item to remove. Whole-project/tmp copying was not used.

Main files: `pilot/simfeedback75/ACCEPTANCE-MATRIX.md`, `contract.json`, `hera-data-gaps.json`, `corpus.py`, `engine.py`, `oracle.py`, `qa.py`, `tests.py`, `verify.py`, `README.md`; ADR091/TIP-SIMFEEDBACK75; `evidence/simfeedback75/final-verification.json`. All new files only; no existing source edits.
