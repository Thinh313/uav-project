# COCKPIT66 — CYBER65 cockpit chuẩn bị cho native

Phạm vi đã kiểm: host/browser mock và replay. Android Activity/manifest là **source chuẩn bị**, chưa compile, build APK, ký, cài hoặc kiểm ART/WebView/HeraHub. Không có SDK, radio, camera thật hay đường gửi lệnh bay. Hai góc nhìn Pilot/Payload cùng một mock GCS, chưa phải hai trạm vật lý được xác thực.

Preview: http://127.0.0.1:8821/ · `node native/cockpit66/server.mjs` từ thư mục aeris. Server chỉ GET tài nguyên whitelist trên loopback, không có command API. Giữ sàn 20 GiB; không mở instance thứ hai khi preview đang chạy.

## Thử luồng chính

1. Chọn Phase One, Thermal hoặc Corona. Đây là chọn nguồn quan sát; không cấp quyền. LiDAR chưa có adapter và bị khóa.
2. Mở phiên mock → Nhận quyền payload. Camera và gimbal được nhận theo bộ; Corona camera cố định chỉ có camera.
3. Bàn giao cho operator còn lại. Cả bộ điều khiển bị khóa khi chờ. Đổi góc nhìn sang người nhận, kiểm chủ sở hữu rồi Chấp nhận hoặc Từ chối. Đổi góc nhìn tự nó không chuyển quyền.
4. Thử chụp/zoom/focus/gimbal mock. Chỉ owner hợp lệ được gửi. Cùng khóa lệnh không tự retry; một thao tác chỉ được dùng một lần trong phiên theo quarantine CYBER65. Mở phiên mock mới để thử lại.
5. Mở phần kiểm lỗi để thử ACK-only, sai mục tiêu, mất liên kết/operator, hết hạn hoặc mất focus. Review giữ trạng thái ACK và metadata tách biệt với bằng chứng thực thi. **Ảnh thực luôn bằng 0**.
6. Lưu workspace, tải lại trang hoặc restart preview rồi Đọc lại kho. Khôi phục lựa chọn và lịch sử đã lưu; phiên vẫn ngắt, không khôi phục quyền. Nếu mất phản hồi ghi, phải đọc lại để đối chiếu trước thao tác tiếp.

Clock là **mock theo bước**, không phải đo real-time hoặc kiểm timeout vật lý. Nút quyền bay chỉ kiểm authority trừu tượng của Pilot; không có mapper lệnh bay. Hình công trình là SVG tổng hợp, không phải video hoặc mô phỏng 3D.

## Persistence và giới hạn

Chỉ hành động đã bấm Lưu workspace mới có trong capsule được lưu. Đây không phải journal lệnh bền vững. Tape tối đa 96 bước, capsule 512 KiB, kho 16 revision bằng transaction/CAS; đầy quota thì từ chối, không tự xóa. Digest không phải chữ ký hay xác thực operator. Cold load replay trong core riêng rồi bỏ toàn bộ authority.

Node portable khớp 44/44 digest gốc. Browser hiện có 42 digest khớp và 2 ca khác làm tròn góc diễn giải, trong giới hạn so sánh 1e-12 rad theo ADR082. Raw/command/identity/owner/clock vẫn exact. Workspace replay giữ hash strict: chuyển giữa engine hoặc đổi WebView chưa được nghiệm thu và có thể bị chặn, giữ dữ liệu để đối chiếu.

Model Phase One, firmware, API, lens/calibration và ảnh/video thật vẫn chưa biết. Thermal/Corona cũng là binding mock, không chứng minh tích hợp thiết bị. Hai operator thật cần authentication, distributed arbitration, transport/loss tests và hardware qualification riêng.

## Kiểm lại không build

`node --test native/cockpit66/model.test.mjs native/cockpit66/compatibility.test.mjs`

`node native/cockpit66/verify-host.mjs evidence/cockpit66/technical-health-next.json`

Script ghi receipt bằng exclusive create; dùng tên mới, không ghi đè bằng chứng. `parity.mjs` đã ghi portable-parity01; không chạy lại cùng đích cũ. Derivation ghi 16 nguồn/hash và thay thế giới hạn, không sửa CYBER65/P22/T25/N44/font gốc.

Android assets dự kiến dưới `assets/cockpit66/` theo assets.json. Không có build system hoặc APK mới trong slice này; kiểm static không thay compile/runtime. Tổng ngân sách phần mới 32 MiB; không cài dependency hoặc tạo bản sao dự án trong tmp.
