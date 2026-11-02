# Kiến trúc và ranh giới H10

## Đường vận hành

Android cockpit/Java-WebView bridge nối Node companion trên loopback 8896. Companion phối hợp mission, payload/operator và hồ sơ; Root quản lý runtime, transport và writer. ArduPilot SITL cùng physics/sensor backend là đường mô phỏng bay. Host publisher trên 8895 tạo media tổng hợp để Android giải mã/hiển thị và lưu bằng chứng.

Workbench web `npm start` trên 8788 là đường lịch sử. Nó không tự chọn cockpit Android/candidate H10, không là bằng chứng một lần bay thành công. ACK, mission readback, mode transition, camera command và ảnh gốc là các loại bằng chứng riêng.

## Source được chọn

`planning/betarc01/runtime-h10/source/aeris_runtime/` có 140 file source được chọn. Product graph có 198 pin; writer contract có 257 sites, 14 owner và dự phòng 60.686.336 B. Candidate H10 và APK giữ trong gói private; file tên mới nhất không tự là release được chọn.

Loader H9 giải logical import theo alias đã khai báo, rồi kiểm target path/SHA/symlink và graph. H10 dùng đường chọn này trước spawn và giữ argv thực. Không đưa module cũ không được chọn vào graph để lách lỗi compatibility.

## Control và kết quả đầy đủ

Progress/ACK vẫn tối đa 4 KiB và 16 management command. Kết quả đầy đủ được lưu dưới một JSON envelope có run, runtimeContext, candidate, PID, sequence và action. Mỗi payload ghi tối đa 64 KiB, tối đa 16 đoạn; file và tổng owner vẫn chịu quota cũ. Root kiểm đúng byte, SHA, path/context và commit cuối trước khi đọc kết quả.

Một action có thể đã có tác động trước khi ACK lỗi. Thiếu ACK không đồng nghĩa chưa thực thi. Không tự gửi lại lệnh không biết kết quả; giữ prefix và raw để kiểm. H10 không cắt dữ liệu hay tăng progress cap.

## Đóng và khôi phục

Hai luồng đóng bình thường dùng chung boundary: kiểm writer/observer, ngừng admission ghi mới, chờ RPC đã nhận hoàn tất reply và trace theo deadline first-byte + 200 ms gốc, sau đó dừng companion. Kiểm lại lỗi và thread drain sau đóng. Không gia hạn deadline bằng một mốc 200 ms mới, không đợi client idle như RPC và không dùng trạng thái đang đóng để che lỗi cũ. Emergency disposal giữ riêng.

Khôi phục workspace/hồ sơ không khôi phục flight hoặc payload authority. Mất link, background, reboot hay input stale phải thu hồi quyền. Một raw prefix có CRC/SHA đúng vẫn có thể incomplete; không chèn footer để biến nó thành hồ sơ hoàn tất.

## Clock và môi trường

Freshness 250 ms, HostHealth 100 ms, writer/RPC 200 ms, input lease 200 ms; speedup 1, cap bù nhịp 500 ms. Không bỏ frame, đổi clock hoặc đổi speedup để đạt pacing. Node hrtime, Python monotonic, Android elapsed và browser performance cần mapping đã kiểm; không so trực tiếp các số từ hai domain.

Artifact tổng 20 MiB và metadata tổng 100 MiB chỉ áp dụng bản cô lập H10 theo quyền đã cấp. Sàn đĩa vẫn 10 GiB cộng reserve/forecast, không phải hạ toàn bộ service lịch sử. Native/export quota và 14 owner giữ nguyên. Source/mock không thay live admission, native-state proof, SDK/image/AVD intake hay gate phần cứng.
