# Manual operator probe: exact shipped/revised recipient

Scope: engineering APK on owned emulator5582, AP target42/component1, one gateway
and one TrainingLink. Physical Xiaomi, Hera calibration, AUTO, real camera and
projector/audio perception remain NOT_CHECKED. Use UI controls for actual operator
acceptance; direct HTTP proofs must be labelled harness-driven. Do not repeat a
failed/uncertain mutation automatically.

1. GET `/api/config`: simulation=true; manual/preflight/package true,
   mission/payloadCamera false. Its token is transient; do not put it in reports.
   GET state must show no controller/AP/lease before explicit Start.
2. Start: POST `/api/action` JSON `{action:'start',session:null,boot:null,
   scenario:'empty-calm'}` (later fresh profile `offset-gust`). Header
   X-Sim-Token and exact localhost Origin required.31sample admission means the
   request can take>30s. Record explicit UI intent and result; no retry on timeout.
3. Wait actual fresh firmware4.7.1, Home(10.854,106.807,AMSL10), GPS/EKF/prearm
   and typed configuration. `preflight` action reads actual values; it does not
   arm. `approve` requires confirmReference=true and confirmHome=true and returns
   approvalId tied to session/boot/Home for30s. No synthetic ready status.
4. `takeoff` with approvalId: check raw normal GUIDED+ARM, ACK and post-send mode
   heartbeat, then physics z<-4.5m and observed LOITER. ACK alone is not a climb.
5. Claim neutral with freshest state challenge: `{action:'claim',session,boot,
   neutral:true,challenge}`. Response leaseId/challenge/input. First input must
   be four neutral axes. Bounded pitch+yaw then release; packet axes order is
   roll,pitch,yaw,lift. Inputs<=20Hz, one in flight; chain the response challenge.
   Each packet includes leaseId,seq,clientAt,axes,focused=true,challenge.
6. Verify two separate cases: pointer release sends release/revokes; background or
   >200ms input stall revokes and sends release RC if verifiable. Later input
   cannot revive the lease. Reclaim is explicit and neutral again.
7. LAND requires only current session/boot, not input lease; gateway preempts a
   pending command and requires observed LAND, physical ground and disarm. `end`
   refuses while airborne/armed, then seals review and requests owned shutdown.
8. Cold review: raw MAVLink run/session/indices, input monotonicity/neutral grant,
   target42/1, mode ACK+heartbeat, actual physics frame/epoch, consecutive1200Hz
   RX→durable INTENT→SENT, exact original model sensor/aux byte oracle, AP trace
   receive/parse, clock brackets and closed process/container identity. Use new
   scoped readback, never old CLI writing old evidence. FullG1 remains false.
9. Session package includes Node raw/review plus hashes/references to larger WAL
   and AP trace. `/api/verify-package` verifies embedded hashes/identity and must
   report external raw not embedded; it does not certify complete raw physics.
   Public SAF export/import/reexport must preserve exact selected bytes and
   restore no input/flight authority.

Known integration repair candidate02: normalize root path before containment
checks in budget/server; three exact font URLs map to bundled native/crew02 fonts.
Original01 failure BUNDLE_PATH remains retained. Candidate02 is not accepted until
actual start, UI, control/physics and raw closure are checked.
