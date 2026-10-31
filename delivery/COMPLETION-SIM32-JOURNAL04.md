# SIM32-JOURNAL04 — kết quả mock/fault injection14/10/2026

**Đạt nghiệm thu trong phạm vi mock; chưa nghiệm thu SITL hoặc pacing1×.** Module mới tách khỏi PIPE03 và toàn bộ source/candidate đóng băng. Không chạy ArduPilot/Docker/SITL, không ký, tích hợp Fly, nối SDK/HeraHub hoặc khởi động ENDURE. Thực hiện Build và Verify tuần tự bởi một agent; không gọi là kiểm định độc lập.

## Sửa đường bảo toàn frame

PIPE03 gửi sensor rồi mới dựng/enqueue row: process chết ở giữa có thể để sensor đã phát thiếu raw. Bản JOURNAL04 ghi input nhận được và **nguyên byte sensor vào write-ahead journal trước khi phát**. Queue256 được đặt chỗ trước computation; intent có sequence/CRC32/hash chain và snapshot bất biến. Chính sách mock mặc định gọi fsync trước publication. Marker ghi kết quả send-return tách riêng; crash thiếu marker giữ UNKNOWN, không tự phát lại, không suy ra chưa gửi hay thực thi từ intent.

Worker nhận bytes đã encode, chỉ nén/ghi archive và snapshot. Adapter gzip xử lý short-write đầy đủ; lỗi ghi dở, quota, flush, snapshot hoặc worker treo khiến archive/capture INCOMPLETE. Canonical intent vẫn giữ sensor/input để đọc lại; recovery không truncate, sửa byte hoặc resume session. Fail một archive không đồng nghĩa mất bản sensor duy nhất, và recover được không đổi FAIL thành COMPLETE.

Signal handler chỉ đặt cờ; normal checkpoint đưa epoch sang DRAINING. Kiểm stop và reserve frame được tuần tự hóa với signal đã được handler quan sát. Không admit frame mới sau stop; frame đã admit chỉ hoàn tất khi còn fresh. Stale3s/clock discontinuity, duplicate/gap/malformed và frame khởi đầu khác0 vẫn terminal. Datagrams nhận nhưng chưa admit được giữ riêng. Lỗi worker xảy ra khi đang recv không chặn ghi RX vào WAL còn hoạt động trước khi từ chối admission.

Đây là module mock riêng, **không thay nguồn runtime PIPE03 đã bàn giao**. Chưa chọn để chạy Fly/SITL. Default bounds512MiB raw/192MiB compressed/WAL16MiB, row8192bytes/record16384bytes là bound mock, không phải ngân sách campaign SITL đầy đủ.

## Kết quả kiểm cuối

| Phạm vi | Kết quả |
|---|---|
| Fault matrix mới nhất, source ghi nhận attempt08 |38/38scenario PASS |
| Dừng khi waiting, dừng ở seal và SIGKILL khi seal, raw receiver receipt |3/3scenario PASS |
| Torn/corrupt WAL, hash chain đúng nhưng semantic sai, gzip hỏng/sửa/lặp, caller mutation, workerfail–recv race |8/8scenario PASS |
| Sensor quan sát thực ở mock receiver |**520packet;0packet thiếu nguyên byte intent trước-send** |
| Computed intent canonical |**524frame khớp sensor và aux với immutable Python model gốc** |
| Emergency attempted-record khi primary WAL lỗi |5record kiểm CRC/full-byte SHA; computed intent bổ sung đối chiếu model khi chưa có trong canonical prefix |
| Đóng process/worker/socket |Mọi PID test đã đóng; không giữ mock service/preview |

49scenario là số của bộ nghiệm thu cuối, không cộng các attempt cũ để phóng đại. SIGKILL là chết tiến trình khi OS vẫn hoạt động. Hai cửa sổ intent/đã gửi trước marker đều giữ nguyên UNKNOWN; ví dụ killwire08 receiver đã thấy packet3, sensor byte có trong WAL nhưng marker chưa ghi. Không biến trạng thái này thành lỗi “chưa gửi” để retry.

Faults gồm SIGTERM/SIGINT lặp ở received/validated/admitted/computed/intent/wire/commit; SIGKILL cùng các pha; pause3,2s rồi stop; WAL short/zero/partial ENOSPC/flush/marker; gzip short/partial; archive write/snapshot/close/fsync; raw/compressed/WAL quota; worker treo; queue đầy; duplicate/gap/truncated/firstframe sai. Queue-full có đúng256computed/receiver packet, frame tiếp theo được lưu RX rồi từ chối **trước bước model**. Worker còn sống ở drain deadline trả INCOMPLETE và được chấm dứt cùng process mock; không được reuse hoặc gọi là seal xong.

Test oracle Verify chạy lại từ artifact, đọc nguyên byte receiver, intent và raw/snapshot; không dựa riêng vào JSON status. Recovery âm tính còn kiểm giữ nguyên SHA file đầu vào trước/sau đọc. Các record SEND mock chỉ là send-return cục bộ; không là ACK, flight execution, ảnh/media hoặc bằng chứng vật lý.

## Trace và tối ưu AP–backend

Đã phân tích lại**6capture/746772raw prefix frame** của PIPE03, giữ riêng2raw sensor row thiếu đã biết và case cuối bị pause/dừng. Pin AP v2/rate1200/speedup1/cap500ms đúng; không chỉnh clock, cap, bỏ frame hay sửa trace.

| Chỉ số trên6capture | Khoảng quan sát |
|---|---|
| AP transport wait trung bình |469–1194µs |
| Host RX→send return trung bình |112–260µs |
| Model step trung bình |54–104µs |
| Serialize sensor trung bình |23–42µs |
| Send syscall/scheduling trung bình |30–100µs |
| Enqueue trung bình |9–33µs |

AP wait includes backend/network/guest scheduling. Chênh duration guest–host chỉ là diagnostic giữa các boundary; có50–1811frame/case cho chênh âm nên không được diễn giải như một interval vật lý nằm hoàn toàn “ngoài backend”, hoặc latency mạng một chiều. Offset brackets có intersection trên các capture này; không chứng minh zero drift, và không dùng ratio quan sát để scale clock. Pearson APwait–host RX→send khoảng0,37–0,68 chỉ là association trên frame, không xác nhận nguyên nhân. Clockprobe cgroup throttle delta bằng0 cũng không loại trừ host/VM scheduling. Sáu capture cũ vẫn0/6RTF≥1; không sửa kết luận này.

Tối ưu đã triển khai trong module mock: **encode row/snapshot một lần, dùng bytes bất biến cho WAL và worker**, tránh serialize lại và tránh caller mutation. Microbenchmark2048row,4replicate đảo thứ tự: encode JSON worker trung bình6,02µs so với tham chiếu bytes sẵn0,108µs; **chi phí encode chuyển sang producer vẫn tồn tại**, không được gọi là giảm toàn bộ chi phí tương ứng.

Benchmark write-ahead trên512row×3replicate/policy, đảo thứ tự, no socket/no AP/UI: prepare+durability mặc định trung bình**74,77µs**, p99 từng lượt123–254µs; benchmark-only process-crash policy23,99µs, p9959,96–84,21µs. Default fsync throughput offline khoảng9615–11202row/s; không coi đó là SITL RTF hoặc deadline1200Hz đã đạt. Policy process-crash-only không được chọn ngầm để lấy tốc độ và chưa bảo đảm power-loss. Nguồn sensor nhập cùng bytes; fake send markers trong benchmark được ghi rõ OFFLINE_IMPORTED_ROWS_NO_SEND, không packet nào được phát.

Ưu tiên tiếp: giữ publication barrier và đo toàn bộ cost → kiểm thực trên SITL khi được ủy quyền/đủ headroom → đo bracket boundary và scheduling/transport → observer-off paired comparator. Giảm physics alone chưa đủ; co-location Linux cũ vẫn REJECT bởi byte oracle, không ký lách gate. Mọi thay speedup/cap/frame/model precision vẫn không được phép ngầm.

## Giới hạn và hồ sơ lỗi

- Không thể giao dịch nguyên tử giữa recv syscall và disk: crash trước bản ghi RX đầu tiên có thể để input receipt chưa rõ. Chỉ bảo đảm sensor đã quan sát ở receiver trong49scenario có pre-send intent đầy đủ, không tuyên bố không mất mọi datagram dưới mọi lỗi.
- Tổng lỗi media/disk, crash OS, mất điện, physical flush survival và archive process production isolation **NOT_CHECKED**. API fsync thành công không tự chứng minh hardware persistence. Lỗi cả WAL và emergency path phải giữ incomplete/unknown, không tạo sensor hoặc hồ sơ giả.
- Actual SITL, managed restart/resume, UI/video/SDK/Hera, campaign dài hạn, benchmark Ragas/DJI và production deployment **NOT_CHECKED**. Không quảng bá performance superiority từ mock.
- Attempt01 tuple recvmsg sai lấy ancillary làm address, sendto từ chối trước sensor đầu; sửa và giữ failure. Attempt02 verifier coi datagram deliberate-unadmitted như lỗi; sửa classification và kiểm unmatched RX ở complete seal. Attempt05 suffix replacement đổi nhầm namespace, fail trước child/socket. Attempt06 compressed-partial hook bắn ở gzip header thay vì post-frame, admission từ chối; sửa attribution frame và giữ partial matrix. Attempt03/04/07 các bộ đã đạt là historical source snapshots, không thay cho kiểm nguồn cuối. Không overwrite receipt, không cộng lỗi thành PASS và không quy lỗi harness thành kết quả AP/SITL.

## Verify, bảo toàn và tài nguyên

R01–R06:6/6implemented và kiểm trong phạm vi mock/offline,100%scope coverage. Overall **READY_FOR_MOCK_INSPECTION; NOT_READY_FOR_SITL_SELECTION/PRODUCT_RELEASE**.49scenario cuối PASS; Python compile/static checks, exact immutable oracle, recovery, read-only trace và preservation receipts đi kèm. Đây không phải phần trăm sẵn sàng sản phẩm.

5880fingerprint entries tương ứng**5877đường dẫn duy nhất** khớp SHA trước/sau, gồm5220baseline bảo vệ gốc và toàn bộ PIPE03/source/receipt đã bàn giao. Source/candidate/trust/SOT/ENDURE/AP binaries/old modules giữ nguyên. Không restart hay sửa ENDURE; các FAIL và khôi phục đường dẫn lịch sử giữ nguyên, không suy path gốc liên tục hiện diện. Hash là integrity tại thời điểm kiểm, không chữ ký mới hay24h acceptance.

Admission full peak256MiB+margin512MiB trên sàn20GiB; kiểm trước mỗi scenario và trong publisher/trace steps. Evidence task khoảng25MiB; các bản sao là module nhỏ/fixture file riêng, không whole-project copy. Không build/install/emulator, không tạo/tmp/dependency/Next/Docker artifact. Không đụng dữ liệu khác; process test riêng đóng và raw fault evidence được giữ. Dung lượng khoảng26GiB tại kiểm cuối; số chính xác trong verification/admission receipts. Không dùng free hiện tại để thay sự cố floor breach ở PIPE03.

Đường dẫn: module`pilot/sim32-journal04`, evidence`evidence/sim32-journal04`, TIP`delivery/TIP-SIM32-JOURNAL04.md`, ADR046. Evidence chính: `fault-suite-attempt08.json`, `closure-tests-receiver-bound.json`, `negative-tests-final.json`, `final-artifact-verification-receiver-bound.json`, `trace-analysis.json`+`trace-interpretation.json`, `offline-benchmark-final.json`, `preservation-after.json`, source/evidence fingerprints và`verification.json`. Helpers dùng case IDs đã tồn tại nên không chạy lại/ghi đè; future work phải có IDs/gate/namespace rõ. Không tự launch SITL tiếp.
