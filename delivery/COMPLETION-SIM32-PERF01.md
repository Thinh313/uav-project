# SIM32-PERF01 — bàn giao kết quả hiện có

Quyết định chủ việc: **bàn giao kết quả hiện có, ghi rõ kiểm bổ sung chưa chạy**. Không khởi động thêm SITL hoặc benchmark khi host dưới sàn20GiB. Đây là increment simulator trên máy reference, với các gate còn mở; chưa nghiệm thu toàn bộ sản phẩm/Hera hay mục tiêu vượt DJI.

## Kết quả và phạm vi nghiệm thu

Đã tối ưu model bằng kernel C float64, cache đại lượng cố định và bộ ghi FIFO có giới hạn. Giữ nguyên bước1200Hz, RK4, seed/profile và độ chính xác số của corpus được kiểm. Đồ họa có cadence60Hz riêng; không bỏ bước physics để giữ FPS. Mất bằng chứng, queue đầy hoặc lỗi ghi không được đánh dấu hồ sơ hoàn tất.

| Cấu hình UI + ArduPilot SITL + physics | Run | RTF đo từ raw | Kết luận |
|---|---|---:|---|
| Không tải, gió lặng; optimized, AP pacing1.10 | ui1791907507117 |1.096485 | Đạt≥1 trong mẫu này |
| Tải giữa1kg, gió ngang; optimized, AP pacing1.10 | ui1791907624118 |1.097259 | Đạt≥1 trong mẫu này |
| Tải lệch1kg, gust; optimized, AP pacing1.10 | ui1791907783253 |1.095509 | Đạt≥1 trong mẫu này |
| Đối chứng baseline, AP pacing1.10 | ui1791907348234 |1.091242 | Đã đạt trước tối ưu ở cùng pacing |
| Optimized, AP pacing mặc định1 | Hai run giữ trong corpus |0.927630;0.935935 | **Chưa đạt≥1** |

RTF dùng `((N−1)/1200) / ((lastHostMonotonicNs−firstHostMonotonicNs)/1e9)` trên khoảng nhận wire đang hoạt động. Bao gồm toàn bộ frame physics trong khoảng này; không phải hệ số của cả thời gian khởi động/đóng tiến trình. Không dùng model clock được gán để suy ra PASS. Mỗi profile UI là một mẫu trên host reference, không đủ kết luận độ ổn định dài hạn hoặc hard real-time.

Pacing1.10 được khai báo và đọc lại `SIM_SPEEDUP=1.100000023841858`, `SIM_RATE_HZ=1200` trong ba run optimized. Baseline1.10 có CLI/config pin nhưng chưa có bước đọc lại speedup mới; trường quan sát đó vẫn null. Cấu hình này tạo headroom pacing trong ArduPilot; **không quy toàn bộ mức RTF tăng cho thuật toán**, vì baseline cùng pacing cũng đạt≥1. Không sửa firmware, không bỏ lockstep, không ngoại suy sensor hay đổi bước model. `runtime.py` mặc định pacing1; preview đang dùng cấu hình khai báo1.10.

Benchmark riêng cho phép tính model ở cùng checkpoint trên không,6000 bước/case, ba lượt đảo thứ tự baseline/optimized, cho tỷ số thời gian **3.159–3.218×**. Median giảm từ khoảng72.93–73.94µs xuống22.83–23.15µs/bước. Đây là headroom tính toán model, loại trừ ArduPilot, transport, journal và renderer, không phải RTF hoặc tốc độ toàn bộ sản phẩm.

## Độ đúng, lưu hồ sơ và regression

- **593888 frame thuộc sáu trace cũ**: sensor/aux khớp số chính xác, sensor serialize khớp byte với raw cũ. Không giảm precision/tolerance để PASS. **20000 derivative ngẫu nhiên** khớp chính xác; ba đầu vào bất hợp lệ bị từ chối.
- **20 kiểm analytic/convergence +5 validation** đạt. Baseline hiện tại từng lỗi bốn ca lý tưởng vì validator từ chối resistance/damping bằng0; đã lưu FAIL và sửa miền không âm. Receipt20-test cũ có trước validator này, không bị viết lại hay dùng để che regression.
- **4 kiểm journal** đạt: FIFO/hash/snapshot, queue overflow phải lỗi, lỗi ENOSPC không seal, raw inline/worker giống nhau. **6 kiểm review seal** đạt: thiếu summary/count gap/lỗi ghi/backlog/closure không rõ không được `recordComplete`.
- **613322 frame mới** của bốn run UI/đối chứng và hai run payload/fault đã replay toàn bộ, kiểm SHA/count. Ba hồ sơ UI optimized có13 checks đạt: biên tập nhiệm vụ, Home/preflight, upload/readback, ARM/AUTO, landing/disarm/ground, đóng writer/SITL và sealed review. Acceptance mới chỉ gắn với source pins thực sự đã chạy.
- Payload regression đạt13 checks: ba camera/hai gimbal synthetic qua hai bus và ArduPilot thật, wrong target/owner/device, phản hồi/ACK không rõ và capability loss. Fault regression đạt6 checks: mất GCS→RTL/land, sensor/backend chết→freshness gate, không tự retry ngoài policy. **ACK và synthetic observation không chứng minh payload thật thực thi, không có ảnh thực.**

Corpus giữ cả baseline stale snapshot, Python-only UI timeout, pacing1 dưới ngưỡng, lỗi syntax của test driver và lỗi TDZ counters ở viewer. Không loại các FAIL khỏi hồ sơ. Native kernel chỉ được build/kiểm cho macOS arm64/CPython3.14 hiện tại; không có fallback âm thầm hoặc bản Android tương đương đã nghiệm thu.

## Source cuối và phần kiểm chưa chạy

Sau các chuyến bay đạt, đã sửa binding pacing của replay và thứ tự khởi tạo counters trong viewer. Bản source cuối đã qua **9 kiểm browser/replay**, gồm render3D, replay chỉ đọc, authority/token, âm thanh tổng hợp mặc định tắt, toolbar48CSSpx thẳng hàng, responsive và không có lỗi JavaScript. Đã xem screenshot cuối; nhãn recorded/provisional/no-real-media vẫn hiện rõ.

**Vòng live đầy đủ UI→SITL trên source cuối: NOT_CHECKED_RESOURCE_FLOOR_OWNER_DEFERRED.** Chủ việc chọn bàn giao hiện có khi máy còn khoảng19.45GiB. Không suy ra vòng live này PASS từ replay9 checks. Source pins của sáu capture mới đều có byte đối chiếu sẵn; ba run UI optimized khác source cuối ở `server.mjs` và `viewer/main.mjs`, đã ghi rõ trong receipt. Kernel/backend/control của ba run vẫn đúng hash.

Ngân sách graphics/native video/local input latency còn mở. Live rendered-frame p95 ở ba profile là17.5/23.8/17.9ms; chưa đủ đạt mục tiêu đề xuất16.7ms. Phân bố có idle hold và closure-inclusive frame age được giữ riêng; không diễn giải RAF thành GPU completion. Chưa kiểm Hera/HIL/flight thật, video mã hóa thực, calibration khí động học/âm thanh hoặc so sánh Ragas/DJI. Mục tiêu vượt DJI vẫn là yêu cầu sản phẩm, chưa phải kết quả đo.

## Bảo toàn, tài nguyên và bàn giao

Đối chiếu cuối: **4051 file bảo vệ khớp SHA**,0 mismatch. App/source/candidate/trust/ENDURE và receipt cũ không bị sửa; không launch soak, ký phần mềm mới hoặc tích hợp Fly. Sự cố đường dẫn gốc trước đây vẫn được giữ; khớp SHA hiện tại không chứng minh các đường dẫn hiện diện liên tục.

Các run live đã hoàn tất khi dung lượng tối thiểu trong run trên23GiB. Cuối task host giảm dưới20GiB; nguyên nhân giảm tổng dung lượng **UNKNOWN**. Chỉ thực hiện đọc đối chiếu và ghi metadata bàn giao nhỏ sau đó, không chạy thêm runtime/build/install/copy lớn. Admission runtime giữ20GiB+640MiB và stop headroom đã có. Không bỏ gate tài nguyên.

Cleanup: xóa hai cache do task tạo `pilot/sim32/__pycache__/journal.cpython-314.pyc`, `pilot/sim32/__pycache__/backend.cpython-314.pyc` và thư mục cache rỗng. State/container sở hữu được đóng/dọn theo từng `closure.json`; không còn backend/container simulator thuộc task. `docker image prune -f` thu hồi0B; không prune volume/container. Không tạo bản sao toàn bộ project vào/tmp, không xóa dữ liệu khác của chủ việc. Giữ kernel51,616B, source archive nhỏ và toàn bộ evidence cần bàn giao.

Preview [http://127.0.0.1:8796/](http://127.0.0.1:8796/) ở trạng thái idle, không run/grant/quyền điều khiển; cấu hình optimized/1.10/1200Hz được hiển thị và admission đang chặn runtime mới vì dung lượng. Không dùng preview idle để tuyên bố kiểm live cuối đã đạt.

Hồ sơ máy đọc: `pilot/sim32/acceptance-contract-v3.json`, `delivery/STATUS-SIM32-PERF01.json`, `evidence/sim32-perf01/verification.json`, `tested-source-availability.json`, `handoff-fingerprints.json`. Contract/report cũ giữ nguyên. REQ-P01/P02/P03 đạt trong corpus reference; REQ-P04 đạt ba mẫu cấu hình1.10 nhưng pacing1 và live source cuối còn mở; REQ-P05 bảo toàn đạt, tài nguyên đang HOLD. Verify theo trình tự Contractor/Builder/Verify do một agent thực hiện, không phải audit độc lập.

Bước tiếp khi đủ tài nguyên: lặp full live trên source cuối với đúng cấu hình/pins; tiếp tục xử lý hạn chế pacer/transport mặc định1 và ngân sách graphics trước khi mở gate calibration/Hera. Không cần hỏi lại để mô tả phần còn mở; chủ việc đã chọn bàn giao thay cho vòng bổ sung hiện tại.
