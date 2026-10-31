# Runtime Unification01: chưa đạt nghiệm thu 30 phút

Ngày: 2026-10-28T15:04:09.590302+07:00. Trạng thái: **NOT READY**.

Đã hợp nhất mã runtime và vòng đời nhiệm vụ, tạo APK development và cài thành công trên emulator. Chưa hoàn tất hành trình Android–SITL hay lượt30 phút. Không có AP hoặc lệnh bay nào được gửi trong chiến dịch này.

## Kết quả đã có

| Phần | Bằng chứng | Giới hạn |
|---|---|---|
| Runtime chủ động |65 file,16 thư viện lá được ghim SHA; bỏ chuỗi import policy/orchestrator của các task cũ |Chưa chứng minh hiệu suất hoặc trải nghiệm vận hành thật |
| Native shell |50 đầu vào,31 Java, APK611.923 byte, ký development; source db20951a…b8e2 |ADB install thành công; chưa chạy UI/handshake thực |
| Snapshot và lifecycle |Workspace bất biến có phiên bản; đồng nhất owner; bootstrap có nonce/source/epoch; guard metadata độc lập; proof đầy đủ có SHA và reader kiểm FSM |JVM/mock và filesystem host thực, không thay bằng chứng Android/AP |
| Linux thực |arm64,Python3.12.3,10 ca metadata/pre-Popen đạt; không mở socket/process hoặc import physics |Không phải SITL bay |
| Bảo toàn |17.117 đường dẫn lịch sử;26 seal/52.095 mục;718 source+120 metadata không drift mới;165 thiếu cũ giữ nguyên |Không suy ra hiện diện liên tục.541 file Android cũ chỉ có baseline trước cài, chưa đối chiếu sau |

## Hai lỗi đã được phân biệt

1. Lượt ngắn candidate02 dừng trước AP: journal lifecycle bị stale khi chờ guard khác prime15 giây, rồi lỗi ghi failure che nguyên nhân đầu. Mã đã sửa bằng bộ quan sát thực, dừng/join có kiểm soát và giữ lỗi gốc. Kiểm host thực đạt; chưa được chạy lại trên Android–SITL.
2. Guardian dừng do `ACTUAL_HOST_DISK_FORECAST15_FLOOR10_RESERVE256`. Dung lượng host suy giảm nhanh; hai mẫu cuối giảm858 MB trong khoảng516 ms. Nguyên nhân phân bổ chưa xác định. Swap chỉ được đo sau sự cố, không chứng minh quan hệ nhân quả. Phần ghi trực tiếp được đo của task nhỏ; vẫn không loại trừ tác động gián tiếp của OS, emulator hoặc các tác vụ khác.

Ứng viên cuối: `f4134ecc91ac6f242154846c42b5729f2586e3f6e5bb87b9874dc0ada41abdc1`. Mọi ứng viên và lỗi trước được giữ nguyên. Đồng hồ5400 giây không reset, guard không nới, không tự khởi động lại sau lỗi tài nguyên.

## Phần chưa đạt

- UI Android và live ACK/bootstrap trong10 giây.
- Điều khiển AP thật trong SITL, manual/assisted1802 giây, đủ frame và đúng các clock.
- Mất link, đóng review, restart và đối chiếu byte trên Android thực trong phiên mới.
- AP reboot, Hera/HeraHub, payload thực và production là các gate riêng, chưa được xác nhận.

## Bước tiếp theo

Giải quyết biến động dung lượng host và nguồn điện trước một chiến dịch admission mới. Giữ sàn10 GiB và dự phòng256 MiB; ngân sách đầy đủ của lượt dài hiện là20.720.435.840 byte (khoảng19,30 GiB), không chỉ kiểm sàn. Sau đó chạy ngắn qua API sản phẩm, chỉ mở lượt1802 giây khi đầy đủ raw/guard/oracle đạt; tiếp tục mất link và persistence. Bản mã hiện tại chưa đủ bằng chứng để gọi là beta vận hành.

## Hồ sơ

- [Root verify](../evidence/runtime-unification01/ROOT-VERIFY01.json)
- [QA độc lập](../evidence/runtime-unification01/qa/ACTUAL-GATE01.json)
- [Chẩn đoán host](../evidence/runtime-unification01/host-pressure-diagnostic01.json)
- [Bảo toàn cuối](../evidence/runtime-unification01/preservation-after01.json)
- [Đóng runtime](../evidence/runtime-unification01/root-runtime-closure01.json)
- [Hướng dẫn API](../evidence/runtime-unification01/host/OPERATOR-RUNNER01.md)

Đã dọn6.397.154 byte scratch build cố định; mọi PID do task tạo đã kết thúc,7 cổng được giải phóng. Docker image prune thu hồi0 byte; không prune container/volume và không xóa bằng chứng cũ.
