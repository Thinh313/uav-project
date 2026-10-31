# Payload Gateway + Real Media: MOCK01

21/10/2026 · **READY trong phạm vi host/mock; NOT READY cho payload thật**

Đã triển khai và thao tác trọn đường trong cockpit AERIS hiện có: discovery → chọn RGB/IR → cấp quyền mock có hạn → điều khiển/đọc lại gimbal và ISO được hỗ trợ → nhận JPEG tổng hợp → gắn vị trí UAV tại exposure mock → review → xuất gói → receiver kiểm lại. Source/candidate/ENDURE được giữ riêng, không đưa gateway vào APK hiện hành.

![Review RGB và IR sau QA](../evidence/payload-gateway01/browser04/review-final-1280.png)

## Người dùng đã làm được gì

- Tìm hai payload mock và xem capability. Chọn payload không tự cấp quyền; chuyển payload thu hồi quyền cũ và xóa readback hiển thị của thiết bị trước.
- Cấp lease60giây cho camera/gimbal đã chọn. Lệnh có ID chống gửi lại; sai station/token/đích/boot, hết hạn, revoke hoặc mất link bị chặn. Lệnh được ghi/fsync trước adapter và kiểm quyền lại sau WAL. Hai lệnh đồng thời tới một thiết bị bị chặn.
- Đổi pitch/yaw theo độ trong frame mock đã khai báo và nhận readback. RGB hỗ trợ ISO whitelist; IR không hỗ trợ ISO/radiometry. Phản hồi sai mục tiêu, mất readback, phản hồi sau revoke hoặc timeout500ms là UNKNOWN. Không tự retry.
- Xem preview tổng hợp qua pipeline codec/relay BIG02. Nguồn H264, canvas và GNSS đều tổng hợp, không phải Sony/Phase One hoặc video thermal thật. Xử lý video không đổi chính sách frame/WAL của flight/physics.
- Chụp JPEG nguyên byte từ khung decode, nối capture intent/event/frame/file và metadata. ACK thiếu exposure event không tạo ảnh hợp lệ. File thiếu/hỏng, GNSS không hợp lệ, sai media epoch hoặc capture quá hạn không được công bố.
- Review ảnh và vị trí WGS84 ellipsoid tại exposure; thời gian±5ms là dữ liệu giả lập. Độ chính xác không gian, lever arm và tọa độ vật thể vẫn UNKNOWN/NOT_DETERMINED. Không suy độ chính xác mapping từ các số này.
- Tải gói `.tar` gồm đúng `manifest.json`, `original.jpg`, `sidecar.json`. Receiver Python tái sử dụng triển khai độc lập của BIG02 kiểm SHA, context và phép tính tọa độ. `gateway.json` là chẩn đoán lineage riêng, không nằm trong gói ba thành viên.
- Khởi động lại gateway thật trên host và reload browser: ảnh cũ giữ nguyên, quyền không được phục hồi. Workspace có writer lock; journal hỏng mở chỉ đọc; file chưa có commit receipt giữ PENDING, không tự xóa hoặc biến thành completed.

## Ma trận nghiệm thu mock

| AC | Kết quả | Chứng cứ |
|---|---|---|
| 1 · Identity/discovery/selection | PASS scoped | Corpus mock cuối, HTTP discovery, UI chọn RGB/IR; unknown firmware/đích bị từ chối. |
| 2 · Quyền và tương quan | PASS scoped | Expiry, post-WAL expiry, wrong station/token, replay, revoke khi reply đang chờ, reboot/link loss, hai command đồng thời; không có flight API. |
| 3 · Gimbal/camera capability | PASS scoped | Readback mock pitch/yaw/ISO qua UI; IR không ISO/°C; sai target/feedback không thành execution. |
| 4 · Event/file/epoch | PASS scoped | UI RGB/IR commit và UI `UNKNOWN_NO_EXPOSURE_EVENT`; thiếu file, hỏng JPEG, stale/config change, source sai bị chặn trong corpus. |
| 5 · Geotag/export/receiver | PASS scoped | Ba gói browser-download qua receiver, gồm RGB cuối và IR; bốn loại negative receiver. Original tải qua UI được đối chiếu đúng byte. |
| 6 · Durability/restart | PASS scoped | Gateway process restart dùng workspace cũ; journal chain/closure; partial tail, fsync failure, commit receipt failure và media/manifest tamper; writer thứ hai bị chặn. |
| 7 · Cockpit UI | PASS scoped | Thao tác browser, layout1280×800 và900×500, glass panel không chạm strip/status, theme/icon/tooltip, reload và clear readback. Không phải Android/HeraHub QA. |

## Kiểm đã chạy

- **22/22 nhóm ca mock cuối đạt** tại `mock04/results.json`. Đây là ca tự tác giả viết/chạy, không phải independent human QA. Không cộng các lần chạy lặp thành số ca mới.
- **6/6 nhóm kiểm HTTP localhost đạt**: lifecycle, quyền, command replay/flight refusal, nonce/origin/Host/method/path, preview epoch sau reload và TAR.
- **3 gói tải bằng browser được receiver nhận**, gồm gói RGB cuối `4ac30c46…53ef9`, IR `90edc1c7…5d00d` và gói trước restart `f8eae2e3…acfc1`. Receiver độc lập về triển khai; không đồng nghĩa người đánh giá độc lập hay nguồn ảnh được chứng thực. Mỗi gói kiểm cùng bốn nhóm lỗi: sai receiver, ảnh hỏng, thiếu member, replay.
- Bốn JPEG tổng hợp đã commit được giữ trong workspace; capture thiếu exposure event không tăng số ảnh. Các JSON tải riêng lẻ từng có timeout công cụ: không báo PASS cho đường đó. Xuất gói TAR là đường đã kiểm thực tế.
- Layout cuối:900×500 panel bắt đầuY102, strip kết thúcY90, panel kết thúcY388 trước statusY402.1280×800 reviewY118 sau stripY106 và kết thúcY664 trước statusY676. Đây là hai viewport host đã kiểm, không là cam kết toàn bộ màn hình/thiết bị.
- Không chạy benchmark photon-to-photon, hardware decoder, CPU/nhiệt, radio/fanout hoặc bay/SITL. Không dùng tuổi frame trên UI như số đo độ trễ camera thật.

## Sửa lỗi và bằng chứng được giữ

`mock01` thất bại do fixture/client mang thừa field của join vào envelope exact-schema; đã sửa tại caller, không nới schema. `mock02/03/04` giữ riêng. `browser01` gặp EPERM khi bind trong sandbox, chưa có hành trình UI; chuyển sang quyền chạy localhost phù hợp và giữ launch lỗi. Không xóa lịch sử lỗi.

QA phát hiện và đã sửa: header quyền lệch trạng thái payload, readback thiết bị trước còn sau selection, media epoch không đổi được sau browser reload, xuất JSON lẻ không ổn định, panel chạm status ở landscape hẹp, tooltip theme chưa theo state. Đã kiểm mục tiêu sau sửa. Chỉnh cuối chỉ là tooltip; targeted reload/theme/persistence đã chạy, không quảng bá một benchmark mới.

## Ranh giới còn mở

| Phần | Trạng thái và bước tiếp |
|---|---|
| Sony/Pixy vật lý | NOT_CHECKED. Chốt model/lens/SKU/fw, SDK license/API, wiring/power/gimbal frame, exposure event, original file và GNSS clock rồi thay mock adapter. |
| Phase One | NOT_IMPLEMENTED_REAL_DRIVER. Contract chung không chứng minh điều khiển P3 hay camera khách hàng. |
| Thermal | Chỉ IR-look mock. Radiometry/°C, calibration và sensor thật chưa có. |
| HeraHub/Android | Chưa ghép gateway vào APK, chưa cài thiết bị, chưa SDK/input/video thật. |
| Nhiều người dùng qua RF | Local mock station scope chưa thay production authentication, hai tay cầm thực, bandwidth/fanout hoặc authority safety qualification. |
| Linux trên UAV/Hera field | Runtime mới chạy trên host, chưa là onboard deployment; khối lượng/CG/nguồn/nhiệt, endurance và field acceptance còn riêng. |

Milestone phần cứng tiếp theo là **một combo Sony ILX-LR1 + Pixy LR cụ thể**, đi cùng hành trình và receiver này. Không cần rewrite cockpit. Không tự tải SDK, mua thiết bị hoặc coi profile mock đã trở thành driver thật.

## Bàn giao và bảo toàn

- [TIP và ADR phạm vi](../planning/payload-gateway01/TIP.md), [runbook chạy lại](../planning/payload-gateway01/RUNBOOK.md), [contract adapter và gate thật](../payload/gateway01/ADAPTER.md).
- [Xác minh cuối](../evidence/payload-gateway01/final-verification01.json), [mock corpus cuối](../evidence/payload-gateway01/mock04/results.json), [HTTP](../evidence/payload-gateway01/http01.json), [receiver RGB](../evidence/payload-gateway01/receiver03-final-rgb.json), [receiver IR](../evidence/payload-gateway01/receiver02-ir.json).
- Scoped preservation kiểm292 đường dẫn hiện hữu, gồm PHONE06/BIG02/APK và các định danh ENDURE đã chốt; không thay kiểm toàn bộ ENDURE hoặc xử lý các incident thiếu đường dẫn cũ. Kết quả và dung lượng cuối trong verification receipt.
- Đã đóng các tiến trình, port, tab kiểm thử; xóa curated stage `.local/payload-gateway01/stage`, khôi phục viewport. Không có project copy/tmp, cài dependency, Docker, APK/build hoặc chữ ký mới. Gói browser-download và bằng chứng kiểm được giữ; bản sao gói trong evidence phục vụ bàn giao.

Giá trị đã chứng minh: hành trình mock trong một cockpit tạo được gói ảnh có liên kết và kiểm receiver/restart. Chưa đo thời gian thao tác so workflow cũ hoặc ưu thế sản phẩm với DJI. LLM không tham gia runtime; không cần so direct-LLM cho authority/hash/geotag xác định. `READY` chỉ áp dụng bảy AC host/mock trên đây.
