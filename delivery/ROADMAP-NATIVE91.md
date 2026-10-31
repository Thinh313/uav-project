# Roadmap overlay sau NATIVE91

18/10/2026. Bổ sung riêng; canonical SOT/source/candidate/ENDURE và mọi module trước Native91 giữ nguyên. Không promote hardware/production gate.

ĐÃ ĐẠT: Android SAF export immutable diagnostic prefix + full workspace/HEAD, independent local receiver và portable raw receiver; cockpit Fly nhận telemetry SITL, synthetic video PiP có nguồn riêng; nhiệm vụ KML/preflight/upload/readback/AUTO/review, foreground-loss failure riêng; restart/reboot không khôi phục quyền. Bản bàn giao development06, nghiệm thu engineering ở emulator, chưa điều khiển Hera thật.

TIẾP THEO KHÔNG CẦN SDK, theo thứ tự:

1. Một nguồn nhiệm vụ: hợp nhất editor cockpit/KML với mission SITL, bỏ việc biên tập hai contract riêng; altitude/Home/frame/camera/semantic readback cùng model. Mock trước, SITL khi đủ ngân sách và giữ sàn20GiB. Chưa tự mở arm hoặc replay quyền.
2. Review vận hành: timeline dễ đọc gồm preflight, Home sau arm, upload/readback, NAV/terminal, sự cố, trace input/video và receipt; thể hiện rõ dữ liệu hiện tại/lịch sử và không kết luận ảnh từ camera ACK. Không đưa ID kỹ thuật lên cockpit chính nếu không giúp quyết định.
3. Qualification Android: accessibility/focus và layout trên runtime đích, renderer/RAM/thermal/latency với clock đo được; faults/reboot tại các điểm hành trình có raw witness. Giữ gate resource/ENDURE riêng, không cộng bằng chứng mô phỏng thành hardware acceptance.

KHI CÓ THIẾT BỊ/SDK: intake target HeraHub/MCU/HID/radio/video; calibration/mapping thật; Phase One/gimbal đơn rồi dual-operator/multi-payload có quyền/session/target/loss riêng; HIL/bench/field. Chưa đủ dữ liệu để khẳng định thời gian bay, ảnh khảo sát, NDAA hoặc tương đương RAGAS/DJI thương mại.
