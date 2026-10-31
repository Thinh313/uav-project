# KEY74 — roadmap overlay

16/10/2026. Source/candidate/canonical SOT, AUTH73/RECEIVER72 cũ và ENDURE giữ nguyên. Nghiệm thu cuối: COMPLETION-KEY74.md, evidence/key74/final-verification.json.

Đã chuẩn hóa enrollment với issuer/admin/pairing/possession fixture; source/receiver scopes; key staging/activation/cancel/terminal revocation; version/validity và receiver readiness. Bridge cô lập giữ replay frontier/transfer owner xuyên key rotation, policy/generation73 mới phải explicit. Receipt lịch sử giữ byte evidence nhưng current trust bị HOLD khi epoch/key đã thay hoặc thu hồi.

Ưu tiên tiếp:

1. Contract trusted clock và external anchor/provider availability/recovery, trước khi mở secure enrollment thật. Kiểm clock-domain/reboot, stale trust snapshots và frontier consistency; không tự sửa mismatch hoặc khôi phục quyền.
2. Provider mật mã/CSR/identity provisioning ngoài băng, key storage và TLS/channel binding theo target cụ thể. Cần scope/ủy quyền riêng cho tạo key/certificate/chữ ký; KEY74 chỉ dùng mock references/proofs.
3. Authority/root CA lifecycle, staged root rollover và recovery khi mất/thu hồi tất cả keys; policy/registry migrations cần giữ frontier và bằng chứng, không bootstrap/reset ngầm.
4. Hai host/ổ độc lập và mạng thật: revocation propagation, stale ACK, outage, concurrency, rollback/physical powercut, bounded storage/load. Mock anchor cùng host không bảo vệ joint rollback toàn trust boundary.
5. Sau các gate đó mới tích hợp HTTP72/native/Fly/Android/HeraHub và release. Không suy năng lực authentication production/flight/NDAA hay ENDURE24h từ corpus mock.

Không dọn, auto retry/repair, keys fallback, reenroll key/identity đã revoke, sửa source đóng băng hay ký mới trong nhiệm vụ74.
