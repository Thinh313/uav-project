# NATIVE94 — lập nhiệm vụ Android tại chỗ

18/10/2026. Authorized: vá gap lớn, rút ngắn tới sản phẩm. SPEC → BUILD → VERIFY do một agent thực hiện, không tuyên bố review độc lập.

## Vấn đề và quyết định

NATIVE93 có một model KML chung nhưng parser/compiler nằm ở laptop. APK mặc định không có token không khởi tạo được workspace. NATIVE94 đưa inspect/compile và kiểm nhập vào APK, giữ schema92 và đầu ra AUTO63. Bridge chỉ phục vụ SITL; trước connect phải biên dịch độc lập trên host và đối chiếu toàn bộ plan đã lưu. Không dùng local planning làm chứng cứ execution.

## Nghiệm thu

- R94-1: parser XML/KML có giới hạn byte/depth/node/feature/coordinate, từ chối declaration ngoài, malformed/namespace/geometry/datum không hỗ trợ. Đối chiếu document với Python kml51 trên corpus có ca xấu.
- R94-2: compiler Android không Node/Python/network; polygon/corridor, camera206 và Home/relative datum giữ đúng toàn bộ plan/hash so với AUTO63. Geometry dependencies sao byte-identical; ghi lineage.
- R94-3: offline APK mở/lưu/inspect/compile được, không có bridge/token; persistence sau force-stop và reboot. Không tự khôi phục quyền.
- R94-4: workspace nhập phải local recompile và khớp exact trước activation; mutation rehashed nhưng sai plan bị chặn.
- R94-5: SITL connect đòi host attestation khớp local committed model/plan; sai model/plan/revision không được connect; không tự cấp quyền/upload/arm/AUTO.
- R94-6: preservation tất cả manifest qua93; sàn20GiB; cleanup unsigned/.build của94.

## Phạm vi

Chỉ namespace native/native94, evidence/native94, delivery94, ADR109. Development APK riêng theo ủy quyền emulator hiện có. Không sửa source/candidate/ENDURE hay module trước. Không SDK/HeraHub/ký production. Không mở rộng synthetic-flat thành địa hình thực. Không tuyên bố thay Ragas hoặc đủ điều khiển Hera. SITL regression mới chỉ khi có ngân sách và cần để xác nhận delta; trường hợp không chạy phải NOT_CHECKED.
