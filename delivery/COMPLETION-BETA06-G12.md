# BETA06 G12: AUTO đầu đạt, campaign NOT READY

Ngày 23/10/2026, giờ Việt Nam. Kiểm native Android cô lập với ArduPilot SITL thực, video nguồn host tổng hợp và payload mock. Không dùng HeraHub, camera thật, APK mới hay chữ ký mới.

## Kết quả

Bản sửa thiếu `import os` đã ghép, qua kiểm source/mock độc lập và chạy đúng hai khoảng ground thực trên 75 giây. Campaign mới chỉ có một controller, một host, một boot Android và hai phiên AP. Người dùng cho phép chạy bằng pin; ngoại lệ này được ghi riêng tại `delivery/G12-POWER-AUTH-20261023.md`. Không thay các ngưỡng dung lượng, thời hạn, quota hoặc quyền.

**N1 đạt:** cockpit Android thực hiện preflight, upload/readback, bay AUTO, điều khiển gimbal mock và lưu một ảnh tổng hợp, sau đó hoàn tất nhiệm vụ, về mặt đất, disarm và đóng review. QA độc lập kiểm raw MAVLink, chuỗi WAL, camera command, media, tương quan payload, index và closure container.

**F1 không đạt điều kiện để bay:** sau discover/select payload, heartbeat Android vượt deadline; phiên local dừng, viewer bị hủy request và host thu hồi quyền. Ca này chưa gửi ARM/AUTO hay lệnh ngắt link/reboot. Root dừng campaign, không chạy lại và không cộng kết quả các thế hệ trước.

| Hạng mục | Kết quả | Phạm vi chứng minh |
|---|---|---|
| Source/mock và sửa ground `os` | PASS | Gate đã đóng băng trước chạy; không vá source đang chạy |
| Hai khoảng ground thực | PASS | 75,224 và 75,282 giây, không phải thẩm quyền bay |
| N1 AUTO và upload/readback | PASS | 12 item upload, 24 item readback qua hai vòng; bốn camera command 206; không PARAM write |
| Video N1 | PASS cửa sổ chọn | 874 mẫu / 30.001,8 ms: 29,1316 fps; P95 upper 48,771 ms |
| Viewer ready / gián đoạn relay 500 ms | PASS | Ready 272,7 ms theo cấu hình hiện hành; phục hồi 571,5 ms, không chứng nhận mọi cold-start |
| AUTO đồng thời payload | PASS tại các điểm quan sát | 74 điểm quan sát, hai sự kiện payload AUTO hợp lệ; không suy ra thời lượng bay liên tục của toàn cửa sổ |
| Ảnh và định vị | PASS lưu tham chiếu mô phỏng | `actualImages: 0`; vị trí tham chiếu host, không đồng bộ exposure và không đủ chuẩn khảo sát |
| F1 mất link chủ động khi bay | NOT RUN | Lỗi heartbeat trước ARM; raw còn nguyên, review chưa hoàn tất |
| Managed restart host, N2, F2 reboot AP | NOT RUN | Không mở host thứ hai hoặc AP bổ sung |
| Cold persistence boot25 | NOT RUN | Không mở boot thứ hai |
| Snapshot Native sau thử | PARTIAL | Giữ được journal 15.467 byte đúng prefix/hash; không có snapshot SHA đầy đủ của 19 file sau thử |

## Chẩn đoán có chứng cứ

Heartbeat request **1103** mất **1.173,4 ms**, vượt deadline **1.000 ms**, với lỗi `LIFECYCLE_REQUEST_DEADLINE`. Request 1102 trước đó ACK trong 27,3 ms. Tại lỗi, `desiredForeground` và `nativeForeground` vẫn true, `documentHidden` false; local session chuyển false. Raw ghi `CLIENT_HEARTBEAT_EXPIRED`, không tự khôi phục quyền. Telemetry AP vẫn có dữ liệu DISARMED; không có ARM, AUTO hoặc fault intent trong phiên F1.

Nguyên nhân khởi phát **UNKNOWN**. Khoảng trễ event loop host khoảng 1.010,84 ms và timer client bị trễ là dấu hiệu tương quan; chưa đủ để quy lỗi cho filesystem, HTTP, CPU, pin hay Android. Không nới timeout để đổi kết quả.

Sau lỗi, thao tác chuyển tab để đóng phiên bị guard từ chối `FOREGROUND_OBSERVATION_REQUIRED` trước khi gửi input. Root dừng publisher qua UI, rồi kết thúc controller để đóng đúng host, AP và emulator sở hữu. Không kích hoạt lại phiên điều khiển nhằm tiếp tục ca đã lỗi.

Root đã truyền đường dẫn tương đối ở tham số `beforeReceipt` của lần thu snapshot sau thử. Helper ghi được journal trước khi từ chối phép `relative_to(R)`; không ghi receipt snapshot đầy đủ. Giữ phần thu được và lỗi nguyên trạng, không ghi đè hoặc chạy lại. QA xác nhận journal giống trước thử: 34 record, 13 pending, append0. Điều này không chứng minh toàn bộ file AVD không đổi hoặc persistence sau reboot.

## Đóng phiên và bảo toàn

QA cuối xác nhận **10.217 đường dẫn bảo vệ, 7 symlink, 1.141 pin, 25 helper và 6.198 entry lịch sử** đúng mode/byte/SHA/link literal. Blob gốc closed-G5 và prefix WAL của fork dữ liệu giữ nguyên; journal ứng dụng được phép append 23.462 byte. 95 đường dẫn thiếu đã biết và sự cố khôi phục 125 đường dẫn trước đây vẫn là giới hạn riêng, không được biến thành tuyên bố toàn repo đầy đủ hoặc hiện diện liên tục.

Hai AP/container đều đã đóng, giữ container và bằng chứng; exit0, không OOM. Emulator PID35056 có closure exit0/error null. Controller PTY session52871 exit0 được quan sát. Host PID34647 và helper PID34741 không có exit số được ghi riêng: **NOT_RECORDED**, không suy từ EOF hoặc PID đã biến mất. Cả bốn PID và các cổng 8872/8873/5972/5582/5583 không còn hoạt động theo kiểm đóng phiên.

Dung lượng tối thiểu quan sát **37.040.041.984 byte, khoảng 34,496 GiB**, trên sàn 20 GiB. Không sửa source/candidate đóng băng, ENDURE, trust hoặc canonical SOT; không build, cài hay ký mới. Docker image prune theo quy định trả 0 B; không xóa container, volume hoặc dữ liệu khác. Không tạo bản sao toàn project ngoài repo. Scratch `evidence/beta06/generation12/codex-tmp-g12-binding-20261023-753_vl_p` đã được dọn trước campaign; không có scratch mới cần giữ ngoài repo.

## Bằng chứng chính

- Source/mock: `evidence/beta06/generation12/qa-final-gate01.json`, SHA `b10bc284f1f9a8610e57eeb4fcdc8eddc5930e604f4a038883ba8d915d1a2e1c`.
- N1: `qa-n1-raw01.json`, `qa-n1-media01.json`, `qa-n1-overlap01.json`, `qa-n1-index01.json` trong generation12. Index SHA `8f3ea9ec059de591c2832458d02020fe63ac70af11fd587d3580416d0106f749`.
- F1: `qa-f1-fault01.json`, SHA `f822d2294a30583ce1a496dc646a76349b5f8d7a9dbc9f26bf127c7459cbfe04`; `qa-f1-raw01.json` chỉ PASS tính toàn vẹn của thực thi chưa hoàn tất.
- Native partial: `qa-native-prefix01.json`, SHA `3e391a0ee64d34abb8ed70a0e9f7e31abeced1bd42e35f95a036ec9d114ec5c5`.
- Root closure: `qa-closure-summary01.json`; QA cuối: `qa-final-runtime-summary01.json`, SHA `c931e90ac30a36fc27ee49a977f2d32c2902023083552cf8adab2ddd47560c7d`.
- `qa-final-completion01.json` và báo cáo PRELAUNCH là trạng thái lịch sử trước chạy, giữ nguyên; nghiệm thu thực tế được ghi thêm, không sửa các receipt đó.

![N1 đã thu xong cửa sổ video trong cockpit Android](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation12/g12-n1-completion.png>)

![Lỗi phiên foreground và viewer được giữ lại trước đóng](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation12/g12-failure-cleanup-p.png>)

![Nguồn publisher đã dừng](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation12/qa-browser-stopped.png>)

## Bước tiếp theo

Ưu tiên tái hiện heartbeat deadline bằng mock/fault injection, đo tách timer client, thời gian vào/ra HTTP host và event loop, giữ nguyên điều kiện thu hồi quyền. Sửa bộ gọi snapshot để dùng đường dẫn tuyệt đối và kiểm failure/finally trước khi mở campaign mới. Chỉ sau source/mock đạt mới có một lượt admission mới cho mất link, restart host, reboot AP và cold persistence; không tiếp tục G12 hoặc tự mở G13 trong nhiệm vụ này.

**OVERALL STATUS: NOT READY** cho milestone Android–SITL trọn luồng. N1 đã đạt trong phạm vi mô phỏng cụ thể, chưa phải beta toàn phần hay khả năng điều khiển Hera thật. Đối chứng LLM trực tiếp không áp dụng cho sửa lỗi và kiểm giao thức xác định này; không đưa ra tuyên bố vượt trội sản phẩm từ kết quả một lượt.
