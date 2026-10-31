# UAV Project - AERIS research handoff

Bản chuyển giao nghiên cứu ngày **31/10/2026**, từ source commit
`6ea4f5027bc93d4f67e10da53c098391d9553f2f` và các file source chưa commit tại thời điểm bàn giao.

**Trạng thái: engineering alpha; beta tích hợp NOT READY.** Repo này là mã nguồn
và bộ hướng dẫn nghiên cứu, chưa phải bộ cài đã nghiệm thu để vận hành Hera thật.

AERIS hướng tới một hệ thống điều khiển UAV đa năng: khảo sát/inspection,
preflight, điều khiển manual/assisted/AUTO, camera/gimbal nhiều payload,
phân quyền operator, video, lưu hồ sơ và review. Chất lượng so với các GCS cao cấp
phải được chứng minh theo từng workflow, không suy ra từ số module hoặc giao diện.

## Đọc trước

1. [Anh gửi các em: hướng dẫn tiếp nhận](docs/handoff/HANDOVER.md).
2. [PDF chuyển giao chi tiết](output/pdf/UAV-PROJECT-HANDOVER.pdf).
3. [Hiện trạng và phần còn thiếu](docs/handoff/STATUS.md).
4. [Cấu trúc và đường chạy](docs/handoff/ARCHITECTURE.md).
5. [Cài đặt, kiểm thử và tái lập](docs/handoff/SETUP-AND-VERIFY.md).
6. [Phạm vi public/private và tính toàn vẹn](docs/handoff/CONTENTS.md).

## Clone đúng bản bàn giao

```sh
git clone https://github.com/nclamvn/uav-project.git
cd uav-project
git checkout research-intake-2026-10-31-r1
git switch -c research/my-work
```

Tag gốc `research-handoff-2026-10-31` được giữ nguyên. Tag intake r1 bổ sung
công cụ tiếp nhận và hướng dẫn; xem [biên bản INTAKE01](docs/handoff/INTAKE01.md).
Tag là mốc source bất biến để trao đổi kết quả. Không coi một nhãn READY trong
milestone lịch sử là nghiệm thu cho toàn bộ bản tích hợp hiện tại.

## Kiểm nhanh, không cần SDK, Android hay drone

Cần **Node.js 22+** và **Python 3.12+** trên PATH. Các lệnh đã được kiểm trên
macOS và CI Linux. Với Windows, nên dùng WSL/Git có symlink thật; bản clone
materialize symlink thành file văn bản không được xem là cùng cây source. Không cần `npm install` cho
các lệnh dưới đây. Chạy từ root repo:

Cách gọn, chạy tuần tự đúng sáu kiểm bên dưới và ghi public HEAD/version:

```sh
node tools/handoff/intake.mjs
```

Hoặc chạy từng lệnh để chẩn đoán:

```sh
node tools/handoff/verify.mjs
npm run check
node planning/vidlife12/runtime/tests/mock.mjs
node planning/vidlife12/runtime/tests/lifecycle-trace.mjs
node planning/vidlife12/runtime/tests/cold-navigation-r02.mjs
python3 tools/handoff/mock_wait.py
```

Đây là kiểm source/mock. Clock và telemetry của mock là dữ liệu kiểm tổng hợp,
không phải chuyến bay, đo FPS hay bằng chứng hội tụ EKF trên thiết bị thật.
Các suite gốc vẫn có trong source; đọc phạm vi và yêu cầu runtime trước khi chạy.
Bộ kiểm công cụ tiếp nhận: `python3 -m unittest discover -s tools/handoff/tests -v`.

Đã nhận gói private? Làm theo [kiểm và dựng workspace riêng](docs/handoff/SETUP-AND-VERIFY.md#4-workspace-riêng-cho-dữ-liệu-private).
Không giải nén vào clone public hoặc dùng manifest public để kết luận cây đã overlay private giống nguyên bản.

## Xem workbench web lịch sử

```sh
npm start
```

Mở `http://127.0.0.1:8788/`. Đây là workbench Plan/Fly/Review đời đầu; API SITL
tắt mặc định. Nó **không** tự khởi động cockpit Android mới nhất hoặc simulator 3D.
Nếu cổng đã được một phiên khác sử dụng, không tự dừng phiên đó.

## Android và SITL mới nhất

Đường mới nhất nằm tại `planning/vidlife12/`, sử dụng APK development được giữ
nguyên, companion Node, ArduPilot 4.7.1 và backend physics. Các artifact này cùng
log chẩn đoán được bàn giao bằng **gói private**, không nằm trong Git public.
SDK/AVD Android không được đóng gói. [Hướng dẫn](docs/handoff/SETUP-AND-VERIFY.md)
liệt kê SHA, cổng, điều kiện admission và các giới hạn máy/kiến trúc.

Lượt S01 đã xác nhận 9 ACK cadence và các mẫu telemetry sau ACK. Lượt này dừng
trước video vì EKF chưa có vị trí ngang tuyệt đối. Bản R02 chỉ tăng thời gian chờ
khởi tạo navigation 30 lên 60 giây host, đã qua mock nhưng **chưa chạy lại SITL**:
dự toán artifact vượt trần 8 MiB đúng 77.824 B. Không bỏ guard để đổi trạng thái này.

## Bản đồ repo

| Đường dẫn | Vai trò |
|---|---|
| `app/`, `services/`, `tools/` | Workbench web, compiler, API, truyền và lưu dữ liệu |
| `native/` | Source Android/WebView/bridge và các revision cô lập |
| `pilot/` | Adapter, payload, mô phỏng, viewer và các milestone R&D |
| `planning/vidlife12/` | Entry hiện tại, runtime source 117 file, mock, QA và contract |
| `planning/betasim-integrated01/` | Companion/product/video và nền tích hợp trước đó |
| `aeris_runtime/` | Namespace runtime lịch sử, không thay cho bản selected |
| `docs/`, `delivery/`, `research/` | ADR, roadmap, báo cáo và thông tin truy nguồn |
| `handoff/` | Manifest SHA của cây public và khai báo phạm vi |
| `output/pdf/` | PDF chuyển giao đã kiểm render |

Repo giữ nhiều revision có chủ đích. Entry point, source, APK, profile và chứng cứ
phải cùng một cấu hình; không ghép tùy ý các file có tên mới nhất.

## Phạm vi bàn giao

- Source public gồm snapshot Git hiện tại và source chưa commit được kiểm kê.
  Các file thiếu ở checkout cũ được xuất từ Git vào bản mới, không phục hồi/ghi lại
  dự án gốc. Năm symlink source tương đối được giữ và kiểm đích.
- BOM, context nội bộ, tài liệu khách hàng và raw web inputs nằm trong gói private.
  Chín file public chỉ được ẩn danh nhãn khách hàng; bản gốc đi kèm overlay riêng.
  Không chỉnh các source của đường VIDLIFE12 154 pins để làm đẹp kết quả.
- Raw của các lượt chẩn đoán gần nhất, candidate pools, APK và image SITL ARM64
  đi trong bộ engineering private. Đây không phải toàn bộ ổ đĩa hay mọi raw log
  lịch sử; [danh mục](docs/handoff/CONTENTS.md) ghi rõ phần chưa đóng gói.
- Clone public đủ để review và chạy mock đã nêu. Chạy lại Android-SITL cần thêm
  bộ private, SDK/AVD đúng cấu hình và admission mới. Đối chiếu checksum không
  biến kết quả cũ thành một chuyến bay đã nghiệm thu trên máy mới.

## Đóng góp và giấy phép

Xem [CONTRIBUTING.md](CONTRIBUTING.md) và [NOTICE.md](NOTICE.md). Không thêm
credential, BOM, hồ sơ khách hàng hay artifact private vào pull request.
Public repository không tự tạo giấy phép open-source mới cho code RtR.
Giữ các giấy phép và attribution của thành phần bên thứ ba.

Lịch sử README trước chuyển giao nằm tại
[docs/HISTORY-README-2026-10-31.md](docs/HISTORY-README-2026-10-31.md).
Các đường dẫn máy cũ và hướng dẫn cũ trong tài liệu đó chỉ là hồ sơ lịch sử.
