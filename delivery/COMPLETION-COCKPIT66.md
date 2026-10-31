# COCKPIT66 — cockpit native dùng CYBER65

**Trạng thái: READY_HOST_BROWSER_MOCK. Android compile/runtime, HeraHub, Phase One thật và hai trạm operator thật: NOT_CHECKED.**

Đã triển khai trong `native/cockpit66`, evidence riêng `evidence/cockpit66`. Không sửa source/candidate đóng băng, CYBER65 gốc, SOT hoặc lịch sử ENDURE. Không build APK, ký, chạy SITL/emulator/soak, cài dependency hay dùng SDK. Preview bàn giao: **http://127.0.0.1:8821/** — PID46109, static GET-only loopback.

## Kết quả trong phạm vi được phép

| Yêu cầu TIP | Kết quả kiểm |
|---|---|
| N66-01 portable CYBER65 | 16 file có derivation/source SHA/derived SHA, thay thế Node crypto/byte length/đọc corpus giới hạn; Node đối chiếu đủ44 digest exact |
| N66-02 cockpit/chọn payload | Phase One, Thermal, Corona; LiDAR ghi chưa có adapter và khóa. Chọn nguồn và đổi góc nhìn không cấp quyền. Barlow tiếng Việt; nền trắng, graphite, vàng phụ |
| N66-03 bàn giao hai operator | Nhận/trả/bàn giao camera+gimbal theo bộ, khóa khi chờ, đúng người nhận xác nhận. Từ chối/hết hạn/mất operator/link/focus thu hồi quyền; lỗi scope thứ hai không để quyền một phần |
| N66-04 lệnh/review | CYBER65 portable xử lý capture/zoom/focus/gimbal; ACK-only/sai mục tiêu không thành bằng chứng thực thi. Metadata mô phỏng không chứng minh exposure/file; ảnh thực0 |
| N66-05 workspace | Tape/review capsule có SHA và semantic replay, transactional CAS, quota16 revision/512KiB mỗi capsule, không tự xóa. Lost commit reply giữ bản ghi, khóa quyền và yêu cầu đọc lại. Reload/restarter preview giữ lựa chọn và lịch sử đã lưu, không khôi phục quyền |
| N66-06 native preparation/QA | Activity/manifest/whitelist và lifecycle revocation source, không bridge radio/flight hoặc external/file navigation. Host/browser QA đạt; actual Android behavior chưa kiểm |
| N66-07 preservation/resource | 24.565 đường dẫn bảo vệ khớp SHA; kiểm riêng ENDURE5.051 đường dẫn khớp (không cộng hai tập thành số file duy nhất). Không thiếu/dataless. Cuối kiểm còn23,73GiB, trên sàn20GiB; phần mới dưới32MiB |

## Bằng chứng định lượng

- Model27/27, comparator8/8, regression CYBER65 gốc33/33; portable Node corpus44/44 exact. Tổng112 ca thuộc bốn nhóm này; không cộng lại corpus browser như coverage độc lập.
- Browser22 quan sát đạt, giữ1 attempt parity chưa đạt trong lịch sử. Corpus browser44/44 tương thích gồm **42 digest exact +2 roundoff**, không phải44 digest giống nhau. Quan sát persisted workspace rev4 sau cold restart, không quyền và không kết nối.
- Bố cục cuối tại1280×800,1024×768,390×844: không tràn ngang, nút tối thiểu44px, nhóm payload đồng đều76px, cặp nút cùng hàng/cỡ. Header desktop56px; màn hình hẹp tự xuống hàng. Viewport đã reset. Ảnh bàn giao và ảnh màn hình hẹp trong evidence.
- Host static43 kiểm, XML/native-source4 kiểm, HTTP preview31 kiểm đạt. Static Java delimiter/source kiểm không phải compile/type checking/ART hoặc kiểm isolation trên Android.

Browser có hai ca gimbal khác góc pitch/yaw diễn giải tối đa1,1102230246251565e-16rad so với Node. ADR082 cho phép comparator whitelist đúng các trường này ở≤1e-12rad; raw/command/identity/owner/time và mọi trường khác vẫn exact. Giữ cả SHA và diagnostic gốc. Kiểm đối kháng từ chối đổi raw, command, quyền, timestamp, nonfinite và vượt bound. Đây là tiêu chí số học engineering, không phải độ chính xác gimbal vật lý hay tiêu chí khách hàng. Workspace hash/replay vẫn strict; migration giữa engine hoặc đổi WebView chưa nghiệm thu, có thể bị chặn và giữ dữ liệu.

## Giới hạn và bước kế tiếp

Hai operator hiện là hai góc nhìn trong một mock GCS, chưa có authentication/distributed arbitration hoặc hai tay cầm. Clock tiến theo bước, không chứng minh timeout real-time. Quyền bay chỉ trừu tượng, không có lệnh bay. Quarantine CYBER65 cho một lần mỗi khóa lệnh/phiên; không phải luồng điều khiển liên tục. Hình công trình tổng hợp không phải video/3D mô phỏng; thông tin Phase One thật vẫn unknown.

Persistence là thao tác lưu explicit; sự kiện chưa lưu còn volatile, không phải durable command journal. Android wrapper còn gate build/runtime/lifecycle/storage/input/video. Không suy ra đã cài hoặc điều khiển được Hera từ kết quả này. Kiểm toàn vẹn hiện tại không chứng minh các đường dẫn đã hiện diện liên tục hoặc ENDURE đạt24h.

Tiếp theo review luồng với kỹ sư, chốt model/API Phase One và contract quyền hai trạm; sau ủy quyền build và headroom phù hợp mới kiểm Android/emulator rồi HeraHub, trước khi nối transport thật. Roadmap overlay riêng: `delivery/ROADMAP-COCKPIT66.md`.

Receipts canonical: `verification.json`, `source-pins-final.json`, `derivation.json` trong namespace source, `browser-qa01.json`, `model-unit04.txt`, `numeric-unit03.txt`, `portable-parity01.json`, `cyber65-regression01.txt`, `technical-health02.json`, `native-source-qa01.json`, `http-qa02.json`, `preservation-after.json`, `artifact-fingerprints.json`. Các attempt cũ vẫn nguyên: layout ban đầu, cold-select incident/source snapshot, browser parity42/44, numeric fixture lỗi, static lexical và HTTP Host-driver attempt. `qa-driver-incidents.json` ghi cách sửa driver; không thay receipt cũ thành PASS.

Không tạo scratch/dependency/build copy trong tmp và không xóa dữ liệu. Snapshot source trước sửa giữ có chủ đích làm bằng chứng sự cố. Preview được giữ làm deliverable; chỉ phục vụ mock cục bộ.
