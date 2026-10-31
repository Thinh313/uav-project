# RECEIVER72 — receiver độc lập cho HANDOFF71

16/10/2026. Dependency: HANDOFF71 package/proof/custody; frozen ARC69 semantic verifier.

SCAN: H71 đã kiểm custody trên namespace69 riêng nhưng receiver còn trong tiến trình bridge. Dung lượng gate hiện 22,43 GiB; baseline 32.826 đường dẫn khớp SHA. Quyết định: tiếp tục host mock nhỏ, ngân sách mới 48 MiB, không build/install. Một agent tách SPEC → BUILD → VERIFY; không gọi là review độc lập.

REQ-01: Receiver tiến trình và workspace riêng; chỉ nhận bytes qua HTTP loopback, không nhận đường dẫn sender/source. Package69, proof/control71 và custody phải bind đúng job, generation, manifest, SHA và receiverId.

REQ-02: Truyền chunk có checkpoint bền vững, bounded body/quota/admission, chặn sai offset/SHA/target, gói thiếu/hỏng không có receipt. Retry chỉ theo thao tác explicit, chunk trùng đúng byte không nhân bản. Gói hoặc chunk ghi dở giữ HOLD, không ghi đè/xóa.

REQ-03: Receipt chỉ sau fsync + readback + replay đầy đủ. Sender kiểm receipt trên bundle của mình rồi ghi bền vững. Mất response sau commit phải đối chiếu receipt hiện có, không nhập lại.

REQ-04: Restart receiver/sender giữ byte/checkpoint/receipt; token và boot đổi; không tự finalize, dọn, replay quyền. Thử SIGKILL trước receipt/sau commit, partial upload, corruption, quota, double writer và 22 corpus H71.

REQ-05: Dashboard receiver phân biệt PENDING, VERIFIED và HOLD, trình bày hash/identity/scope, kiểm browser. Không có endpoint quyền/dọn.

REQ-06: Kiểm lại baseline + ENDURE, sàn 20 GiB; giữ mọi fault artifact. Không đổi source/candidate/canonical SOT/modules cũ, SDK/SITL/emulator/APK/signature.

AC: Mỗi REQ có evidence định lượng; Python verifier đối chiếu byte/receipt độc lập thuật toán; HTTP test dùng process receiver và sender khác nhau. Same-host process/storage isolation chỉ là engineering mock, hai máy/ổ độc lập và xác thực danh tính/PKI/powercut vật lý NOT_CHECKED. Không có signature mới; SHA không xác thực nguồn.

Decisions: không cần hỏi lại vì yêu cầu hiện tại đã ủy quyền receiver mock/replay. Chọn thêm module thay vì sửa H71. Receipt72 là commit marker mới; không giả là receipt ARC69 hay chứng cứ ảnh thực. Dữ liệu staging giữ nguyên, chỉ explicit finalize có thể hoàn tất file còn thiếu từ bytes đã hash đúng; file tồn tại khác byte giữ HOLD.
