# SIMSITL76 — pitch+yaw và proximity qua ArduPilot thật

16/10/2026. **DONE / READY trong phạm vi INTERNAL QUAD SITL; không là nghiệm thu Hera, SIM32 pacing hay sản phẩm.** Một agent thực hiện SPEC/BUILD/VERIFY; bộ giải mã thứ hai không là kiểm định độc lập bởi người khác.

Dùng ArduCopter4.7.1/dbe79216 binary SHA011627d4… đã có, imageUbuntu534baea6… cố định, localhost5896, internal quad physics, requested speedup1. Không build/install, không force arm, không sửa source/candidate/trust/SOT/ENDURE, không SDK/HeraHub/HID/Fly hay ký mới. Internal physics khác SIM32 external backend; không suy ra Hera giống thật hoặc pacing đã sửa.

## Kết quả thực run03

| Phép kiểm | Quan sát và phạm vi |
|---|---|
| Preflight | Firmware/version, typed named profile reads, GPS/EKF/Home và AP proximity observed; đọc lại cấu hình sau EKF startup; normal arm.57parameter entries trong snapshot có cả unsolicited boot data, không gọi tất cả là named profile validation. |
| Pitch+yaw |4/4tổ hợp dấu RC2±50/RC4±80,1.5s/case, trong Loiter: RC echo và attitude/yaw-rate đúng dấu; signed pitch deltas0.0221–0.0357rad, yaw rates0.535–0.539rad/s; |roll/pitch|<0.6rad và altitude3..7m trong phạm vi check. Guided return-to-origin giữa ca được ghi raw, không reset pose ngầm. |
| Đối chứng tránh vật cản |AVOID_ENABLE0 → vị trí north đạt12.3477m, đi qua planeảo12m. Sau explicit return, readbackAVOID_ENABLE2 → tiến đến gần vật cản rồi dừng, minimum surface clearance1.665346m (trừ sphere reference0.3m), tail3s max|vx|0.110109m/s,160proximity frames trong ca. Margin fixture2m; không xác nhận claim Hera10m/creep. |
| Mất/khôi phục sensor |Ngừng virtual sensor TX khi RCneutral: last forward distance boot112776ms, fresh attitude114927ms, proximity output hết hạn. Khi explicit restore, AP xuất dữ liệu mới. Không chứng minh aircraft tự dừng khi người lái tiếp tục đẩy cần hoặc mất sensor thật. |
| Kết thúc |LAND mode9, fresh landed_state1, heartbeatdisarmed(base_mode89), rồi writer đóng và container được stop/remove sạch. Container stop không thay bằng chứng hạ cánh. |

Virtual sensor8sector DISTANCE_SENSOR từ ray FRD chuyển bằng attitude sang NED, cm wire range0.2..20m. AP xuất proximity đã tổng hợp, không chỉ ACK hoặc local send. Virtual plane không có lực contact trong built-in world; baseline crossing là ca software negative, không là hướng dẫn huấn luyện va chạm. Sensor message không có target/session; host guard pin context, không có claim firmware xác thực sender.

## Bằng chứng và AC

Mock **45/45**, lifecycle/resource mock **8/8**, live checks **10/10**, cold semantic gates **7/7**, final adversarial bites **8/8**. Các suite độc lập về phạm vi, không cộng thành tỷ lệ trưởng thành sản phẩm.7/7REQ scoped checked: R76-01preflight,02pitch/yaw/landing,03proximity/braking,04faults,05raw/replay,06lifecycle,07resources/preservation.

Raw5931rows,13480APframes,6639TXframes,741virtual sensor batches. Second Python parser uses bitwise CRC/pinned full dialect; confirms sequence/SHA chain, RX retained, every TX intent paired with write-return and behavioral criteria from raw. RawSHA`b13d78fd6d1b45f60c7aa207b8cabecb9319702bbc93e5cd27e7a195df13c60e`. Hashes are local integrity, not signatures or authentication. Captured all MAVLink bytes; no1200Hz external physics full-frame/oracle claim. Initial/final clock domains remain separate; speedup1 request does not establish stable real-time pacing.

Eight bites: missingrow, resealedCRC fault, wrongtarget validCRC, wrongavoidparam validintegrity, missinglandingmarker, unexpectedbootASCII, noattituderesponse despiteACK and collisionpenetration despiteACK. Final parameter bite first passes raw integrity before semantic rejection. No raw fixture copies/deletions; mutations in memory with reproducible code.

## All attempts and repairs retained

run01 is a reservation only: case-sensitive absent-container string gate failed before creation;0AP/client/flight. run02 is actual container1: guest-ready gate required SERIAL0 console line that was not printed before connection;0client/arm; container stopped/removed, error GUEST_READY retained. Explicit run03 is actual container2/final: passive kernelLISTEN5760 proof in exact CID, no TCP probe, one client and one successful flight. Source versions archived before actual runs. No auto retry/reconnect/force arm or further starts;2actual-container budget exhausted.

Mockfirstfailure legacy decoder lackedRC70; fixed harness checks, no legacy source change. Cold-parser-v1 rejected12interleaved startup ASCIIbytes`Init Gyro**\n`; narrow exact sequence/bound≤64/beforeARM exception added, originalraw and failedparser retained. The initial wrongparam bite failed at TX pairing too early; v2 pairs return and checks semantic rejection. No failed receipt rewritten or counted as successful flight.

## Bảo toàn / tài nguyên

43,803protected paths exactSHA before/after,0missing/changed; active runtime pins and source archives also exact. This is point-in-time equality, not continuous original-path presence or ENDURE24h acceptance. All ENDURE attempts/history remain unchanged.

Launchminimum22GiB, agreedfloor20GiB, runtime stopreserve20.5GiB; minimum observed in accepted run28.790GiB, final28.763GiB. Module/evidence/state approximately3.43MiB before reports of256MiB campaign budget. Onboard logging disabled intentionally; full MAVLink wire retained. CPU1/RAM256MiB/read-only root+16MiB tmpfs, boundedstate/logs/deadline. All ownedcontainers gone; no new server/preview kept. Docker image prune ran after both actual containers,0B reclaimed; no volume/container pruning elsewhere. No project/tmp copies, installs or scratch/build folders, no user/evidence files deleted.

## Remaining gates

Reference one-flight functional evidence only: no controlled repeatability/counterbalanced performance proof, real Hera mass/inertia/motor/sensor calibration, loaded/gust cases or high-rate/sustained coupled turns. No physical impact/collider terrain, live3D/audio/HID, nor dropout-under-continuing-input acceptance. Next justified work is bring these measured protocol cases into the isolated SIM32 external-physics path when its performance/resource gates permit, and collect the15missing Hera data groups from SIMFEEDBACK75. No automatic next campaign or signature authorized by this report.

Authoritative receipts: `final-verification.json`, `cold-readback-run03.json`, `bites-run03-v2.json`, `run03/driver-result.json`, `run03/wire.jsonl`, `run03/launch.json`, `run03/closure.json`, `preservation-before/after.json`, sourcepins/archives and artifactmanifest. Readme at `pilot/simsitl76/README.md`.
