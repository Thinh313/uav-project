# AERIS · M1-COCKPIT03

27/10/2026 · **Đạt luồng native manual/assisted trong phạm vi Android–SITL, có phần hoãn rõ ràng. Toàn M1/Beta vẫn NOT READY.**

Đã ghép cockpit cô lập: **khảo sát → preflight thực → Fly manual/có trợ giúp → review → restart**. Người vận hành sửa và lưu vùng đa giác trong Android; cockpit dùng cùng lõi điều khiển đã nghiệm thu, dữ liệu AP thật trong SITL và hồ sơ bền vững. Không dùng telemetry dựng sẵn để thay cho kết quả bay.

## Kết quả nghiệm thu

| Phần | Chứng cứ thực |
|---|---|
| Khảo sát | Biên tập tên, tạo/sửa vùng tham chiếu 4 điểm, lưu 4 revision. Lượt bay gắn revision4, SHA `b1b8552b91ba7301423eaa77f3924e452cdbe5cd218f7714bf9a81c43db09ab4`. WGS84, mét, độ cao so với Home; đây là mặt phẳng tham chiếu tổng hợp. Corridor đã kiểm bằng mock; chưa bay corridor trong lát cắt này. |
| Preflight | Native quan sát firmware **4.7.1-dev / dbe79216**, đối chiếu 39/39 tham số đúng kiểu, GPS/EKF/Home và freshness. Hash khảo sát, run/epoch/boot/profile/AP/model/config/source được liên kết; WebView không tự cấp quyền. |
| Bay có trợ giúp | Consent rõ ràng → GUIDED/ARM không force → hiển thị/xác nhận Home sau ARM → cất cánh 3 m → hover → LOITER → giữ/thả cần → BRAKE → consent mới/lease mới → LAND chủ động → ground/disarm → đóng sạch. LOITER có AP giữ vị trí/thái độ, không phải ACRO. |
| Thao tác cần | Input touch thực được inject vào Android emulator. Giữ tiến 1.745 s, dịch chuyển theo hướng đầu drone 1.051 m; hover trước manual 2.995 s. Chưa chứng minh cần vật lý/HID. |
| Thu hồi quyền | UP thu hồi lease trước BRAKE17; CRC heartbeat native xác nhận BRAKE trước neutral/relinquish. Lease thứ hai khác lease cũ và gắn với LAND từ thao tác native. Không suy thực thi từ ACK; không có unknown send hoặc lỗi native ở lượt đạt. |
| Vật lý và clock | **87.735 frame** khớp FRAME/STAGE/AP và replay bằng model Python gốc; **708.529 AP event**, **7.825 native record**. Không bỏ frame, fsync trước sensor, speedup1/cap500 ms giữ nguyên. RTF **1.000201×**, 73.112 s model / 73.097 s receive wall. |
| Địa lý | Kiểm toàn cửa sổ armed: 92 vị trí, không loại outlier; giữ 177 mẫu trước quyền trong raw. Xa Home tối đa 1.140 m / giới hạn10 m; cao tối đa 3.071 m / giới hạn5 m. |
| Review | 1 hồ sơ khớp khảo sát revision4, preflight/source, AP/model/config và terminal native anchor. Receiver độc lập xác nhận **8 nhóm ground/disarm mới**, riêng biệt sau LAND. Mở thẻ hồ sơ nạp **116 điểm trình bày**; mọi raw vẫn giữ. Trạng thái trong app vẫn chờ đối chiếu ngoài, không tự tuyên bố hoàn thành độ phủ/ảnh. |
| Restart | Mở lại Activity nạp đúng khảo sát và lịch sử; **16 file bất biến khớp SHA** trước/sau. NO_SESSION, owner=false, binding chưa stage, epoch mới; không tự nối lại, cấp quyền hoặc tiếp tục bay. Chi tiết 116 điểm mở lại được sau restart. |
| Giao diện | Kiểm actual Android các pane, theme sáng/tối, vị trí nút và vùng Home. Header/telemetry cùng lề RtR, hai đảo tách rời, Barlow Việt, nút native56 px, vị trí HOLD/LAND/CLOSE cố định. Sửa lệch pha WebView/native qua xác nhận trình bày sau hai RAF. Chưa đo UI FPS hoặc chứng nhận mọi thiết bị/font scale. |

Các điểm quỹ đạo là dữ liệu trình bày theo pha bay, không đồng nhất với tần số physics. Toàn bộ frame và native raw vẫn được giữ, đối chiếu riêng. Review đã kiểm metadata/chi tiết sau khi bấm thẻ; **chưa chứng minh bản đồ quỹ đạo review hiển thị rõ**, vì pane review che nền bản đồ. Không quảng cáo tự động mở đầy đủ chi tiết từ overview.

## Kiến trúc và lỗi đã xử lý

WebView chỉ biên tập/hiển thị qua bridge hẹp. Nút bay và cần điều khiển là Android native, dùng đúng **Owner03/Flight02**, nguồn clock, lease, journal và một socket/writer đã pin. Không boot legacy writer hoặc vòng bay mock Native98. Các phần mới nằm trong `native/betaintegrated01/cockpit03/`; host/AP/physics/oracle cũ giữ nguyên.

Mock và QA độc lập đã kiểm quota/pending, fsync sau rename, trùng ID/revision, record/seal hỏng, liên kết sai boot/config, dữ liệu ground cũ hoặc bị mâu thuẫn, clock tương lai, callback cũ và bridge không có API bay. JVM có adapter JSON kiểm thuật toán; DOM doubles kiểm logic, không được coi là Android/compositor. Sau đó mới kiểm parser và hành trình trên Android thật trong emulator.

**Lượt nominal01 thất bại trước CONNECT:** bộ lọc `PendingExplicitAction` cũ không nhận STAGE_BINDING, làm nút kết nối không được mở. Lượt này giữ đủ 4.405 frame prefix, native flight bytes=0, không ARM/lệnh bay; không được cộng vào lượt đạt. Adapter nonflight mới bọc bộ lọc cũ với envelope có kiểu, giữ TTL/replay/clock, chỉ cho STAGE/CLOSE/STATUS và xử lý đúng warm foreground. Không sửa bộ lọc cũ hoặc cho phép intent gửi lệnh bay. Lượt nominal02 chỉ mở AP sau khi staging đã xác nhận đúng SHA, không owner và chưa nối socket.

Các APK01/02, ảnh chuyển màn hình lỗi, receipt và input archive đều giữ. Một giả thuyết tương thích ERROR đã được hủy khi đối chiếu nguồn hiện hành cho thấy PUSH/STATEfalse đã hiển thị đúng; đề xuất và bằng chứng hủy được giữ, không gọi đó là lỗi sản phẩm. Một assertion tên khảo sát của test cũng được sửa vì Root đã đặt con trỏ giữa chuỗi; Android lưu đúng thao tác nhập, không phải lỗi persistence.

## Bảo toàn và tài nguyên

Boundary trước/sau khớp **17.117 mục legacy**, các seal cũ **1.620 / 48 / 830 / 1.651 / 4.251 / 2.977** mục, không có drift mới. 165 đường dẫn thiếu và 97 tracked deletion có sẵn giữ nguyên; không tự phục hồi hoặc sửa lịch sử. Source/candidate đóng băng, ENDURE và canonical SOT không đổi; không suy ra ENDURE đã đạt24 giờ.

Gate entry20/livefloor10 GiB + reserve256 MiB và prime15 s thật giữ nguyên. Dung lượng thấp nhất quan sát **21.53 GiB**, pin thấp nhất **41%**. Dùng quyền chạy pin người dùng đã cấp cho lượt kiểm ngắn này, ghi nguồn thực; không sửa chính sách ENDURE. Đã đóng cả **2 host/AP starts và 1 emulator**, không chạy lại. Forced AP stop không được dùng làm bằng chứng hạ cánh.

Đã dọn scratch build riêng và 3 bản sao tạm trên Android:

- `/data/local/tmp/aeris-control01-m1cockpit03-nominal01.json`
- `/data/local/tmp/aeris-control01-m1cockpit03-nominal02.json`
- `/sdcard/aeris-control01-ui-7614a4b423994288b77f4e55526f0187.xml`

Giữ raw, workspace, journal, AVD và các bản sao bằng chứng trên host. Không copy toàn dự án vào tmp, không cài dependency. Docker image prune thu hồi0 B; image AP pin vẫn có.

## Bản bàn giao và phần chưa đạt

APK development được chọn: **`native/betaintegrated01/cockpit03/dist/aeris-cockpit03-development-03.apk`**, 443,680 byte. SHA256 **`3086cc4c4f503c34f5fd336e2b7450df135781a512858faa6a91af9e15860114`**. Dùng lại chứng thư development, v2/v3 đã kiểm độc lập; **không ký production**. 37 input pin hiện hành và 44 pin oracle khớp; snapshot input từng APK giữ riêng để tái lập.

Môi trường đã kiểm: API33 ARM64/ranchu, 1280×800/160 dpi, GPU/WebView quan sát trên owned emulator. Kết nối của bản engineering này giới hạn profile emulator; **chưa nghiệm thu Xiaomi/HeraHub/HID, Hera thật hoặc payload thật**. AP là ArduCopter4.7.1-dev đã pin và quad-X tham chiếu, không phải mô hình Hera đã hiệu chuẩn. Không có camera/video/ảnh thật.

Còn gate riêng cho lượt30 phút, Beta tích hợp video/payload, AUTO upload/readback/khảo sát hoàn chỉnh, media/độ phủ, bản đồ review, thiết bị thật và production. Chưa chứng minh mọi tỷ lệ màn hình, FPS/độ trễ UI, khí tượng/tải Hera hay ưu thế DJI. Lát cắt này chứng minh giá trị cụ thể so với màn diagnostic trước: cùng lõi bay được đưa vào hành trình nhiệm vụ có lưu/review/restart. Không có thay đổi thuật toán AI hoặc phép so sánh LLM trong task.

**Disposition: READY_NOMINAL_NATIVE_COCKPIT_WITH_DEFERRED. Toàn M1/Beta NOT READY; tiếp tục các gate còn lại theo roadmap, không mở rộng tuyên bố từ một lượt nominal.**

## Hồ sơ đối chiếu

- `evidence/betaintegrated01-m1cockpit03/qa/FINAL-QA.json`
- `evidence/betaintegrated01-m1cockpit03/verification01.json`
- `evidence/betaintegrated01-m1cockpit03/qa/full-actual-nominal02/results.json`
- `evidence/betaintegrated01-m1cockpit03/qa/workspace-actual-nominal02/results.json`
- `evidence/betaintegrated01-m1cockpit03/android-exit01/restart-result01.json`
- `evidence/betaintegrated01-m1cockpit03/native/build-03.json`
- `evidence/betaintegrated01-m1cockpit03/preservation-after01.json`
- `evidence/betaintegrated01-m1cockpit03/cleanup01/closure.json`

Áp dụng Vibecode6.3: Builder native/UI triển khai, QA độc lập kiểm, Contractor sở hữu admission/actual orchestration/đối chiếu và báo cáo. Không cộng các nhóm test chồng lấp thành chứng nhận chất lượng thị trường.
