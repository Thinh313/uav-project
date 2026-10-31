# CYBER65 · Phase One / dual-operator / multipayload contract

15/10/2026 · **READY_FOR_SCOPED_MOCK_REPLAY**. Đây là module terminal-first riêng, chưa nối native/Fly hay thiết bị. Không có server, SDK, radio, video decoder hoặc transport thật.

## Đã làm

| Thành phần | Contract / hành vi | Giới hạn còn lại |
|---|---|---|
| Phase One | Descriptor có phiên bản; model/firmware/lens/API/calibration giữ null; profile chưa biết bị chặn dispatch | Chưa có thông tin camera khách, API hay tương thích cơ/điện/gimbal thật |
| Semantic controls | Capture, zoom/focus theo %, gimbal pitch/yaw theo độ; kiểm kiểu/giới hạn; exposure/ISO/aperture/download/LiDAR chưa ánh xạ | Ánh xạ MAVLink tổng hợp dùng P22/T25, không phải Phase One SDK |
| Dual-operator | Hai identity mock cục bộ, quyền riêng aircraft/camera/gimbal; một owner mỗi scope; bàn giao cần current owner và recipient xác nhận | Một mock GCS chung; chưa có hai tay cầm/radio, provisioning, xác thực remote hay receiver enforcement |
| Fault/lifecycle | Freeze khi bàn giao; release/expiry/loss/reboot/reconnect/clock lỗi thu hồi ticket; không tự cấp lại quyền/retry/failover | Chính sách mất link/emergency của máy bay thật chưa được khách/RtR duyệt; không phát lệnh RTL/ARM/AUTO |
| Routing | Ba camera fixture: component100, proxy component1/device2, component101; manager154/device1 và2; target tường minh tách khỏi view selection | Không chứng minh số payload vật lý; LiDAR chỉ slot chưa hỗ trợ. Ambiguous ACK key khóa đến generation mới, chưa phù hợp điều khiển liên tục |
| Review | Intent/send/ACK/progress/reject/consistent-unattributed metadata/file declaration tách rõ; actualImages luôn0; không tự nhận execution | Không có ảnh thật, physical exposure, gimbal motion hay timestamp calibration thật |
| Integrity | Corpus/raw hex/hash, review yêu cầu trusted replay digest; file thiếu/giả/tamper/incomplete không được nhận là đầy đủ; import chỉ inspection lịch sử | Hash/local epoch/CRC không phải cryptographic authentication; trusted replay digest phải lấy từ replay độc lập được người gọi tin cậy |

Policy mock (heartbeat1500ms, grant1400ms, transfer800ms) chỉ là fixture đề xuất để kiểm; không là yêu cầu Research Partner hoặc giá trị firmware/radio thật. Authority aircraft chỉ là mô hình quyền, không có mapper lệnh bay. Chọn feed không chuyển quyền hoặc đổi command target.

## Bằng chứng

33 unit checks +44 authored replay scenarios +157 inherited regression tests đạt ở scope tương ứng; không cộng lại các lần chạy cũ. Corpus44 chứa180 assertions; oracle Python riêng kiểm392 assertion trên29 frame TX mock, đối chiếu CRC/layout/target/params và loại trừ component khác. Oracle không phải kiểm receiver vật lý. P22 có vector C đã lưu; đợt này không build lại C.

Các lỗi đã giữ: driver01 thiếu receipt đầy đủ vì trường diagnostic undefined; attempt02 có5 scenario lỗi (proxy fixture thiếu focus capability và hai expectation thông báo lỗi quá hẹp); unit01 phát hiện raw-budget failure chưa đặt historyIncomplete. Đã sửa fixture/driver và latch incomplete/revoke trong module mới, không sửa P22/T25. Receipt final-readback01 giữ FAIL do so sánh digest cũ sau khi nhãn ACK reject/progress đã tách; readback02 chỉ cho phép đúng delta hai nhãn REJECTED, toàn bộ44 scenario vẫn đạt. Không sửa receipt lỗi cũ.

## Dùng trong development

`CustomerMockSession` mặc định dùng Phase One profile chưa biết, nên không dispatch camera. Test/replay phải chọn rõ `SYNTHETIC_PROFILES`. Tạo credential cục bộ qua mock issuer; connect không cấp quyền. Heartbeat rồi claim từng scope với explicit consent. Bàn giao: current owner gọi transfer → scope bị freeze → đúng recipient accept; decline/expiry không khôi phục grant. Ticket gắn session/generation/config SHA/authority epoch/revision.

`loadCorpus()` kiểm SHA corpus; `replay(corpus, scenario)` chỉ chạy scenario thuộc đúng corpus. `inspectHistoricalReview(text, {expectedCorpusSha256, expectedReplaySha256})` kiểm nội dung/scope và trả `authorityRestored:false`; không tạo session hoặc cấp quyền.

Re-run chỉ sau kiểm dung lượng>=20GiB+16MiB, dùng **tên receipt mới** cho `qa.mjs attemptNN`; không ghi đè audit receipts. Không chạy nguyên bản `pilot/protocol22/protocol.test.mjs`: after-hook của nó ghi vào corpus cũ. Harness `protocol22-regression.test.mjs` giữ nguyên assertions, chỉ chuyển import/fixture references và output sang evidence/cyber65. Bản gốc vẫn byte-identical. Node unit tests là mock, không build APK hay khởi động SITL.

## Tiếp theo và các unknown

CY-RM02/03/04 đã có nền contract/corpus mock; chưa đóng gate phần cứng. U03–09, U18–20 vẫn mở: exact camera/API/licence/gimbal, topology và authentication, role/handover/loss/emergency policy, allowed payload mix, real video/time/quality thresholds và native installation. Lấy các dữ liệu này trước adapter vendor/bench. Sau đó native cockpit và hai station bench → HIL faults → controlled flight/ảnh thực. Không tự tích hợp Fly, ký mới hoặc chạy lại ENDURE từ module này.

Tài liệu liên quan: [TIP](../../delivery/TIP-CYBER65.md), [ADR080](../../docs/ADR-080-CYBER65-MOCK-AUTHORITY.md), [ma trận Research Partner](../../planning/cyber64/ACCEPTANCE-MATRIX.md), [completion](../../delivery/COMPLETION-CYBER65.md). Dữ liệu và code thử được giữ có chủ đích; không tạo project/tmp copy hoặc dependency/build directory.
