# COMPLETION · MAPPING51

15/10/2026 · **DONE / PASS_SCOPED_MOCK_REPLAY**, 7/7 yêu cầu TIP trong phạm vi mô phỏng host. Một agent thực hiện các pha specification, build, verify tuần tự; không phải đánh giá độc lập hay nghiệm thu Hera.

## Kết quả bàn giao

Preview riêng http://127.0.0.1:8805/, mã tại `pilot/mapping51`, dữ liệu riêng `.local/mapping51/operator`. Sau kiểm cuối kho operator trống: revision0, chưa nạp mẫu, chưa chọn KML, chưa có phương án/quyền mock/ảnh thật. PID preview hiện86033; `preview2.json` ghi quan sát chỉ đọc. Không thay đổi source/candidate/SOT/trust/ENDURE, không nối vào Fly, không SDK/APK/build/SITL/emulator hoặc ký mới.

Luồng hoàn chỉnh: nạp KML hoặc ví dụ tổng hợp → chọn rõ Polygon/LineString → cấu hình camera và nhiệm vụ → xác nhận mặt đất phẳng tổng hợp → xem tuyến và dự đoán GSD/overlap/nhòe/readout/khoảng chụp → nạp quan sát mock → đối chiếu camera, GNSS máy bay và GNSS payload/PPK → gõ mã phương án và xác nhận → chạy từng bước mock → đóng/review → xuất, kiểm nhập lại bằng semantic replay.

### KML/corridor

Parser Python thư viện chuẩn, KML2.2 UTF-8≤256KiB, namespace và cấu trúc có giới hạn. Hỗ trợ Polygon/LineString/MultiGeometry với feature selection tường minh, tối đa16 đối tượng/1024 tọa độ tổng; giữ nguồn/SHA, Z và altitudeMode. Không tải NetworkLink, không resolve external entities hoặc file/network; tên hiển thị dạng text. BOM giữ nguyên khi nhập browser. KMZ/gx:Track/Point mission chưa hỗ trợ.

Chỉ clampToGround có thể lập phương án trong increment này, độ cao AGL lấy riêng từ mô hình phẳng đã xác nhận. Z của clamp được giữ và ghi rõ bỏ qua khi tính AOI, không biến thành độ cao bay. Absolute/relative, đối tượng ẩn và polygon có lỗ được giữ để xem, không tự chuyển thành mission; lỗ vẫn hiện cutout trong preview.

Polygon dùng read-only import từ `app/core/survey.mjs` đóng băng. Corridor là các vùng chữ nhật mở rộng đầu/cuối riêng cho từng đoạn, các làn song song và chụp serpentine; khúc cua có thể chụp dư/trùng và các đường nối chưa kiểm. Đây là mô hình thu nhận có giới hạn, không phải tuyến giao thông đã kiểm an toàn hoặc offset corridor trơn. Bounded local ENU: latitude±70°, extent≤2,5km,≤512 leg/10.000 lệnh chụp dự kiến. Chưa có DEM, địa hình, động lực học, năng lượng, vật cản hay kiểm vùng trời. GSD/overlap và footprint là dự đoán danh nghĩa, không phải độ phủ hoặc độ chính xác thực.

### Mapping Readiness

Profile camera tổng hợp có phiên bản: lens/sensor/resolution, ISO, khẩu độ, shutter, exposure/readout, focus, chu kỳ tối thiểu, calibration ID và provenance. Kiểm settings quan sát phải khớp; digital zoom, tilt/rate, storage và test-image fixture có gate. Global shutter mẫu không đại diện shutter của Sony/Hera. ISO/khẩu độ chỉ đối chiếu giá trị, không chứng minh độ sâu trường ảnh/nhiễu/chất lượng quang học.

GNSS điều hướng khác GNSS payload. RTK kiểm FIX, correction age, sigma khai báo, base/reference đúng; PPK kiểm chuẩn bị ghi raw/base đồng thời, tọa độ và identity/reference riêng. `PPK_RECORDING_PREPARED` không phải PPK đã xử lý. Không ngầm đổi RTK→PPK khi mất CORS. Freshness ràng buộc process clock/session/boot/aircraft/camera, age≤10s, correction≤2s theo engineering policy mock v1, không phải chuẩn đo vẽ hoặc mặc định RtR.

Review gắn full SHA phương án/quan sát/context; mã8hex chỉ hỗ trợ nhập xác nhận. Thay input chưa lưu chặn nút start; lập lại phương án hoặc đổi identity/clock/nguồn thu hồi xác nhận. Sai mục tiêu, reboot, sequence cũ, clock lùi, stale hoặc mất link làm ngắt/thu hồi; không tự retry/resume. Tách trigger/ACK/exposure/file declaration tổng hợp; actualFiles luôn0. Không có camera, ảnh thật hoặc lệnh bay. Không suy ra đủ điều kiện bay thực từ READY_FOR_MOCK.

### Persistence/review

Nhật ký riêng append-only, SHA chain, exclusive create và fsync/readback,≤64 records/16MiB,≤2MiB mỗi record. Cold read/import reparse nguồn, recompile plan và semantic replay; phát hiện sửa bytes hoặc rehash trạng thái giả. Restart giữ draft/plan/lịch sử nhưng ngắt session, xóa quan sát và quyền. GET không viết lại lịch sử; thao tác ghi rõ ràng sau restart thêm RESET. Bản nhập lịch sử chỉ kiểm hồ sơ, không khôi phục quyền.

Torn/missing/unknown/link/corrupt file làm kho bị chặn; dữ liệu vẫn giữ. Không tự sửa/xóa/prune. Sau lỗi ghi hoặc mất phản hồi, phải đọc lại/reconcile; không phát lại mutation tự động. Một cooperating owner/root; không chứng nhận chống owner filesystem đối kháng. Capacity có dự phòng và sàn host20GiB; không làm đầy volume thật để thử.

## Kiểm chứng

**199 ca kiểm đạt**, không cộng các receipt cũ:

| Receipt | Số ca | Phạm vi |
|---|---:|---|
| host5 |113| KML negatives, geometry/analytic/rotation/footprint samples, readiness, clock/identity/loss, replay và journal faults |
| edge3 |24| BOM/encoding/style/ID, camera model/settings/capacity, PPK identity,64-record quota, competing owner, links/pending |
| crash5 |13|3 tiến trình Node riêng bị SIGKILL tại after-create/after-write/after-sync, đọc lại và giữ hồ sơ |
| browser5 |49| Chromium nhập KML/corridor, chỉnh camera/PPK, stale/mất phản hồi, restart PID, xuất/kiểm nhập, input race,1280/1024/360 |

`verification1.json` và lượt đối chiếu lại `verification2.json`:49 kiểm nghiệm thu đạt; scenario receipts199, source pins, cú pháp13 module JS/2 Python, closure/PID và source capture SHA đều đạt. Lượt2 chạy nguyên logic verifier, chỉ đổi tên output để giữ receipt1; không ghi đè receipt. Không coi hai lượt metadata verification là398 ca chức năng.

Browser không có lỗi JS/request ngoài, không tràn ngang, các control có kích thước52px. Đã xem ảnh review1280 và360. Chữ dài/details được bọc dòng, pending form không làm hiện các dự đoán mới trước khi commit. Hình học được kiểm bằng analytic GSD, các hướng quay và mẫu footprint độc lập với thao tác UI; không chứng minh coverage thực ngoài hiện trường.

Host5/edge3/crash5 kiểm core trước sửa UI cuối; browser5 kiểm UI cuối, pins4/5 giữ core runtime tương ứng, verifier cuối thay riêng cách đối chiếu metadata process. Đây là kiểm hồi quy theo phần thay đổi; không tuyên bố mọi receipt cũ chạy trên cùng toàn bộ SHA cuối.

Các lần lỗi trước được giữ: host1 lỗi góc khi ghép corridor vào planner cũ, corridor cuối tạo các làn theo đoạn có kiểm hướng; crash1 worker thoát top-level await trước SIGKILL, worker cuối giữ event loop thật; browser4 lỗi hiển thị kết quả kiểm nhập, browser5 kiểm lại luồng này. Verifier attempt01 đọc exit metadata chưa có trong functional receipt, sửa để đối chiếu với immutable cleanup receipt theo đúng PID. Không sửa receipt cũ để báo PASS.

## Bảo toàn và preview

Baseline19.596 đường dẫn bảo vệ và inventory5.051 đường dẫn ENDURE khớp; bao gồm nghiên cứu camera/demo và completed HERASTORE50. Không khôi phục hay sửa đường dẫn bảo vệ trong nhiệm vụ này. Xem `preservation-final.json` và `artifact-fingerprints.json` cuối; SHA không phải chữ ký phần mềm.

`preview1.json` là quan sát lịch sử. Kiểm lại phát hiện8805 connection refused, các PID49/50/51 trước không còn và không có listener8803/8804/8805; nguyên nhân UNKNOWN. Ghi `preview-recheck-incident1.json`, chỉ khởi động preview51 mới86033 và kiểm GET/kho trống trong `preview2.json`. Không khởi động lại49/50 hay ENDURE và không suy ra ENDURE24h PASS hoặc health liên tục từ các receipt này.

Ngân sách nhiệm vụ32MiB; verification2 ghi10.944.512 byte cấp phát, free23.306.240.000 byte (~21,7GiB). Số cuối ở preservation-final. Không install dependency, build, copy toàn dự án, tạo distDir hoặc dùng Docker.

## NOT_CHECKED và bước tiếp

- SDK/HeraHub, Android XML/runtime/lifecycle, camera/gimbal/calibration/exposure feedback, ảnh/raw GNSS/base và PPK thực, field accuracy hoặc chuyên gia nghiệm thu.
- Corpus KML khách hàng thật; full KML/KMZ, hole-aware/absolute/relative/terrain/3D compiler; cross-engine numerical portability.
- An toàn tuyến thực, địa hình/vật cản/geofence/vùng trời, động lực học và năng lượng.
- Mất điện vật lý, full-volume ENOSPC, filesystem writer đối kháng; Fly integration hoặc bản ký mới.

Bước hợp lý tiếp: đưa KML và profile thu nhận thực của demo vào corpus, chốt hợp đồng timestamp/capture/GNSS/base theo payload và kiểm adapter bằng replay trước khi bench/SDK/field. Không chuyển dữ liệu mock thành bằng chứng camera hoặc chất lượng bản đồ.

## Dọn scratch

Đã kiểm vắng26 root thử do nhiệm vụ tạo; raw proof cần thiết còn trong evidence. Không dọn kho người dùng hoặc bằng chứng trước:

- `.local/mapping51-browser1`
- `.local/mapping51-browser2`
- `.local/mapping51-browser3`
- `.local/mapping51-browser4`
- `.local/mapping51-browser5`
- `.local/mapping51-crash1-after_create`
- `.local/mapping51-crash2-after_create`
- `.local/mapping51-crash2-after_sync`
- `.local/mapping51-crash2-after_write`
- `.local/mapping51-crash3-after_create`
- `.local/mapping51-crash3-after_sync`
- `.local/mapping51-crash3-after_write`
- `.local/mapping51-crash4-after_create`
- `.local/mapping51-crash4-after_sync`
- `.local/mapping51-crash4-after_write`
- `.local/mapping51-crash5-after_create`
- `.local/mapping51-crash5-after_sync`
- `.local/mapping51-crash5-after_write`
- `.local/mapping51-edge1`
- `.local/mapping51-edge2`
- `.local/mapping51-edge3`
- `.local/mapping51-host1`
- `.local/mapping51-host2`
- `.local/mapping51-host3`
- `.local/mapping51-host4`
- `.local/mapping51-host5`
