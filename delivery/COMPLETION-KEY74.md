# KEY74 — Completion / Verify

16/10/2026. STATUS: DONE cho contract cấp danh tính/vòng đời khóa mock/replay. OVERALL: READY trong scope này; chưa PKI/cryptographic authentication hay triển khai endpoint production.

Enrollment source/receiver cần realm/config/issuer/admin, pairing nonce+boot+TTL, approved scope và mock possession proof. Key descriptors có version/validity/fixture reference, không chứa hoặc sinh cryptographic key material. Rotation STAGE giữ old ACTIVE/new STAGED; ACTIVATE cần ACK đúng các receiver/principal/key hiện tại, tăng version/epoch và retire old key. Thu hồi key/identity terminal, không fallback/re-enroll/khôi phục quyền. Giữ history/receipt/dữ liệu, không xóa.

Bridge74 dùng AUTH73/RECEIVER72 nguyên trạng trong namespace mới. Policy epoch/key đổi yêu cầu generation73 mới explicit, không rewrite policy/log cũ. Registry giữ sequence/nonce/transfer-owner xuyên rotation và reserve trước side effect73; nguồn không thể reset sequence khi thay key. Archived receipt chỉ là historical consistency, không current authentication. Không retrofit HTTP72/Fly hay dùng SDK.

## Requirement coverage

6/6 REQ implemented và checked (100%) theo TIP-KEY74, giới hạn ở mock/replay.

| REQ | Kết quả | Chứng cứ |
|---|---|---|
| 01 / identity/issuer/scope/pairing/possession và receiver binding | PASS; self-assertion, wrong root/role/realm/epoch/receiver, unknown/none proof, reused identity/key/reference bị chặn | unit-r03/results.json; contract.json |
| 02 / stage/activate/cancel, validity/version/readiness | PASS; STAGED chưa dùng được, ACK sai receiver/missing, future/expired/stale approval bị từ chối; concurrent activate đúng một commit | unit-r03/results.json; corpus-r02/results.json |
| 03 / revocation terminal và historical evidence | PASS source và receiver; không auto rotate/re-enroll/fallback; old receipt/data giữ byte, current trust HOLD | unit-r03/results.json; corpus-r02/results.json |
| 04 / AUTH73 bridge/policy generation/replay frontier | PASS; fresh policy/nonce/higher sequence qua key rotation; reset sequence bị chặn; reserve gap giữ frontier và explicit recovery | unit-r03/results.json; corpus-r02/results.json |
| 05 / durability/fault/corpus/Python | PASS; cold reopen byte-identical, rollback/torn giữ HOLD; actual SIGKILL ở log/anchor boundaries;22 corpus | process-r02/results.json; Python final receipts |
| 06 / preservation/sàn/budget/docs/fingerprint | PASS trong final-verification.json;38.437 protected paths,5.051 ENDURE,26 preview72 SHA khớp; không đổi module/source/candidate cũ | preservation-before/after.json; module-pins.json; artifact-manifest.json |

## Quantitative verification

- Unit/fault cuối: **54/54**, **23 fixtures** (`unit-r03`). Corpus: **22/22** (`corpus-r02`), luân chuyển source/receiver xen kẽ, kiểm epoch, higher sequence, sai receiver, revoke, cold reopen và historical data/receipt.
- Process fault: **2/2** actual child SIGKILL qua public mock enrollment control (`process-r02`). Log sync trước anchor → HOLD, không repair; anchor đã sync → đọc lại đúng receipt, replay old-boot bị chặn, không auto pairing/dữ liệu/quyền.
- Python lifecycle implementation riêng: **22/22**, **110/110 negative bites** (admin body swap, unknown proof, wrong receiver ACK, sequence reset, nonce reuse).
- Frozen Python AUTH73 verifier: **44/44** historical generations, **132/132 negative bites**; frozen Python72 byte/control/receipt verifier: **22/22**; frozen ARC69 package/Base64/WAL/frame/SHA verifier: **22/22**. Các nhóm lồng nhau; không cộng thành số năng lực riêng hoặc bằng chứng cryptographic authentication.
- Syntax/build health và preservation/budget/free bytes cụ thể nằm trong module-pins.json/final-verification.json. Không build/install/dependencies/emulator/SITL/SDK; semantic package replay vẫn JS frozen. Một agent tách SPEC/BUILD/VERIFY, không auditor độc lập.

## Retained incidents / refinements

Development runs unit-r01 (42), unit-r02 (51), corpus-r01 và process-r01 giữ nguyên. Final bổ sung strict malformed-input/direct-clock guards và ca reserve frontier đã commit nhưng AUTH73 disk gate từ chối: dữ liệu không đổi, request cũ không reuse, fresh nonce/higher sequence explicit hoàn tất. Không sửa module cũ.

Lần gọi Python AUTH73 đầu truyền sai corpus root, subprocess nonzero ban đầu chưa được assert; không tạo output/verdict. Đã ghi verification-invocation-incident.json, sửa corpus-view adapter ở namespace mới và kiểm return/output đúng. Final44/44 là output thực từ invocation đã sửa; không dùng lần lỗi làm PASS.

RFC5280 reference được capture từ IETF Datatracker sau rfc-editor trả429; lưu nguồn/SHA trong sources.json. Chỉ dùng thuật ngữ issuer/subject/validity/key usage/revocation, không X.509/CRL implementation hoặc compliance claim; không promotion vào canonical SOT.

## NOT_CHECKED / gaps

Real cryptographic possession/PKI/certificates/TLS/secure enrollment/key hardware; authority/root CA rollover hoặc recovery khi toàn bộ keys bị mất/thu hồi; trusted clock/cross-host/reboot mapping; external trusted anchor và joint rollback toàn ledger+anchor+oracle/root; multi-host revocation propagation/network/powercut vật lý; performance/large-data/soak/storage rotation; SDK/Android/HeraHub/Fly/HTTP72 security retrofit/release. Current HTTP72 preview vẫn unsigned.

Mock CA/oracle do trusted harness cấp, không endpoint cho sender đăng ký proof. Registry bootstrap config pin master scopes/authority; không xác nhận thiết bị thật hay actual key material. Lower-level storage/provider registration là trusted plumbing, không wire API. Không có digital signature/software signature mới, authorityRestored=false, actualImages=0; không thay selected/trust/ENDURE hoặc suy PASS24h mới.

FILES CHANGED: chỉ tạo native/key74/*, evidence/key74/*, fixture evidence/auth73/key74/* và evidence/receiver72/key74/*, docs/ADR-090-KEY74-ENROLLMENT-ROTATION-REVOCATION.md, delivery/{TIP,ROADMAP,COMPLETION}-KEY74.md. Không scratch/project copy/dependency install; không dọn dữ liệu hoặc xóa lock. Footprint và sàn20GiB được kiểm trong final-verification.json.
