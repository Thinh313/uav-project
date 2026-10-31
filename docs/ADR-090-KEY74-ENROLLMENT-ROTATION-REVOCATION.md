# ADR-090 — mock identity lifecycle và AUTH73 epoch/replay frontier

Accepted16/10/2026. Enrollment qua pairing→admin authorization+subject possession fixture; key references chỉ mô tả fixture, không chứa hoặc tạo key material thật. Roles/purpose/realm/issuer/receiver scopes và validity phải bind toàn payload. Oracle là trusted harness test double, không chứng minh possession mật mã; production capability=false.

Rotation stage giữ old ACTIVE, new STAGED. Activate cần admin, proof possession đã stage và ACK readiness đúng từng physical receiver trong scope, current receiver principal/key; scope không được mở rộng. Activate tăng security epoch và key version, old RETIRED/new ACTIVE. Revoke key/identity terminal, hủy staging liên quan, không fallback hoặc auto re-enroll. Epoch thay đổi làm old AUTH73 policy fail closed; không rewrite old logs/policy. Snapshot policy mới yêu cầu generation AUTH73 mới, explicit pairing/claim và floor/anchor gates.

Registry giữ sender/receiver replay frontier theo principal+physical receiver+direction xuyên key rotation, đồng thời nhớ challenge nonce. Bridge phải prevalidate claim bằng AUTH73 rồi sync reserve frontier trước ghi AUTH73; crash sau reserve có thể bỏ qua sequence nhưng không được reuse. Sequence gaps được phép, không auto retry. Frontier không thay receipt/data verification72; archived receipt giữ byte evidence và được báo HISTORICAL_ONLY khi current epoch/key không còn hợp lệ.

Registry+anchor có flock riêng, exclusive immutable records, fsync và bounded quota. Log sync trước anchor sync; mismatch giữ HOLD, không repair/dọn. Reopen chỉ đọc, volatile pairing/boot cũ bị fence. Admin operations requestId/revision/TTL nên replay hay approval stale không ghi thêm.

Tham khảo khái niệm issuer/subject/validity/key usage/revocation từ [RFC5280](https://datatracker.ietf.org/doc/html/rfc5280); đây là contract ứng dụng mock, không X.509/CRL implementation hay tuyên bố compliance. Các cập nhật/errata và PKI production phải thẩm định riêng. Source capture và SHA nằm trong evidence/key74/sources.json. Không private key, MAC, digital signature, certificate mới hay software signing.

Giới hạn: authority/root CA lifecycle thật, cryptographic provider, secure enrollment transport, trusted clock, hardware key/external anchor, joint rollback toàn trust boundary, recovery sau mất/thu hồi tất cả keys, multi-host/Android/HeraHub và vận hành dài hạn chưa kiểm. Bootstrap root có quyền xác lập scope là cấu hình do operator/harness pin, không tin self-asserted identity từ wire.
