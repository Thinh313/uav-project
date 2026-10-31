# Hai nhánh bàn giao và milestone runtime máy nhận

Anh giữ bản phát triển tại repo private `nclamvn/aeris`. Các em nhận bản nghiên
cứu public tại `nclamvn/uav-project`, với lịch sử Git độc lập. Hai repo đã có
snapshot source ở mốc chuyển giao; từ đây mỗi bên có thể phát triển trên branch
riêng, trao đổi thay đổi bằng diff/PR và ghi rõ revision, không ghi đè nhau.

## Các mốc cần dùng

| Vai trò | Repo và tag | Dùng để làm gì |
|---|---|---|
| Bản gốc tiếp tục phát triển | nclamvn/aeris, development-handoff-2026-10-31-r2 | Source và context private của anh; cần quyền truy cập |
| Bản giao nhóm nghiên cứu | nclamvn/uav-project, research-runtime-2026-10-31-r2 | Clone source, chạy mock và chuẩn bị runtime máy nhận |
| Gói dữ liệu riêng | UAV-PROJECT-PRIVATE-HANDOFF.tar và MILESTONE05 supplement | Context/BOM, artifact, APK/image và raw chẩn đoán; không upload public |

Các tag handoff và intake r1 cũ giữ nguyên. Source sản phẩm nền vẫn là mốc
6ea4f5027bc93d4f67e10da53c098391d9553f2f cùng source chưa tracked đã được kiểm kê.
R2 thêm công cụ tiếp nhận, cấu hình mẫu và hồ sơ kết quả, không thay code runtime,
source/candidate đóng băng, guard hoặc lịch sử ENDURE. Không ký phần mềm mới.

## Kết quả thực tế ở R2

Engineering alpha, beta tích hợp NOT READY. Runtime receiver đã dựng được với
2.628 dependency, giữ đủ sáu artifact pool và hardlink nội bộ. Công cụ mock đạt
15 bài kiểm; Node/Python intake và CI là bằng chứng riêng với runtime thật.

Lượt Android–SITL duy nhất đã qua admission metadata/artifact/disk và host prime
15 giây thực. Android, companion và ArduPilot khởi động; UI đi tới connect,
discovery và 39/39 tham số. Lượt dừng sau 129,571 giây host ở
PUBLIC_UI_WAIT_DISARMED_READ_ONLY_NAVIGATION_READINESS. Profile dự kiến 180 giây
chưa hoàn tất. EKF nhận 93 mẫu flags167(0xA7), thiếu vị trí ngang tuyệt đối;
pin mô phỏng 25,149–25,151V đạt ngưỡng. Guard preflight từ chối đúng.

Cold verifier giữ khớp 37.279 nhóm RX/INTENT/SENT/STAGE, unknown-send0. Recording
vẫn INCOMPLETE_RECORDING; AP-stage đủ byte riêng không là flight acceptance.
Không ARM, AUTO hoặc RC manual; encoder/publisher0frame, chưa nghiệm thu video.
Tài nguyên thuộc lượt đã đóng, không có secondary error ở owner.

Đây là kiểm trên máy tác giả với SDK/AVD cache được khai báo, chưa là kiểm độc lập
trên một máy nghiên cứu khác, Xiaomi, HeraHub hoặc payload thật.

## Nhóm bắt đầu

```sh
git clone https://github.com/nclamvn/uav-project.git
cd uav-project
git checkout research-runtime-2026-10-31-r2
git switch -c research/team-work
node tools/handoff/intake.mjs
python3 -B -m unittest discover -s handoff/receiver-runtime03/tests -v
```

Đọc capsule `handoff/receiver-runtime03/README.md` để profile/plan/prepare/check
runtime cô lập. Gói private gốc vẫn giữ source tại handoff ban đầu; helper mới
chạy từ clone R2 hoặc supplement, không suy ra gói cũ tự chứa code mới.

Tạo contract/profile/plan và workspace private ngoài Git. SDK/system image/AVD
không có sẵn trong repo. Baseline thực là macOS ARM64, CPython3.14, Node24,
Android API33/default/arm64-v8a rev2, emulator37.2.12, platform-tools37.0.1 và
Docker image Linux ARM64 có SHA đã khai báo. Máy khác cần intake cấu hình riêng.
Không app-clear/wipe/reset quota, khôi phục authority hoặc thay binary trong pin.

Chỉ mở owner gốc khi full preview và các live gate còn đạt. Slot lỗi s02 trong
máy kiểm đã được dùng và giữ lại; không xóa để thử lại. Các em tạo một campaign
mới được khai báo, kiểm mock/admission và giữ đủ bằng chứng trước lượt mới.

## Việc đầu tiên nên làm

Tái lập nguyên tag, phân tích GPS/Home, datum và clock/frame của nguồn sensor
đối chiếu EKF. Chứng minh nguyên nhân thiếu vị trí ngang tuyệt đối trước khi sửa.
Không coi việc tăng timeout hoặc một ACK là đã hội tụ/execution. R02 có source
chờ navigation60s nhưng chưa có candidate đủ điều kiện; không thế vào S01 ngầm.
Sau khi giải quyết blocker, chạy trọn workflow nhiệm vụ, video/payload, mất link,
reboot, persistence và SAF/receiver rồi mới xét beta simulator.

## Tính toàn vẹn và giới hạn dữ liệu

BOM, tài liệu khách hàng, raw log và artifact host thuộc gói private. Public chỉ
có code, cấu hình mẫu, summary và digest; không có credential hay khóa production.
Các nhãn khách hàng đã ẩn danh trước đây vẫn giữ, không nhập lịch sử Git private.
Raw lượt receiver05 được bổ sung riêng cùng manifest, không sửa gói391MiB gốc.

Checkout AERIS trên host còn 98 đường dẫn tracked thiếu đã ghi nhận từ trước.
Milestone không stage chúng thành deletion; Git snapshot giữ đúng blob HEAD.
272 file source chưa tracked đã được đối chiếu đúng byte với bản xuất và commit
vào bản phát triển private để một clone mới nhận đủ source. Việc này không khẳng
định các đường dẫn trên checkout cũ đã hiện diện liên tục hoặc đã được phục hồi.
