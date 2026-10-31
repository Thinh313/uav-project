# INTAKE01: kết quả tiếp nhận từ clone sạch

31/10/2026. Kiểm trên một checkout mới tải từ GitHub, không dùng `.local`, runtime
hoặc môi trường Python của cây AERIS gốc. Host kiểm vẫn là máy Mac hiện tại;
đây không phải nghiệm thu trên một máy nghiên cứu/Android/HeraHub khác.

## Mốc gốc đã kiểm

- Public commit `94c3ef8d740c5ebdb3b6fff900e4efa93f822be0`, tag
  `research-handoff-2026-10-31`, tạo nhánh đúng hướng dẫn README.
- Cả sáu lệnh source/mock trong README chạy thành công. Source manifest đối chiếu
  12.531 file được liệt kê; manifest tự nó được Git commit bảo vệ.
- Base mock 36 checks, lifecycle 18 checks, health 4 checks, portable wait 3 cases.
  Đây là các suite riêng, không phải một phần trăm nghiệm thu sản phẩm.
- `npm start` mở được HTTP root, `/sitl.html`, `/legacy.html` và font: HTTP 200.
  `/api/sitl/status` trả 503 khi SITL tắt mặc định. Chỉ kiểm HTTP, chưa kiểm đồ họa.
  Process group thử nghiệm đã đóng, không khởi động autopilot/Android.
- Gói private gốc khớp SHA256 do bên giao cung cấp và đủ 24 checksum thành phần.
  Kiểm manifest bên trong và dựng private workspace được ghi ở kết quả cuối.

## Những chỗ cần hoàn thiện khi tiếp nhận

README đủ để bắt đầu source/mock, nhưng phần private trước đây mới mô tả thủ công
việc kiểm và giải nén. Bản intake bổ sung lệnh kiểm có pin SHA ngoài archive,
kiểm đường dẫn/manifest và dựng một workspace private mới có ngân sách dung lượng.
Không nạp dữ liệu private vào một public working copy hoặc phục hồi quyền vận hành.

Source base `6ea4f50...` là mốc AERIS trước khi xuất bản public. Nó khác public
commit/tag; đừng nhầm một hash upstream với HEAD của clone mới. Intake cần ghi
cả source base và public HEAD để so kết quả đúng cấu hình.

Gói private gốc được giữ nguyên. Source runtime, APK và 154 input pins của đường
VIDLIFE12 không đổi trong bản sửa công cụ tiếp nhận. Khi overlay private khôi phục
chín file gốc đã ẩn danh, cây đó là PRIVATE_DERIVED, không còn là public snapshot
nguyên byte. Việc kiểm private và việc kiểm public phải được ghi riêng.

## Sửa và kiểm lại công cụ

- Thêm `intake.mjs`: chạy đúng sáu kiểm source/mock, ghi Node/Python, public HEAD
  và source base riêng. Không cài dependency hoặc mở runtime.
- Verifier public kiểm kind, size, SHA và realpath của từng mục. Symlink bị biến
  thành file text hoặc thư mục cha trỏ ra ngoài repo sẽ bị từ chối.
- Thêm `private_bundle.py verify/prepare`: SHA ngoài archive, đúng 24 thành phần,
  manifest lồng, đường dẫn an toàn và workspace mới ngoài Git. Image chỉ kiểm byte
  và chuỗi định danh OCI, không load/chạy.
- Bộ kiểm công cụ có 36 ca private và 8 ca source, được chạy qua 2 unittest methods.
  Có các ca corruption, traversal, sai overlay/hardlink, thiếu dung lượng và
  metadata provenance. Đây là kiểm adversarial bằng fixture nhỏ, không phải bay.
- Lần kiểm gói đầu của helper mới bị từ chối `EXPORT_PUBLIC_MANIFEST_BINDING`.
  Điều tra xác nhận đúng 3 khác biệt biên tập đã khai báo: 2 bản gốc giữ nguyên
  trong HISTORY và prefix `.gitignore` với append 330 byte. Verifier đã sửa để
  đòi chứng cứ riêng cho đúng 3 mục đó; source còn lại vẫn phải khớp byte tuyệt đối.
  Lượt lỗi và HOLD01 được giữ riêng, không ghi đè thành PASS.

## Gói thật và workspace nhận

Gói gốc SHA256 `52fd3330...a92fd28` được kiểm lại thành công sau sửa verifier:
12.532 mục source, 334 mục context, 2.976 mục engineering, 2.037 hardlink,
5 symlink và đúng 9 overlay. Image archive khớp OCI index/config/blob và ARM64;
image chưa được load hoặc chạy.

Đã dựng một workspace private mới ngoài Git, đối chiếu 15.838 file trong plan
cuối và giữ receipt. Kiểm receiver độc lập xác nhận chỉ 9 file source public
khác do overlay đã khai báo, đúng SHA bản gốc private. Đối chiếu lại engineering
bằng SHA/size/mode và từng cặp inode hardlink. Bốn mock core 36/18/4/3 đều đạt từ
workspace nhận, không import cây AERIS gốc. Không có remote Git hoặc quyền operator
được khôi phục.

Bản clone public và workspace private là hai đầu vào khác nhau, đã được kiểm riêng.
Các receipt/log chi tiết nằm trong gói addendum private; báo cáo public này không
liệt kê tên file khách hàng hoặc BOM. Gói gốc và tag handoff ban đầu giữ nguyên.

## Phạm vi kết luận

Đạt tiếp nhận source/mock không có nghĩa beta simulator đã đạt. SDK/AVD vẫn là
prerequisite riêng; R02 chưa có nghiệm thu thực và gate artifact chưa được thay.
Các ca legacy bị floor dung lượng hoặc timing trong báo cáo trước vẫn là phần
chưa giải quyết, không được đổi trạng thái chỉ vì một clone mới chạy được mock.
