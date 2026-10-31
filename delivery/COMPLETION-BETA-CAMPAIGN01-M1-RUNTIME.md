# AERIS · M1 runtime cô lập và Android–SITL ngắn

27/10/2026. **Đạt phạm vi ghép adapter và lượt chỉ đọc ngắn. M1 đầy đủ và Beta vẫn NOT READY.** Lượt30phút chưa chạy vì admission dung lượng không đạt. Không dùng kết quả này làm nghiệm thu bay manual/AUTO hay drone thật.

## Kết quả thực tế

Host journal phân đoạn, clock và AP drainer đã ghép với external SITL; native Android là writer MAVLink duy nhất. APK development05 và AP03 được đối chiếu SHA với artifact đang cài/chạy trước CONNECT. Chỉ nối loopback/owned emulator, manual=false, profile NO_MEDIA_M1_RUNTIME. Đây là shell chẩn đoán, chưa phải cockpit cuối.

- **71.350 frame**: đủ RX/INTENT/SENT, **71.350 dòng timing**, **71.350 frame được trace AP bao phủ**. Đối chiếu độc lập toàn bộ byte sensor với model Python nguyên bản đạt; không lấy mẫu/bỏ frame để đạt kết quả.
- **578.561 AP events**, giữ cả đuôi chưa được backend nhận vào model và các lần AP phát lại PWM trong lúc chờ. Đuôi này không được tính thành frame đã thực thi.
- Model59,4583s trên59,4427s khoảng nhận frame; RTF **1.000249×**. Giữ speedup1/cap500ms. Đây là phép đo ngắn bên host với UI chẩn đoán, chưa phải benchmark cockpit3D/video hoặc nghiệm thu vận hành dài hạn.
- Clock590 request,585 match hợp lệ; bracket/tuổi clock được kiểm tại RX và sau INTENT fsync trước sensor send. Lịch sử được ghi theo luồng, pending/recent có giới hạn. Chưa tái chứng minh mọi chính sách clock/cross-domain từ lượt ngắn này.
- Native nhận firmware4.7.1/custom dbe79216, Home/vị trí và23 tên tham số. Decoder độc lập kiểm CRC/target; các command thực gửi chỉ có512 và511. Mọi heartbeat quan sát đều unarmed; không ARM/takeoff/AUTO.
- Native đóng và đối chiếu được985 bản ghi bằng anchor giữ ở kênh điều phối ngoài raw.26 checkpoint đóng có cùng elapsed31,86289114s. Sau force-stop/relaunch Android,4 file raw giữ nguyên SHA; UI mới NO_SESSION, không tự nối hoặc khôi phục quyền.
- Raw gốc, bản sao và gói tar128 file đã kiểm byte/hash. Archive khoảng193,6MiB; anchor tin cậy không được suy ra từ chính gói nhận.

Native monitoring chồng lấp khoảng35s của capture host có ngân sách60s; phase active khoảng31,86s. Model thực có59,4583s, không gắn nhãn đã kiểm đủ60s mô phỏng. Native raw thực chỉ có1 segment; luân chuyển native được kiểm mock/JVM, còn host/AP có luân chuyển trong capture thực.

## Những lỗi đã sửa và bằng chứng giữ lại

Lượt actual01 thất bại và được giữ nguyên. Audit tìm được34.033 nhóm RX/INTENT/SENT khớp model, nhưng chỉ34.032 STAGE; bộ đếm cũ tăng sau ghi STAGE nên báo thiếu một frame đã gửi và gọi nhầm đó là input chưa được nhận. Runtime02 tách admission, SENT và timing commit, giữ attempted-stage/phase đúng và chặn gửi lại. Fault injection sau SENT với guard prime thực15s đã kiểm độc lập.

Guard cũ giữ64 mẫu theo từng check. Dưới tải ghi cao, cửa sổ đo co xuống vài mili giây rồi chiếu rate đó ra15s. Runtime02 giữ lịch sử theo cadence có giới hạn, lấy đủ15s từ host thật trước ghi, kiểm floor/forecast ở từng write/send và giữ diagnostic khi từ chối. **Entry20GiB, floor10GiB+256MiB và forecast15s không giảm**. Không sửa/monkeypatch module M1-MOCK hay runtime01.

Emulator01 đã dừng sạch do forecast sau biến động khoảng1,9GiB/2s, trước khi mở AP. Tác nhân cấp phát chưa xác định. Exact64 mẫu gây lỗi guard actual01 không được ghi, nên không kết luận một hoạt động host cụ thể là nguyên nhân; bug cửa sổ đo được xác nhận bằng source và ca tái hiện xác định.

Intent CONNECT cũ bị từ chối tại lifecycle. Cờ controller khi đó chỉ là đã gửi intent, không phải socket kết nối; thông báo tiến độ gọi “đã kết nối” trước đó đã được đính chính. APK05 chỉ tiêu thụ explicit intent một lần sau resume/foreground, có ID/TTL/cancel/replay fence; callback log thực ghi QUEUED foreground=false rồi CONSUMED foreground=true. Resume/history thông thường không tạo phiên mới. onPause vẫn thu hồi/đóng owner.

Các artifact link dynamic đầu tiên, AP trước sửa nhánh báo lỗi cạnh tranh dữ liệu, lỗi compile Android và ca QA schema/reader đều còn receipt; không promote hoặc cộng thời gian các lần thất bại. AP03 mới giữ object thuật toán/model/pacer cũ, thêm observer được kiểm unit Linux; chưa chứng nhận tương đương toàn bộ hành vi điều khiển firmware khi bay.

## Đóng tài nguyên và phạm vi an toàn của kết luận

Hai AP kết thúc bằng **forced simulator stop, exit-9** sau grace; parent quan sát EOF và drain trace. Đây không phải kết thúc AP graceful, hạ cánh hay an toàn máy bay. Native đóng có journal/anchor; emulator02 dừng theo owner, exit0. Không còn container của task hoặc class build tạm. Không gửi lệnh bay từ host controller.

Hash/anchor chỉ chứng minh tính toàn vẹn và local sync theo wrapper được tin cậy; không chứng minh mất điện vật lý, xác thực nguồn từ xa, execution từ ACK hay cấp quyền công bố. Một số nhãn scope trong snapshot foundation vẫn là nhãn policy mock; actual transport được chứng minh riêng bằng raw/CRC/process/artifact, không dùng nhãn đó làm PASS.

## Dung lượng, bảo toàn và cleanup

Lượt short được admission với cận peak gốc+bản sao+export **2.298GiB**. Cận30phút là **55.016GiB**, chưa tính floor10GiB+256MiB. Host cuối khoảng21,4GiB nên từ chối30phút; không ký lách gate, không đổi fsync, speedup hoặc bỏ frame. Đây là cận định dạng được khai báo/kiểm, không lấy bitrate trung bình ngắn để suy ra chắc chắn cho30phút.

17.117 định danh baseline,1.620 mục bàn giao trước,48 file M0 và830 mục M1-MOCK không có sai lệch mới.165 đường dẫn thiếu từ baseline và97 tracked deletions từ trước vẫn giữ hiện trạng; không tuyên bố toàn codebase đủ file hoặc đường dẫn gốc hiện diện liên tục. Source/candidate đóng băng, canonical SOT và lịch sử ENDURE không sửa.

Đã dọn class/scratch build của task và4 file scratch Android dùng chuyển binding/XML, sau khi lưu bằng chứng. Docker image prune thu hồi0B; không prune container/volume. Giữ AVD riêng đã khởi tạo ở .local/betaintegrated01/android để tái dùng, giữ toàn bộ raw/receipt/artifact thất bại. Không tạo bản sao project trong /tmp, không cài SDK/dependency mới, không ký production hoặc push/publish.

## Còn lại để đạt M1 và Beta

Tiếp theo là manual/assisted với input thực, neutral takeover, mất link/AP reboot và30min cùng candidate đã định danh. Cần giải quyết admission bằng định dạng lossless có đối chứng hoặc lưu trữ phù hợp; giữ nguyên các gate. Rồi mới ghép cockpit cuối, workbench, video/payload và corpus nhiệm vụ toàn Beta. Lượt này không kiểm AUTO, ảnh/video,4payload/dual-operator, 3D/audio, HeraHub/Xiaomi thật, hiệu chuẩn Hera hay bay thực.

## Hồ sơ kiểm chứng

- [Nghiệm thu Contractor](../evidence/betaintegrated01-m1runtime/verification-final01.json)
- [QA độc lập actual02](../evidence/betaintegrated01-m1runtime/qa/actual02-cold-audit.json)
- [QA restart Android](../evidence/betaintegrated01-m1runtime/qa/actual02-restart-review.json)
- [Source/candidate/ENDURE bảo toàn](../evidence/betaintegrated01-m1runtime/preservation-after01.json)
- [Admission60s/5m/15m/30m](../evidence/betaintegrated01-m1runtime/actual02/control/duration-admission.json)
- [Quyết định sửa runtime02](../planning/betaintegrated01/m1runtime/ADR-RUNTIME02.md)
- [APK development05, chỉ emulator](../native/betaintegrated01/runtime02/dist/aeris-m1-runtime-development-05.apk)
- [Raw/native export tar](../evidence/betaintegrated01-m1runtime/actual02/m1short02-raw-native.tar)
- [Tiến độ kế tiếp, không ghi đè SOT cũ](../planning/betaintegrated01/PROGRESS-M1-RUNTIME.json)
- [QA tổng hợp, source hiện tại](../evidence/betaintegrated01-m1runtime/qa/FINAL-QA-M1-RUNTIME.json)
