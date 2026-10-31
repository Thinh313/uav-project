# BETA06: launcher ARM và bản sửa readiness

**Trạng thái: NOT READY cho beta Android–SITL.**

## Kết quả chính

BETA06 vẫn NOT READY. Launcher đã dùng artifact ARM thực và lưu được đầy đủ bằng chứng lỗi trong phạm vi capture. Lượt Android–SITL mới dừng trước telemetry; không có ARM, AUTO hay cấp quyền payload. Bản sửa parser tiếp theo đã qua kiểm source/mock độc lập nhưng chưa được ghép vào ứng dụng hoặc chạy chiến dịch mới.

## Nguyên nhân đã chứng minh

ArduPilot ghi “Waiting for connection” vào stdout (249 byte), còn “SERIAL0 on TCP port 5760” ở stderr (52 byte). G3 chỉ tìm cả hai trong stdout nên báo GUEST_SERIAL_READY_DEADLINE dù tiến trình còn chạy. Exit 137 phát sinh khi đóng container có kiểm soát, OOM=false; không phải bằng chứng binary tự crash. Container 6f4a07b36e87bcd2e809d5f1baa4ca7494417b966b3aef0b8a757d7d8ce1c502 được giữ nguyên.

## Bản sửa đã kiểm

Hai file mới nằm trong pilot/beta06g4/flight, tái dùng artifact và helper G3 bất biến. Parser đọc hai luồng cùng lần attach với offset/tail riêng, ghi vị trí marker và SHA từng prefix, từ chối trộn mảnh giữa luồng hoặc giữa attempt, tràn log, CID sai và tiến trình đã chết. Giữ fsync, giới hạn lưu log, exact-CID, deadline, speedup 1 và resource guard. Builder có 12 ca readiness + 11 ca lifecycle; QA độc lập có 15 nhóm và chạy lại 23 kiểm Builder. Không cộng các số này thành số kịch bản bay thực.

## Giới hạn và quyết định dừng

G3 dùng một cửa sổ host 30 phút và chính sách không mở thêm AP sau kịch bản thất bại. Phiên đã đóng; không reset clock, retry Connect hoặc sửa pins để chạy lách. G4 hiện chỉ là bản sửa source/mock: chưa wiring app/controller, chưa có pins và có 0 request thực. Nhiệm vụ AUTO cùng video/payload, mất link, reboot và restart vẫn cần nghiệm thu trên một chiến dịch mới với gate độc lập.

## Các lỗi khác được giữ nguyên hồ sơ

Nguồn Chrome đầu tiên dừng do tab bị ẩn. Nguồn được restage có kiểm soát sang IAB cùng VP8-720P30-V1/RGB tổng hợp. Một interval sau đó bị STALE_OBSERVATION ở khoảng 69,6 giây; nguyên nhân khởi phát còn UNKNOWN. Interval đó bị từ chối và không được cộng vào interval 75,443 giây đạt sau cùng. Đây là video tổng hợp, không phải ảnh camera thực hay chứng cứ phơi sáng.

## Bảo toàn và dọn dẹp

Không build/ký/cài APK mới, không sửa source/candidate hoặc ENDURE. Đối chiếu nguyên trạng theo baseline không đồng nghĩa mọi file của repository đều hiện diện: 95 thay đổi tracked có sẵn trước tác vụ được giữ nguyên, không tự khôi phục/xóa. Các fixture nhỏ của Builder/QA được tự dọn; không copy cả dự án, không cài dependency. Đã chạy docker image prune -f và thu hồi 0 B; không xóa container hay volume.

## Bước còn lại

Nối bản sửa readiness đã kiểm vào launcher/app/controller của một chiến dịch cô lập mới, đóng pins và kiểm độc lập trước khi chạy. Sau đó nghiệm thu N1 AUTO/video/payload → F1 mất link → restart có chứng cứ → N2 đối chứng → F2 reboot. Chỉ báo beta đạt khi có raw execution, media/overlap, invalidation và persistence thực tương ứng. Không cần SDK/HeraHub cho phần kiểm SITL này.

## Phương pháp và giá trị

Áp dụng Vibecode Kit 6.3, phân vai Builder và QA độc lập. Giá trị đo được là chuyển lỗi khởi động không rõ nguyên nhân thành nguyên nhân parser có log thực, rồi kiểm bản sửa bằng replay và fault injection. Không có LLM trong runtime nên baseline LLM trực tiếp không áp dụng; chưa có kết quả hiệu suất hoặc chất lượng bay mới.

## Ma trận kết quả

| Yêu cầu | Kết quả | Phạm vi bằng chứng |
|---|---|---|
| Artifact ARM 0755, SHA gốc | Đã chạy tới console SERIAL0/Waiting | ACTUAL CONSOLE; chưa xác nhận firmware qua MAVLink |
| Log lỗi launcher | 11 receipt và 49 file lỗi đã đối chiếu SHA; không tràn log | ACTUAL DOCKER + independent replay |
| Readiness stdout/stderr | Sửa cô lập; replay log thực và ca phủ định đạt | SOURCE/MOCK; chưa nối app/controller |
| Video + clock trước kết nối | Interval mới 75,443 giây đạt, hai vai có gia hạn định kỳ | ACTUAL GROUND; chưa phải FPS/latency khi bay |
| AUTO đồng thời video/payload | Chưa đạt: lần kết nối N1 bị từ chối trước telemetry | 0 ARM, 0 AUTO, raw 0 byte |
| Mất link, reboot, restart sau nhiệm vụ | Chưa chạy do N1 thất bại | Không tái sử dụng kết quả thế hệ cũ |
| Kho Android | 19 file / 34 bản ghi giữ nguyên SHA, không dùng thêm SAF | ACTUAL HASH PRESERVATION; không phải kiểm restart G3 |
| Source/candidate/ENDURE | 4.791 đường dẫn baseline, 385 pins và 49 file lượt lỗi không đổi | Đối chiếu baseline đã chốt |
| Đóng phiên và dung lượng | Host/emulator đóng sạch; cổng riêng đóng; container lỗi giữ lại | Tối thiểu đo được 36,11 GiB; image prune thu hồi 0 B |

## Bằng chứng

- [qa-actual-launch-failure01.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/qa-actual-launch-failure01.json>)
- [qa-ground-final-replay01.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/qa-ground-final-replay01.json>)
- [qa-ground-stale-diagnosis01.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/qa-ground-stale-diagnosis01.json>)
- [android-store-after-failed-launch-04.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/android-store-after-failed-launch-04.json>)
- [qa-preservation-after-runtime03.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/qa-preservation-after-runtime03.json>)
- [qa-pins-after-runtime03.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/qa-pins-after-runtime03.json>)
- [root-runtime-closure-inventory01.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/root-runtime-closure-inventory01.json>)
- [android-closure04.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/android-closure04.json>)
- [app-closure.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation03/host-app03/app-closure.json>)
- [builder-readiness-correction02.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/builder-readiness-correction02.json>)
- [qa-correction-final03.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation04/qa-correction-final03.json>)
