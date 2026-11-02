# Cài đặt và kiểm lại bản bàn giao H10

## 1. Chốt đúng snapshot

Clone tag `research-handoff-2026-11-02-h10` theo README. Ghi commit thực nhận bằng `git rev-parse HEAD`, tạo branch nghiên cứu riêng và giữ source manifest. Không lấy source mới nhất của nhiều revision ghép thành một candidate.

Cấu hình tác giả đã kiểm là macOS ARM64, Node 24.14.1, CPython 3.14.6. Đường public H10 dùng Node 24 và Python hiện có, không cần package install, Android hay drone. Chỉ ghi kết quả của phiên bản thực sự chạy trên máy nhận; không suy ra mọi Node/Python/OS đều được hỗ trợ.

Windows nên dùng WSL/Git có symlink thật. Một clone chuyển symlink thành file văn bản không được coi là cùng cây source. Không dùng runtime APK/image ARM64 trên nền khác rồi giữ nguyên nhãn nghiệm thu.

## 2. Verify và mock public

Chạy `node tools/handoff/verify.mjs` từ root để kiểm danh sách SHA/kind. Manifest chỉ chứng minh các entry được liệt kê, không kiểm mọi file lạ. `npm run check` kiểm cú pháp workbench lịch sử, không chạy toàn bộ sản phẩm.

Chạy `python3 -B tools/handoff/h10_intake.py` để kiểm H10 portable. Wrapper chọn 13 phương thức kiểm từ source hiện tại; dùng Node 24+ và Python 3.12+, đã kiểm với Node24.14.1/Python3.14.6. Path adaptation chỉ cho test và fixture media synthetic/derived thay input private g105 được khai báo rõ. Nó kiểm codec, Root reconstruction, Node-Python writer IPC/fsync, managed close và biên cap20/100MiB; không mở Android/SITL, không cấp quyền hoặc tạo flight acceptance. Các kiểm gốc trong `planning/betarc01/runtime-h10/test-*.py` vẫn giữ source đã HOLD nhưng có dependency private và đường dẫn tác giả; không chạy mù toàn bộ rồi tạo file giả cho đủ pin.

`node tools/handoff/intake.mjs` và bộ receiver-runtime03 là lối tiếp nhận lịch sử của VIDLIFE12/R2. Chúng vẫn dùng để xem lại phạm vi cũ, không tự chọn H10, không áp trần H10 cho một candidate cũ và không là một lệnh chạy Android-SITL mới nhất.

## 3. Nhận bộ riêng

Nhận gói và checksum qua kênh tin cậy, giữ ngoài mọi clone dùng để push public:

- Gói gốc `UAV-PROJECT-PRIVATE-HANDOFF.tar`, SHA bắt đầu `52fd3330`, giữ nguyên byte ở mốc ban đầu.
- Supplement MILESTONE05 đã kê khai, dùng khi nghiên cứu đường runtime máy nhận R2.
- `UAV-PROJECT-H10-SUPPLEMENT-2026-11-02.tar.gz` cùng `.manifest.json` và `.sha256`, bổ sung source/raw/artifact đã kê khai của H10.

Checksum nằm trong archive không tự xác thực người gửi. Kiểm toàn gói và manifest trước giải nén, dùng đích mới ngoài Git, không ghi đè hoặc tự tiếp tục một preparation dở dang. Công cụ `python3 tools/handoff/verify_h10_supplement.py --help` mô tả cách nhận các tham số `--archive`, `--sha256` và `--manifest`. Đây là kiểm stream chỉ đọc, không giải nén. SHA kỳ vọng phải nhận từ kênh tin cậy, không lấy digest trong chính archive làm thẩm quyền. Công cụ của supplement phải đọc manifest của đúng mốc; helper gói gốc không chứng nhận supplement mới.

Gói gốc có context/BOM/overlay private, engineering replay kit và image đã kê khai. Supplement mới không nhân bản SDK/AVD/cache hoặc Docker image. Đối chiếu đầy đủ danh mục phần đã có và phần thiếu; “toàn vẹn” là các byte/phạm vi được kê khai, không phải bản sao toàn ổ đĩa.

## 4. Replay và provenance

Giữ raw và candidate nguyên byte. Đường dẫn tuyệt đối trong log/spec là dữ liệu máy tác giả; không thực thi argv hay sửa trực tiếp các file đó để vừa máy mới. Nếu tạo view/path map phục vụ replay, công bố nó là bản suy ra chỉ đọc và giữ SHA nguồn.

m801 forensic-only không cấp quyền resume/archive hoặc qualification. Root/QA đã đối chiếu current data, nhưng một người nhận mới cần tái lập phạm vi byte/replay bằng công cụ và nguyên bản được giao. Không dùng decoder 75 file cho trạng thái 83 file và không gửi lại g103 APPLY.

## 5. Môi trường Android-SITL

Baseline đã ghi nhận gồm Android API 33/default/arm64-v8a rev2, emulator 37.2.12, platform-tools 37.0.1, AVD 2 GiB RAM/4 cores, không snapshot. Android SDK/system image/AVD userdata không được cung cấp trong Git hoặc supplement H10. Đó là cấu hình quan sát, chưa là cấu hình tối thiểu hay cam kết vendor còn phân phối đúng revision.

APK development được giữ có SHA đầy đủ trong MILESTONE06-H10. Nó không phải signature production. Kiểm package, activity, certificate, Android/WebView/codec/input và serial thực. Quyền `adb root` của emulator cũ không là quyền áp lên điện thoại hoặc HeraHub thật.

Image Linux ARM64, AP executable, source/candidate, profile và descriptor phải đúng các hash đã kê khai. Không tự cài phần thiếu hoặc thay binary trong pin. Các port 8895/8896 là loopback media/companion của profile, không phải một cấu hình mạng phổ quát cho mọi thiết bị.

## 6. Admission mới trước lượt thực

Mock -> source/fixture closure -> pure resource preview -> current native-state contract -> live admission -> lượt ngắn -> review raw -> mới xét 600 giây. Trước launch kiểm nguồn pin/AC, sàn 10 GiB cộng reserve/forecast, cap artifact20/metadata100 MiB, quota native/export, source/image/SDK/pin, cổng/PID và shutdown reserve.

Trên host cũ, entry pin 30% và dừng 20% là guard đang giữ; máy nhận phải dùng policy đã được review và quan sát nguồn thật. Trần MiB không phải ngưỡng free-space GiB. Một số service lịch sử có cap/floor khác và vẫn giữ policy riêng.

Không tự clear/wipe app, reset counter/quota, xóa lock, retry POST hoặc khôi phục authority. Nếu thiếu prerequisite hoặc admission từ chối, ghi NOT CHECKED/NOT READY và lý do, giữ các kết quả đã có.

## 7. Hồ sơ sau mỗi lượt

Lưu argv, stdout/stderr, host/AP elapsed và clock domain, boot/session/frame, input/quyền, raw TX/RX, readback/mode, media proof, closure và SAF receiver. Tách primary cause với cleanup secondary. Xác nhận actor thuộc lượt đã dừng; không dọn phiên của người khác.

Không báo PASS chỉ từ elapsed time, một ACK, ảnh chụp giao diện hay tên file acceptance. Các em nhận source để bắt đầu R&D ngay; phần Android-SITL, hardware bench/HIL và bay thật vẫn có gate riêng.
