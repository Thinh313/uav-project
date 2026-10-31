# RECEIVER72

Receiver độc lập process/storage trên cùng host cho H71. Node + Python stdlib hiện có; không build/install. Chạy từ thư mục aeris, kiểm `df -h /` trước. Không dùng API này cho mạng bên ngoài hay quyền điều khiển bay.

`node native/receiver72/service.mjs --initialize` tạo `.local/receiver72/preview01`, UI `http://127.0.0.1:8827/`. Lần sau bỏ `--initialize`; không xóa lock hay tạo workspace thay thế khi lỗi. GET `/api/state` cho receiverId, boot và token mock process-local. Service mới không kết nối writer/H71/ARC69 cũ.

Sender CLI dùng `R72_SENDER_CONFIG` JSON với dir mới dưới `.local/receiver72/`, endpoint loopback, receiverId đã chọn và jobDir H71 đã xuất. `initialize:true, action:"state"` chỉ chuẩn bị bundle; `action:"send",limit:1` truyền một checkpoint, `action:"send"` explicit tiếp tục phần còn thiếu; `action:"finish"` yêu cầu kiểm/commit, `action:"reconcile"` lấy receipt đã commit. Mỗi invocation là process sender riêng. Không retry fetch thất bại; kiểm trạng thái trước khi người vận hành tiếp tục. Token cũ không sống qua restart. Peer/manifest/receipt trong sender không tự sửa.

Body chunk16KiB; chỉ file đã fsync mới thành checkpoint. Gói có byte lỗi, chunk bị ghi dở, receipt bị ghi dở hoặc file tồn tại khác byte giữ HOLD. Snapshot build còn thiếu file sau crash được explicit finalize hoàn tất từ chính bundle đã nhận; không overwrite. Quota32MiB receiver, manifest64KiB, bundle34MiB và reserve có thể chặn sớm hơn. Giới hạn32 transfers; không tự eviction, không dọn để tránh quota.

Kiểm: `R72_RUN=<fresh-name> node native/receiver72/tests.mjs`; sau đó `R72_RUN=<fresh-name> node native/receiver72/process-qa.mjs` (cần quyền loopback bind). Mỗi run tạo namespace evidence mới và giữ cả failure. `python3 native/receiver72/verify.py <receiver-root> --output <fresh-output>` kiểm hash/receipt bằng implementation khác. `native/archive69/verify-packages.py` kiểm byte/WAL/frame SHA; semantic vẫn từ verifier JS đã pin.

Không có cleanup, quyền, MAVLink/flight/SITL/HeraHub SDK, chữ ký hay lựa chọn candidate. Receipt unsigned và control proof nội bộ không chứng minh nguồn tin cậy; hai máy/ổ độc lập, secure transport/auth, powercut vật lý, Android chưa kiểm.
