# Survey & Inspection Workbench 01

2026-10-24. **READY-with-deferred trong phạm vi host/mock. Chưa nghiệm thu native, SITL tích hợp hoặc vận hành thực địa.**

Preview: http://127.0.0.1:8890/ . Entry: `pilot/workbench01/server.mjs`. Bản này cô lập, không sửa ứng dụng/candidate đóng băng hoặc lịch sử ENDURE. Không build APK, chạy SITL/emulator, dùng HeraHub/SDK hay ký production. Manifest bàn giao chỉ kiểm toàn vẹn cục bộ, không phải chữ ký phát hành.

## Kết quả người dùng

Một ứng dụng có luồng KML → lập phương án polygon/corridor → kiểm trước diễn tập → duyệt → Fly replay → đánh giá ảnh/độ phủ → đề xuất bay bù → lưu/xuất/nhập workspace. Người dùng thay AGL, tốc độ, hướng, chồng phủ, camera tổng hợp, Home, pin, tải và gió rồi tính lại. Không cần lấy số từ nhiều trang kiểm kỹ thuật.

Planner/parser/readiness từ mapping51, ENU từ survey và kiểm hình học mission55 được tái dùng nguyên byte. Contract riêng Workbench cho mock 10–120 m, 0,5–15 m/s không thay contract native92 hẹp hơn, không chuyển thành quyền upload hoặc bay thật.

## Phạm vi nghiệm thu

| AC | Kết quả | Chứng cứ và giới hạn |
|---|---|---|
| A1 KML/model | PASS host/mock | Polygon, corridor, lựa chọn feature, Home cấu hình rõ; kiểm thêm AOI ở 51°N ngoài fixture cũ. Từ chối bowtie, entity/NetworkLink, holes và absolute altitude cho lập tuyến. Không suy KML Z thành AGL. |
| A2 Lập tuyến/dự toán | PASS mô hình tổng hợp | GSD, footprint, interval, nhòe dự kiến; công suất hằng + tải + gió đối đầu + về Home + dự phòng. Nhóm tuyến theo ngân sách từng lượt; tuyến đơn vượt khả năng bị chặn. Chưa hiệu chuẩn Hera; không mô phỏng thay pin/động lực học. |
| A3 Cockpit/quyền | PASS mock | Đổi phương án, mất link và restart đều không giữ quyền. Cần kết nối/duyệt lại chủ đích. Không có transport phát lệnh aircraft. |
| A4 Ảnh/độ phủ | PASS fixture tổng hợp | Ba lớp dự kiến/có ảnh tổng hợp hợp lệ/ảnh tổng hợp đạt ngưỡng; hash pixel, exposure, camera/plan, clock, pose. ACK không đủ. Nhòe/clipping/thiếu ảnh/sai camera/clock/tilt có lý do riêng. Không chứng minh chất lượng ảnh camera thật. |
| A5 Bay bù | PASS đề xuất | Sinh vùng và đoạn cần bổ sung, gắn hash phương án/phân tích và xác nhận riêng. Hồ sơ đang review không bị sửa bởi xác nhận. Chưa tạo/duyệt tuyến bay bù an toàn hoặc tự thực thi. |
| A6 Workspace/receiver | PASS host/browser | Xuất file thật từ UI, nhập qua file chooser, receiver CLI tiến trình riêng kiểm lại; chống sửa hash/nội dung và sai schema/binding. Reload và host restart khôi phục kết quả, không quyền. Lỗi lưu khi host tắt được báo rõ, số liệu còn trong bộ nhớ. Không có crash journal hoặc danh mục lịch sử đầy đủ trong slice này. |
| A7 UI/UX | PASS phạm vi đo | 32 tổ hợp: bốn màn hình × hai theme × bốn viewport; 14 mẫu dialog và thêm hai mẫu dialog Home cuối. Không tràn ngang, nút ≥48 CSS px, rail trái/phải cùng tâm Y, số liệu cùng mép logo. Popup nằm trong viewport, phần dài cuộn. Không chứng nhận toàn bộ pixel/native dp hoặc độ đọc dưới nắng. |
| A8 Bảo toàn/ngân sách | PASS | 12.925 mục bảo vệ, 8.527 entry lịch sử, handoff/reuse tham chiếu G17: hợp kiểm 14.025 identity, khoảng 1,11 GB byte được đối chiếu. Đúng SHA/lstat và mtime nơi baseline yêu cầu. Sàn vật lý 20 GiB và gate Android–SITL 29 GiB giữ nguyên. Không khẳng định đường dẫn hiện diện liên tục hay toàn repo không thiếu file. |

## Những gì đã quan sát

- Mẫu polygon: 12 tuyến, 264 vị trí chụp. Ca đầy đủ đạt 100% độ phủ footprint tổng hợp theo tâm ô 5 m.
- Ca thiếu dải ảnh: 159 mẫu đạt, 105 khai báo thiếu; độ phủ có ảnh/đạt mẫu còn **92,107%**, vùng cần bổ sung khoảng **2.800 m²** theo lưới. Không lấy số lệnh chụp làm số ảnh thật.
- Corridor: 8 tuyến, 392 vị trí, dự toán hai lượt pin. UI chạy nominal tới review với 392 mẫu đạt; ca mất link giữ prefix, thu hồi quyền và buộc kết nối/duyệt lại.
- Nhòe/clipping có thể làm số ảnh đạt giảm mà diện tích phủ vẫn cao do ảnh lân cận chồng phủ. Một ô có ảnh đạt không đủ chứng minh giao hội nhiều góc hay photogrammetry đạt chuẩn.
- Workspace xuất từ browser 348.777 byte đã được tiến trình receiver riêng xác nhận; đây là file mẫu polygon/blur, không gộp với lượt corridor sau đó. Bản export trong Downloads được giữ như đầu ra người dùng.

## Kiểm kỹ thuật và provenance

- `mock-tests04.json`: **25 nhóm PASS**, gồm geometry, optics, energy, authority, pixel/clock/camera, refly và semantic receiver. Các lần 02/03 không cộng lại thành nhóm mới.
- `math-oracle01.json`: **4 ca PASS**, Python winding number + phép quay footprint, công thức viết riêng so với JS. Cùng assistant thực hiện; không giả là QA độc lập bên ngoài.
- `http-tests02.json`: **7 nhóm PASS**, loopback, origin, allowlist, compile, consent, receiver và CSP/font.
- `browser-layout03.json` + `layout-verification02.json`: 32 tổ hợp cuối, số liệu bounding box và màu thực từ trình duyệt. Các ma trận trước giữ nguyên, không cộng trùng.
- `browser-journey-final.json`, `browser-corridor-loss01.json`, `browser-corridor-nominal01.json`, `dialog-*.json`, `browser-export-receipt01.json` giữ nguồn và phạm vi từng lượt.
- Đây là tự kiểm bằng tool/terminal/browser theo các pha đặc tả → Builder → Verify của một assistant. Không có human review hoặc agent review độc lập. Không có runtime AI; đối chứng LLM không áp dụng cho phần toán xác định này. Lợi ích thao tác, thời gian/công so với spreadsheet/GCS khác chưa được đo; không tuyên bố vượt DJI.

## Lỗi/giới hạn được giữ nguyên

1. Preview đầu bị sandbox từ chối bind loopback; giữ receipt, mở lại bằng quyền chạy preview cục bộ, không nới guard.
2. Một negative test ban đầu sửa proposal thành mảng rỗng vốn đã rỗng vì ảnh chồng phủ đủ. Giữ FAIL ở `mock-tests01.json`; sửa fixture để thực sự thay đổi dữ liệu, không bỏ assertion.
3. QA screenshot phát hiện chữ trắng kế thừa từ root ở theme sáng. Sửa body token và màu tuyến/lớp phủ; giữ ảnh/ma trận trước sửa và đo lại bản cuối.
4. Harness iframe bị CSP chặn đúng. Bỏ cả harness và ngoại lệ framing tạm; dùng viewport CUA trực tiếp. Trang chính cuối giữ `frame-ancestors none`.
5. Thử dừng host ở cuối replay đã lỡ cửa sổ lỗi analyze: replay hoàn tất trước khi host dừng. **Finish/analyze outage NOT_CHECKED**, không báo PASS cho ca này. Kiểm riêng thao tác lưu khi host đã tắt: không báo thành công, giữ kết quả trong bộ nhớ; sau restart người dùng lưu lại chủ đích đạt. Chưa kiểm crash trong khi đang ghi/đang diễn tập.
6. LocalStorage giữ workspace hiện tại được lưu/lượt hoàn tất gần nhất. Chưa thay thế journal nhiệm vụ bền vững, lịch sử nhiều lượt hay kho bằng chứng đã có ở các module khác.
7. Chưa có DEM/tiles bản đồ thật, bám địa hình, vùng trời cập nhật, báo cáo kiểm tra theo tài sản/khuyết tật, ảnh RGB/thermal thật, driver payload, hiệu chuẩn pin/camera, native/Android–SITL hoặc hardware. SHA là integrity/consistency, không xác thực người gửi.

## Dung lượng và cleanup

Không cài dependency, tạo bản sao dự án, build output, APK, Docker hoặc scratch ngoài repository. Đã bỏ ba file harness do chính tác vụ tạo: `pilot/workbench01/qa-layout.html`, `qa-layout.css`, `qa-layout.mjs`; giữ receipt lỗi trong evidence. Đóng tab QA tạm và reset viewport. Preview Workbench có chủ đích được giữ cho người dùng, không có tiến trình bay mới.

Git vẫn có 95 đường dẫn thiếu đã tồn tại từ trước, ngoài baseline bảo vệ được kiểm; không tự phục hồi hoặc quy thành lỗi mới. Kết quả bảo toàn không sửa lịch sử các sự cố khôi phục cũ. Xem `preservation-final.json` và `handoff-manifest.json` cho bytes/hash/dung lượng thực.

## Bước tiếp theo

Giữ nguyên gate beta/G17. Sau khi scope mock được người dùng xem, nối model Workbench vào native cô lập với cùng provenance và trạng thái quyền, rồi kiểm Android–SITL khi admission thực đạt. Đường ảnh camera thật, DEM và hiệu chuẩn vẫn có gate riêng; không chuyển các con số tổng hợp này thành chất lượng khảo sát thực địa.
