# Ghi nhận họp21/10/2026: video, ảnh định vị, RGB/thermal và vận hành đêm/tầm xa

Loại hồ sơ: USER_REPORTED_FEEDBACK + CONTRACTOR_ASSESSMENT/PROPOSED_PRIORITY. Không phải lỗi đã tái hiện trên AERIS hoặc chứng cứ bay/camera Hera thật. Không sửa canonicalSOT, feature-matrix cũ, candidate, source đóng băng hoặc ENDURE. Không launch/build/test phần mềm trong lượt tổng hợp này.

## Nội dung và xác nhận của người dùng

- F-MEDIA01: streaming xuống điện thoại, máy tính, tablet không mượt. Người dùng xác nhận CHƯA RÕ đoạn gây giật; model camera, codec/profile, giao thức, topology, sốviewer và môi trường mạng chưa biết. Không tự kết luận lỗi decoder/Android/radio hay camera.
- F-MEDIA02: chụp hình cần gắn định vị. Người dùng xác nhận tọa độ CAMERA/DRONE LÚC CHỤP. Tọa độ vật thể trong ảnh ngoài scope hiện tại, không tự thêm LRF/terrain intersection/targetgeolocation vào gate cơ bản.
- F-MEDIA03: camera có thermal/RGB và các loại khác. Đây là bối cảnh/yêu cầu payload; chưa có model/firmware/API/stream/radiometric capability được xác nhận. Không kết luận Hera đang thiếu sensor.
- F-OPS04: bay ban đêm và bay tầm xa. Bối cảnh/yêu cầu khai thác; chưa có độ rọi, cự ly, payload/khối lượng, gió, battery reserve, RF/linkrole và điều kiện nhiệm vụ. Không suy diễn sốkm hay khả năng nightautonomy đã đạt.

## Đối chiếu AERIS từ báo cáo giữ lại, chưa chạy lại

F19 EO/IRlive đang P0: có contract/video local tổng hợp, thiếu stream camera thực và đo end-to-end/loss/reconnect/đa thiết bị. Cliplocal/3D/RAF không thay video trên đường truyền thật. F21 ảnh/video có GNSS đang P0: có trigger/giao thức tổng hợp nhưng không có nghiệm thu exposure/file thật/timeGNSScorrelation; P1 actualFiles=0. F20/F22 có nền routing nhưng chưa live RGB/IR switching/sync trên target. F23 radiometry còn chưa qualified. F29 nightautonomy/VIO chưa đạt và khác vận hành đêm có người lái. PHONE06 chưa SOURCE_READY, chưa APK/kiểm Xiaomi. Các kết quả P1 Android–SITL trong scope cũ vẫn giữ, không áp sang source/cấu hình mới.

## Ưu tiên đề xuất trong milestone tích hợp kế tiếp

P0-A LiveVideo: nối đầu-cuối có đo, không tiếp tục chỉ trình diễn3D. Phân tách camera→encode→airlink→receiver→decode→display và receiver→fanout→thiết bị xem. Mỗi feed bind camera/stream/session, codec/resolution/FPS/bitrate và timestamps. Đo capture-to-display khi có clockmapping/uncertainty, p50/p95/p99, jitter/loss/freeze/recovery/CPU/RAM/heat và sốviewer. Nếu thiếu captureclock ghi UNKNOWN, không lấy callbackage/RAF thànhglass-to-glass. Có nguồn test encode timestamp/frameID để cô lập decode/network trước camera thật. Boundedbuffers/controlpriority; video nghẽn không được chặn lệnh điều khiển/WAL. Chính sách bỏ frame video trễ nếu chọn phải riêng, có counter và không áp sang mất frame vật lý/raw bằng chứng.

P0-B CaptureGeotag: captureID/imageIndex + camera/vehicle/run + exposure/capturetime + đúng tọa độ khi chụp + altitude datum/GNSSquality/timeuncertainty + originalfilehash. Kiểm ảnh gốc/EXIF và sidecar có nguồn; giữ nguyên original, dẫn xuất geotag nếu sửa metadata có hash/lineage riêng. MissingGNSS/clock/captureevent hoặc timestampreboot phải UNKNOWN/quarantine, không điền0 hay dùng vị trí laptop/điện thoại hoặc vị trí lúc tải file. ACK/khai báoCAMERA_IMAGE_CAPTURED không tự chứng minh file ảnh/EXIF đã tồn tại. Đối chiếu độc lập fixturemovingtrajectory và ảnh/timegốc, chốt errorbudget theo nhiệm vụ. Không hứa survey-grade accuracy chỉ vì cóGPS.

P0-C RGB/ThermalViewing: chọn đúng payload/feed, RGB/IR/PiP khi có capability, label/cameraID/frameage riêng, snapshot đi đúng nguồn. Đổi nguồn xem không tự đổi quyền điều khiển. Thermal palette/range hiển thị theo dữ liệu hỗ trợ; không tạo sốđộC từ màu. Radiometricmeasurement/EOIRregistration/sync có gate riêng theo sensor/calibration, chưa bắt buộc nếu chỉ cần xem thermal. MAVLink CameraProtocol không tự đồng bộ chính xác thermalmetadata với từng frame.

P0-D Night/RangeReadiness: giao diện đêm hạn chếchói, nhận biết nguồnRGB/IR và ảnhcũ, C2/video linkhealth riêng, GNSS/EKF, Home/độ cao/địa hình, pin dự phòng/khả năng về ngượcgió và mấtlink/failsafe có log. Đây là yêu cầu kết hợp phần mềm+sensor/radio/airframe+thửthực tế. Chưa xác nhận range/nightflight từ UIdarkmode, thermal hoặc mô phỏng. Nightautonomy/VIO vẫn gate nâng cao riêng.

Trình tự: hoàn thiện PHONE06 cài/transport/workflow tối thiểu làm thiết bị thử; ghép ngay test stream thật qua mạng ở scope được kiểm và capturegeotag vào cùngcockpit/review; nối RGB/IR target khi có cấu hình; kiểm loss/degradedlinks/bandwidthsharing; sau bench mới nghiệm thu điều kiện đêm/cựly thực. Không dựng thêm demo rời hoặc thay các gate cũ bằng checklist mới.

## UI và điều kiện nghiệm thu đề xuất

Cockpit ưu tiên video/bản đồ; selectorRGB/IR rõ, PiP chỉ khi hỗ trợ; luôn thấy tuổi feed/trạngtháimấtvideo độc lập trạngtháikếtnốiđiềukhiển. Review hiển thị ảnh trên bản đồ tại vị trí chụp, thời gian/GNSSquality/datum/nguồn/sai số khi biết; thiếu dữ liệu thể hiện rõ. Các chỉ tiêuFPS/resolution/latency/cựly/sốviewer/saigeotag phải được chốt theo cấu hình, không tự đặt thành chuẩn khách hàng. PASS phải có raw/ảnh/media/measurement và đúnghardware/softwareprofile; synthetic/host/physicalAndroid/bench/field phân biệt.

## Nguồn kỹ thuật đã đối chiếu21/10/2026

- https://mavlink.io/en/services/camera.html : discovery/capabilities/streaminfo, imagecapture và giới hạn metadata thermal đồng bộframe. Tiêu chuẩn giao thức, không chứng nhận implementation AERIS.
- https://mavlink.io/en/messages/common.html#CAMERA_IMAGE_CAPTURED : có UTC/boot timestamp, lat/lon, altMSL, cameraorientation, imageindex/result/fileURL. Tên trường relative_alt không được tự coi là AGL đo thực nếu firmware/source chưa chứng minh.
- https://gstreamer.freedesktop.org/documentation/rtpmanager/rtpjitterbuffer.html : buffer/reorder/lostpacket/latency có cấu hình. Là ví dụ cơ chế kỹ thuật, chưa quyết định chọn GStreamer hoặc chứng minh chữa giật.

Các yêu cầu ở trên là đề xuất thiết kế/nghiệm thu từ feedback, không phải kết quả test mới. Source-reference pins đọc lại trong lượt tổng hợp:

{
  "planning/product-standard01/feature-matrix.json": "5490f3c4a8073e22a6f882689fa9f74c2f3b38b2791b407d07ef49c68eff6859",
  "delivery/COMPLETION-NATIVE89.md": "8bc24450ea1c4375e2fd5686c068f0736ea7863cdf266e4ae19616da5ad56e57",
  "delivery/COMPLETION-NATIVE90.md": "f07700e6e58e0c5b04738273d4182ad01dea3857fdeaff478de804260abec1f8",
  "delivery/COMPLETION-INTEGRATION03-03.md": "a67b69e356464b172fc137e20881b62d3461368267f1aed82b6cf56d1ccef5af",
  "planning/phone06/TIP.md": "90feb086be102139688965c768f1070fa233442cfda94b093f7149ec92044f29"
}
