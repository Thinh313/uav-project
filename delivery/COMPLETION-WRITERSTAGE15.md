# WRITERSTAGE15: kết quả kiểm ngắn Android–SITL

**Kết quả: đạt phạm vi sửa product writer và kiểm navigation/preflight chỉ đọc. Chưa nghiệm thu bay hoặc beta stable.**

Anh đã cho phép tăng riêng trần artifact của campaign này từ 9 lên **10 MiB**. Bản cô lập đã được đóng gói bằng cơ chế candidate nội bộ, dùng lại APK development và ArduPilot ARM đã kiểm; không build/ký APK mới, không ký production và không thay lựa chọn phát hành.

Nguồn đang tiếp tục phát triển nằm ở `planning/writerstage15`. Toàn bộ raw, lượt lỗi, kiểm độc lập và báo cáo nằm ở `evidence/writerstage15`. Báo cáo này cập nhật trạng thái hiện tại; báo cáo PRELAUNCH trước đó vẫn được giữ nguyên như một mốc lịch sử.

## 1. Thay đổi thực chất

Đường ghi cũ fsync lại mọi thư mục tổ tiên sau mỗi append, dù các namespace phía trên không thay đổi. Bản sửa giới hạn tối ưu vào các đường product đã khai báo: vẫn ghi ledger/quota bền vững trước ghi, fsync dữ liệu và thư mục cha trực tiếp; vẫn fsync mọi namespace thực sự vừa tạo, theo thứ tự từ dưới lên. Chỉ bỏ việc fsync lặp lại các tổ tiên không thay đổi. Các writer ngoài phạm vi này giữ cách đồng bộ cũ.

Trace chẩn đoán mới có trần **4 KiB**, ràng buộc candidate/context/PID, CRC và SHA, tách 21 nhóm đo trong từng thao tác. Nó giữ lỗi đầu tiên cùng thao tác trước đó, hoặc hai thao tác cuối khi chưa có lỗi. Trace không ghi toàn bộ lịch sử độ trễ. Các stage lồng nhau có thời gian giao nhau, không được cộng như các đoạn độc lập.

Trần artifact đã được thống nhất qua một hằng/predicate và contract kiểm tra tại candidate, preview, HostHealth, monitor và guardian. Bản sửa cũng tách entry mới có phiên bản để không làm candidate S01 phụ thuộc vào entry đã bị thay đổi.

## 2. Guard và giới hạn giữ nguyên

| Điều kiện | Kết quả |
|---|---|
| Artifact | 10.203.136 / 10.485.760 byte trước S02; tính đủ cả chín pool |
| HostHealth RPC | 100 ms, không nới |
| Product writer commit | 200 ms, không nới; commit trễ vẫn là đã commit và cấm retry |
| Input freshness | 250 ms, không nới |
| Trace writer | 4 KiB |
| Metadata | 64 MiB, không nới |
| Dung lượng | Sàn 10 GiB, reserve 256 MiB và ngân sách peak thực, không nới |
| Nguồn, deadline, process, physics, clock, frame và fsync trước sensor | Giữ nguyên; không đổi speedup hoặc bỏ frame |

Preview từng từ chối đúng khi ngân sách metadata thiếu 77.824 byte. Không sửa con số inventory, không loại bằng chứng khỏi quota và không tăng cap. Chỉ 13 file QA tĩnh của chính task này được nén filesystem APFS bằng công cụ hệ thống, giảm 245.760 byte phân bổ thực. SHA, byte đọc thông thường, kích thước logic, mode và mtime được giữ nguyên; inode/flags/allocation có thể thay đổi và đã ghi hồ sơ. Không áp dụng thao tác này vào source, candidate, raw S01/S02 hoặc ENDURE.

## 3. Mock và đối chứng filesystem

Root đã chạy độc lập **46 phương thức kiểm**: 22 writer/trace, 7 guard, 11 policy artifact, 2 entry có phiên bản và 4 namespace/fault injection. Các lượt chạy lại không được cộng thành số kiểm mới. Kiểm cú pháp 9 module JavaScript và AST Python đạt.

Ba phép đối chứng dùng filesystem thật, admission mock và độ trễ fsync được tiêm có kiểm soát:

| Phép kiểm | Fsync | Thời gian | Ý nghĩa |
|---|---:|---:|---|
| Writer cũ, thêm 30 ms mỗi fsync | 8 | 276,98 ms | Commit xong nhưng quá 200 ms, từ chối phát lại |
| Writer mới, cùng cách tiêm | 4 | 144,66 ms | Commit đạt; byte dữ liệu và ledger đúng |
| Writer mới, riêng payload fsync thêm 230 ms | 4 | 232,39 ms | Vẫn bắt quá hạn, committed=true và cấm retry |

Đây là bằng chứng giảm IO thừa dưới điều kiện kiểm soát. Nó chưa xác định được nguyên nhân chính xác của lỗi HOSTISOLATE14 trước đây là filesystem, lock hay lập lịch host.

## 4. Hai lượt thực đã dùng

### S01: lỗi trước endpoint, đã giữ bằng chứng

S01 dừng sau 8,41 giây, trước Android/AP/product writer. Guardian còn một cap 9 MiB bị bỏ sót, dẫn đến `SHARED_ORIGINAL_CAP` và `PRODUCT_RUNTIME_GUARDIAN_DIED_BEFORE_ENDPOINT`. Đây là lỗi tích hợp thực của bản sửa cap ban đầu. Không dùng lượt này làm bằng chứng writer đã chạy.

Đã sửa tận điểm bất nhất bằng contract cap thống nhất, kiểm cả các predicate và policy trước actor. Giữ nguyên 22 file S01 cùng candidate lỗi. Có một thay đổi tạm thời vào entry ngoài candidate của chính task; đã phục hồi đúng byte HOLD02 và dùng entry `-r03` mới cho S02. Không tuyên bố các đường entry cũ hiện diện liên tục. Candidate S01 đã được full-load lại thành công sau phục hồi.

### S02: kiểm ngắn đạt mục tiêu chỉ đọc

Candidate: `da4b32e4a7703c7a99079cddc7982f04f600c68a5d392b5802474cf45fb1bf39`.

Run: `writerstage15-disarmed02`. Owner PID 31511. Thời gian host **167,2049 giây**, bao gồm khởi động, quan sát và đóng; không phải thời lượng bay. Exit 0, stderr rỗng, stdout được thu đủ và có SHA. Không retry campaign tự động.

| Quan sát/đối chiếu độc lập | Kết quả |
|---|---|
| Discovery và cohort tham số | 39/39 tham số đúng kiểu, cohort COMPLETE, không pending |
| Navigation | `DISARMED_READ_ONLY_NAVIGATION_READINESS`, ready=true |
| Preflight gốc | `READY_SCOPED_READONLY`, scope `OWNED_ROOT_SITL_ONLY_NOT_PHYSICAL_HERA` |
| Model khảo sát | SHA của saved plan nối đúng original Android state |
| Product writer | Tổng 236 thao tác, trace không chốt lỗi; hai thao tác cuối 3,171375 / 4,857959 ms |
| Writer byte/protocol | Hai payload range, digest request/response, context/PID/candidate và commit ref khớp độc lập |
| HostHealth | Counter 1.837; tám cặp cuối join đúng nonce và nguyên byte request/response; tail max 2,098542 ms |
| Frame raw | 53.957 RX = INTENT = local SENT = stage rows; unknown-send = 0 |
| AP stage | 431.656 event được kiểm; byte trạng thái `COMPLETE_BYTES_UNATTESTED` |
| Clock | Tuổi atomic permit lớn nhất 151,738958 ms < 250 ms |
| Power helper | 302 guardian + 211 monitor query, digest toàn wire và last request khớp; raw power row đều AC |
| Đóng monitor | Drain bền vững, không lỗi phụ; guardian RPC trong failed-drain = 0 |
| Đóng actor | Emulator exit 0, helper exit 0 và group gone; không còn PID, cổng hoặc container của lượt kiểm |

Hai latency writer và tám latency HostHealth là các mẫu cuối còn được giữ, **không phải maximum/p99 toàn lượt**. `sendall` trả về không tự chứng minh bên nhận đã xử lý. Kiểm Root đối chiếu payload và protocol trong phạm vi byte đã lưu, không suy ra quyền bay.

Android state poll gốc mới 5,878958 ms khi chủ động kết thúc; DOM observation cũ hơn, khoảng 391,59 ms. Không dùng tuổi state poll để tuyên bố DOM cũng đạt freshness.

Lượt này chủ động dừng bằng sentinel `READ_ONLY_DIAGNOSTIC_COMPLETE_REQUESTED_PHYSICAL_DISPOSAL_NOT_FLIGHT_ACCEPTANCE`. Terminal và journal vẫn giữ đúng trạng thái đóng chẩn đoán: main journal `INCOMPLETE_RECORDING`, recordingAccepted=false, flightAcceptance=false. Guardian dùng exceptional physical disposal; không nhận thành normal completed flight. Không ARM, upload, manual, AUTO hoặc video; quyền=null, không tự phục hồi quyền, ảnh thực=0.

## 5. Toàn vẹn và vệ sinh

Kiểm cuối đã đối chiếu SHA/kích thước/mode qua 7.446 đường dẫn duy nhất thuộc các scope có giao nhau: nguồn/ENDURE/receiver gốc, pool artifact cũ, NAVFIX13, HOSTISOLATE14, 141 file HOLD04, S01 và hai gói bàn giao private. Không cộng các scope chồng nhau thành số file duy nhất.

Hai candidate S01 và S02 đều full-load đạt với 119 file bundled và 154 external pins mỗi bản. S02 đã đóng baseline 210 file. Git HEAD AERIS và hai checkout public/intake giữ nguyên; 98 đường tracked đã thiếu từ trước không thay đổi và không được stage. Không sửa bản bàn giao hoặc lịch sử ENDURE. Không commit/push trong task này.

Các fixture mock/fsync/namespace/compression do task tạo đã được dọn, không còn bytecode cache mới dưới nguồn cô lập. Đã chạy `docker image prune -f`, thu hồi 0B; không prune container hoặc volume. Không tạo bản sao toàn dự án vào thư mục tạm, không cài dependency hay tải image mới.

## 6. Mức sẵn sàng và bước tiếp

**Đã gỡ chặn lượt kiểm ngắn chỉ đọc của writer/navigation/preflight. Chưa đạt beta stable.** Chưa có bằng chứng từ task này cho điều khiển manual/AUTO liên tục 10 phút, video/payload đồng thời, mất link/reboot trong bay, chất lượng UI trực quan đầy đủ, HeraHub hoặc drone thật.

Bước tiếp hợp lý là đưa đúng candidate này qua lượt nhiệm vụ ngắn có điều khiển, kiểm đóng review và thu hồi quyền; chỉ mở lượt tích hợp 10 phút khi các điều kiện trước đó đạt. Giữ nguyên ngưỡng 100/200/250 ms, không quay lại sửa riêng lẻ hoặc mở campaign lặp vô hạn. Hai slot thực của task WRITERSTAGE15 đã dùng hết; không tự mở lượt thứ ba.

## Hồ sơ đối chiếu

- `ROOT-QA-GATE04.json`: source/mock và policy trước runtime.
- `ROOT-FINAL-BASELINE02.json`, `ROOT-FINAL-NEW02.json`, `ROOT-FINAL-SLOWPAYLOAD02.json`: đối chứng fsync.
- `ROOT-LAUNCH01.json`, `diagnostic-S01-bootstrap01.json`, `S01-CLOSED-BASELINE01.json`: lỗi S01 được bảo toàn.
- `ROOT-ADMISSION04.json`, `FROZEN-CANDIDATE02.json`, `ROOT-LAUNCH02.json`: admission, candidate và lượt S02.
- `ROOT-S02-WRITER-PREFLIGHT01.json`, `ROOT-S02-POWER-IPC01.json`: Root kiểm độc lập payload, preflight, power wire và IPC.
- `ROOT-COLD-S02-FRAMES01.json`: raw frame/AP stage, closure và actor.
- `diagnostic-S02-writer01.json`, `diagnostic-S02-disposition02.json`: kiểm cold độc lập của reviewer.
- `PRESERVATION-FINAL01.json`, `S02-CLOSED-BASELINE01.json`, `CLEANUP01.json`: toàn vẹn và đóng task.
- `COMPLETION-WRITERSTAGE15.json`: kết luận máy đọc được và fingerprint các receipt.
