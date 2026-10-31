# SIM32-PACING02 — Completion / Verify

14/10/2026 · DONE testing · **NOT READY cho pacing1× ổn định dưới tải host.** Contractor/Builder/Verify tuần tự bởi một agent, không phải kiểm định độc lập.

## Kết luận

Đã chạy đủ9lượt UI + ArduPilot SITL và4probe ground-only, không retry. Chỉ1/9lượt đạt RTF toàn capture≥1;6/9đạt luồng UI/control/review. Hai lượt tải cao timeout, một lượt bay kết thúc nhưng clock observer làm review thành `INCOMPLETE_CAPTURE`. Tất cả raw model của13capture, **1,240,400bước**, replay khớp byte sensor và aux bằng model bất biến; điều đó không biến lượt UI, clock hoặc frame-correlation thất bại thành PASS.

Source/candidate/trust/ENDURE và INSTRUMENT01 giữ nguyên: **4809/4809file SHA khớp**,0drift. Exact experimental AP v2 ARM64 binary `f2be1f349f84b4aedaa5912b3050f64f476f3218bc4f68b34ad4de11393c2d08` dùng read-only, không build/ký/tích hợp Fly. `SIM_SPEEDUP=1`, `SIM_RATE_HZ=1200`, cap500000µs giữ nguyên và có actual readback. Không scaling clock, sensor extrapolation hay bỏ bước model để nâng tốc độ.

## Thiết kế phép kiểm

Ba vòng cân bằng thứ tự [0,2,6], [2,6,0], [6,0,2] added CPU workers. Cùng profile reference offset1kg/gust/seed, nhiệm vụ7m, compiler/request hash và profile hash giống nhau; cùng observer ON, viewport1280×800, existing viewer/driver read-only. Mỗi lượt boot fresh owned container/state; worker dừng trước lượt kế. Tải0 là không thêm worker, không có nghĩa host idle. Per-case `*-host.jsonl` và worker CPU-time logs đo tải thực, RSS, load average, AC và disk.

Host10logical CPU,32GiB RAM, AC được quan sát. Load nền thay đổi lớn; snapshot có load average44.8, Codex/WindowServer/VM và compressor đang hoạt động. Chưa đo đầy đủ thermal/frequency/ambient processes theo thời gian nên không quy mọi thay đổi chỉ cho worker. Các group là mô tả n=3 với thứ tự cân bằng, không significance hay causal estimate. Observer-cost on/off thống kê và long-duration vẫn NOT_CHECKED.

RTF=`((processed_frames−1)/1200)/(Python_last_receive−Python_first_receive)`, toàn active wire capture, không startup/closure. Failed/interrupted cases vẫn trong denominator. Rolling1s/5s dùng count trong cửa sổ clock đầy đủ và overlapping, không coi các cửa sổ là mẫu độc lập. Không chờ thêm/chọn lại endpoint để ép RTF vượt1.

## Kết quả nhiều lượt

| Added workers | RTF min | Median | Max | RTF≥1 | UI pass |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.915460× | 0.962632× | 1.000268× | 1/3 | 2/3 |
| 2 | 0.929969× | 0.934852× | 0.999743× | 0/3 | 3/3 |
| 6 | 0.528299× | 0.707474× | 0.974787× | 0/3 | 1/3 |

| Case | RTF | UI | Servo interval p99ms | Maxms | Debt bị cắt(s) |
|---|---:|---|---:|---:|---:|
| m01w0r1 | 1.000268× | PASS | 6.754 | 38.361 | 0.000000 |
| m02w2r1 | 0.999743× | PASS | 6.776 | 60.629 | 0.044768 |
| m03w6r1 | 0.974787× | PASS | 6.181 | 137.516 | 2.703292 |
| m04w2r2 | 0.934852× | PASS | 6.734 | 176.423 | 7.198352 |
| m05w6r2 | 0.528299× | FAIL | 10.935 | 383.184 | 90.634301 |
| m06w0r2 | 0.962632× | FAIL | 6.706 | 635.590 | 4.201763 |
| m07w6r3 | 0.707474× | FAIL | 8.196 | 498.006 | 49.354404 |
| m08w0r3 | 0.915460× | PASS | 6.776 | 269.004 | 9.643561 |
| m09w2r3 | 0.929969× | PASS | 6.705 | 202.604 | 8.145365 |

Pacer sleep batching~5ms nên wall servo không đều1200Hz ngay cả khi mean RTF≥1. Phân bố p50/p95/p99/max, absolute period error, burst/gap counts, lag và rolling extrema trong `runs/*/jitter-clock-cap.json`. Lượt đầu đạt1.000268× nhưng rolling1s có min0.561667; mean đạt không chứng minh nhịp ngắn hạn ổn định.

Ở lượt tệ nhất m05, AP transport wait trung bình1408.855µs/frame, riêng đoạn này đã vượt ngân sách833.333µs. Model compute trung bình116.113µs, host receive→send return261.759µs. AP wait bao gồm backend/network/host+guest scheduling và chồng lên host responder; không cộng các đoạn chồng nhau hay quy phần dư riêng cho network. Debt ledger khép kín và ghi90.634301s bị cắt ở lượt này. Bằng chứng cho thấy throughput/latency đường xử lý là giới hạn thực; giữ cap không tạo năng lực xử lý mới.

m05/m07 timeout và bị dừng theo deadline; review giữ `simulationExecution=interrupted`, không hoàn tất giả. m06 kết thúc ground/disarm nhưng `Clock probe identity` làm tổng capture incomplete: observer không lưu offending response nên chưa biết chính xác nonce/địa chỉ nào hoặc có phải late reply. Raw model oracle và AP own-clock ledger vẫn kiểm được dưới nhãn diagnostic; clock coverage toàn lượt không đạt. Receipt gốc không được sửa thành sealed/PASS.

## Cap500ms và stale

| Pause yêu cầu(ms) | Pause đo bằng Node hrtime(ms) | RTF probe | Tổng debt bị cắt(ms) | Kết luận |
|---:|---:|---:|---:|---|
| 450 | 450.085 | 1.003085× | 0.000 | Đối chiếu short-probe đạt |
| 550 | 549.916 | 0.998809× | 48.208 | Đối chiếu short-probe đạt |
| 900 | 904.810 | 0.940303× | 797.888 | Đối chiếu short-probe đạt |
| 3200 | 3200.781 | 0.815776× | 2740.540 | FAIL frame/stale |

450ms không clip. 550ms có48.208ms clip ở frame6334. 900ms có797.888ms tổng clip; frame6173 vào cap với debt−1080.432ms. Tổng clip phụ thuộc debt đã có và diễn biến sau pause, không phải đơn giản duration−500. Frame-based gap association dùng Python backend send gaps:450.702/554.128/907.467ms; không coi những số đó bằng pause duration của miền Node hay latency một chiều.

Probe3200ms chỉ ground,0ARM/mode commands. Control guard từ chối khi stale và không ghi control bytes; sau SIGCONT cùng PID, physics tiếp tục dù vượt3s. Backend stale check hiện nằm ở recv timeout, chưa từ chối suspension trước khi tiêu thụ queued packet. Đây là gap phải xử lý, không tự cấp lại authority hoặc nghiệm thu recovery.

Probe dài có2duplicate servo datagrams. Source AP thực có `wait_ms >1000` với UDP timeout100ms; comment nói10seconds không khớp code. AP parser có2zero-delta sensor parses; sync frame IDs thiếu6330/6331 và range lệch tới14261 trong khi raw unique model0..14259 vẫn chính xác. Gate one-to-one AP/model frame correlation từ chối và được giữ FAIL. Diagnostic AP debt equation vẫn khép kín, clip2.740540s. Hai retry datagram AP không phải GCS/flight-command retry; cả stimulus/test không gửi lệnh bay thật.

Unique model frames/byte oracle không mất bước; AP pending requests khi writer được đóng và duplicate/zero-delta parses được báo riêng. Không lấy raw oracle thành full protocol/mission acceptance. Post-pause configuration readback3200ms chưa chạy, giữ NOT_CHECKED.

## Miền clock và lỗi phương pháp đã bị loại

Python backend/clock observer dùng `time.monotonic_ns`; AP stage/probe dùng guest `CLOCK_MONOTONIC`. Cặp Python–guest có uncertainty và compatible constant-offset intersections ở các đoạn quan sát; không chứng minh zero drift hoặc phủ đầy m06 khi observer chết.

Node MAVLink/pause driver dùng `process.hrtime.bigint`. Phát hiện mốc Node và Python không trùng; calibration current-only cho offset cỡ−34281s và không chứng minh mapping lịch sử. Các field `cap.postResumeFirstSecond*` ở3receipt probe ngắn đã tính bằng cách ghép trực tiếp hai miền nên **REJECTED**, giữ nguyên artifact ban đầu trong `clock-domain-incident.json`, không dùng để kết luận. Thay bằng `pause-frame-association.json` dựa frame IDs; không scale hay đổi clock. RTF/debt/jitter own-clock và raw hash vẫn giữ đúng nghĩa gốc. Cần calibration bracket Node↔Python ngay admission/suốt run trước mọi tương quan cross-domain tương lai.

## Verify và tài nguyên

Implementation coverage5/5REQ-P01..P05=100%; feature đo/kiểm đã hoàn tất, performance/fault acceptance có FAIL như trên. `acceptance-contract.json` mới và `verification-summary.json` ghi **TESTS_COMPLETED_NOT_READY_FOR_ROBUST_1X**. Initial `analysis-completion.json` giữ PARTIAL do probe duplicate bị strict assertion; `analysis-resolution.json` bổ sung diagnostic và full13raw replay, không bypass gate.

Analytic reporting fixtures đạt3checks (uniform1200Hz, gap600ms giữ lại, reverse clock từ chối). Syntax checks ở `syntax-final.json`; không có AP/source build mới và không claim full upstream CI. Source pins của campaign không drift; legacy file hashes4809khớp. Đây là đối chiếu tại thời điểm kiểm, không chứng minh original paths luôn hiện diện trong quá khứ hoặc ENDURE24h đạt.

Sàn20GiB và peak budget4GiB được admission trước campaign; monitor mỗi giây có reserve768MiB, không gate breach. Tại preservation cuối còn~25.52GiB. Đã đóng13container/backend/state,24CPUworkers và preview8798; dọn13thư mục runtime state do task tạo, mọi evidence vẫn giữ. Docker image prune0B; không prune volumes/containers, xóa user data, tạo project copy/tmp install hay thay preview cũ. `cleanup-final.json` và fingerprint verification là bằng chứng riêng, không chữ ký phần mềm.

## Ưu tiên sửa tiếp

1. Guard suspension/transport epoch trước consume queued servo; stale phải kết thúc hoặc yêu cầu phiên mới rõ ràng, không tự tiếp tục physics như không có gián đoạn.
2. Correlator nonce/late response và AP duplicate sensor replies: capture raw lỗi, bounded outstanding identity, khôi phục frame lineage; vẫn fail-loud với foreign response. Calibrate/label tất cả counter domains trước phép trừ.
3. Tối ưu critical AP↔backend path và scheduling với đối chứng cùng workload: khảo sát chạy physics cùng guest/process seam để giảm round trips, hoặc CPU/service reservation có số đo; giữ float64/model oracle/rate1200/cap500ms. Chạy lại ma trận nguyên vẹn sau sửa, không chỉ lượt dễ.
4. Hiển thị actual RTF/lag/overload trong simulator UI: `AP pace1×` hiện là cấu hình danh định, không phải hiệu suất đo. Graphics/native Hera/SDK/HIL/calibration và Ragas/DJI comparative gates vẫn tách riêng.

Không phát hành hay tích hợp Fly từ kết quả chưa đạt này. Báo cáo và inventory mới nằm hoàn toàn ở namespace PACING02/delivery/docs mới; không rewrite canonical SOT/candidate/ENDURE.
