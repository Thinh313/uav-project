# P1 OPERATOR · TIP / Blueprint

Goal: operator hoàn tất một nhiệm vụ trong APK cô lập và thực hiện nhiều thao tác payload hợp lệ trên Fly chính, không phải mở lab rồi restart sau mỗi lệnh. Đóng UI-COPY-01, unit/range và one-shot limit có nghĩa. Scope engineering Android/SITL, chưa HeraHub/Phase One/remote two-operator/production/AI autonomy.

Baseline: native/native98verify development05 và evidence/native98verify/module-fingerprints.json. Mọi source/evidence cũ bất biến. Namespace mới native/operator01, evidence/operator01, delivery/COMPLETION-OPERATOR01.*. Reuse module source only, không copy whole project; package vn.rtr.aeris.operator01 để không cạn UI quota hay sửa private old apps. Cùng AVD sở hữu emulator-5582 và isolated ArduPilot image/binary đã pin; native MAVLink pure channel, passive bootstrap/observer. Builder phải pin protocol refs/decisions, source/APK, parameters/rig và workload.

## Decisions được Contractor chấp thuận

- D1: gimbal repeated absolute setpoints dùng GIMBAL_MANAGER_SET_PITCHYAW287, explicit manager/device, deg UI→rad wire, unused rates NaN; không autoreplay/timer resend. Không quảng cáo continuous joystick/rate control khi stop/deadman chưa có proof. Tối đa10 explicit input intents/s; UI pacing rõ, không âm thầm drop một intent đã nhận.
- D2: camera capture single-shot cmd2000 có captureSeq riêng theo camera tăng đơn điệu,param3=1,param4 sequence. Mỗi explicit new intent tối đa1 wire attempt, không retry. Chưa đảm bảo reliable-command retransmission protocol.
- D3: ACK77 cho repeated camera commands không có invocation id nên chỉ ghi ACK_UNATTRIBUTED, không complete/unlock/promote intent khác. Image index/settings/pose là independent observations hoặc CONSISTENT_UNATTRIBUTED, không execution/media/causality. Không dùng browser-counter làm ảnh thực. Discovery512/authority1001 mơ hồ vẫn giữ fence; không suy ACKdevice1 thành quyềndevice2.
- D4: authority/capability/current target/generation/revision/foreground/freshness recheck ở send boundary sau WAL. No grant/reconnect/retry/restore tự động; revoke/transfer/boot/linkloss giữ pending UNKNOWN. Gimbal primary manager status phải fresh/đúng device. Chọn payload không chuyển quyền.
- D5: UI chính của Fly dùng nguồn native. Replace fake shutter/payload/zoom/settings handlers và fake shotcount; lab chỉ giữ diagnostic. Status unknown khi linkclosed/stale/uninitialized; controls units/ranges tách biệt, select target rõ, observed vs requested rõ, quota/limit/UNKNOWN visible. Giữ RtR white/black/yellow phụ, blur-glass islands và typography/icon system cũ; chưa UI rewrite.
- D6: intent/history/queue/session có quota hữu hạn, raw durable không xóa. Đề xuất512intents/session được phép nếu tính RAM/journal budget và tests; quota phải chặn trước wire và UI báo, không tự retire evidence. Không gỡ mọi bound để đạt replay.

## Acceptance criteria bắt buộc

P1-A01: trong một APK/cùng mission, operator tạo >=3 capture intents, >=2 zoom và2 focus values, >=3 gimbal angles, sau đó AUTO→ground/disarm→review; một socket/generation, mỗi intent <=1 write. UI Fly chính phải thực hiện thao tác, không coi lab-only API là đạt.
P1-A02: UNKNOWN đúng cho linkclosed/stale/bootmissing; %/°/rad/range/default/control validation đúng. Không disarmed từ placeholder, không fake images.
P1-A03: repeated requests là explicit new intent with owner/session/revision/sequence and exact prepared→wire SHA binding; no automatic retry from timeout/ACK.
P1-A04: delayed/duplicate/old/wrong ACK và observations không chứng minh causality/execution; ACK_UNATTRIBUTED không promote request, actualImages0 cho synthetic.
P1-A05: manager/device2 identity đúng, explicit msg287 target/device/units và rate bounds; no broadcast/no stale primary; no use ACK to confer authority.
P1-A06: handover/lease/operator loss giữa prepare→write từ chối wire cũ; new owner có explicit consent, không inherit pending. Mock mandatory + practical Android action case.
P1-A07: commonlink/background/APboot/cameraboot revoke/freeze đúng, pendingUNKNOWN, no reconnect/regrant/resend. Android/SITL separate active-owner+pending loss case, passive observer ground/disarm and nativeUNKNOWN review.
P1-A08: rate/queue/intent/WAL/disk bounds explicit refusal before wire; retain raw, no evidence auto-delete; flight heartbeat remains independent of presentation throttling. Fault injection mandatory.
P1-A09: stale/out-of-order/duplicate/contradictory observations rejected or labeled uncertainty, preserve bytes; known state tied to correct boot/session/target.
P1-A10: mock/adversarial before Android; pinned development APK real Android–SITL nominal + loss; independent generated upstream parser verifies CRC, sequence, command units/route/plan/readback and operation count. At least one held-out parameterized sequence not used to tune implementation. Root/QA verifies, not Builder verdict alone.
P1-A11: process+coldboot persistence retains closed raw/workspace/reviews and old private data; no restored authority or automatic raw/connection generation, signature/SHA pins preserved. Freeze protection includes N98verify+N98accept and all prior baselines.
P1-A12: allAC pass for P1 DONE. Two authenticated remote operators, real PhaseOne/Hera, broad mapping quality, performance superiority, production and physical safety NOT_CHECKED outsideP1; no whole-product DONE.

## Work / verification budget

Builder first implement/mock/source delta and report; do not spawn agents or touch runtimes without message to Root. Root/QA may review while Builder works. Then one dev build (targeted repair allowed), bounded Android/SITL nominal+fault+restart. Start runtime only after root admission/preservation and serialized ownership. Keep same speedup1/freshness1500ms/fsync-before-consumer/send; no physics frame dropping. No automatic campaign retry: retain failure, identify cause, targeted repair, finite next case. Stop on resource gate or no new evidence after repeated approach; report blocker, not DONE.

Output: source + scoped ADR, tests/data/raw/pins; Builder Completion with AC disposition, missing, source delta and exact commands. Contractor Verify includes USER OUTCOME,AC coverage,scenario results,technical health,value evidence,limits/disposition and overall READY/NOTREADY. Extra internal steps are not milestones and not end-user completion reports.
