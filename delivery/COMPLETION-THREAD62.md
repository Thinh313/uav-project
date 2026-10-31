# COMPLETION — THREAD62

Status: **PARTIAL_DIAGNOSTICS_VERIFIED_STABLE_1X_FAILED**. Phép đo và toàn vẹn đã kiểm; mục tiêu pacing ổn định1× chưa đạt. Một agent thực hiện các pha specify/build/verify; không tuyên bố review độc lập bởi người khác.

Đã triển khai module cô lập `pilot/thread62`, không tích hợp Fly/candidate hay ký phần mềm. Observer là tiến trình con đọc đúng unique64-bit thread ID của backend bằng Apple libproc; query200Hz có timestamp trước/sau, CPU user/system, trạng thái thread và deadline bị lỡ. Mọi sample được giữ trong binary bounded; overflow/query sai/CPU regress fail loud.

| Lượt | Frame sensor+aux khớp gốc | RTF toàn lượt | RTF thấp nhất khối đủ5s | Clip cap500ms | Driver |
|---|---:|---:|---:|---:|---|
| R1 | 83,591 | 0.606000× | 0.318833× | 32,460 | PASS_BOUNDED_COUPLED_CAPTURE |
| R2 | 95,850 | 0.809602× | 0.241833× | 11,015 | FAIL |

54 kiểm mock và33 kiểm cuối có phạm vi đạt. Tổng179.441 frame sensor+aux được đối chiếu toàn bộ với mô hình gốc, RX/INTENT/SENT và AP receive/parse; WAL CRC/SHA, thứ tự fsync-trước-sensor được kiểm. Có thêm đúng một servo tail ở mỗi lượt đến lúc stop: frame83591 và95850 giữ nguyên rawHex riêng, không advance model hoặc gửi sensor. Không cộng tail này vào số frame đã xử lý. Cap clipping bỏ nợ thời gian (44.782267s /18.282149s), không bỏ frame vật lý; vì vậy không báo tốc độ1× từ elapsed time.

R1 hoàn thành takeoff/neutral hold/LAND và đóng bình thường. R2 driver FAIL `PHYSICS_STALE_OR_FUTURE` trong lần gọi LAND đầu; yêu cầu LAND đã có thể được thực thi một phần trước khi guard từ chối. Driver thực hiện thêm một LAND trong nhánh cleanup, rồi quan sát ground/disarm và END. Có hai LAND invocation ở R2: không mô tả là chỉ một lệnh hay một phiên driver PASS. Raw/oracle PASS và đóng writer thành công không xóa FAIL của driver. Không tự phát lại input hay khôi phục quyền.

UI1920×1080 cùng scene thực chạy trong hai lượt;12.896 draw rows được thu nguyên chuỗi JSON thành27 khối ≤500rows, kiểm SHA/count/deadline/tail không thiếu. Tốc độ UI54,45 /54,62Hz; đây là draw rate, không phải physics1200Hz. Browser Review đã đối chiếu SHA318,2MiB raw của R2; screenshot `evidence/thread62/review-R2-1920.png`. Viewport được trả mặc định sau kiểm.

## Phân biệt đoạn chậm

R1 frame70603: receive→send339,143792ms, CPU main thread0,909042ms. Durable-intent337,04075ms; write+fsync chỉ0,824666ms, còn336,216084ms ngoài các syscall đo được. Có62 query bracket nằm trọn trong frame, đều thấy RUNNING_OR_RUNNABLE; CPU của cửa sổ covering chỉ1,123ms. Đây là chứng cứ main thread ít chạy CPU trong đoạn chậm, không chứng minh độc quyền nguyên nhân scheduler hay GIL.

R2 frame94727: Frame chậm nhất R2 mất85,995958ms với0,81025ms CPU; chỉ hai query nằm trọn span, đều RUNNING_OR_RUNNABLE. Fsync p99/max R1:1,066167/72,599667ms; R2:0,545167/55,467167ms. Có cả sample WAITING và UNINTERRUPTIBLE; state này không cung cấp filesystem wait reason. Query chậm nhất104,196583ms /39,184542ms; mỗi lượt603 missed sample deadlines được ghi rõ, không nội suy thành sample giả.

Tải host quan sát không được cố định: load1m cao nhất16.402/22.209. Không dừng tiến trình ngoài phạm vi. Không thể quy khác biệt hai lượt thành hiệu quả tối ưu hoặc quy toàn bộ regression so với ISOLATE61 cho observer. Chưa có actual observer-on/off A/B trên cùng workload.

## Ranh giới và bằng chứng

Không có exclusive host runqueue-wait counter hoặc kernel filesystem-wait duration. Libproc CPU counters có lượng tử microsecond; trạng thái là sample, không phải thời lượng. Khớp clock host–guest dựa nonce bracket (max126,938374ms /40,909125ms), không suy ra one-way latency chính xác. Guest per-thread CPU/runqueue counters giữ riêng và có0 lỗi observer, không trộn với host CPU.

Cả hai lượt dùng cùng nguồn đã pin, ArduCopter4.7.1, rate1200, speedup1, negative debt cap500000us, AP trace tmpfs/physical host WAL, không preallocation fallback hoặc bỏ frame. Same source không đồng nghĩa same background load. Header/close cùng fsync; snapshot UI chỉ atomic replace và không được gọi là durable evidence.

Đối chiếu22.977 đường dẫn bảo vệ trước và sau chạy:0 missing/0 SHA đổi, gồm chuỗi bảo vệ source/candidate/ENDURE. Chỉ là kiểm ở hai thời điểm; không tuyên bố liên tục hiện diện hay nghiệm thu ENDURE24h. Giữ nguyên các sự cố/attempt cũ. Không build APK, emulator, SDK/HeraHub, signature hoặc soak mới. AP/backend/observer của cả hai phiên đã đóng; tmpfs được export và kiểm SHA trước khi dừng container. Docker image prune đã chạy đúng hygiene; không prune volume/container. Không tạo scratch project hay dependency install nên không có scratch cần xóa.

Dung lượng lúc lập báo cáo21.74GiB, trên sàn20GiB. Admission mỗi lượt≥22,5GiB, quota2,25GiB /forecast1GiB, guard20GiB+768MiB được giữ. Không chạy thêm lượt trong increment này (đã dùng đủ2attempt).

## Ưu tiên tiếp theo

1. Tách timestamp/CPU của encode, CRC/SHA, append và khoảng đợi GIL trong durable-intent; không tối ưu fsync dựa vào wall-only. Thiết kế phép bác bỏ nguyên nhân scheduler/GIL, thay vì coi RUNNING là thời gian chạy thật.
2. Đo observer on/off với cùng phiên bản và workload mock cố định, rồi fixture host-load có ngân sách; chỉ can thiệp tiến trình thử do module tự sở hữu. Không so các lượt môi trường nền khác nhau như A/B nhân quả.
3. Sau mock và headroom đủ, chạy SITL+UI để kiểm lại toàn bộ original oracle/barrier/cap/freshness; chỉ công bố1× khi whole/window/no-clip cùng đạt. Không nới speedup/cap/freshness hoặc giảm durability để tạo PASS.

Nguồn API: ABI đã pin từ Apple SDK `sys/proc_info.h`, `libproc.h`, `mach/thread_info.h`; tham khảo [Apple XNU observability](https://github.com/apple-oss-distributions/xnu/blob/main/doc/observability/recount.md) và [fill_taskthreadinfo](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/bsd_kern.c). Đơn vị CPU và identity còn được kiểm bằng mock CPU/sleep thực; tài liệu không thay kết quả host này.

Bằng chứng chính: `verification-final.json`, `source-pins-v2.json`, `preservation-before/after.json`, `timing-R1/R2.json`, `runs/*/thread-analysis.json`, `io-verification.json`, `io-analysis.json`, `attribution-verified.json`, `readback.json`, `closure.json`, `UI-R1/R2/manifest.json`, `handoff-processes.json`.
