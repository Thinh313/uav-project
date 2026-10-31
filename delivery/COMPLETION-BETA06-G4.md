# BETA06 G4: tích hợp launcher

**NOT READY: bị chặn trước AP bởi Local browser use.**

## Kết quả

Đã ghép bản sửa launcher vào ứng dụng G4 cô lập, đóng băng source/helper và vượt gate QA độc lập. Đã mở companion cùng emulator, kiểm APK và khôi phục dữ liệu Android. Phần bay tích hợp chưa chạy vì công cụ báo Local browser use đang bị tắt trong Work settings. Người dùng cho biết sẽ bật; các lần kiểm trong phiên vẫn trả trạng thái disabled. Đây là blocker công cụ trước AP, không phải kết quả fail của nhiệm vụ bay hay launcher G4.

## Bản sửa và kiểm chứng

Runtime/readiness đã sửa từ trước được giữ đúng SHA, ghép vào đường gọi thực G4 app/adapter/profile. Parser nhận marker từ stdout và stderr cùng attempt, đối chiếu prefix SHA/offset/count, giữ liveness/exactCID/descriptor/resources và log có fsync. Phần source/mock giữ riêng với bằng chứng Android thực. UI quan sát chỉ thay cadence chẩn đoán500/400ms, không thay heartbeat750ms, TTL3000ms hay freshness1200ms; bootstrap và giao thức observer tái dùng nguyên byte.

## Diễn biến có giới hạn

Host PID36163, controller35855, emulator36415 được mở theo cửa sổ45phút/2700s đã khai báo trước. Một precheck getprop chỉ đọc chạy khi emulator còn offline đã bị từ chối trước setupintent. Sau khi ADB đã online, Root ghi quyết định riêng và thực hiện setup bằng commandId mới; không lặp thao tác UI hoặc bay. Android cold-start609ms là thời gian am báo cho app, không phải cold-start video. Root đóng modal nhiệm vụ, mở bảng trước bay và chọn ArduPilot SITL thật; Connect chưa bấm.

## Vì sao không chạy phần bay

Nguồn video là một điều kiện nghiệm thu của yêu cầu này. Gate bắt buộc publisher/viewer cùng config, clock hiệu lực và interval75s trước mỗi Connect. Chưa có quyền browser nên không thể tạo nguồn đúng cohort IAB/VP8/RGB. Không dùng trình duyệt/công nghệ khác để vượt cài đặt bị tắt, không bỏ gate video hay chạy bay riêng rồi gắn nhãn tích hợp. Chưa có request AP, container mới, telemetry, authority hay payload lease.

## Bảo toàn và tài nguyên

Snapshot sau chuẩn bị vẫn đủ19file/34record, journal không append, không thêm SAF/PENDING. Kiểm sau đóng xác nhận5.063đường dẫn baseline và653pins không drift, bao gồm source/candidate/ENDURE và bằng chứng lỗi G3. Không build/ký/cài APK mới, không sửa lịch sử hay xoá container/evidence. Dung lượng nhỏ nhất trong guard emulator khoảng39.34GiB, cao hơn sàn20GiB; cuối phiên khoảng39.31GiB. Tất cả4PID riêng đã vắng và5cổng riêng đóng. Không có copy dự án, dependency install hay scratch của Root; fixture nhỏ Builder/QA được tự dọn theo receipt.

## Phần còn lại

Sau khi Local browser use thực sự bật, cần mở một phiên kiểm mới có định danh/deadline/gate riêng, bảo toàn phiên đã đóng. Tiếp tục N1 AUTO/video/payload → F1 mất link → restart có chứng cứ → N2 đối chứng → F2 reboot, giữ ngưỡng/media/disk/quyền hiện tại. Bản ghép đã đạt gate source/mock; toàn bộ yêu cầu tích hợp vẫn NOT READY cho đến khi có raw execution, media/overlap, invalidation và reboot thực. Chưa có SDK/HeraHub hay bằng chứng bay thiết bị thật.

## Phương pháp

Áp dụng Vibecode Kit6.3 với Builder và QA độc lập. Không có LLM trong runtime, nên baseline LLM trực tiếp không áp dụng. Giá trị đạt được trong phiên là bản ghép đã kiểm và dữ liệu Android được bảo toàn; chưa có số đo hiệu suất video khi bay hoặc độ tin cậy nhiệm vụ mới.

## Ma trận nghiệm thu

| Hạng mục | Trạng thái | Bằng chứng / giới hạn |
|---|---|---|
| Ghép launcher readiness hai luồng vào app cô lập | PASS SOURCE/MOCK | G4 app → adapter → runtime → SHA marker/proof; firmware/profile/exactCID guard vẫn bắt buộc. |
| Gate độc lập trước runtime | PASS SOURCE/MOCK | 100 nhóm kiểm chọn lọc; 653 pins, 29 helper, 27 source, 132 stage. Không phải 100 chuyến bay. |
| APK và khởi động Android 13 | PASS ANDROID PREPARATION | APK SHA df49885…753d không đổi; boot06/API33/4CPU/WebView101, mở app một lần. |
| Dữ liệu Android qua cold boot và chuẩn bị UI | PASS HASH PRESERVATION | 19 file/34 bản ghi; journal SHA và prefix nguyên trạng so với G3, 13 PENDING/3 quota còn lại, không clear/cài lại. |
| Nguồn video host → viewer Android | BLOCKED | Local browser use bị tắt trong Work settings; chưa mở publisher/viewer, chưa có interval75s. |
| AUTO + video/payload đồng thời | NOT CHECKED | Chưa Connect/ARM/AUTO, 0 AP request mới. Không dùng kết quả thế hệ trước để lấp gate. |
| Mất link, reboot và restart sau nhiệm vụ | NOT CHECKED | Chưa đủ điều kiện đi tiếp từ N1. Không gửi lệnh lỗi hoặc tự phục hồi quyền. |
| Bảo toàn và đóng phiên | PASS ACTUAL/READONLY | 5.063 đường dẫn bảo vệ và 653 pins không đổi; host/emulator/controller đã dừng, cổng riêng đóng. |

## Bằng chứng

- [qa-integration-pre-runtime-gate04.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/qa-integration-pre-runtime-gate04.json>)
- [qa-native-before-n1-preservation04.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/qa-native-before-n1-preservation04.json>)
- [android-device06.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/android-device06.json>)
- [android-activity-start-initial-06.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/android-activity-start-initial-06.json>)
- [android-store-before-n1-06.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/android-store-before-n1-06.json>)
- [android-store-after-browser-pending-06.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/android-store-after-browser-pending-06.json>)
- [root-browser-blocker-observation01.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/root-browser-blocker-observation01.json>)
- [root-setup-offline-decision01.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/root-setup-offline-decision01.json>)
- [app-launch.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/host-app04/app-launch.json>)
- [app-closure.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/host-app04/app-closure.json>)
- [android-closure06.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/android-closure06.json>)
- [root-preservation-after-browser-block04.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/root-preservation-after-browser-block04.json>)
- [root-runtime-closure04.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/root-runtime-closure04.json>)
