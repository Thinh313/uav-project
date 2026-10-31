# SIMTRAIN53 — scoped closed-loop training prototype

This is an isolated host simulator, not an APK, HeraHub integration, calibrated Hera aircraft, signed release or council acceptance. It extends the approved SIMTRAIN52 plan without modifying prior modules/candidate/SOT/trust/ENDURE.

Run `node pilot/simtrain53/server.mjs` from the project root if its owned server is not already running. Open http://127.0.0.1:8807/. Docker Desktop and the already installed local AP image are required. Nothing starts, arms or flies automatically on page load/restart. Only loopback target42/component1 of the attested owned Docker instance can receive control. No physical radio, discovery fallback or arbitrary endpoint/command API.

## Try the flow

1. Choose empty/calm, central1kg/calm or offset1kg/gust. Press **Mở phiên SITL mới**. Each profile is a provisional3kg reference quad (+1kg for loaded cases), not a measured Hera.
2. Wait for EKF/GPS/Home/pre-arm. Initial cold alignment took roughly40–50seconds. Use **Đọc lại cấu hình** after those checks become ready; the30second configuration TTL is kept.
3. When preflight passes, press **Cất cánh GUIDED ·5m**. Arm is normal, never forced. Success requires observed mode plus a physical climb, then LOITER.
4. Press **Nhận quyền input**, neutral first. W/S forward/back, A/D lateral, arrows vertical/yaw. Input is keyboard training input; camera orbit is separate. Focus loss,200ms stale/suspension, malformed input or identity changes revoke the lease. Reclaim explicitly; it never revives from a later packet.
5. Press **LAND** in the persistent header, wait for ground and disarm, then **Kết thúc**. Each engineering session is bounded to120simulated seconds /150host seconds; land well before expiry. Deadline closure is incomplete, not successful flight completion.
6. Review the retained session/history after restart. Successful operator closure starts a bounded offline raw/model readback; no new simulator or command. New start is locked during verification. Select a closed record and check SHA again. A hash check compares current raw bytes with the retained local readback; it is not a software signature or full flight acceptance.

The UI uses a4GiB retained-evidence quota, reserves1GiB before each explicit new session and requires≥24GiB host free space for peak/margin above the20GiB floor. No automatic deletion, eviction, reset, campaign retry or old-runtime invocation. A full quota requires a separately controlled archive workflow; do not delete evidence to bypass the gate.

The standing workspace has no active AP instance at handoff. SIGINT stops its server and requests closure of only its current owned controller. Raw/state remain. Do not invoke old SIM32/ENDURE helpers, reuse an occupied run ID or force-remove another container. Failed/ambiguous control remains failed; no automatic command replay.

## Architecture and evidence

- New Node HTTP/control adapter and managed Python backend/controller; existing firmware, fused physics, MAVLink service and Three.js are imported/mounted read-only. Rendering never writes aircraft state.
- Raw1200Hz RX→durable intent→local sensor send markers, consecutive frame checks, original-model byte oracle, AP receive/parse observer and nonce host/guest plus Node/backend clock brackets. Local send/ACK is not promoted to execution.
- Render selection/interpolation is explicitly a presentation stage; it does not remove raw physics frames. Audio is RPM-derived synthesis, muted on stale/end; new live acoustic output/listening is NOT_CHECKED.
- Three successful actual SITL flows: empty/calm, central/calm, offset/gust. A first unarmed preflight freshness failure is retained. All4captures,305,475sensor+aux frames match the immutable original. Functional tests do not constitute a controlled payload performance A/B experiment.
- Whole-run receive RTF≈1.0002–1.0003 at requested1×, cap500ms. Five-second windows can fall below1; receive gaps have p99≈7.6ms and max≈55.6ms. **Full G1 pacing is unaccepted.** Browser RAF timings include intentional350ms stalls/screenshots and are not GPU completion or native projector measurements.

See delivery/COMPLETION-SIMTRAIN53.md and evidence/simtrain53/verification1.json. Source adjustments after the physical matrix (rejected-RX preservation, review/quota/finalizer, clearing local input before LAND) received focused mock/static checks, not a fifth full SITL regression. The automatic verifier success path after a new operator closure was not replayed as an additional actual flight; existing-receipt and failure paths were checked separately. No hidden promotion to full-product READY.

## Remaining gates

Finish pacing/jitter/phase budgets and controlled longer UI/load matrices, then rerun integrated final-source regression. Next are mission upload/readback/AUTO survey/corridor, camera/gimbal/images, takeover/resume and instructor faults. Physical impact/terrain/rain/propwash/ground effect, advanced Stabilize/gamepad controls, remote training, high-end Hera art/audio calibration, actual laptop/projector rehearsal and packaged deployment remain separate work. All25full planned requirements remain unaccepted; current implementation covers a bounded subset.
