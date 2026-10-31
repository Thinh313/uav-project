# AUTH73 — Completion / Verify

16/10/2026. STATUS: DONE trong phạm vi contract mock/replay. OVERALL: READY cho scope này; chưa xác thực mật mã production và chưa tích hợp bảo mật vào HTTP receiver72 đang chạy.

Đã triển khai module native/auth73 riêng: policy/version/realm/epoch, source principal/key/root allowlist, receiver identity, challenge nonce/boot/TTL, source sequence và sender nonce. Receiver ghi ADMIT log+anchor trước side effect dữ liệu72. Receipt bind source claim, sender intent/nonce, receiver và receipt72 sau readback; sender chặn receipt thuộc sai gói/phiên/trạm. Restart không khôi phục challenge/admission dùng để ghi; explicit claim mới tăng sequence để tiếp tục transfer chưa commit.

Proof provider chỉ tra fixture oracle. Không private key, MAC, digital signature hoặc chứng minh possession thật; assurance luôn MOCK_ONLY_NOT_AUTHENTICATED, productionAuthenticated=false. Khóa có tên trong fixture là định danh giả lập. Production mode bị từ chối. Module72, source/candidate/canonical SOT và ENDURE không đổi.

## Requirement coverage

6/6 REQ implemented và checked (100%) trong scope TIP-AUTH73.

| REQ | Kết quả | Chứng cứ |
|---|---|---|
| 01 / exact contract, identity, role, purpose, epoch, source/root/receiver/content binding | PASS mock; valid fixture proof vẫn bị từ chối khi tuple sai; không fallback production | unit-r03/results.json; native/auth73/contract.json |
| 02 / nonce/sequence/expiry/clock/replay fences | PASS; challenge đã dùng, sequence cũ, nonce collision mô phỏng, old boot, wrong receiver, expired/future/rollback bị chặn | unit-r03/results.json; corpus-r02/results.json |
| 03 / durable admission và sender receipt contract | PASS; không data trước ADMIT, revocation sau admission chặn ghi; receipt phải thuộc local intent/claim, commit trước expiry | unit-r03/results.json; corpus-r02/results.json |
| 04 / ledger/anchor/restart/fault và floor | PASS; actual SIGKILL giữa log/anchor giữ HOLD không repair; sau anchor sync không auto data/quyền, explicit fresh claim hoàn tất | process-r02/results.json; unit-r03/results.json |
| 05 / corpus và implementation đối chiếu riêng | PASS22 corpus; Python22 contract +66 negative bites,22 receiver byte/control/receipt,22 package/WAL/frame | python-contract-final.json; python-r72-final.json; python-package-final.json |
| 06 / preservation, report và fingerprint | PASS;34.025 protected paths,5.051 ENDURE và26 preview72 khớp SHA; native13 file giữ nguyên so lần bàn giao PARTIAL | preservation-after.json; module-pins.json; final-verification.json; artifact-manifest.json |

## Quantitative results

- Final unit/fault: **60/60** (`unit-r03`), corpus: **22/22** (`corpus-r02`), actual process SIGKILL windows: **2/2** (`process-r02`). Các positive/negative assertions nằm trong ca kiểm, không cộng trùng thành capability mới.
- Python contract verifier: **22/22**, negative bites **66/66** (body swap, unknown evidence, receipt commit sau expiry). Frozen Python72 verifier: **22/22**; frozen ARC69 package/Base64/WAL/frame/SHA verifier: **22/22**. Semantic replay vẫn verifier JS72/69 đã pin; không gọi đây là auditor độc lập.
- Syntax: **10/10** module JavaScript, errors0. JSON contract hợp lệ. Không build/install/emulator/SITL hay SDK.
- No deletion, auto retry/repair, quyền khôi phục hoặc ảnh thực. Không ký mới, không thay selected/trust/candidate/ENDURE/controller. Không có kết luận ENDURE24h mới.

## Disk interruption / retained evidence

Lần bàn giao trước dừng ở PARTIAL khi host còn19,53GiB, dưới sàn20GiB. Đã giữ code và test artifacts, không ghi completion/final fingerprint, chỉ thực hiện Python và SHA audit in-memory; không xóa dữ liệu để tiếp tục.

Người dùng sau đó xác nhận sẽ giải phóng lên22GiB. Kiểm thực tế thấy26,93GiB; đối chiếu lại toàn bộ protected/ENDURE/preview và native module SHA trước khi lưu các receipt cuối. Native map SHA vẫn `1325b8390fa1115e4205234ce70e24e11cb05956e361e0c88e8fc59d08be59bd`, gồm13 file, đúng byte của bản đã kiểm60/22/2. Chỉ chạy lại các verifier chỉ đọc để lưu output, không rerun workload, ký, sửa module hay triển khai endpoint mới. Sàn và ngân sách32MiB được ghi lại trong final-verification.json.

Development evidence `unit-r01`51 ca, `unit-r02`56 ca, `corpus-r01`, `process-r01` và Python contract trước đó được giữ nguyên. Final runs bổ sung concurrency assertion mạnh hơn (đúng một admission commit), current-key revocation sau admission, gate data trước admission, nonce collision và commit-time expiry. Các fault/torn/rollback replicas chỉ ở namespace test mới, không xóa/ghi đè hồ sơ nguồn.

## NOT_CHECKED / remaining gaps

Cryptographic verification/identity provisioning/PKI/TLS/key hardware và key rotation thật; trusted clock/cross-host reboot mapping; external trusted anchor/joint rollback protection; hai host/ổ độc lập/mạng thật và powercut vật lý; large-data streaming/resource/latency/soak; Android/HeraHub/Fly/release hoặc repair partial69/cleanup. HTTP receiver72 cũ giữ nguyên unsigned, không suy rằng ứng dụng đang có authentication production.

Mock oracle do harness cấp, không là API để sender đăng ký proof. Mock anchor có thể bị rollback cùng ledger/oracle nếu cùng trust boundary bị sửa; chưa bảo vệ trường hợp này. Sender local receipt là historical evidence với bundle hiện tại; cần receiver getReceipt/readback để biết remote data hiện tại. Mock TTL dùng injected clock, không suy độ đúng clock host thật.

FILES CHANGED: chỉ tạo native/auth73/*, evidence/auth73/*, fixture evidence/receiver72/auth73/*, docs/ADR-089-AUTH73-SOURCE-RECEIPT-REPLAY.md và delivery/{TIP,ROADMAP,COMPLETION}-AUTH73.md. Không tạo scratch/dependencies/build copies; không có gì bị dọn. Một agent tách SPEC/BUILD/VERIFY, không tuyên bố review độc lập.
