# SIM32-INSTRUMENT01 — Completion / Verify

14/10/2026 · AERIS · private simulator engineering increment. Contractor → Builder → Verify do cùng một agent thực hiện; không phải audit độc lập.

## Kết quả và phạm vi

Đã đo từng đoạn AP/backend và clock host–guest bằng ArduPilot SITL thực, rồi sửa pacer trong sandbox riêng. Ba capture UI + SITL đạt RTF trung bình≥1 ở tốc độ danh định1×, giữ đầy đủ bước vật lý và byte sensor. Đây là kết quả trên nhánh thử nghiệm ARM64, chưa nghiệm thu pacing stock amd64, Hera thực hay sản phẩm hoàn chỉnh.

Module mới: `pilot/sim32-instrument01`. AP dependency/build mới: `runtime/sim32-instrument01-build/ardupilot`. Evidence mới: `evidence/sim32-instrument01`. Original app/services/candidate/trust/ENDURE, module SIM32 và mọi receipt cũ giữ nguyên. Không Fly integration, SDK/HeraHub, ký release/candidate hay chạy lại ENDURE.

## Đo lường và nguyên nhân trong lượt đối chứng native

AP observer có bounded128MiB mmap trace, ghép frame với backend16MiB trace; overflow/missing stage từ chối nghiệm thu. Ghi JSON servo send/receive, parse, pacer/debt/sleep và backend model/serialize/send/enqueue. Clock UDP diagnostic ghép nonce và hai timestamp ở mỗi phía, giữ cả timeout; báo khoảng offset/drift theo nhân quả, không lấy hiệu hai clock làm latency một chiều chính xác. Cgroup observations được lưu; các capture UI có0throttle quan sát.

Original AP là static ELF nên LD_PRELOAD không hoạt động trên AP, dù standalone selftest đạt. B1 được giữ ở trạng thái backend/clock-only; không dùng làm AP observer PASS. Chuyển sang source commit `dbe792162d06cab66c3475fd5556bf7a120f119e` trong checkout riêng, direct observer, compiler native ARM64. Control/on dùng cùng binary SHA; architecture khác original amd64 nên không suy kết quả về nguyên nhân lịch sử .928/.936×.

Cặp UI cùng binary trước sửa: observer-off `ui1791935355382` đạt0.998731867×; observer-on `ui1791935179602` đạt0.997428878×. Chỉ một cặp, chưa đủ ước lượng overhead thống kê hay loại trừ thứ tự/tải host.

Trong observer-on, ledger AP khép kín: wall106.931133s = target106.656624004s − debt-endpoint0.019067s + negative-debt bị cắt0.272141s − quantization0.030880004s + wall chưa được tính0.052315s. Residual0µs. Backend model trung bình36.99µs; transport wait AP bao gồm network/backend/scheduling và chồng lên host responder, không cộng các đoạn chồng nhau. Raw đầy đủ và p50/p95/p99/max trong `runs/*/direct-analysis.json`.

## Chính sách pacer v2 được khai báo rõ

- Một wall-clock snapshot được dùng nhất quán cho trừ sleep và cập nhật last-wall. Công việc giữa các lần đọc không bị bỏ khỏi accounting.
- Giữ tối đa500ms nợ âm thay cho100ms của pacer đối chứng. Có thể phát các đợt frame nhanh hơn wall-time để bắt kịp; đây là thay đổi policy công khai, không phải nhịp đồng đều.
- `SIM_SPEEDUP=1`, `SIM_RATE_HZ=1200`, bước model1/1200s; readback chỉ đọc trước/sau bay xác nhận. Không clock scaling, extrapolation, bỏ bước hay resend mission ngoài policy. Backend stale3s và authority/target gates giữ nguyên; không tự resume khi stale.
- Thay đổi chỉ ở AP sandbox thử nghiệm, chưa là firmware production hay hành vi stock ArduPilot được nghiệm thu.

## Kết quả UI / control / độ đúng

| Profile reference, provisional | Run | Frame physics | RTF trung bình | UI/control checks |
|---|---|---:|---:|---:|
| Không tải / lặng gió | `ui1791935717843` | 127,810 | 1.000493853× | 13/13 |
| Tải giữa1kg / gió ngang | `ui1791935879739` | 128,090 | 1.000942491× | 13/13 |
| Tải lệch1kg / gust có seed | `ui1791936043964` | 130,391 | 1.000422714× | 13/13 |

RTF = `((frame_count−1)/1200) / (host_last_receive−host_first_receive)`; chỉ cửa sổ wire active, không gồm startup/closure. Mỗi profile có một lượt~106–109s active. Tất cả có duplicates0, journal count/raw hash khớp, queue drained, writer sealed, container đóng có flush AP trace. Sau v2 không quan sát negative-debt clipping; wall chưa tính chỉ3–4µs toàn capture. Nợ âm sâu nhất−450.284ms ở case không tải, còn49.716ms tới cap: headroom hẹp, chưa có bảo đảm sustained1×.

13kiểm gồm biên tập mission→compiler, Home/preflight/grant, upload/readback, payload3camera/2gimbal synthetic qua AP, ARM/AUTO có heartbeat quan sát, chống lặp action, terminal-ground/disarm/closure và sealed review. Không coi camera ACK là ảnh thực hoặc hardware execution. `review.json`/UI receipt giữ provenance simulation và physicalMedia=false.

Replay toàn bộ12raw capture mới bằng Python model bất biến trước tối ưu: **1,226,103frame**, sensor UTF-8 encoded bytes và aux RPM/energy/ground khớp chính xác; frame IDs/rate/raw SHA/count khớp. Bao gồm raw khỏe của attempt lỗi driver, không biến attempt lỗi thành mission PASS. Đối chứng này xác nhận model tối ưu trả cùng output cho motor input đã ghi; chưa chứng minh hiệu chỉnh Hera hoặc quỹ đạo hai flight khác timing hoàn toàn giống nhau.

Fault v3 đạt6kiểm: sai aircraft target bị chặn trước wire, mất GCS thực→RTL/land, quan sát ground/disarm, nhiệm vụ gián đoạn không hoàn tất giả, AUTO không replay, backend chết/stale chặn điều khiển. Probe ground-only SIGSTOP/SIGCONT300.102ms trên cùng owned PID dưới deadline3s giữ16,231frame liên tục, raw replay exact và clipping0. Probe ngắn không là performance acceptance hay tự khôi phục chiến dịch.

## Jitter và giới hạn đồ họa phải giữ mở

| Profile | Backend packet p95ms | Maxms | Packet>0.8333ms | Render interval p95ms | Maxms | Display age p95ms |
|---|---:|---:|---:|---:|---:|---:|
| Không tải / lặng gió | 0.137250 | 24.956667 | 49/127810 | 17.5 | 791.8 | 201 |
| Tải giữa1kg / gió ngang | 0.145666 | 29.178375 | 53/128090 | 17.5 | 790.9 | 200 |
| Tải lệch1kg / gust có seed | 0.145833 | 9.649084 | 32/130391 | 17.5 | 799.5 | 197 |

AP sleep được batching~5ms; servo wall interval không đồng đều1200Hz. Backend deadline excursions và renderer tail có thật, dù mean RTF≥1. Các interval render có navigation/startup; p95~17.5ms chưa đạt mục tiêu đề xuất16.7ms trên toàn capture. Existing viewer giữ3524/3539/3537rAF callbacks không render trong tương ứng6963/6991/6985callbacks để pacing hiển thị; đó không phải physics-step drop. Counts/raw được giữ, không xoá outlier. Canvas910×726 trong viewport1280×800, ANGLE Metal Apple M1 Max; không suy thành native Hera GPU benchmark. Đã xem ảnh Preflight/Fly v2offset; UI reused read-only, không là nghiệm thu thiết kế mới.

RTF margin nhỏ, một lượt/profile và khoảng offset/drift có uncertainty. Chưa kiểm repeated/randomized overhead, kéo dài1×/nhiều host load & power states, hard real-time, full upstream AP CI, SDK/native input/video, HIL/flight, calibration Hera hoặc A/B Ragas/DJI. Độ đúng control/logging đạt trong scope không chứng minh sản phẩm vượt DJI.

## Sự cố giữ nguyên và provenance

1. Static original binary khiến AP preload coverage fail; B1 và standalone selftest riêng.
2. Dependency/build failures pexpect/littlefs/lwip và compile amd64 emulated bị dừng có log; native build dùng cùng checkout, không project copy.
3. NativeD1/StartupE1 chờ TCP serial0 làm admission observer deadlock,0frame/không ARM. CLI nowait được khai báo ở các lượt mới; không rewrite lần lỗi.
4. NativeC1 binary diagnostic trung gian chưa archive trước relink: SHA/source/raw giữ nhưng exact binary có gap `NOT_ARCHIVED`; không dùng làm cặp exact binary.
5. FaultV2 import path sai, fail trước ARM; raw khỏe vẫn replay riêng. FaultV3 tên mới, không retry tự động/ghi đè.

Các receipt chẩn đoán nằm `static-binary-incident.json`, `startup-gate-incident.json`, `direct-source-change.json`, `fault-driver-incident.json` và logs. Final tested AP SHA **`f2be1f349f84b4aedaa5912b3050f64f476f3218bc4f68b34ad4de11393c2d08`**,4sourcefile+binary archive ở `pacer-v2-source`, exact flags/submodule pins và compile commands ở `build-final.json`. Checksums không phải software signature.

## Tài nguyên và bảo toàn

Preservation cuối: **4406/4406file SHA khớp**,0missing/0drift. Là đối chiếu tại thời điểm kiểm, không khẳng định original path hiện diện liên tục trong quá khứ. ENDURE trạng thái/bằng chứng cũ không đổi và không được biến thành PASS.

Sàn20GiB giữ trong các lượt mới; resource gate khai báo peak8GiB và runtime headroom. Cuối cleanup còn~34.36GiB. Dừng hết owned AP/backend/container và preview8797 sau idle/no grant; preview8796 cũ không đụng. Đã dọn1,182object/config amd64 chưa hoàn tất23,566,195byte trước build ARM64; hai failed-state EEPROM32,768byte đã snapshot đúng SHA vào evidence trước dọn. `docker image prune -f` thu0B; không prune volumes/containers. Giữ image fixed-tag/build native làm dependency tái sử dụng. Không scratch ngoài repo, whole-project copy hoặc xóa dữ liệu người dùng.

## Bàn giao và thứ tự tiếp theo

Contract mới `pilot/sim32-instrument01/acceptance-contract.json` và `verification-summary.json` ghi REQ-I01..I04 theo phạm vi. `final-fingerprints.json` ràng buộc source/binary/evidence/report; kết quả kiểm manifest trong `fingerprint-verification.json`.

Ưu tiên tiếp: ma trận repeated1× theo host load/clock uncertainty và worst-case debt/jitter, đủ đối chứng on/off để định lượng overhead; kiểm cap saturation và failure semantics có gate sàn trước run. Sau đó xử lý render tail/state freshness trên module riêng. Chỉ tiến tới calibration Hera/HIL và đối chứng Ragas/DJI khi có SDK/thiết bị/cấu hình thực và tiêu chí đã chốt. Nhánh pacer v2 không tự thay stock AP, frozen candidate hay Fly.
