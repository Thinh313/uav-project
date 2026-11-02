# UAV Project / AERIS - H10 research handoff

Bản bàn giao nghiên cứu ngày **02/11/2026**. Tag bất biến:
[`research-handoff-2026-11-02-h10`](https://github.com/nclamvn/uav-project/tree/research-handoff-2026-11-02-h10).
Bản gốc private của anh tiếp tục tại `nclamvn/aeris`, tag
`development-handoff-2026-11-02-h10`. Hai repo có lịch sử riêng; các tag cũ giữ nguyên.

**Engineering alpha. Beta tích hợp NOT READY; G1-G4 chưa được nghiệm thu.**
Đây là mã nguồn, công cụ và hồ sơ để tiếp tục R&D. Chưa phải bản cài đã nghiệm thu
để vận hành Hera thật và chưa có bằng chứng so sánh vượt DJI.

## Các em đọc trước

1. [Anh gửi các em: tiếp nhận H10](docs/handoff/HANDOVER.md).
2. [PDF chuyển giao hiện tại](output/pdf/UAV-PROJECT-HANDOVER.pdf).
3. [Hiện trạng, bằng chứng và giới hạn](docs/handoff/STATUS.md).
4. [Kiến trúc và ranh giới pipeline](docs/handoff/ARCHITECTURE.md).
5. [Cài đặt và kiểm lại](docs/handoff/SETUP-AND-VERIFY.md).
6. [Public/private, manifest và phần không được đóng gói](docs/handoff/CONTENTS.md).
7. [Hai repo và định danh H10](docs/handoff/MILESTONE06-H10.md).
8. [Milestone tiếp theo](docs/handoff/NEXT-MILESTONE.md) và [biên bản tiếp nhận](docs/handoff/ACCEPTANCE.md).

## Clone đúng mốc

```sh
git clone https://github.com/nclamvn/uav-project.git
cd uav-project
git checkout research-handoff-2026-11-02-h10
git switch -c research/team-work
git rev-parse HEAD
```

Ghi commit thực nhận, không dùng source baseline private làm public HEAD.
Manifest `handoff/SOURCE-MANIFEST.json` đối chiếu các file public được liệt kê;
không coi một workspace có overlay private là cùng cây public nguyên byte.

## Bắt đầu không cần Android hoặc drone

Cấu hình mới đã kiểm trên máy tác giả: Node **24.14.1**, CPython **3.14.6**,
macOS ARM64. Với hệ khác, ghi đúng phiên bản và kết quả của máy nhận.
Không cần `npm install` cho các kiểm source/mock được nêu. Windows nên dùng WSL
và Git có symlink thật.

```sh
node tools/handoff/verify.mjs
npm run check
python3 -B tools/handoff/h10_intake.py
```

H10 portable chọn 13 phương thức kiểm từ source hiện tại, dùng Node 24+ và Python
3.12+; version đã kiểm thực là Node24.14.1/Python3.14.6. Wrapper có path adaptation
chỉ cho test và media fixture synthetic/derived thay input private g105, giữ code
sản phẩm nguyên bản. Có codec/Root reconstruction, Node-Python writer IPC/fsync,
managed close và biên cap20/100MiB. Đây không phải toàn bộ 34 kiểm gốc hoặc nghiệm
thu runtime. Fixture và mock RPC không là dữ liệu bay hay qualification thiết bị. Các `test-*.py` gốc trong runtime H10 còn cần fixture
private/đường dẫn đã kê khai; public clone không tự tái lập 34 kiểm host-coupled.

Bộ intake lịch sử vẫn có:

```sh
node tools/handoff/intake.mjs
python3 -B -m unittest discover -s handoff/receiver-runtime03/tests -v
```

Hai lệnh này kiểm đường VIDLIFE12/R2 và capsule cũ theo contract của chúng.
Chúng không tự chọn H10, không sửa cap của candidate cũ và không chạy simulator mới.
`npm test` là suite lịch sử rộng hơn, có các điều kiện fixture/timing/dung lượng;
không công bố toàn suite xanh chỉ từ các kiểm source ở trên.

## H10 đã đạt gì

- H8 và H9 có bốn lượt SDK cold boot thực đã kiểm APK/private state và đóng bình thường.
- H9 sửa alias giữa graph source và Node loader. g105 đã qua companion READY,
  đăng ký native và rollover, rồi FAIL tại kết quả SEAL_PRODUCT vượt progress4KiB.
- H10 tách full result thành dữ liệu bền vững có tham chiếu SHA/context; progress
  giữ 4 KiB. Normal writer closure dùng chung deadline RPC200ms, không che EOF/lỗi.
- 34 phương thức source/mock trên máy tác giả đạt, gồm Node client -> Python writer
  Unix RPC/fsync -> Root reader với metadata budget mock. Chưa thay G1 Android thực.
- m801 forensic thực thu raw 250.880 B, SDK đóng bình thường. Đối chiếu riêng có
  83 file/9 thư mục, lifetime generation10, hai journal đóng/rỗng, tám archive,
  không pending. Đây không phải SDK qualification, G1 hoặc một chuyến bay.

Artifact tổng **20 MiB**, metadata tổng **100 MiB** đã được chấp thuận cho bản cô lập.
Freshness250ms, HostHealth100ms, writer200ms, native/export quota, speedup1/cap500ms
và sàn đĩa10GiB cộng reserve/forecast giữ nguyên. Mỗi lượt vẫn phải admission mới.

Điểm tiếp tục là contract cho trạng thái83file. Không dùng decoder75file, không
retry g103 APPLY, tự archive hoặc khôi phục quyền từ một receipt forensic.
Sau G1 mới là polygon/corridor Android-SITL cùng video/payload, mất link/reboot,
persistence/SAF và 600 giây bay tích hợp liên tục.

## Runtime, APK và dữ liệu riêng

Git public chứa source, hướng dẫn và công cụ portable. Raw, candidate pool,
engineering APK, AP binary và image đã kê khai được giao riêng; SDK/AVD/cache
không được đóng gói. Cần supplement H10 và manifest/checksum tương ứng, không coi
gói private cũ tự có dữ liệu mới. [Hướng dẫn tiếp nhận](docs/handoff/SETUP-AND-VERIFY.md)
phân biệt kiểm byte, replay, admission và runtime thực.

Không overlay BOM, tài liệu khách hàng, credential hoặc raw vào clone dùng để push.
Không tự sửa raw/candidate lịch sử, reset app/counter/quota hoặc cài binary thay pin.
HeraHub, Xiaomi, radio/MCU, Phase One/RGB/thermal và gimbal thật còn gate riêng.

## Bản đồ source

| Đường dẫn | Vai trò |
|---|---|
| `app/`, `services/`, `tools/` | Workbench lịch sử, compiler, storage/API và kiểm |
| `native/` | Source Android/cockpit/bridge, các revision và journal native |
| `planning/betarc01/runtime-h10/` | Source H10 được chọn, test/contract và các entry đã pin |
| `planning/betarc01/command_h10/` | Companion và đường kết quả lossless |
| `planning/betarc01/node_alias_h9/` | Loader source-bound dùng chung |
| `planning/nativejournal17/` | Native journal, archive/receiver và kiểm nguyên bản |
| `pilot/` | Mission, payload/operator, MAVLink, physics/3D và corpus |
| `docs/handoff/`, `handoff/` | Hồ sơ chuyển giao, manifest và công cụ tiếp nhận |
| `output/pdf/` | PDF chuyển giao đã kiểm render |

`npm start` mở workbench đời đầu trên `http://127.0.0.1:8788/`, API bay tắt mặc định.
Nó không khởi động cockpit Android H10 hoặc simulator 3D mới nhất. Không dừng một
phiên khác để giải phóng cổng. Các revision giữ có chủ đích; đọc contract trước launch.

## Đóng góp, lịch sử và giấy phép

Xem [CONTRIBUTING.md](CONTRIBUTING.md), [NOTICE.md](NOTICE.md) và
[phạm vi nội dung](docs/handoff/CONTENTS.md). Public repository không tự cấp license
open-source mới cho code RtR; giữ attribution/giấy phép của thành phần bên thứ ba.

[INTAKE01](docs/handoff/INTAKE01.md), [MILESTONE05](docs/handoff/MILESTONE05.md) và
README lịch sử là hồ sơ mốc31/10. Các kết luận EKF/cap/entry trong đó không là
kết luận mới của H10. [Tin nhắn bàn giao](docs/handoff/MESSAGE-TO-TEAM.md) dùng để
anh gửi các em cùng đúng tag và bộ dữ liệu riêng.
