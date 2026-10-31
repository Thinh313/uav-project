# HANDOFF71 — roadmap overlay

16/10/2026. Canonical SOT và source/candidate/ENDURE giữ nguyên.

Đã đóng gate host/mock: đọc thế hệ CLEAN_CLOSED/FREEZE của ROTATE70, package69+chứng cứ control/custody, adopt/export/import qua ArchiveManager69 nguyên trạng, receipt binding/readback sau restart, explicit reconciliation không nhập trùng. Writer nguồn và preview69 cũ không đổi. Receiver hiện là workspace riêng trên cùng host.

Ưu tiên tiếp:

1. Bên nhận trên máy/ổ độc lập và quản lý danh tính/chữ ký/custody: kiểm nguồn tin cậy, vận chuyển sidecars+package và receipt về sender. Hash nội bộ chưa xác thực nguồn.
2. Quy trình có kiểm để giải quyết partial69 adopt/export/import; hiện giữ HOLD, không auto retry/repair. Phân biệt dữ liệu đã commit nhưng thiếu bridge receipt (đã reconcile được) với69 chưa commit (chưa có API repair).
3. Retention/tombstone ROOT70 có export+receiver receipt và xác nhận rõ trước dọn. Manifests70 vẫn tham chiếu mọi frozen generation; không được gọi cleanup69 để xóa chúng. HANDOFF71 không có endpoint dọn.
4. Android/storage/powercut và schema migration thật khi đủ headroom/thiết bị, rồi mới gate tích hợp native/di chuyển writer gốc/ký phát hành.

Không mở gate SDK/HeraHub/flight/SITL/ENDURE24h hoặc ký từ kết quả handoff mock. Required unrun gates nằm trong COMPLETION-HANDOFF71.md và final-verification.
