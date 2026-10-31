# Survey01 · Hợp đồng triển khai

12/10/2026 · Phần mềm 0.3 · TIP-SURVEY01. Đây là prototype workflow khảo sát cho HeraHub; chưa là APK/native GCS hay kết quả nghiệm thu bay. Owner chọn khảo sát/lập nhiệm vụ; bổ sung BOM Hera và yêu cầu SOT. Quyết định độ sáng đủ được giữ nguyên.

## Quy trình đã triển khai

Vẽ polygon bằng chạm → kéo đỉnh hoặc sửa tọa độ → nhập thông số camera/độ cao/GSD/overlap/hướng tuyến → tính và kiểm → lưu local hoặc xuất AERIS v2 → nạp vào mô hình → ACK → readback đúng digest → chạy/tạm dừng/tiếp tục/kết thúc diễn tập. Fly giữ mission đã readback; Plan có thể chỉnh bản nháp khác. Reload chỉ khôi phục plan và tiến độ đã lưu, không khẳng định vehicle đang chạy.

UI ở 1280×800 là reference browser cho HeraHub. Giữ map chính, inspector trắng, workspace đen, vàng nhấn ít, Plex/SVG offline. Không đưa mã linh kiện/giá BOM lên màn hình tác nghiệp. Frame tọa độ có polygon WGS84 thật, chưa có nền map tiles hoặc DEM; site mặc định là khu vực mẫu không được xác nhận để bay. Camera mẫu không tự trở thành HeraSight calibration.

## Mô hình tọa độ/hình học

`core/survey.mjs` chuyển lat/lon WGS84 qua ECEF vào local ENU. Hằng ellipsoid a=6378137m, f=1/298.257223563; origin là trung bình tọa độ đỉnh, height ellipsoid=0 cho phép chiếu 2D. Đảo ENU bằng giao đường Up với ellipsoid. Phạm vi planner: 3–64 đỉnh, diện tích ≥100m², khoảng cách cặp đỉnh ≤3km, latitude ±80°, không cắt dateline. Phép chiếu không là orthometric height/geoid hoặc kết quả khảo sát trắc địa được chứng nhận.

Nguồn phương pháp: [PROJ topocentric conversion](https://proj.org/en/stable/operations/conversions/topocentric.html), [GeographicLib LocalCartesian implementation](https://raw.githubusercontent.com/geographiclib/geographiclib/main/src/LocalCartesian.cpp). Đây là căn cứ công thức và scope; không dùng PROJ/GeographicLib runtime hoặc tự nhận compatibility với chúng. Chưa có kiểm đối chiếu thư viện geodetic độc lập cho toàn phạm vi.

Polygon được kiểm duplicate, cạnh chồng, self-intersection và giới hạn extent trước khi cấp phát tuyến. Heading 0° là tuyến theo Bắc ENU, không phải compass magnetic. Xoay polygon vào cross/along-track; scan line cắt bằng quy tắc half-open, ghép cặp giao điểm; polygon lõm tạo nhiều đoạn riêng cùng strip. Đường nối thẳng được kiểm các khoảng giao boundary: nếu ra ngoài polygon thì cảnh báo và chặn readiness. Chưa có obstacle/airspace fence/route connector planner.

Camera ideal nadir: footprint ngang/dọc = AGL trên mặt phẳng tham chiếu × sensor dimension/focal length. GSD = footprint ngang/imageWidth. Khi có target GSD thì suy altitude từ camera và cập nhật altitude hiển thị; giới hạn 5–120m chỉ là miền prototype, không là giới hạn bay Hera hoặc quy định pháp lý. Cross-track spacing áp side overlap một lần; trigger spacing áp front overlap một lần.

Strip centers được phân đều giữa nửa-footprint tính từ hai biên cross-track, khoảng không lớn hơn nominal spacing; vùng hẹp dùng một strip giữa. Mỗi đoạn tuyến có ceil(length/trigger)+1 ảnh lý tưởng gồm endpoints. Distance gồm tuyến và nối; thời gian = distance/cruise speed, không gồm quay đầu/cất-hạ/gió/hover/battery reserve. Đây là thiết kế tính toán riêng, không nhận parity QGC. Không chứng minh không hở coverage ở mọi góc cạnh hoặc chất lượng ảnh thực.

`flat-reference` khai báo mặt phẳng để diễn tập camera. `relative-launch`, `terrain`, `amsl` được giữ distinct trong package; khi thiếu AGL/DEM/reference elevation thì footprint, GSD, số ảnh và distance chưa xác định, readiness false. Không dựng một DEM giả để đạt nút xanh. Có thể lưu một bản nháp thiếu dữ liệu để xử lý tiếp; không nạp nó vào mô hình.

## File, storage và phiên

AERIS `aeris-survey` v2: operational=false, model=wgs84-enu-polygon-flat-v2, coordinateSystem=WGS84; chỉ lưu settings/polygon/camera và frame, không tin số liệu dẫn xuất từ file. Import giới hạn 256KB, schema strict; toàn bộ geometry tính lại. Thư viện local tối đa 50 tên, cùng tên thay bản local, giữ file lỗi thay vì ghi đè âm thầm. Export chưa chứa geofence, vehicle/camera commands hoặc terrain package cho autopilot.

[QGC format](https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html) có schema/complex items riêng. Chưa triển khai `.plan` parity, mission compiler hoặc tự gắn tọa độ cho gói M0 v1. Engine/import v1 và các test cũ vẫn giữ để kiểm regression; UI v2 không tự chuyển legacy cục bộ thành site thật.

MissionSession dùng SHA-256 canonical package, vehicle/session/transaction identity; một upload pending không bị request thứ hai thay thế. ACK accepted chưa cho chạy; readback phải đúng package digest. Reject/mismatch/abort không tự trở thành thành công. Simulated progress không giảm và không vượt line count; resume giữ số tuyến đã observed. Snapshot restore kiểm package/digest/readiness, trả trạng thái uploaded/completed và yêu cầu thao tác chạy lại. Không dùng persistence để tuyên bố execution sau reboot.

Core `flight.mjs` giữ byte như trước: mode request/ACK/fresh telemetry reconciliation, stale data, lost video độc lập và event log. MissionSession là rehearsal riêng, chưa nối execution mode với autopilot. Các nút trong điều kiện diễn tập chủ động bơm dữ liệu; không có transport nền gửi lệnh.

## Hera device seam

`core/device.mjs` có capability profile phân observed/unknown và context browser-review/android-device/replay. Browser không được khai báo Android observations. InputAdapter cần transport/source/calibration và binding explicit; không gán L/R/AUTO từ BOM/ảnh. Đây là interface/replay seam, chưa đọc HID/UART/SDK của Hera hoặc decode video. Raw installed build/density/codec/radio/power vẫn unknown.

## Ngữ cảnh BOM trong SOT

BOM nguồn `0.BOM26.xlsx`: 41 sheet, 6.483 main-column rows, 7.617 công thức, 32 cached errors có sẵn, không missing formula cache. Có sheet ẩn/shifted columns và block lặp; row counts không phải số parts unique hoặc tổng một máy bay. SOT chọn 28 claim theo sheet, một flagged set lỗi nguồn và năm integration unknowns, cùng 17 facts intent/proposal/unknown từ giai đoạn trước. 51 facts không đồng nghĩa 51 capability đã verify.

Các sheet HeraLink V1.1 dùng Getac/radio DDL hoặc DTC; ebox và HeraSight có tên Cube Orange/Jetson/RTK/IO. Các part này hỗ trợ thiết kế seam phần mềm, không quyết định cấu hình v2 hoặc actual MAVLink routing. Raw XLSX mirror và derived context được kernel fingerprint; source-owner và nghi thức thay revision tại `sot/README.md`.

## Bằng chứng và phần tiếp theo

BOM so fresh original bằng 135.315 nonempty cells, cache/formula/type; byte mirror/hash giữ nguyên. Kiểm geometry bằng analytic rectangle, winding, 24 headings, concavity, invalid shapes, workload/camera bounds và round-trip; session checks ACK/readback/race/abort/reload. Browser QA gồm reference/touch, kéo/vẽ đỉnh, edit coordinate, local library/export/import, mission states và stale/video modes; inspect screenshots trước bàn giao. Bằng chứng cuối tại `evidence/survey01`.

Chưa kiểm actual Android/Hera, RAGAS source/build, QGC fixtures, DEM/geoid, video latency, SITL/HIL, hoặc operator aesthetic acceptance. Đây là phần tích hợp sau, không đổi thành PASS do prototype và integrity tests sạch. Bước kế tiếp: map/terrain providers và offline package, version-pinned QGC camera/mission compiler, rồi source/SDK/native adapter trên cấu hình được xác nhận.
