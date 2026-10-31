# SIM32-PACING01 — phân tích pacing mặc định1×

Đã phân tích **898211 frame của bảy trace sẵn có**, không chạy model hay SITL mới. Giữ nguyên source SIM32, app/source/candidate đóng băng, ENDURE và receipt trước. Dung lượng kiểm đầu task đã lên khoảng43GiB; phạm vi lần này vẫn chỉ phân tích offline. **Chưa xác nhận lỗi pacing1× đã được sửa.**

## Phần đã xác định

| Run / cấu hình khai báo | RTF tính lại | Mean khoảng nhận packet | Physics median / mean | Wall dư so với pacing khai báo |
|---|---:|---:|---:|---:|
| Native kernel, pacing1 |0.927630 |898.35µs |46.04 /52.08µs |8.368s |
| Native kernel + native socket timeout, pacing1 |0.935935 |890.38µs |44.79 /50.66µs |7.304s |
| Baseline Python, pacing1.10 |1.091242 |763.66µs |94.71µs median |0.777s |
| Optimized không tải, pacing1.10 |1.096485 |760.00µs |36.58µs median |0.310s |
| Optimized tải giữa/gió ngang, pacing1.10 |1.097259 |759.47µs |36.96µs median |0.242s |
| Optimized tải lệch/gust, pacing1.10 |1.095509 |760.68µs |37.67µs median |0.405s |
| UI cũ, pacing1 |0.928351 |897.65µs | Physics elapsed khoảng12.49% wall |8.209s |

Nhịp model là1200Hz, tức833.33µs/bước; target wall khi khai báo1.10 là757.58µs/bước. Đo bằng `(N−1)/rate` trên khoảng timestamp host nhận packet đầu→cuối, không tính bước đầu không có interval. RTF UI cũ trước đây0.928358 gồm bước đầu; receipt cũ giữ nguyên, số chuẩn hóa lần này ghi riêng. Sai khác first-step khoảng8ppm không giải thích hụt6–7%.

**Chi phí kernel giảm nhưng RTF mặc định gần như giữ ở vùng0.93.** Tổng elapsed đo trong physics chỉ6.704s và6.487s, tương đương5.80% và5.69% wall của hai run native1. Con số này gồm cả preemption, không phải CPU time thuần. Nó thấp hơn phần wall dư8.368s/7.304s. Phép trừ mô tả nếu loại mọi elapsed physics vẫn chỉ cho0.9847/0.9924; đây không phải dự báo hoặc bound nhân quả vì pacer/concurrency có phản hồi. Kết quả đủ để ưu tiên đo phần ngoài kernel thay vì suy RTF từ benchmark kernel3×.

**Độ chậm xuất hiện theo từng khoảng vận hành.** Các cửa sổ đầy đủ10 giây model của native1 có RTF0.809–0.999; native socket1 có0.844–0.998. Không phải mỗi bước đều có thêm một offset cố định. Native1 có103 khoảng nhận trên10ms, max140ms; native socket1 có151 khoảng, max161ms. Các khoảng nhanh hơn target có bù một phần khoảng chậm: không được cộng riêng mọi khoảng trễ rồi coi đó là tổng thiếu hụt. Một cửa sổ/một run không chứng minh long-run hoặc nguyên nhân.

**Chưa có dấu queue đầy hoặc hồ sơ mất frame trong hai run1×.** Raw count/rate/sequence/SHA đạt, duplicate0, queue max10/14 trên capacity256, đã drain/seal. Điều này loại dấu hiệu overflow được quan sát trong hai run, không loại GIL contention, delay writer hoặc scheduling. Pearson giữa elapsed physics trước đó và gap nhận kế tiếp chỉ0.171/0.203; mô tả này không xác nhận hay bác bỏ nhân quả.

Mean gap sau cadence snapshot lớn hơn group thường, nhưng phần chênh nhóm mô tả chỉ khoảng0.573s/0.463s; không đủ lấy làm lời giải độc lập cho8.368s/7.304s. Group cadence có confounding, writer chạy bất đồng bộ và pacer có bù. Không quy hết phần dư cho filesystem, network hoặc ArduPilot.

## Control flow và giới hạn bằng chứng

Nguồn pinned `dbe792162d06cab66c3475fd5556bf7a120f119e` cho thấy JSON gửi servo, chờ sensor, lấy delta timestamp model rồi gọi `time_advance()`. Khi time sync bật, pacer tích lũy sleep debt theo target speedup và trừ thời gian ngủ thực; debt âm được giới hạn ở−100ms. Vì có cơ chế bù này, lập luận đơn giản “usleep oversleep cộng dồn nên hụt7%” chưa đủ. [SIM_JSON.cpp](https://github.com/ArduPilot/ardupilot/blob/dbe792162d06cab66c3475fd5556bf7a120f119e/libraries/SITL/SIM_JSON.cpp), [SIM_Aircraft.cpp](https://github.com/ArduPilot/ardupilot/blob/dbe792162d06cab66c3475fd5556bf7a120f119e/libraries/SITL/SIM_Aircraft.cpp).

Header cũng có hai counter thuộc hai class: JSON servo counter và Aircraft pacing counter; không được hiểu hai lần tăng counter trong source thành hai frame physics. `use_time_sync` mặc định true và các flag no-time-sync/no-lockstep là optional. [SIM_JSON.h](https://github.com/ArduPilot/ardupilot/blob/dbe792162d06cab66c3475fd5556bf7a120f119e/libraries/SITL/SIM_JSON.h), [SIM_Aircraft.h](https://github.com/ArduPilot/ardupilot/blob/dbe792162d06cab66c3475fd5556bf7a120f119e/libraries/SITL/SIM_Aircraft.h).

Đây là control-flow inspection của source commit đi với metadata binary, không phải instrumented sleep trace hoặc rebuild proof. Linux SITL `get_wall_time_us()` đọc CLOCK_MONOTONIC trong guest; raw đo clock monotonic trên macOS host. Chưa có cặp clock offset/drift để tách VM scheduling khỏi nhịp host. Không trừ trực tiếp timestamp thuộc hai domain để gán latency một chiều.

Runtime dùng Linux/amd64 trong Docker bridge trên Mac arm64, giới hạn2CPU/384MiB. Đây là cấu hình đã ghi, **không phải bằng chứng cgroup đã throttle**: capture thiếu `cpu.stat`, CPU stage trace và VM clock pairs. Không tự đổi CPU/memory để tạo số tốt hơn.

Đặc biệt, hai run mặc định1 chưa có readback `SIM_SPEEDUP` mới của PERF01; chỉ có CLI/config pin khai báo1. Ba run optimized1.10 có readback. Mọi kết luận pacing ở hai run1 phải giữ nhãn cấu hình khai báo; cần readback trong nghiệm thu kế tiếp.

## Hướng xử lý ưu tiên — chưa chạy

1. **P0: instrument đúng đoạn trước khi sửa pacer.** Ở backend ghi theo frame: rx→step begin/end→serialize end→send return→enqueue end; worker ghi dequeue/end/queue depth và snapshot/fs action. Ở AP sandbox riêng ghi servo send→sensor receive→sync enter, target period, debt trước/sau, sleep requested/actual và sync exit. Ghép frame identity; paired clocks có uncertainty/offset/drift rõ, không lấy thời gian host làm thời gian guest. Thu cgroup `cpu.stat`, process CPU/RSS và chế độ nguồn cùng cửa sổ. Raw/journal phải giữ nguyên full count/SHA và fail-loud; instrumentation không được silently drop để giảm overhead.
2. **P1: thử từng yếu tố khi được mở runtime gate.** Cùng seed/profile/mission1200Hz, pacing1 và readback, lặp/counterbalance đủ để phân biệt nhiễu host. Tách UI/replay cadence, writer thread với process writer, và transport xuyên VM với backend Linux cùng môi trường. Đo overhead riêng của instrumentation. Kernel Mac hiện tại không dùng như binary Linux; việc build ABI Linux hoặc AP sandbox instrumented cần increment riêng, pin/license/ADR và admission peak, không sửa binary/candidate đang bảo vệ.
3. **P1: chọn correction từ stage trace.** Nếu sleep-debt/clock sai thì sửa pacer trong sandbox nguồn riêng với deadline theo clock monotonic và elapsed thực; nếu bridge/context switch là chính thì đồng vị trí AP/backend; nếu GIL/journal là chính thì tách writer có queue/byte budget, seal/count/error gate. Các phương án là conditional, chưa có root cause để chọn một cách như lời giải đã chứng minh.
4. **Gate sau sửa:** cùng golden corpus593888 frame byte-exact, analytic/convergence/domain, payload/authority/fault/full raw seal; full UI+SITL trên source cuối, không tải/tải giữa/tải lệch, default1 readback, RTF≥1 theo denominator chuẩn cùng p95/p99/max và cửa sổ thời gian. Ghi failed/aborted samples. Graphics, calibration Hera/native video và ENDURE giữ gate riêng.

Không đổi ngầm pacing1 thành1.10, không scale clock sensor, không bỏ bước/frame, không no-lockstep, không hạ độ chính xác hoặc gọi playback là bay. Cấu hình1.10 đã đạt trong PERF01 vẫn là trường hợp tách biệt, không chứng minh default1 đã sửa.

## Verify và bàn giao

REQ-T01/T02: đủ898211 frame, SHA uncompressed/count/servo/rate/monotonic/gap-sum/RTF consistency đã kiểm. REQ-T03: control flow và giả thuyết được phân biệt; **root cause unconfirmed**, thiếu AP timing/clock/cgroup đã ghi. REQ-T04: kế hoạch correction cụ thể và gate giữ nguyên; implementation/live tests mới **NOT_CHECKED**.

Preservation đầu task:4391 đường dẫn duy nhất khớp SHA, gồm4051 protected cũ và343 file handoff trước có giao nhau. Check cuối và fingerprints nằm trong `evidence/sim32-pacing01/verification.json` và `handoff-fingerprints.json`. Không sửa receipt cũ, không source/candidate/ENDURE mutation, không Docker/SITL process/build/install hoặc cleanup phát sinh. Script chạy `python3 -B`, không tạo cache. Không có scratch dependency/project copy cần xóa. Một agent thực hiện Contractor/Builder/Verify, không audit độc lập.
