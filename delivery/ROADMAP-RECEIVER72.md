# RECEIVER72 — roadmap overlay

16/10/2026. Canonical SOT, candidate, ENDURE và module cũ giữ nguyên. Kết quả nghiệm thu cuối nằm trong COMPLETION-RECEIVER72.md và evidence/receiver72/final-verification.json; không suy PASS chỉ từ implementation.

Đã triển khai receiver/sender process riêng, bundle H71 qua HTTP mock, checkpoint chunk, fsync/readback/replay trước receipt, sender receipt binding và restart không auto finalize. Receipt72 là commit marker của receiver mới, không phải receipt69 của sender và không xác thực nguồn bằng chữ ký. `currentIntegrity: PASS` ở phase PENDING chỉ nói các chunk đã nhận đang đúng; gói chỉ hoàn tất ở VERIFIED với receipt kiểm lại đạt. UI luôn ghi “Chưa công bố receipt” khi còn PENDING.

Ưu tiên tiếp theo:

1. Contract xác thực nguồn và receiver/custody, replay protection/cross-host identity, secure transport và quản lý khóa: chuẩn bị mock trước; chưa ký mới trong nhiệm vụ72.
2. Kiểm trên hai máy/ổ độc lập và mạng thật: mất kết nối, mất response, thay receiver, dung lượng/quota, crash/powercut; vẫn không tự dọn. Hiện process/storage riêng trên cùng Mac chưa thay bằng chứng này.
3. Kiểm hiệu suất và truyền corpus lớn gần quota: hiện16KiB chunk để có nhiều checkpoint trên corpus nhỏ, whole envelope bounded giữ RAM; chưa có streaming payload quy mô lớn hay SLA latency/soak mới.
4. Bàn giao có trusted receipt trước khi xem xét retention/tombstone có xác nhận. Không dùng cleanup69 cho frozen generation70. Partial69 repair vẫn là gap cũ, không bị receiver72 tự sửa.
5. Android/HeraHub và tích hợp native/Fly chỉ sau các gate riêng, đúng target/hardware; không suy năng lực bay thật hay quyền từ receipt mock.

Không có autorun, auto retry, cleanup, quyền khôi phục hay gate ENDURE24h mới trong overlay này.
