# SIMTRAIN53 — điều khiển vòng kín đã kiểm trong phạm vi simulator

15/10/2026. **PARTIAL — prototype hoạt động, chưa nghiệm thu toàn bộ G1 hoặc sản phẩm hội đồng.** Tiếp tục kế hoạch SIMTRAIN52 sau khi người dùng giải phóng dung lượng. Bản mới nằm riêng tại `pilot/simtrain53` và `evidence/simtrain53`; workspace `http://127.0.0.1:8807/`. Không sửa các increment trước, source/candidate, SOT/trust hay ENDURE. Một agent tách bước đặc tả → triển khai → kiểm; không gọi là kiểm định độc lập.

Đã nối input bàn phím → RC override MAVLink → ArduPilot4.7.1 → physics tham chiếu → snapshot →3D. Có preflight từ telemetry/cấu hình/Home, cất cánh GUIDED5m, điều khiển trong LOITER, LAND, quan sát ground/disarm và hồ sơ sau phiên. Vị trí/thái độ không do UI hoặc waypoint animation tạo ra. Đây là quad-X3kg, thêm1kg khi có tải; **chưa hiệu chỉnh Hera**, chưa có SDK/HeraHub, joystick thiết bị hoặc APK mới.

## Kết quả thực

| Lượt | Profile | Hành trình | Frame oracle | RTF nhận toàn lượt |
|---|---|---|---:|---:|
| browser1 | Không tải / lặng gió | FAIL ở preflight, chưa arm; cấu hình hết TTL khi EKF/Home đang khởi tạo | 77.670 | 1,000224 |
| browser2 | Không tải / lặng gió | PASS phạm vi cất cánh → input → lỗi input → LAND/disarm | 75.914 | 1,000314 |
| browser3 | Tải giữa1kg / lặng gió | PASS cùng phạm vi, có review ground/disarm | 75.941 | 1,000323 |
| browser4 | Tải lệch1kg / gió giật seed32 | PASS cùng phạm vi, thêm JSON lỗi/origin/token | 75.950 | 1,000203 |

**305.475 frame sensor và auxiliary snapshot khớp byte với model gốc bất biến.** Ba lượt có luồng bay chứa227.805frame; lượt preflight thất bại giữ riêng77.670frame. WAL có chuỗi SHA/CRC, RX/INTENT/SENT, intent fsync trước gửi; mọi frame đã admitted có AP receive/parse stage tương ứng. Tail AP sau khi backend đóng được giữ riêng, không tính là frame đã trả lời. Local send hoặc ACK không được gọi là thực thi.

Các lượt đều yêu cầu1200Hz/speedup1/cap500ms; không đổi ngầm speedup, không bỏ physics frame. Chỉ có ba profile chức năng, không phải thí nghiệm A/B tải đã counterbalance. Có tải host do kiểm/readback khác nhau; không suy ưu thế hiệu năng hoặc độ giống Hera từ bảng này.

**G1 chưa đạt toàn bộ.** RTF toàn lượt gần1× không chứng minh pacing tốt: profile tải lệch/gió có một cửa sổ gần5s chỉ0,983837×; central có cửa sổ0,999564×. P99 khoảng cách nhận frame khoảng7,56–7,62ms, đỉnh39,77–55,58ms trong ba lượt có bay. Giữ các giá trị này và mọi lỗi trong denominator. Browser RAF ghi p95 khoảng10ms trên ANGLE Metal/M1Max, nhưng bao gồm chụp ảnh và cố tình stall350ms; đây không phải GPU-completion, native-projector FPS hoặc nghiệm thu60FPS.

## Phạm vi kiểm và thiếu

| AC | Kết quả | Bằng chứng / giới hạn |
|---|---|---|
| AC01 bảo toàn/tài nguyên | PASS phạm vi host | 20.334 SHA bảo vệ khớp;5.051đường dẫn ENDURE không đổi; khoảng1,12GiB artifact/4GiB quota, sàn20GiB giữ tại các điểm kiểm |
| AC02 firmware/endpoint/preflight | PASS phạm vi đã thử | Target42/1, container/PID/image/AP SHA; pre-arm/firmware/Home/4tham số và kiểu kiểm từ raw; RC encoder khớp generated C header |
| AC03 Guided/Loiter/Land | PASS phạm vi đã thử | 3luồng actual SITL,67check browser tổng cộng; không phải Stabilize, joystick hay AUTO |
| AC04 fault/authority | PARTIAL | 20contract checks; mất focus/stall/JSON lỗi thực;5ca datagram mock. Reboot/mất mạng AP thực trong luồng mới chưa kiểm |
| AC05 UI/3D/review | PARTIAL | Renderer nhận physics; LAND cố định ở header;27check handoff, history sau restart và SHA; actual projector,3người chấm visual, live audio/listening chưa kiểm |
| AC06 pacing/matrix | PARTIAL | Toàn bộ raw/oracle và clock brackets đạt kiểm nội dung; pacing/jitter, dài hạn và hồi quy full source cuối còn mở |

Các số kiểm là coverage theo phạm vi, không phải chứng nhận sản phẩm. Toàn bộ25yêu cầu đầy đủ trong kế hoạch vẫn chưa được nghiệm thu; ghi tiến độ tách riêng tại `evidence/simtrain53/progress1.json`, không viết lại canonical SOT đang đóng băng.

## Các sửa lỗi và bằng chứng giữ lại

- Lượt đầu hết hạn configuration30s trước khi EKF/Home xong. Giữ FAIL, thêm thao tác đọc cấu hình riêng; không kéo dài TTL, ép arm hoặc tắt pre-arm.
- Claim input gồm attestation trước, challenge mới rồi neutral-first; browser/Node/backend/guest không bị coi là chung clock. Lease200ms không tự sống lại khi packet mới đến.
- Lượt4 có một input đến muộn khi đã sang LAND; server từ chối. UI cuối xóa lease/các phím ngay trước khi gửi LAND. Kiểm client bằng mock pending-response; không gọi request bị từ chối là lệnh đã bay.
- Rà soát cuối sửa lưu raw trước khi từ chối datagram cụt.5ca mock kiểm truncated/rate/duplicate/foreign peer/PWM; không có thêm AP/flight instance. Raw lỗi giữ lại và không có CLOSE thành công.
- History kiểm cả5file raw hiện tại theo SHA của biên bản lưu, từ chối manifest thiếu/escape/symlink, phân biệt luồng chưa bay với luồng có takeoff/land. Không suy tính xác thực chữ ký từ hash.
- Sau operator-end, nguồn cuối chạy validator offline có giới hạn, khóa start trong lúc kiểm. Validator không yêu cầu operator cố ý stall hoặc dùng manual mới công nhận tính toàn vẹn raw. Existing-receipt/failure paths đã kiểm riêng; **success path tự chạy sau operator-end chưa được lặp bằng lượt SITL thứ5**.

Các chỉnh nhánh RX lỗi, quota/history/finalizer và xóa input trước LAND xảy ra sau matrix vật lý; có kiểm mock/static tập trung, chưa có full coupled regression trên toàn bộ source cuối. Đây là deferred cụ thể, không được che bằng PASS của bản trước.

## Bàn giao và bước tiếp

Workspace đang chờ thao tác, không có instance AP tự chạy. Chọn profile → mở phiên → chờ EKF/Home → đọc lại cấu hình → cất cánh → nhận quyền → điều khiển → LAND → ground/disarm → kết thúc/review. Phiên engineering giới hạn120s mô phỏng/150s host; cần LAND trước hết giờ. Start dùng live storage admission, quota4GiB và dự phòng1GiB/phiên, không khóa cứng số lượt đã kiểm và không tự xóa hồ sơ.

Host quan sát: MacBookPro18,2/M1Max,32GiB RAM,10CPU, macOS27.0.1/26A434, AC100%; actual projector chưa kết nối/nghiệm thu. Dung lượng đầu khoảng38,5GiB, cuối khoảng37,5GiB. Không dependency install, project copy/tmp, build image/APK, ký release, chọn candidate hay chạy lại ENDURE. Chỉ server localhost mới giữ chạy; controller/backend/container của4lượt đã đóng. Docker image prune sau từng lượt thu hồi0B, không đụng volume/container khác.

Ưu tiên kế tiếp: hồi quy source cuối trong luồng đóng, xử lý jitter/phase của AP–backend với workload UI cố định rồi nghiệm thu G1. Sau đó mới nhận AUTO survey/corridor, upload/readback, camera/gimbal và ảnh giả lập, instructor/fault và rehearsal màn hình chiếu. Chưa phải bản cài HeraHub, thay Ragas hoặc vượt DJI đã được đo.
