# DUAL67 — hai phiên cockpit độc lập

**Local two-client mock**, không phải bản cài Android hoặc liên kết hai tay cầm/radio thật. Hai tab có JavaScript context, token phiên và lựa chọn payload riêng; một server loopback phân xử quyền. Không dùng SDK, build APK, ký hoặc gửi lệnh bay.

Mở [Pilot](http://127.0.0.1:8822/pilot) và [Payload](http://127.0.0.1:8822/payload). Bấm Kết nối ở từng phiên; không có quyền được cấp tự động. Phiên đang dùng cùng role sẽ bị từ chối thay vì chiếm phiên cũ.

## Thử luồng

1. Trong Payload chọn Phase One rồi Nhận quyền. Chọn Thermal trong Pilot: lựa chọn ở Payload không đổi và Pilot chưa có quyền.
2. Payload Bàn giao cho Pilot. Cả camera và gimbal khóa. Pilot đọc trạng thái và Chấp nhận đề nghị hiện tại. Operator cũ không còn điều khiển được.
3. Chụp/zoom/focus/gimbal mock. Review phân biệt ACK và metadata; không chứng minh exposure/file, ảnh thực0. Mỗi khóa lệnh dùng một lần mỗi thế hệ transport theo CYBER65 quarantine.
4. Mở phần kiểm lỗi của owner → Mô phỏng mất liên kết phiên này. Client khóa ngay và ghi quyền chưa xác nhận. Server thu hồi khi quá3000ms không heartbeat, trong lúc peer vẫn hoạt động. Ngắt phiên là thu hồi explicit ngay; cả hai đường đều không tự nối lại/cấp quyền.
5. Kết nối phiên mới rồi nhận quyền lại explicit. Reset transport mock chỉ dành Pilot: xóa authority/transaction/quarantine của core hiện tại, không xóa tape. Không khôi phục quyền từ lịch sử.
6. Xuất review JSON trước khi dừng server. Đây là dữ liệu in-memory, không phải journal bền vững. Restart server mất trạng thái volatile và tạo boot/token mới. Các receipt QA đã lưu ở evidence được giữ riêng.

## Giới hạn kỹ thuật

- Actor do server gắn với opaque token; action chứa boot/sequence/revision. Không tự retry lệnh sau timeout/mất phản hồi. Thứ tự admit trên server xác định một người thắng tranh chấp CAS.
- Role là fixture tự chọn trên localhost, chưa có trusted enrollment/production authentication/TLS/remote deployment. Hai tab không chứng minh hai máy tính, radio hoặc Android lifecycle. Loopback không nhận kết nối từ tay cầm khác.
- Outer station timeout3000ms, proposal8000ms là policy mock mới. Core CYBER65 vẫn dùng clock theo bước20ms/intent và10ms/feedback, với deadline1400/800ms cũ. Hai clock được lưu riêng. Host timer không phải thời gian thực cứng hoặc failsafe bay được nghiệm thu.
- Bounded4096 events, tổng entry UTF8≤4MiB, export≤5MiB,32station-history và core-history guard trước eviction. Đầy quota/clock lỗi khóa quyền, giữ tape, không tự dọn. Heartbeat cũng dùng quota; không dùng preview này làm soak hay dịch vụ dài hạn.
- Phase One thật model/API/lens/calibration unknown; Thermal/Corona là fixtures; LiDAR khóa vì chưa có adapter. Raw protocol chỉ qua MockTransport. Flight commands encoded0, actualImages0.
- Replay có SHA và tái thực thi deterministic; không phải chữ ký hoặc kiểm định độc lập bởi bên khác. Import/inspect chỉ trả kết quả lịch sử, không cấp authority vào server đang chạy.
- Desktop1280×720 đã kiểm. CSS responsive có triển khai nhưng override1024/390 của CUA không áp dụng: actual vẫn1280×720, nên hai kích thước này **NOT_CHECKED**, không dùng tên ảnh attempt làm bằng chứng.

## Kiểm terminal-first

Chạy từ thư mục aeris; không cần dependency install.

`node --test native/dual67/arbiter.test.mjs`

`node native/dual67/run-corpus.mjs evidence/dual67/corpus-next.json`

`node native/dual67/http-qa.mjs evidence/dual67/http-next.json`

HTTP QA tự dùng/dừng service riêng ở8822; không chạy khi preview đang giữ port. Test dùng injected monotonic clock và có deliberate duplicate để kiểm fencing; client UI không retry. `node native/dual67/server.mjs` mở preview thật bằng host monotonic clock. Server chỉ bind127.0.0.1:8822, cùng Origin, token và body-bound; chữ “thật” ở đây chỉ nói HTTP/clock host, không nói drone.

Receipt dùng exclusive create, chọn tên mới. Không ghi đè các run trước. Source/candidate/ENDURE và COCKPIT66 được đọc/pin, không sửa. Không tạo bản sao dự án hoặc dependency/build trong tmp; sàn20GiB và ngân sách phần mới32MiB.
