# RECEIVER72 — Completion / Verify

16/10/2026. STATUS: DONE trong phạm vi engineering mock/replay trên host. OVERALL: READY cho scope này; chưa là remote receiver thương mại, Android hay release ký.

Receiver chạy tiến trình và workspace riêng, chỉ nhận manifest/chunk qua HTTP loopback. Sender đóng bundle từ H71 đã xuất, receiver kiểm byte, proof/control/custody, replay package69 và fsync snapshot trước ghi receipt72. Sender đối chiếu receipt với bundle gốc của mình và lưu bền vững. Không đọc writer nguồn từ receiver, không nối tới engine điều khiển.

## Requirement coverage

6/6 REQ implemented và checked (100%) theo TIP-RECEIVER72, không đếm các gate ngoài scope thành PASS.

| REQ | Kết quả | Chứng cứ |
|---|---|---|
| 01 / độc lập process, byte/source/target binding | PASS same-host; PID sender/receiver khác nhau, 22 corpus đi qua HTTP | process-r02/results.json; unit-r04/results.json |
| 02 / checkpoint, thiếu/hỏng, quota và disk floor | PASS; chunk sai/thứ tự sai/ghi dở giữ hoặc từ chối; không có receipt gói thiếu | unit-r04/results.json; process-r02 interrupted body và offline receiver |
| 03 / fsync-readback/replay, receipt về sender | PASS; mất final response explicit reconcile đúng receipt cũ, không ghi thêm | process-r02/results.json; Python22 receipt/proof +23 package/frame checks |
| 04 / restart, crash, không khôi phục quyền | PASS; ba SIGKILL ở CHUNK_SYNCED/SNAPSHOT_VERIFIED/RECEIPT_SYNCED, restart chỉ đọc, explicit finish | process-r02/results.json; runtime-final.json (96 file byte-identical) |
| 05 / UI receiver và trạng thái chính xác | PASS 7/7 tại viewport1280×720, console errors0; pending không công bố receipt, receipt giữ sau reload/restart | browser-qa.json; browser-pending.png; browser-final.png |
| 06 / preservation, dung lượng, scope | PASS32.826 đường dẫn +5.051 ENDURE khớp SHA, native source pins không drift, không dọn/ký/build | preservation-before.json; preservation-after.json; module-pins.json |

## Quantitative verification

- Unit/fault cuối: **31/31**; HTTP/multi-process/crash cuối: **15/15**, bao gồm **22/22** corpus H71. Đây là các nhóm lồng nhau; không cộng22 thành số ca khác.
- Python implementation riêng: **22/22** receipt/chunk/proof/custody và **1/1** preview; checker ARC69 riêng: **23/23** package/Base64/WAL/frame/SHA. Semantic replay vẫn dùng verifier JS frozen, không gọi đây là auditor độc lập.
- Syntax: **7/7** module JS hợp lệ, errors0. Không build/install/type pipeline cần thiết cho module Node/browser này.
- Managed restart preview: **96/96** file SHA giữ nguyên; receipt `15df74a0a3d0adbf444e34b9a57f3e73153b7426f614b5acab81a2f2789a6ce0`; boot đổi; receiverId giữ nguyên. Các trạng thái legacy bằng nhau ngoại trừ observation `quota.freeBytes` động; file nguồn/selection/quyền không đổi.
- Snapshot bảo toàn cuối ghi `freeBytes=23633920000` (~22,01GiB), trên sàn20GiB; budget task48MiB được kiểm lại trong final-verification.json. Không tạo scratch/dependencies/build copies; không xóa gì để thu hồi dung lượng.

Preview: http://127.0.0.1:8827/; PID93820, lock93828 tại observation runtime-final. Workspace `.local/receiver72/preview01`, sender `.local/receiver72/sender-preview01`; source H71/ARC69/R70 cũ giữ nguyên. Receipt72 tách biệt receipt69 cũ và chỉ chứng minh consistency unsigned.

## Incidents / refinements retained

unit-r01 dừng do expectation tên lỗi `SCHEMA|KEY` khác lỗi đúng `EXACT_SHAPE_REQUIRED`; extra source path đã bị chặn đúng. unit-r02 (26 ca), unit-r03 (30 ca) và process-r01 (14 ca) là development runs được giữ nguyên. Trong quá trình development bổ sung kiểm partial snapshot, lock loss và checkpoint sender; final-source gate là unit-r04 + process-r02 với module-pins.json, không dùng run đang chạy/mã cũ làm nghiệm thu cuối.

Observation legacy lần đầu giả định JOURNAL68 có wrapper `state` và so toàn bộ view kể cả freeBytes; sửa riêng phép đọc/so sánh, lưu runtime-observation-incident.json và cả before/after. Không phục hồi file, sửa history hoặc thay dịch vụ cũ.

## NOT_CHECKED / gaps

Hai máy/ổ độc lập, mạng thật, authenticated identity/secure transport/chữ ký và trusted external rollback anchor; powercut vật lý/Android/HeraHub; dữ liệu lớn sát quota, memory/latency SLA/soak mới; repair partial69, cleanup/retention và tích hợp Fly/release. Whole-store coherent rewrite/rollback không được SHA tự thân phát hiện; cần anchor tin cậy ở bước tiếp. Receipt sender lưu offline là bằng chứng lịch sử; current receiver integrity phải GET/reconcile lại, không suy từ file receipt cũ.

Không có SDK, SITL/emulator/APK, flight commands, tự retry/finalize/dọn, phục hồi quyền hay chữ ký phần mềm mới. ENDURE không có kết luận24h mới. Giữ toàn bộ fault/corrupt artifacts. Quyền khôi phục0 và ảnh thực0 ở cả receiver/sender.

FILES CHANGED: chỉ tạo native/receiver72/*, evidence/receiver72/*, docs/ADR-088-RECEIVER72-PROCESS-TRANSPORT.md và delivery/{TIP,ROADMAP,COMPLETION}-RECEIVER72.md. Canonical SOT không đổi; roadmap overlay ở ROADMAP-RECEIVER72.md.
