# Roadmap overlay sau NATIVE88

Canonical SOT/source/candidate/ENDURE giữ nguyên. Xem COMPLETION-NATIVE88.md và evidence/native88/verification.json cho phạm vi chứng cứ.

ĐÃ KIỂM: cockpit Android sampled UI ngày/đêm và viewport thấp; sửa hidden/grid và heading; hai nhiệm vụ KML→AUTO→review thực trên ArduPilot SITL; background và duplex loss đang bay, thụ động theo dõi failsafe/RTL/hạ cánh; xác nhận mặt đất→đóng gián đoạn→phiên mới chỉ đọc; raw streaming SAF→receiver; quota workspace giữ thế hệ cũ; persistence sau app/Android restart.

P1 BENCH KHI CÓ THIẾT BỊ: thu intake có danh tính/firmware/SDK, ngưỡng đo đã duyệt. Cài development riêng; chỉ đọc trước. Input/calibration và mất input, video/độ trễ và stale-frame, transport/radio mất link. Không arm qua đường chưa nghiệm thu.

P1 PAYLOAD: Phase One đúng camera/lens/custom gimbal và SDK trước, sau đó Sony/thermal/corona/LiDAR. Điều khiển–ACK–trạng thái–ảnh thực phải đối chiếu riêng. Hai operator và nhiều payload chỉ sau routing/authority/timeout đơn kênh đạt trên bench.

P2 HIL/FIELD: hiệu chuẩn động lực Hera/tải/gió/pin theo dữ liệu đo; mapping/corridor/địa hình/Home/datum với dữ liệu thực; failsafe và flight modes theo cấu hình được duyệt. Mô phỏng internal quad chưa phải digital twin Hera.

RELEASE GATES: receiver source authentication/key lifecycle, performance/ENDURE thật, signed deployment và production/Hera acceptance. NATIVE88 không tự mở các gate này và không cho phép production signature hoặc tiếp tục mission không rõ kết quả.
