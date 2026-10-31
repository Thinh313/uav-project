# SIM32 — bàn giao increment mô phỏng vòng kín

Ngày 13/10/2026. Trạng thái: **REFERENCE_FUNCTIONAL_VERIFIED_WITH_OPEN_QUALITY_GATES**. Đây là increment engineering trên host, chưa nghiệm thu toàn bộ SIM32 hay sản phẩm Hera. Một agent thực hiện tuần tự Contractor/Builder/Verify; không phải audit độc lập.

## Đã chạy và kiểm

AERIS simulation workspace tại `http://127.0.0.1:8796/` dùng adapter riêng nối ArduCopter 4.7.1 đã pin binary, chạy trong container Linux/amd64 giới hạn 2CPU/384MiB trên Mac arm64. Servo thực của autopilot đưa vào backend vật lý 6DOF RK4; backend trả sensor để đóng vòng kín. Renderer/audio đọc trạng thái model, không viết chuyển động cho drone. Source và candidate sản phẩm vẫn đóng băng; không tích hợp Fly hay ký phần mềm mới.

Luồng Plan → xác nhận Home/datum → preflight chỉ đọc → upload/readback → ARM/AUTO → bay/hạ cánh → review đã chạy qua UI. Virtual Home AMSL10m, độ cao nhiệm vụ relative Home. Chưa dùng địa hình hay drone thật.

| Corpus nghiệm thu trong phạm vi reference | Bằng chứng |
|---|---|
| Quad 3kg không tải, không gió; nhiệm vụ hoàn tất | `evidence/sim32/runs/flight10/acceptance.json`, 11 checks |
| Thêm tải giữa 1kg, gió ngang; nhiệm vụ hoàn tất | `evidence/sim32/runs/flight11/acceptance.json`, 11 checks |
| Tải lệch 1kg, gust seed32; nhiệm vụ hoàn tất | `evidence/sim32/runs/flight12/acceptance.json`, 11 checks |
| Mất heartbeat GCS khi bay: AP thực RTL, land/disarm; không ghi nhiệm vụ hoàn tất | `evidence/sim32/runs/fault02/acceptance.json`, 6 checks |
| 3 camera/2 gimbal synthetic trên 2 bus qua routing AP thực; sai target/owner/device, ACK trễ/trùng, capability và mất bus | `evidence/sim32/runs/payload06/acceptance.json`, 13 checks; ground-only |
| UI live biên tập nhiệm vụ 7m, Home/grant/readback, payload POV, bay và đóng/seal review | `evidence/sim32/live-browser-qa05.json`, 12 checks |

20 kiểm physics và 4 kiểm domain/profile/battery đạt. Sáu run reference đã replay đầy đủ **593.888 frame**; sensor/model outputs và SHA raw khớp đúng model version đã pin. Đây là kiểm integrity/tính lặp lại của model, không phải đối chứng khí động học độc lập. Các source version thiết yếu cho run nghiệm thu có bản byte khớp; 10 pin của module không được dùng trong các run lịch sử còn thiếu archive version riêng, được ghi tại `scoped-acceptance-index.json`. Không tuyên bố tái dựng đầy đủ mọi source lịch sử.

Payload peer là mock có giao thức đi qua ArduPilot thật. ACK và pose/settings phù hợp không chứng minh quan hệ nhân quả hay execution của payload thật. Ảnh/video thực không có. Inspector giới hạn một ACK key mỗi generation để chống tương quan nhầm; thao tác camera/gimbal lặp như sản phẩm vẫn cần thiết kế transaction/authority tiếp theo.

Viewer dùng màu đen/trắng và vàng phụ, control chung 48CSSpx thẳng hàng, metric NED→scene, các góc Orbit/Follow/Top/Payload. Âm thanh tổng hợp theo RPM ước tính và khoảng cách, mặc định mute, dừng khi mất focus/stale. Screenshot và walkthrough đã kiểm; native48dp, SPL/Doppler Hera và encoded video chưa kiểm. Landmark synthetic không có collision.

## Hiệu suất đã đo và khoảng trống

Máy reference: Apple M1 Max,32GiB,macOS27.0.1, Node24.14.1/Python3.14.6, Chromium ANGLE Metal. Cấu hình đầy đủ và raw distributions tại `host-reference.json`/`verification-runtime03.json`.

| Workload | Số đo | Kết luận trong phạm vi đo |
|---|---|---|
| Replay, canvas1280×800, 1.332 RAF intervals | p95 9,6ms; p99 10,2ms; max266,6ms; 4 interval>16,7ms,1>33,3ms | Percentile đáp ứng mục tiêu graphics đề xuất trên host; giữ spike, không suy ra GPU completion/Hera |
| UI live + AP + payload, canvas910×726, 7.339 intervals | p95 9,2ms; p99 9,3ms; max33,4ms | Workload/resolution khác replay, không gộp thành benchmark1280×800 live |
| Physics snapshot age live,7.249 samples | p95 200ms; p99 211ms; max246ms | Frame age model→viewer; không phải video latency |
| Vật lý active-wire RTF flight10/11/12 | 0,956 /0,995 /0,972 | Mục tiêu≥1× **chưa đạt** |
| Vật lý UI live RTF | 0,928 | Còn cần tối ưu có đối chứng đúng số học/corpus |

Distribution toàn walkthrough gồm hold sau closure vẫn giữ nguyên: frame max141,7ms, snapshot-age p99 2.977ms/max4.303ms. Không dùng số live-only để che phần stale/closure. API roundtrip và render submission không chứng minh mục tiêu local input→feedback100ms hay GPU execution. Hard real-time, native Android/Hera, encoded video budgets, calibration vật lý và đối chứng Ragas/DJI **NOT_CHECKED**.

Mass/CG/inertia/thrust/lag/drag/battery là profile reference có version và giả định rõ, chưa hiệu chỉnh Hera. Chưa hỗ trợ arbitrary airframe, tải treo, CFD, propwash, ground effect, contact/bounce thực hay khí động học mưa. Cần dữ liệu đo cùng cấu hình trước khi chốt tolerance và fidelity. Mục tiêu vượt DJI là yêu cầu sản phẩm; chưa có kết quả so sánh chứng minh.

## Bảo toàn và sự cố đường dẫn

Kiểm giữa triển khai khớp đủ3.576 file bảo vệ. Kiểm cuối phát hiện22 đường dẫn thiếu; nguyên nhân **UNKNOWN**. User đã cho phép khôi phục riêng file thiếu bằng đúng SHA gốc. Đã tạo lại22 đường dẫn bằng exclusive-create từ bản sao xác minh độc lập, không ghi đè file có sẵn. Signed9 và package aliases không được ký lại; font khôi phục byte gốc; BOM trùng SHA tìm được ở `Downloads/BOM260110.xlsx`; hai ảnh trùng SHA ở corpus BENCH06.

Kiểm sau khôi phục: **3.576 file bảo vệ +5 file requirements +3 receipt baseline đều khớp SHA;24 file source final và bản sao đều khớp**. Incident/verification FAIL trước phục hồi còn nguyên tại `protected-inventory-incident.json` và `verification-runtime02.json`. Receipt phục hồi01/02 và kiểm runtime03 là hồ sơ mới. **Không suy ra đường dẫn gốc hiện diện liên tục**, không xóa lỗi lịch sử hay đổi ENDURE thành PASS.

Flight06 từng vi phạm sàn tài nguyên; UI01 bootstrap lỗi, UI02 software-renderer/preflight timeout, payload04 startup stale, fault01 pin drift và các lần lỗi khác được giữ. Test sau sửa là run mới; không nối interval, retry campaign hay sửa receipt cũ.

Đã đóng toàn bộ physics/SITL sở hữu SIM32. Preview8796 còn chạy, không có session/grant. Dọn hai thư mục state rỗng `.local/sim32/flight01`, `flight02` và `pilot/sim32/__pycache__`; Docker image prune thu hồi0B. Không tạo whole-project copy/tmp hay xóa dữ liệu khác. Dung lượng cuối khoảng24GiB, trên sàn20GiB. Source/candidate/ENDURE chỉ được khôi phục đường dẫn đúng byte theo ủy quyền; không launch soak, ký mới, SDK/HeraHub hay radio/flight thật.

## Bước ưu tiên tiếp

1. Tối ưu đường physics/serialization/logging để đạt≥1× trên workload live đã khai báo, giữ oracle/full raw, đo CPU/queue/drop và so trước/sau; bổ sung local feedback timing, restart/overload corpus.
2. Hoàn thiện transaction/authority camera/gimbal cho thao tác lặp, encoded mock video có timestamp/faults và liên kết media/review. Chưa suy ra thiết bị thật từ mock.
3. Sau đủ dung lượng, kiểm Android runtime/input/video/persistence; tiếp đến SDK/HeraHub bench, calibration Hera, HIL rồi flight gate. NATIVE31 APKdevelopment chưa có emulator/ART/UI acceptance.
4. Chốt cấu hình và thực hiện phép đối chứng Ragas/DJI theo protocol; chỉ kết luận ưu thế theo metric/workflow đã đo.

Nguồn trạng thái hiện tại là `pilot/sim32/acceptance-contract-v2.json` cùng `evidence/sim32/verification-runtime03.json` và scoped acceptance index. Contractv1, canonical SOT và mọi mốc đóng băng vẫn là lịch sử riêng; report này không thay thế chúng.
