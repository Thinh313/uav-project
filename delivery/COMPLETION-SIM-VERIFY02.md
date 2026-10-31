# SIM-VERIFY02: kiểm gói bàn giao trên Android và SITL

**Trạng thái: NOT READY. Chưa nghiệm thu để bên nhận tự vận hành trọn chuyến bay.**

Đã cài APK engineering lên emulator-5582, mở cockpit và observer 3D trong Android WebView, rồi khởi động ArduPilot 4.7.1 với physics tham chiếu thật. Đây là bước tiến từ kiểm cấu trúc gói sang kiểm chạy thực. Chưa thực hiện cất cánh hoặc điều khiển manual trong lượt này; không có bằng chứng bay để thay cho phần còn thiếu.

## Những thay đổi đã thực hiện

Các thay đổi chỉ nằm trong các bản nhận cô lập dưới `.local/simverify02`, không sửa source SIM-HANDOFF01 gốc, candidate, canonical hoặc ENDURE.

1. Sửa chuẩn hóa đường dẫn gốc: dấu `/` cuối đường dẫn làm kiểm containment từ chối file hợp lệ bằng lỗi `BUNDLE_PATH`. Giữ kiểm chống thoát đường dẫn, sai SHA và symlink.
2. Bổ sung đúng ba route font Barlow trong gói. Không mở fallback phục vụ file tùy ý.
3. Sửa dispatch nút LAND để vẫn gửi yêu cầu khẩn khi giao diện đang chờ một thao tác khác. Ba ca mock đạt; chưa chứng minh LAND thực thi trên chuyến bay.
4. Bổ sung `integrator.c` còn thiếu trong dependency closure bằng đúng byte SHA gốc. Không đổi phương trình vật lý.
5. Chuẩn bị file mountpoint rỗng, không executable tại `runtime/sitl/arducopter`, để Docker có thể chồng binary đã khóa SHA lên thư mục chỉ đọc. Mount thực tế của binary và thư mục đều có `RW: false`.

Gói engineering sửa lỗi được lưu riêng trong `delivery/sim-verified02`. Tên thư mục không có nghĩa đã nghiệm thu chức năng; trạng thái gói vẫn là NOT READY. APK, chứng thư development và gói gốc được giữ nguyên.

## Kết quả kiểm

| Hạng mục | Kết quả | Phạm vi bằng chứng |
|---|---|---|
| Gói gốc đúng byte/hash | PASS về byte | Gói vẫn không khởi động được nguyên trạng vì lỗi đường dẫn. Doctor PASS không thay kiểm chạy thực. |
| Host sửa lỗi, APK cài và mở cockpit | PASS | Emulator Android do tác vụ sở hữu; chưa có Xiaomi hoặc HeraHub. |
| Firmware và telemetry | PASS trong lượt quan sát | AP system/component 42/1, ArduCopter 4.7.1, GPS/EKF/Home và bốn tham số đúng kiểu đã được quan sát. |
| Physics và AP trao đổi sensor | Có bằng chứng thực | 231.613 frame liên tiếp; kiểm CRC/chuỗi SHA và tương quan AP được ghi ở raw-audit01.json. Không có WAL CLOSE, nên chỉ là prefix toàn vẹn của lượt thất bại. |
| Pacing 1× | FAIL | 193,011 giây mô hình trong 209,799 giây host, RTF khoảng 0,920. Speedup vẫn 1, cap vẫn 500 ms. |
| Preflight UI | PARTIAL | Mở được, cuộn được đến checkbox/xác nhận/cất cánh. Chưa duyệt và cất cánh trong thời hạn phiên. |
| Manual → LAND/disarm → review | NOT RUN | Không gửi ARM; không dùng ACK hoặc hoạt cảnh để suy ra bay. |
| Kết thúc sau phiên hết hạn | FAIL | Nút Kết thúc phiên trả `FRESH_OBSERVED_SESSION_REQUIRED`; link chết chưa được giải phóng để mở phiên mới. |
| Observer 3D | PASS về render emulator | GLB/HDR/PBR và màn trạng thái stale đã hiển thị. Chưa chứng minh scene theo drone đang bay hoặc GPU laptop/máy chiếu. |
| Âm thanh | NOT CHECKED thực tế | Chưa nghe/đo âm thanh khi bay hoặc đo mute sau mất nguồn trên một phiên đang bay. |
| SAF export/import của hồ sơ chuyến bay | BLOCKED | Chưa có hồ sơ thực thi đóng hợp lệ. Không xuất metadata rồi gọi đó là kiểm raw đầy đủ. |
| Restart và thu hồi quyền khi đang điều khiển | NOT RUN | Không tự nối lại hoặc khôi phục quyền. Cần lượt nghiệm thu riêng sau sửa lifecycle. |

Lượt thực: `rfebb3af9a261492cabd8`, session `20db2511-1e97-4259-be91-af90bd914819`, boot `b2f1c857-a4b9-42ee-82cd-110a9ca19cc7`. Backend dừng với `PROBE_DEADLINE`; runtime ghi `UNREQUESTED_BACKEND_END_OR_DEADLINE`. Đây là lượt thất bại, không phải kết thúc nhiệm vụ thành công.

## Lỗi phải sửa tiếp theo

**P1: lifecycle phiên thất bại.** Khi controller/backend kết thúc, phải thu hồi quyền, đóng transport và ghi hồ sơ thất bại bền vững. Không yêu cầu physics còn fresh để lưu sự cố đã mất nguồn. Cho phép một phiên mới chỉ qua thao tác rõ ràng sau closure, không tự retry, không khôi phục quyền.

**P1: trạng thái lỗi còn sót.** `lastError` vẫn hiển thị lỗi launch trước trong khi phiên mới đã có telemetry. Cần lỗi gắn run/session và phân biệt lỗi hiện tại với lịch sử.

**P1: hợp đồng thời hạn không thống nhất.** Policy recipient ghi `apSeconds: 300`, projection đọc `maxAPSeconds` nên rơi về 210 giây; UI cũng đếm 210 giây từ trước admission. Phải thống nhất tên trường và mốc bắt đầu, chừa thời gian LAND/closure rõ ràng. Chưa thay thời hạn hoặc chạy lại để lách kết quả thất bại.

**P1: pacing và đóng journal.** Đo tiếp nguyên nhân RTF 0,920; bảo toàn đủ frame, fsync trước sensor, speedup 1 và cap 500 ms. Ghi manifest prefix thất bại hợp lệ thay vì giả WAL CLOSE thành công. Chưa có đủ bằng chứng kết luận bottleneck.

**P2: bố trí preflight.** Panel cuộn được, nhưng ở 1280×800 các nút cuối không xuất hiện ngay và thông báo nằm gần cạnh panel. Cần thể hiện vùng cuộn và trạng thái thao tác rõ hơn. Không kết luận nút mất hoặc không thể tiếp cận.

Sau sửa lifecycle và mock/fault injection, kiểm một lượt gọn trên APK: refresh preflight → xác nhận Home → takeoff → neutral claim → pitch/yaw nhỏ → release/background → LAND/disarm → review → SAF export/import. Chỉ sau đó mới mở rộng tải/gió, Xiaomi và trình chiếu. AUTO/KML/payload không có đường thực thi trong gateway này và không thuộc nghiệm thu manual hiện tại.

## Bảo toàn và đóng tác vụ

- Đối chiếu 17.117 identity lịch sử, 76 entry SIM-HANDOFF01 và 258 entry BETA-VIDEO03: không phát sinh drift. 165 đường dẫn đã thiếu từ baseline vẫn được ghi là thiếu; không khẳng định hiện diện liên tục hoặc phục hồi chúng.
- ENDURE không bị sửa và không được nghiệm thu lại trong tác vụ này. Gói gốc giữ SHA `6b36304d31554f32299021feb3cde770bbad31168ab093f08a9cac741fc3bfd3`.
- Host dừng theo launcher, exit 0. Watcher emulator phát hiện executable chuyển từ launcher sang QEMU nên từ chối tự kill; đã giữ log lỗi, xác minh đúng PID/start time/AVD/port và đóng emulator qua ADB. Không thao tác thiết bị thật.
- Không build APK, tải SDK/dependency/asset hoặc ký mới. Không xóa container, volume hay raw evidence. Docker image prune thu hồi 0 byte; không có bản sao dự án trong `/tmp` hoặc distDir mới cần dọn.
- Gate 20/10 GiB và guard được giữ. Kiểm cuối còn khoảng 24 GiB trống. Các recipient và raw được giữ làm hồ sơ, không phải scratch bị bỏ quên.

Đã chạm giới hạn sửa và host start trong TIP. Theo [Vibecode Kit v6.3](/Users/os/.codex/skills/vibecode-kit/SKILL.md): “Hết ngân sách hoặc không tăng giá trị: nêu evidence và lựa chọn, không tự tuyên bố hoàn tất, hạ quality floor hoặc đổi scope âm thầm.” Do đó dừng lượt này với NOT READY, không kéo dài runtime hoặc đánh dấu hoàn tất.

## Bằng chứng chính

- `evidence/simverify02/preservation-final01.json`
- `evidence/simverify02/raw-audit01.json`
- `evidence/simverify02/path-tests01.json`
- `evidence/simverify02/ui03-fix-tests01/land-busy.json`
- `evidence/simverify02/end04c-console.json`
- `evidence/simverify02/emulator-closure02.json`
- `.local/simverify02/receiver04/evidence/simhand01/runs/rfebb3af9a261492cabd8/`

**Giá trị đã chứng minh:** tìm và sửa các lỗi chỉ xuất hiện khi bên nhận chạy gói thực; xác nhận APK và AP/physics có thể kết nối trong môi trường này. Chưa chứng minh hoàn thành chuyến bay manual, trải nghiệm huấn luyện hoặc thay thế Hera thật. Đối chứng LLM không áp dụng cho phép kiểm deterministic này; không có claim vượt DJI hoặc chứng nhận thương mại.

## Gói chẩn đoán được chọn

Chỉ chọn `delivery/sim-verified02/AERIS-SIM-VERIFY02-DIAGNOSTIC02-NOT-READY.tar.gz`, SHA `4c0794f432b26afab8f6f733ecca5a4da8f9c67c4e91abef68efaf5f454322a7`. Gói gồm 112 member thường, checksum manifest đúng wire 65 byte và dependency closure có mountpoint. Contractor đã đối chiếu toàn bộ member và parser contract. Đây là kiểm cấu trúc, không nghiệm thu chức năng. Attempt01 được giữ nguyên và bị loại do checksum không tương thích parser; không dùng receipt PASS về byte của attempt01 để suy ra có thể khởi chạy. Xem `LATEST-DIAGNOSTIC.json`, receipt loại attempt01 và `contractor-archive-verification02.json`.
