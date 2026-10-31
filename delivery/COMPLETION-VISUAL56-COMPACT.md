# VISUAL56 · Compact operator chrome

15/10/2026. Yêu cầu: bỏ “Chuyến bay tham chiếu”, giảm chiều cao header/thanh phát và ưu tiên không gian cảnh. Chỉ sửa index.html, style.css và ui.mjs của module visual56. Không thay model/renderer/physics/replay/server hay module đóng băng.

Đã xóa hẳn khối tiêu đề/status khỏi DOM và cập nhật paint không tham chiếu node đã xóa. Header desktop68→48px, thanh phát73→48px, footer28→20px: cảnh thêm53px. Mobile header54→44px, thanh phát62→48px, footer32→20px: thêm36px. CSS dùng token chiều cao thống nhất, nhóm nút header có cùng hit area40px; timeline có hit area32px, track2px và tiến độ cập nhật theo vị trí thực. Trắng/graphite, vàng dùng cho play/timeline. Panel thông số tiếp tục mở/đóng theo thao tác; không mở thêm tính năng điều khiển.

Đã xem screenshot bằng CUA ở1920×1080,857×988,390×844 và320×568. Desktop stage964px, header48px, transport48px, footer20px; header buttons height40px và centerY23,5px. Mobile390 stage732px,320 stage456px; không scroll ngang. Kiểm play/pause, Home seek00:00/progress0%, toggle panel; console error/warning cuối rỗng. Node syntax đạt. Không viết test suite cho thay đổi bố cục nhỏ. Không có reviewer độc lập; chưa đánh giá với máy chiếu hoặc tuyên bố vượt DJI.

Bằng chứng bổ sung: evidence/visual56/compact-ui-browser.json, compact-ui-1920.jpg, preservation-compact-before.json và preservation-compact-final.json. Hồ sơ VISUAL56 gốc được giữ; fingerprint gốc của3 file chỉnh UI được supersede bởi compact-ui-fingerprints.json, không viết lại receipt gốc. Không tạo dependency/scratch ngoài repo, không xóa dữ liệu hoặc ký bản mới.
