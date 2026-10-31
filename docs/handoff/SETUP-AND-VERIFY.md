# Tiếp nhận, chạy và kiểm lại

## 1. Source/mock không cần hardware

Dùng Node.js 22+ và Python 3.12+ trên PATH. Các lệnh ở README không cài package,
không mở Android, không kết nối autopilot và không cấp quyền operator.

`tools/handoff/verify.mjs` đối chiếu SHA256 của cây bàn giao, bao gồm symlink tương đối.
Sau khi chủ động sửa source, manifest phải thay theo review; mismatch không được bỏ qua.

Bốn suite mock tách biệt được chạy trên bản source public: base 36 checks,
lifecycle 18 checks, health 4 checks và portable wait 3 cases. Không cộng các suite
thành tỷ lệ trưởng thành; một số yêu cầu được kiểm lại ở nhiều lớp.

`npm run check` kiểm cú pháp workbench gốc. `npm test` là bộ lịch sử rộng hơn,
có ca tạo fixture/localhost server, có điều kiện dung lượng và timing. Lượt đầu
trên host bàn giao ghi 331/387 pass, 56 fail: thiếu fixture synthetic ở 15 ca,
40 ca bị guard free-space cũ chặn và 1 ca timing chưa ổn định. Fixture đã được bổ sung
đúng byte và có lệnh `node tools/handoff/prepare_legacy_fixture.mjs` để tái dựng
record synthetic trong runtime bị ignore; các ca bị ảnh hưởng được kiểm riêng lại. Lượt kiểm riêng acceptance/geo14 sau bổ sung đạt 27/27; không công bố toàn suite xanh.
Log đầy đủ được chuyển trong gói private, kết quả cuối nằm tại `handoff/VALIDATION.json`.

## 2. Workbench lịch sử

`npm start` dùng loopback 8788, `AERIS_ENABLE_SITL` không bật mặc định.
Đây là đường cũ để đọc UI/workflow. Không lấy hình ảnh workbench này thay cho
cockpit Android mới nhất hoặc một lần kiểm simulator thành công.

## 3. Bộ engineering private

Các em nhận riêng ba phần, kèm manifest và checksum:

- `PRIVATE-CONTEXT.zip`: BOM/context nội bộ, tài liệu khách hàng, raw web inputs,
  các bản gốc trước ẩn danh và một số artifact host-specific. Không đưa lên Git public.
- `ENGINEERING-REPLAY-KIT.tar.gz`: evidence các lượt chẩn đoán gần nhất,
  candidate pools, APK development/input archive và AP executables được giữ lại.
- `SITL-LINUX-ARM64-IMAGE.tar.gz`: Docker image Linux ARM64 đã dùng,
  image ID `sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84`.

Không có Android SDK/AVD, toàn bộ runtime cache hoặc mọi raw log lịch sử.
Các công cụ và receipt phụ thuộc riêng host cũ không tự trở thành hợp lệ trên máy mới.

## 4. Workspace riêng cho dữ liệu private

Giữ clone public ở tag intake r1. Dùng công cụ từ clone này để kiểm gói gốc
rồi dựng một thư mục mới **ngoài mọi Git checkout**. Công cụ không cần package cài
thêm, không load Docker image, không mở SDK/emulator hoặc cấp quyền operator.

Nhận `UAV-PROJECT-PRIVATE-HANDOFF.tar` và SHA256 từ người giao qua kênh tin cậy.
Một checksum ở ngay trong archive chỉ phát hiện hỏng, không xác thực người gửi.
SHA gói gốc đã bàn giao:
`52fd3330c64c327cc5827be61ff4f9cda20dd1a5bede1d20c08ee4dd0a92fd28`.
Các tên/path bên dưới là ví dụ; thay `/path` và `/work` bằng nơi nhận thực tế:

```sh
python3 tools/handoff/private_bundle.py verify \
  /path/UAV-PROJECT-PRIVATE-HANDOFF.tar \
  --sha-file /path/UAV-PROJECT-PRIVATE-HANDOFF.tar.sha256 \
  --report /work/private-verify.json
python3 tools/handoff/private_bundle.py prepare \
  /path/UAV-PROJECT-PRIVATE-HANDOFF.tar \
  --sha-file /path/UAV-PROJECT-PRIVATE-HANDOFF.tar.sha256 \
  --destination /work/uav-project-private \
  --report /work/private-prepare.json
```

Report và destination phải chưa tồn tại, ngoài Git. `verify` kiểm toàn gói,
manifest source, context, hardlink/mode engineering và chuỗi định danh image.
`prepare` kiểm lại rồi mới admission theo allocation dương cộng floor 10 GiB và
reserve 256 MiB. Khi bị từ chối, không bỏ guard hoặc tái dùng thư mục dở dang.
Công cụ không ghi đè, tự xóa hay tiếp tục một preparation cũ.

Gói gốc giữ source public ở commit `94c3ef8...`, không tự chứa công cụ intake r1.
Hai README/Git-guide trước biên tập được chứng minh bằng file HISTORY tương ứng;
`.gitignore` giữ đúng prefix gốc và phần append đã biết. Các khác biệt biên tập
này được ghi riêng, không bỏ kiểm byte của source sản phẩm. Chín file public ẩn
nhãn khách hàng được overlay về bản gốc; workspace kết quả là
`PRIVATE_DERIVED_NOT_PUBLIC_SNAPSHOT`, không phải public tree nguyên byte.
Manifest public nằm trong cây đó sẽ khác đúng các overlay đã khai báo. Các em
chạy bốn mock core dưới đây từ workspace private, không dùng manifest public
để chứng nhận cây đã overlay:

```sh
cd /work/uav-project-private
node planning/vidlife12/runtime/tests/mock.mjs
node planning/vidlife12/runtime/tests/lifecycle-trace.mjs
node planning/vidlife12/runtime/tests/cold-navigation-r02.mjs
python3 tools/handoff/mock_wait.py
```

Giữ `private-handoff-artifacts/PREPARATION-RECEIPT.json` cùng report bên ngoài.
Kiểm hash, mode và hardlink đã được hoàn tất trước receipt. Không thêm remote public
hoặc đẩy workspace này lên mạng. Kit chứa file readonly có chủ đích; tạo phiên R&D
mới theo contract, không sửa raw/candidate cũ. SDK/AVD và launch profile trên máy
nhận vẫn cần intake riêng trước chạy thật.

Chỉ import image sau khi có đủ dung lượng và chấp thuận môi trường:

```sh
gzip -dc /path/SITL-LINUX-ARM64-IMAGE.tar.gz | docker load
docker image inspect sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84
```

Kiểm image ID, OS/architecture và executable SHA, không chỉ tag.
Image này là Linux ARM64. Windows/Linux x86_64 hoặc Mac khác cấu hình cần một
baseline build/SDK phù hợp, không thay binary âm thầm rồi giữ nhãn nghiệm thu cũ.

## Baseline Android đã ghi nhận trên host gốc

Spec cũ dùng API 33, system image `default/arm64-v8a` revision 2,
Android Emulator 37.2.12 và platform-tools 37.0.1. AVD cấp 2 GiB RAM, 4 cores,
không snapshot, tắt camera giả lập. Đây là cấu hình đã quan sát, không phải
khuyến nghị cấu hình tối thiểu hoặc cam kết SDK manager còn cấp đúng revision.

Spec trong kit giữ nguyên các đường dẫn tuyệt đối của máy tác giả. Nhóm cần lập
spec/intake mới cho máy nhận và kiểm executable/image/config SHA; không sửa tay
spec cũ hoặc đổi binary rồi coi lại là cùng evidence. Bản kiểm tiếp nhận này không
cài SDK, không mở emulator và không kiểm controller thực.

## 5. Android và APK

Package retained là `vn.rtr.aeris.betasim09`, activity
`vn.rtr.aeris.mission.ProductActivity`. APK SHA256:
`8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1`.
Đây là APK development, không phải production signature.

Đầu tiên kiểm Android version, WebView, codec, màn hình/input và ADB serial.
Chỉ định serial rõ khi install hoặc reverse cổng. Khi companion đã được khởi tạo
đúng profile, Android cần đường loopback 8896 và media 8895 qua adapter đã kiểm.
Một thao tác `adb install` thành công chỉ chứng minh cài được, không chứng minh
navigation, video, persistence hay tương thích HeraHub.

Đối với điện thoại thật, chưa có kết quả nghiệm thu Xiaomi trong snapshot này.
Không dùng quyền `adb root` đã cấp riêng emulator cũ làm quyền áp lên thiết bị thật.
SDK/MCU/radio, payload/gimbal và thermal còn gate bench riêng.

## 6. Admission và lượt thực

Dùng descriptor/spec/candidate cùng revision và chạy kiểm chỉ đọc trước.
Quy trình hiện tại: mock -> pure allocation/admission -> lượt Android-SITL ngắn
-> review raw -> mới xét lượt 10 phút. R02 chưa qua bước allocation vì vượt 76 KiB.

Giữ floor 10 GiB cộng reserve/forecast và ngân sách case thực. Một số service
lịch sử có floor 20 GiB riêng; không diễn giải policy mới là quyền sửa hằng số
cũ. Cần AC/battery/lid, cổng rảnh, native lifetime counters, writer/owner,
source/SDK/image pins và shutdown reserve đúng profile. Không tự clear app,
xóa lock, reset quota hoặc retry POST để vượt admission.

## 7. Kiểm sau mỗi lượt

Lưu argv, stdout/stderr, boot/session/frame, request/ACK, timing domains và SHA
artifact. Đối chiếu raw TX/RX, accepted frame groups, mission readback/mode,
video source/receiver/warm proof và closure. Đọc lại SAF ở receiver độc lập.

Khi lỗi, giữ primary cause trước cleanup và ghi secondary errors riêng.
Kiểm PID/port/container sở hữu đã dừng, ghi nguồn có được đóng đủ hay incomplete.
Không báo PASS chỉ vì hết thời gian, có ACK, screenshot hoặc tên file acceptance.

## 8. Khi thiếu prerequisite

Ghi `NOT_CHECKED` hoặc `NOT_READY`, giữ kết quả đã có và nêu đúng phần chặn.
Không suy ra máy mới có lỗi giống máy cũ chỉ từ một timeout. Baseline raw và
thiết bị/SDK khác nhau phải được ghi vào báo cáo; ưu tiên ca nhỏ phân biệt nguyên nhân.
