# BETA-CAMPAIGN01 · M1-CONTROL01

27/10/2026 · **PARTIAL / NOT READY** · native diagnostic controller + owned Android emulator + external ArduCopter 4.7.1-dev ARM SITL.

Đã triển khai native sticks bốn trục, consent/lease 200 ms, assisted GUIDED/ARM/Home/takeoff/LOITER, release hữu hạn và đóng phiên khi lỗi. Trong kiểm thực, cần tiến đã làm drone di chuyển; mất đường MAVLink khi vẫn giữ cần dẫn tới GCS failsafe LAND và ground/disarm. AP khởi động lại trên mặt đất bằng EEPROM lưu lại, native discovery chỉ đọc và không tự khôi phục quyền. Đây là app chẩn đoán native cô lập, chưa phải bản cockpit sản phẩm đã tích hợp đủ manual/video/payload.

## Kết quả đã đo

| Phép kiểm | Kết quả và phạm vi |
|---|---|
| Điều khiển cần tiến trong LOITER | 1.968 m theo hướng đầu drone, input liên tục 1.914 s trước cắt link. Touch được inject bằng ADB vào Android thật của emulator, không phải HID/tay cầm vật lý. |
| Assisted | Non-forced ARM, xác nhận đúng Home mới sau ARM, cất cánh 3 m; hover quan sát 2.293 s trước manual. Cao nhất 3.073 m; xa Home đã xác nhận tối đa 6.227 m. |
| Mất link khi giữ cần tiến | Chỉ cắt native MAVLink; FDM/clock/passive vẫn chạy. Tại deadline GCS 5 s còn armed/LOITER, cao 2,979 m. LAND sau 5.281 s từ heartbeat forwarded cuối; raw có GCS Failsafe, không có lệnh LAND native gây nhiễu. |
| Ground/disarm sau failsafe | Hai nhóm heartbeat + landed + position mới và riêng biệt sau LAND, thỏa độ cao tuyệt đối ≤0,4 m. Không dùng AP forced-stop hay ACK làm bằng chứng hạ cánh. |
| Reboot AP trên mặt đất | Container/boot/epoch mới, cùng byte AP, no-wipe và EEPROM 16.384 B khớp SHA snapshot; 39 tham số đúng kiểu, không ARM/RC/consent. PID số 8 được tái dùng trong namespace mới, không gọi đó là PID số thay đổi. |
| Native input/authority | 247 input, 1 consent, 246 lease renewals, 55 input-wire bindings. Producer → local write tối đa 59.739 ms. Đây chưa phải độ trễ từ tay người tới phản ứng drone; tuổi dữ liệu ở kernel/network chưa đo. |
| Toàn vẹn frame | **115.208 FRAME/STAGE/AP-covered** của hai lượt khép kín, replay đúng byte bằng model Python gốc. Không mất frame, fsync trước gửi sensor; speedup 1, cap 500 ms. |
| Persistence hẹp | 28 file journal trong bốn run khớp đúng byte với tar đã xuất trước khi Activity restart. Mở lại không CONNECT, màn hình NO_SESSION. Chưa chứng minh full workspace/cockpit persistence ở lát cắt mới này. |

| Lượt khép kín | Frame | AP event | RTF đo được |
|---|---:|---:|---:|
| actual-loss05 | 89,997 | 727,631 | 1.000155× |
| actual-ground206 | 25,211 | 203,853 | 1.000242× |

## Những bản sửa đã kiểm

- Native APK02 chặn GPS sentinel/STATIC/undefined và EKF không đủ điều kiện. Giữ nguyên arming checks; trạng thái EKF 0xa7 đã từ chối cấp quyền, chỉ khi quan sát 0x33f mới tiếp tục. Nguyên nhân nội bộ khiến EKF cần thời gian hội tụ chưa được chứng minh từ covariance nội bộ.
- Host control02 cho chờ TCP khởi tạo tối đa 20 s/200 attempts trước byte AP đầu tiên. Sau bất kỳ byte AP nào, EOF vẫn đóng epoch, không reconnect tự động.
- Host control03 dùng journal transport hữu hạn 32 MiB/40 segment, dự toán thêm original/copy/export 96 MiB. Mock với guard/fsync thật chứng minh vượt ngưỡng 8 MiB cũ vẫn đóng và kiểm anchor được; chạm quota mới vẫn dừng và giữ prefix.
- Bộ kiểm Android13 đọc focus từ dumpsys window đầy đủ. Action dựa geometry XML ban đầu đã xem ảnh, kiểm focus/state/screenshot mới trước từng tap; không nói mọi screenshot từng tap đều đã được xem trực quan.

## Vì sao chưa nghiệm thu toàn mốc

**Giữ nguyên kết quả gốc của oracles03: CONTROL_NOT_READY.** Oracle lấy vị trí khởi tạo 0,0 chưa hợp lệ làm gốc kiểm bán kính, nên cờ horizontal-envelope vẫn FAIL. Đối chiếu độc lập theo cửa sổ Home sau ARM đã công bố trước kiểm cho kết quả 6,227 m trong giới hạn 10 m; đây là bằng chứng bổ sung, không viết lại kết quả oracle gốc hay quảng cáo toàn bộ mốc PASS.

Luồng nominal thả cần → observed BRAKE → neutral/relinquish → consent mới → người dùng ra LAND hiện có code và mock, **chưa hoàn tất kiểm thực**. Roll/yaw/throttle mới kiểm mapping bằng mock, kiểm bay thực mới dùng cần tiến. AP reboot thực chỉ trên mặt đất, dùng bản sao EEPROM chính xác trong thư mục state mới; không có chứng cứ reboot khi đang bay hoặc đường dẫn gốc hiện diện liên tục. Chưa có HeraHub/Xiaomi/HID, calibration Hera, full cockpit/media hay lượt 30 phút.

Hai P2 native còn để riêng: lỗi callback cuối có thể cản release singleton, và lỗi tạo Thread trước khối start có thể giữ reservation. Đường callback đang dùng bắt lỗi ghi checkpoint; chưa coi các kiểm hiện tại là chứng nhận production.

Đã dùng hết ngân sách 5 host starts + 1 emulator start. Không mở vòng thử mới, không hạ gate hay đổi tiêu chí sau khi thấy dữ liệu. Bước tiếp theo: qualification oracle địa lý bằng corpus có startup 0,0/invalid và Home mới, sau đó kiểm nominal ngắn với thả cần/BRAKE/LAND và mở rộng trục điều khiển trong milestone kế tiếp.

## Bằng chứng lỗi giữ nguyên

| Lượt | Phân loại |
|---|---|
| nominal01 | Docker nhận TCP trước AP, EOF trước byte đầu; 0 frame, chưa CONNECT native/chưa lệnh bay. Giữ failed prefix. |
| nominal02 | 30 s chưa đủ điều kiện EKF, không consent/ARM. 36.848 frame/model/AP kiểm được; native bị force-stop nên journal chỉ là prefix, không có terminal commit. |
| loss03 | Đã bay và thấy GCS LAND nhưng transport chạm quota 8 MiB. 87.948 nhóm frame hoàn chỉnh chỉ là retained prefix; thiếu hồ sơ hoàn chỉnh và ground qualified, không PASS. |
| loss05 | Khép kín đủ frame, native commit, failsafe và ground/disarm. Giữ cờ FAIL bảo thủ của oracle gốc như trên. |
| ground206 | Khép kín, no-wipe retained EEPROM, discovery chỉ đọc và không khôi phục quyền. |

Không cộng interval hay frame của lần lỗi để thay bằng chứng hoàn chỉnh. Giữ cả lỗi fixture QA/root (sai offset/nhãn operator và lệnh shell chỉ liệt kê thay vì hash), dùng receipt hiệu chỉnh riêng, không sửa lịch sử.

## Bảo toàn và vận hành

Áp dụng Vibecode Kit 6.3: Builder native/host, QA độc lập và Contractor thực hiện các launch. Kỷ luật provenance: mock, app Android thực trên emulator, AP SITL thật, raw replay và kiểm trực quan giới hạn được tách rõ; không suy thành thiết bị hay drone thật.

Boundary check: 17.117 mục legacy và bốn seal cũ (1.620 / 48 / 830 / 1.651 mục) không drift so với baseline. 165 mục thiếu từ trước và 97 tracked deletion có sẵn giữ nguyên, không tự khôi phục. Source/candidate/ENDURE/canonical SOT không sửa. Không tuyên bố ENDURE đạt 24 giờ.

Gate entry 20 GiB / live floor 10 GiB + reserve giữ nguyên, hai journal guard có prime 15 s thật. Free thấp nhất quan sát 21.19 GiB. Emulator và toàn bộ host/AP của tác vụ đã đóng; native force-stop. Dọn đúng 5 file truyền/XML của tác vụ trên Android, không xóa journal/AVD/bằng chứng. Docker image prune thu hồi 0 B. Không tạo bản sao dự án trong tmp; thư mục build riêng hiện trống.

APK development cô lập: `native/betaintegrated01/control02/dist/aeris-control01-development-02.apk`, SHA256 `b0e99a320938970190912cb64d0843d10bc50e4475e8b3ce6d21936438779212`. Không ký production, không công bố, không commit/push trong tác vụ này.

## Hồ sơ tham chiếu

- TIP: `planning/betaintegrated01/TIP-M1-CONTROL01.md`
- QA đóng kín: `evidence/betaintegrated01-m1control01/qa/actual-loss05/closed-cold01.json` và `qa/actual-ground206/closed-cold01.json`
- Native authority: `evidence/betaintegrated01-m1control01/qa/actual-loss05/native-authority01.json`
- Source manifest hiện hành: `evidence/betaintegrated01-m1control01/host/runtime-manifest05.json`
- Native build: `evidence/betaintegrated01-m1control01/native/build-02.json`
- Preservation: `evidence/betaintegrated01-m1control01/preservation-after01.json`
- Progress: `evidence/betaintegrated01-m1control01/PROGRESS.json`

**Disposition: giữ các kết quả đạt trong phạm vi hẹp; M1-CONTROL01 còn PARTIAL / NOT READY, toàn M1/Beta chưa được nghiệm thu.**
