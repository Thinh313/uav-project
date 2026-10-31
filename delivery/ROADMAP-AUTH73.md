# AUTH73 — roadmap overlay

16/10/2026. Canonical SOT/source/candidate, ENDURE và preview72 giữ nguyên. Nghiệm thu scoped nằm trong COMPLETION-AUTH73.md và evidence/auth73/final-verification.json.

AUTH73 bổ sung contract mock cho identity/purpose/epoch/receiver/package binding, challenge nonce, source sequence bền vững, sender intent và receipt binding. Log và mock anchor giữ riêng; restart không khôi phục challenge hoặc quyền ghi dữ liệu. Source sequence tăng nghiêm ngặt trong phạm vi principal/policy/receiver ledger; cho phép gap để không khóa luồng khi request chưa tới receiver. Receipt lịch sử được đối chiếu riêng với trạng thái dữ liệu receiver hiện tại.

Ưu tiên tiếp:

1. Chuẩn hóa provider xác thực mật mã và identity provisioning/key lifecycle theo contract đã kiểm; registry nguồn tin cậy, revocation, policy migration và key-role/domain separation. Chưa có quyền tạo khóa/chữ ký hoặc release mới từ nhiệm vụ73.
2. Trusted clock và external durable anchor thật: clock-domain/reboot mapping, anchor outage và quy trình phục hồi có kiểm. Mock anchor cùng host không bảo vệ joint rollback ledger+anchor+oracle.
3. Transport xác thực hai chiều giữa hai host/ổ độc lập, channel/session binding và failure recovery. AUTH73 hiện là adapter mock-call/subprocess; HTTP receiver72 cũ vẫn unsigned, chưa retrofit hay bảo mật production.
4. Corpus lớn, streaming, resource/latency/long-run gates; adapter73 hiện giới hạn manifest16KiB/log1MiB/256 events/8 challenges mỗi boot, không eviction tự động.
5. Chỉ sau các gate trên mới bàn tới tích hợp runtime/Fly/Android/HeraHub và release. SDK/phần cứng/flight/cleanup/repair partial69 đều cần scope và nghiệm thu riêng.

Không dùng kết quả mock làm bằng chứng authentication thật, ảnh thực, quyền điều khiển, ENDURE24h hoặc chữ ký phần mềm.
