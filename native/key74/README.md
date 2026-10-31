# KEY74 — identity provisioning / key lifecycle mock

Contract library và test harness, chưa là dịch vụ enrollment production. Không tạo key material, MAC, digital signature, certificate, APK hay software signature. `fixtureRef` là nhãn giả lập, không là public key thật. Xem contract.json và docs/ADR-090-KEY74-ENROLLMENT-ROTATION-REVOCATION.md.

Operator/harness pin master config: realm, authority/admin, allowed roots và physical receiver IDs. Receiver enrollment trước source. `beginEnrollment` tạo pairing nonce/boot/TTL; admin request bind config/registry/revision/payload; mock CA cung cấp admin authorization và subject-possession fixture. Sender không có endpoint tự đăng ký proof hoặc tự cấp identity.

Rotation: `STAGE` với possession của key kế tiếp giữ old ACTIVE/new STAGED; `ACTIVATE` cần admin và ACK readiness đúng receiver principal/key/id trong scope. Scope không đổi, version tăng; old RETIRED/new ACTIVE. `CANCEL` hoặc thu hồi staged key giữ dữ liệu và không tự activate. `REVOKE_KEY`/`REVOKE_IDENTITY` terminal, không fallback/re-enroll/recover tự động.

Bridge `Receiver74`/`Sender74` subclass AUTH73 nguyên trạng. Current registry epoch/key/scope được kiểm trước mỗi operation. Thay key/epoch tạo policy+ledger generation mới một cách explicit, không sửa log/policy cũ. Registry giữ sequence/nonce/frontier và transfer owner xuyên generation; reserve được sync trước side effect73. Lỗi sau reserve có thể làm gap sequence; dùng fresh nonce/higher sequence, không retry request cũ. Low-level append/register-provider là trusted in-process plumbing, không API wire/untrusted caller.

Current authentication sau revoke/rotate bị HOLD; `archivedReceipt` chỉ trả historical byte/proof consistency và currentTrust=HOLD_REVALIDATION_REQUIRED. Mock CA/oracle/anchor cùng host không chống attacker sửa/rollback toàn trust boundary. Root CA rollover, recovery sau mất/thu hồi tất cả keys, cryptography, TLS/secure enrollment, trusted clock và hardware integration chưa kiểm.

Từ thư mục aeris, kiểm `df -h /` và dùng tên run chưa tồn tại:

```
K74_RUN=ten-moi node native/key74/tests.mjs
K74_RUN=ten-moi node native/key74/corpus-qa.mjs
K74_RUN=ten-moi node native/key74/process-qa.mjs
python3 native/key74/verify.py evidence/key74/corpus-ten-moi --output evidence/key74/ket-qua-moi.json
```

Không cần dependency/build/install. Mỗi run giữ toàn bộ evidence, kể cả fault/rollback/torn replicas. Chỉ dùng namespace native/key74, evidence/key74, evidence/auth73/key74 và evidence/receiver72/key74. Không chạy initializer trên preview/module/source/candidate/ENDURE cũ; không tự sửa anchor hoặc xóa lock khi HOLD. Single-agent SPEC/BUILD/VERIFY không là auditor độc lập.
