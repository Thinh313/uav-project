# M1: overlay sau kiểm lifecycle05, chỉ dùng khi được phép kiểm thực tế trở lại

20/10/2026. Hiện tại chỉ sửa và kiểm mock/replay theo lựa chọn của người dùng. Dung lượng tăng không tự cấp quyền chạy Docker/AP, Android/emulator, SITL, browser server, build hoặc ký. Tài liệu này không phải admission hay lệnh khởi động. Giữ nguyên M1-ACCEPTANCE-SEQUENCE04.md và các receipt cũ.

## Bản kiểm kế tiếp

Dùng source-ready02 trong evidence/integration03-lifecycle05/builder khi được phép, sau đối chiếu đúng cả bốn pin và dependency bootstrap04. runtime05 SHA586a0d2d8f9193dbc4e0ce420059d3cb3b4b8ca3b2c06b9c54f6fd6a76e07842; sourceIdbc50dfa5bdca8bcdd8de1f8a82bdbbfc128defc6ac7ef559dd90facd0f4c503d. Đây là controller kiểm thử cô lập, chưa tự thay thế runtime04 trong một phiên thật. APK04/source07/observer đã pin được tái sử dụng; chưa cần build hoặc chữ ký mới.

Harness chỉ đổi binding R sang fixture root; command/branch của controller được thực thi dưới Docker/socket/process/clock fakes. Observer parser và digest firmware trong fixture là synthetic, không chứng minh tính đúng firmware, CRC, flight dynamics, độ trễ hoặc mọi lịch thread thực. Ca UNKNOWN do launch không thu được CID hợp lệ chưa phải lời hứa tự thu hồi mọi container.

## Điều kiện đóng phiên không được suy diễn

Caller của lần chạy thực phải thu giữ stdout và exit status của đúng controller. Chỉ chấp nhận đóng sạch khi đồng thời:

1. Process kết thúc với exit0, không bị kill/timeout/mất stdout, và không còn worker hoặc tài nguyên sở hữu chưa rõ trạng thái.
2. Có đúng seal CLOSURE05 của run/container đang kiểm, status CLOSED_SUCCESSFULLY, closurePersisted=true, exitCode0 và không lỗi cleanup.
3. closure.json parse được, đúng run qua launch/seal và containerId, stopped=true, error=null, không lỗi cleanup; các diagnostic/raw liên quan vượt các receiver riêng.

closure.json có persistence05=ATTEMPTED_REQUIRES_PROCESS_SEAL_RECEIPT không đủ chứng minh persistence hoặc thành công. Sau một ngoại lệ nghiêm trọng có thể còn file JSON hợp lệ, nhưng không có process seal: phải giữ UNSEALED/UNKNOWN hoặc FAILURE. Không dùng chữ CLOSED, thời gian chạy, JSON hợp lệ hoặc một receipt tự khai làm thay thế. Không retry mutation, reseal file hay ghi đè run cũ.

## Cửa kiểm thực tế còn nguyên

Sau khi người dùng cho phép kiểm Android–SITL trở lại, cần admission mới: ít nhất29GiB ổn định30s trước boot,26,25GiB sau boot và guard21GiB để bảo vệ sàn20GiB. Kiểm PID/port/cachedimage/pins và tình trạng đóng phiên trước. Trích nguyên byte raw còn chưa thu của run thất bại cũ trước Activity theo runbook04; không suy diễn đã sealed từ UI.

Trong fresh runID, thay riêng entrypoint rig bằng runtime05 đã kiểm; không đổi APargs, speedup1/cap500ms, fsync/frame hoặc guard1500/3000ms. Phải có bằng chứng bootstrap connect thực một lần/0TX và gueststreams cần thiết sẵn sàng trước nativeconnect; AP_CREATED và host publishedport không đủ. Giữ pre-stop inspect/guest/logs và thất bại đầu tiên. Lỗi chặn các bước phụ thuộc, không tự retry hoặc nối interval.

Toàn bộ10AC INTEGRATION03 vẫn bắt buộc: typed cohorts/load/freshness sau20kframe; KML polygon/corridor/QGC; nominal AUTO và accepted review; operatorB độc lập/consent/routing; partition/pilotloss; observer3D airborne30s; đúng selectedrun/SAF/receiver; processrestart+coldboot/privatepreservation; toàn bộ UI; managedclosure và protectedSHA. P1 OPERATOR01 đã đạt scope riêng được giữ nguyên, không tự chuyển sang APK/configuration tích hợp mới.

HeraHub/HID/video/PhaseOne/media thật, calibration simulator và production có gate riêng. ENDURE không thay đổi, không restart hoặc cộng thời gian các attempt cũ. Không tuyên bố DJI parity hay chứng nhận từ kiểm mock.
