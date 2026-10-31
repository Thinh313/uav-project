# ROADMAP sau NATIVE92

18/10/2026. Model KML cockpit/native/SITL đã hợp nhất, qualified engineering; baseline source/candidate/ENDURE vẫn đóng băng.

1. P1 — mở rộng compiler/import corpus với KML thật của khách: nhiều feature, corridor hẹp/gấp khúc, kinh tuyến biên, self-intersection, thứ tự tọa độ, Home/relative/MSL/AGL và options. Cho người vận hành xem diff nguồn→tuyến→mission items, diện tích/thời gian/ảnh kèm giả định. Native KML parser offline là gap hiện hữu; không gọi host bridge thành giải pháp standalone.
2. P1 — AUTO corridor và failure matrix trên cùng model: mất foreground/link trong upload và AUTO, reboot trước/sau commit, sai session/boot/HEAD, nhập stage không hợp lệ. Thực hiện với namespace mới và đủ dung lượng; giữ bằng chứng thất bại, không tự cấp lại quyền.
3. P1 — chuẩn hóa UX nhiệm vụ: chọn/import KML dễ dùng, options corridor/heading/overlap đầy đủ trên UI, cảnh báo Home/terrain và mã lỗi thân thiện; focus/IME, accessiblity, screen sizes, thao tác vật lý cần kiểm trên runtime đích. Canvas preview hiện là WGS84 cục bộ, chưa thay bản đồ sản phẩm/terrain3D.
4. P1 — bench HeraHub khi có thiết bị/API: transport MCU/HID, mapping/calibration/deadman, serial/firmware/capability và input watchdog; video đúng payload/tuổi nguồn; Phase One identity/settings/trigger/media; quyền dual-operator riêng flight/payload. Hiện chưa có thiết bị/SDK, chưa chứng minh điều khiển Hera.
5. Gate riêng — product integration/candidate/trust/release, resource/thermal/pacing và ENDURE24h. Không tự tích hợp vào source/candidate đang đóng băng hoặc ký production từ các PASS engineering này.

Bước kế tiếp đề xuất: corpus KML khách + AUTO corridor và faults trên cùng model, sau đó thu hẹp bridge dependency để có native standalone. Không tăng mock coverage rồi gọi là hardware readiness.
