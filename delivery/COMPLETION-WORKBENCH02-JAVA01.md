# Workbench02 Java01

Ngày 24/10/2026. **READY trong phạm vi ghép hai bản vá Java, kiểm store trên host và typecheck; native/Android–SITL vẫn NOT READY.** Một assistant chuyển pha Contractor, Builder và Verify theo Vibecode 6.3, không phải review độc lập.

## Đã ghép

Theo `planning/workbench02/JAVA01-TIP.md` và TIP gốc, chỉ sửa hai source Java Workbench02 đang được cho phép, cùng hai file kiểm:

- `WorkspaceStore.java`: constructor ba đối số vẫn dùng quota sản phẩm 8 MiB; overload bốn đối số chỉ nhận quota từ 1 KiB đến 8 MiB, không cho nới giới hạn. Load/save áp dụng cùng quota. Từ chối symlink ở tên root trước khi tạo/đọc store. Giữ 16 thế hệ, reserve Android 128 MiB, CAS, fsync, giới hạn body và không tự xóa thế hệ.
- `ShellActivity.java`: version của request phải là JSON Number có giá trị bằng 1, không dùng getInt để ép chuỗi hoặc số phân số thành phiên bản hợp lệ.
- Runner lưu đầy đủ command/stdout/stderr, chặn ghi receipt dưới sàn, giám sát dung lượng giữa lúc chạy lệnh, timeout hữu hạn và dọn compiler scratch do nó tạo. Không cài thêm toolchain.

SHA sau ghép trùng candidate đã kiểm trong RAM từ lượt trước:

| Source | SHA-256 |
|---|---|
| WorkspaceStore.java | `ab0b64dcaac5e0cd101ce099489d0e9e462cac57fea0a803076df4418aed021b` |
| ShellActivity.java | `4b42f3a135e5970c276d62dde3de1e31e3ffd34c5f72ec7023080950320a19c3` |

## Nghiệm thu

| Phép kiểm | Kết quả và giới hạn |
|---|---|
| Store host | 19/19 PASS: save/load, instance restart, SHA/CAS, dedup, quota/generation/body bounds, corruption, pending, pointer rollback, foreign entry, body/root symlink và fault ở publish/fsync/rename/head sync. |
| Restart tiến trình | Hai JVM riêng ghi rồi đọc đúng head/body SHA, PASS. Không phải restart Android hoặc mất điện. |
| Version predicate | 11/11 PASS trên đúng biểu thức trích từ source, với q.opt giả lập: chấp nhận số 1, từ chối chuỗi, phân số, boolean, null, số sai và giá trị không hữu hạn. Không phải chạy JSONObject/Broker Android thật. |
| Typecheck | Hai Java source compile PASS với source/target 8 và Android 37 stubs đã cài. Có ba warning tùy chọn Java 8 cũ và ghi chú API deprecated; không có compile error. Không chứng minh tương thích ART/minSdk 26 hay SAF. |
| Bridge regression | 25/25 nhóm Node mock/projection PASS ở `bridge-mock04.json`. Nhãn ANDROID trong ca mock vẫn là giả lập Node. Không cộng các lượt trước thành số ca mới. |
| Bảo toàn | Trước/sau 14.025 identity bảo vệ, 65 file Workbench01 và native reuse pins đều khớp. 22 file có sẵn khác trong snapshot Workbench02 không đổi; bridge giữ SHA `cb5c9511970cf388f09a888e2c25b73162983aea9a920237d4fcc2b2706572f7`. |

Bằng chứng: `evidence/workbench02/java-check01.json`, `java-command-log01.json`, `java-verification01.json`, `bridge-mock04.json`, `preservation-java-before01.json`, `preservation-java-after01.json`. JDK 26.0.2.1 được ghi trong stderr của log java -version; trường javaVersion stdout rỗng vì công cụ in phiên bản ra stderr, không phải thiếu log phiên bản.

Callback directory sync trong ca host thường là no-op; file descriptor sync vẫn chạy trên host, và có fault injection callback. Những phép kiểm này không chứng nhận directory fsync Android, atomicity/power-loss của thiết bị hay phục hồi khi khôi phục toàn bộ một store cũ. Pointer rollback được phát hiện khi các body mới còn hiện diện. Store chỉ chứa dữ liệu; không có bước cấp lại quyền điều khiển.

## Admission và phần còn thiếu

Nguồn dung lượng lúc đầu khoảng 30,02 GiB. 31 mẫu thật trong 30.002,31 ms đạt ngưỡng ít nhất 29 GiB, không có decline quan sát được; minimum 32.194.560.000 byte, khoảng 29,98 GiB. Hàm admission thuần của G17 được tái dùng chỉ đọc và kiểm SHA, không chạy campaign G17. Đây là **PASS_RESOURCE_SAMPLES_ONLY**, không phải admission đầy đủ.

Workbench02 chưa có APK hiện tại, ART/SAF/UI chưa nghiệm thu và chưa có controller SITL được qualification cho shell này. Host preparatory chỉ chuẩn bị model, không mở flight dispatch. Vì vậy **NOT_ADMITTED_SOURCE_RUNTIME_GATES_UNMET**, không mở emulator/AP/SITL, không ARM hoặc gửi lệnh bay. Không hạ guard, không dùng ứng dụng/campaign G17 cũ thay cho Workbench02 mới.

Qua rà soát source còn thấy nhánh catch lỗi I/O trong `onActivityResult` gọi `deliver(q,null,e,false)`, trong khi deliver chỉ giải phóng busy khi release=true. Sau khi request SAF đã sở hữu busy, nhánh lỗi này có thể giữ busy và chặn thao tác sau. Đây là phát hiện tĩnh trên source hiện tại, chưa tái hiện Android; không được che bằng kết quả store hoặc typecheck. Chưa sửa ngoài hai candidate đã giao. Cần sửa và kiểm lỗi SAF/phiên trước khi build/qualification native tiếp theo.

Yêu cầu ghép hai bản vá: 2/2 đạt trong phạm vi host/typecheck. Native integration, actual persistence/restart Android, SAF thật và AUTO/video/payload vẫn NOT_CHECKED. Không có APK mới, ký development/production, SDK hay HeraHub. Chưa đo lợi ích thời gian/công người so với CLI; không có cơ sở tuyên bố parity DJI hoặc sẵn sàng bay thật.

## Dung lượng và bàn giao

Đã xóa duy nhất compiler scratch `native/workbench02/.check`. Giữ `store-fixtures01` và `store-process01` gồm dữ liệu test/fault và symlink test làm bằng chứng; không xóa dữ liệu/bằng chứng cũ. Không tạo scratch ngoài repo, cài dependency hoặc chạy Docker. Báo cáo và manifest mới bổ sung lịch sử, không viết lại receipt hoặc báo cáo cũ.
