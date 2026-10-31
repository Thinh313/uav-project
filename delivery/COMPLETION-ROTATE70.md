# ROTATE70 — Completion report

16/10/2026 · DONE_SCOPED_HOST_MOCK_CONTROLLED_ROTATION. R70-01…08:8/8 trong phạm vi host/mock. Single agent chuyển Contractor→Builder→Verify theo transfer6.3; không tuyên bố kiểm định viên độc lập.

Đã triển khai root-control journal riêng tại native/rotate70, dùng Store/DurableSession JOURNAL68 nguyên trạng trong các thế hệ riêng .local/rotate70. BEGIN sync → CLOSE/SEAL và kiểm byte/catalog/semantic → FREEZE → cold seed đã đóng → STAGE → SELECT commit → writer mới có boot mới và quyền rỗng. Plan ràng buộc boot/control/current bytes, exact phrase, một lần/60s. Không tự chuyển tiếp pending hoặc rollback. Trước SELECT mà crash thì HOLD; sau SELECT chỉ mở committed target lạnh nếu gate đạt. Lỗi lock/IO/source/corruption/quota giữ hồ sơ, chặn admission.

Rollback tạo physical generation mới dựa trên baseline cũ; giữ các store cũ/failed candidate chỉ đọc. Không ghi tiếp WAL frozen, không hoàn tác lệnh, không cấp lại grant/token/pending/transaction, không downgrade software/schema. Source/schema68 giữ nguyên nên chưa chứng minh migration giữa hai phiên bản. Không dọn dữ liệu và không có cleanup endpoint.

| Kiểm trên bản backend cuối | Kết quả | Receipt |
|---|---:|---|
| Unit/fault/restart/rollback/lock/resource/source | 20/20 | evidence/rotate70/unit03.txt; tests-r03/results.json |
| Corpus DUAL67 receipt/checkpoint + rotation/archive/restart | 22/22 | evidence/rotate70/corpus-r01/results.json |
| HTTP mock/connect/claim/capture/rotate/rollback/restart/token | 17/17 | evidence/rotate70/http-r01/results.json |
| Real process SIGKILL boundaries | 6/6 | evidence/rotate70/crash-r01/results.json |
| CUA UI explicit mock rotation/rollback + managed restart | 8/8 | evidence/rotate70/browser-qa.json |
| Python implementation riêng kiểm byte/base64/SHA/frame/chain | 24/24 gói | evidence/rotate70/python-byte-verification.json |
| Python implementation riêng kiểm control/selection/frozen+seed anchors | 23/23 root | evidence/rotate70/python-control-verification.json |

Corpus giữ exact receipt parity với corpus gốc. Chỉ các event bootId bằng boot hiện tại của review gốc được rebind sang boot70 mới; negative old-boot inputs giữ nguyên. Checkpoint đối chiếu với instance Arbiter nguyên trạng dùng cùng boot mới, tách khỏi live writer. Đây là hai đường kiểm tất định cùng agent, không phải independent auditor. Gói frozen tương thích unpack69 và parser Python; không suy ra ảnh thật hoặc causal execution từ ACK.

SIGKILL thực tại BEGIN_SYNCED, OLD_WRITER_CLOSED, STAGE_SYNCED, SELECT_SYNCED, ACTIVATED và STAGE_SYNCED của rollback. Precommit giữ nguyên selected cũ/HOLD; explicit rollback tạo writer mới và giữ bytes các generation trước. Postcommit restart đúng committed selection, không quyền. Unit còn kiểm plan stale/hết hạn/single-use, pending handover, mất root-lock, SEAL IO không chắc chắn, thay bytes trước SELECT, alias/missing/control corruption/unknown/source mismatch/quota reserve. Một ca unit01 thất bại vì view quota ném TREE_SYMLINK thay vì trả trạng thái HOLD; đã sửa chỉ trong rotate70, giữ receipt cũ, unit02=17/17 và unit03=20/20 sau bổ sung ba ca fault. Không sửa fixture hỏng để đổi verdict.

UI QA chỉ dùng preview01 synthetic mới, không import dữ liệu nhiệm vụ thật. Đã connect/claim/capture mock, nhập exact phrase chuyển rồi rollback và SIGTERM/restart riêng service. Preview cuối PID79759/root-lock79767, rootBoot root-f22902e53dc60f9b88468cf6782ec8f9 tại http://127.0.0.1:8825/. Selection rollback g-6037fb87809917e797d0a4d1125fe0c6 có liveBoot live70-12c639047ee267dd4ed233a1c1741e2b, committed hiện tại0, grants/stations/pending/transactions rỗng. Ba generation được giữ: INIT5 kết quả/1capture synthetic, ROTATE2 kết quả, ROLLBACK2 kết quả lịch sử; current OPEN-only run chưa seal là live/NOT_FINAL. Ảnh thực0, quyền khôi phục0. Không đổi writer JOURNAL68 gốc hoặc ARCHIVE69. Screenshot browser-final.png; viewport thực1280×720, hai nút plan42px cùng hàng, không overflow ngang; chưa kiểm các viewport khác, không override viewport.

Before/after guard và final-verification kiểm cumulative26.798 đường dẫn cùng5.051 ENDURE (các tập có giao). Chỉ endpoint SHA, không tuyên bố đường dẫn hiện diện liên tục hoặc ENDURE24h đạt. Runtime/source/dependency pins, raw receipts và artifact manifest nằm trong evidence/rotate70. Giữ sàn20GiB; resource số cuối ở final-verification. Artifact budget48MiB; không clone toàn project, install dependency hay tạo scratch build cần dọn. Không khôi phục/xóa bằng chứng cũ, build APK/SITL/emulator/soak/ký mới hoặc tích hợp Fly.

Technical health có số module syntax và DOM-ID checks trong technical-health.json; build/APK/signature excluded, Android lint/types NOT_CHECKED. READY chỉ cho phạm vi host/mock. Chưa kiểm mất điện vật lý/F_FULLFSYNC/storage Android/HeraHub, receiver khác máy, production identity/transport enforcement/chữ ký/anti-rollback anchor ngoài host, migration thật và vận hành dài hạn. Hash-chain chỉ consistency, chưa chống coherent rewrite toàn root. HTTP mock dùng logical1ms/action, không nghiệm thu timing thực. Retention root70 chưa có tombstone, giữ mọi generation cho tới quota; không lấy archive69 cleanup để xóa các root-manifest đang tham chiếu. Roadmap overlay ghi các gate tiếp.
