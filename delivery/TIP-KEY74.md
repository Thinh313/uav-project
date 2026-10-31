# KEY74 — provisioning và key lifecycle cho AUTH73

16/10/2026. Scope đã được người dùng ủy quyền: contract mock/replay, không SDK/khóa thật/chữ ký mới. Một agent tách SPEC/BUILD/VERIFY; không gọi là review độc lập. Ngân sách32MiB, sàn20GiB+32MiB; không build/install/SITL/ENDURE workload.

REQ-01: Danh tính source/receiver có realm, principal, scope roots/receiverIds, key reference mock/version/validity và issuer. Enrollment cần pairing nonce+boot+TTL, admin approval và mock subject-possession proof. Chặn tự cấp, wrong role/root/receiver/issuer/realm, reuse identity/key/fixture reference.
REQ-02: Rotation explicit STAGE→ACTIVATE (hoặc CANCEL), giữ scope, tăng key version, readiness ACK đúng các receiver hiện tại. STAGED chưa dùng được; sau activate old RETIRED, new ACTIVE; không tự kích hoạt, không sửa AUTH73 policy/log cũ.
REQ-03: Thu hồi key/danh tính terminal, chặn stale proof và current receipt trust, không khôi phục quyền. Key/identity hết hạn bị chặn theo clock mock. Giữ lịch sử/receipt, không xóa dữ liệu hay tự dùng key khác.
REQ-04: Bridge cô lập dùng AUTH73 nguyên trạng ở generation/policy mới; security epoch fence và replay sequence/nonce frontier giữ xuyên rotation/restart. Không reset source sequence khi thay key, không auto migrate, explicit fresh nonce/claim để tiếp tục. Conservatively reserve frontier trước side effects AUTH73; lỗi sau reserve không tự retry.
REQ-05: Registry append-only+fsync+mock external anchor, bounded/quota/floor/single writer; kiểm restart, rollback/torn, SIGKILL windows, adversarial cases và22 corpus H71 qua R72/AUTH73 mới. Python đối chiếu implementation riêng.
REQ-06: SHA preservation toàn baseline+ENDURE+preview72; TIP/ADR/Completion/roadmap overlay/module+artifact fingerprints. Không đổi module/source/candidate/canonical SOT cũ, không ký hoặc tự dọn.

Kiến trúc: native/key74; evidence/key74; fixture anchors/auth logs chỉ tại evidence/auth73/key74, receiver stores chỉ tại evidence/receiver72/key74. Registry master policy pin allowed source roots/receiverIds và authority/admin mock. Provider73 được cấp bởi harness, không có enrollment/proof-registration endpoint cho sender. Operations kiểm exact schema+expected revision/requestId, TTL và proof domain. Mock anchor cùng host không bảo vệ joint rollback; true PKI/TLS/key storage/trusted clock/remote enrollment NOT_CHECKED.

Decision: ưu tiên source+receiver lifecycle; authority/root CA rollover, recovery sau thu hồi toàn bộ khóa và multi-host sync là gate tiếp, không ngầm phục hồi trong nhiệm vụ này. Không UI mới vì yêu cầu hiện tại là contract; không retrofit HTTP72/Fly.
