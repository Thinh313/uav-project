# ROADMAP sau NATIVE93

18/10/2026. Corridor Android–SITL đã qualified trên một fixture: nominal hoàn tất, duplex loss và APK restart có failsafe/khôi phục bằng chứng. Giữ riêng phần engineering và nghiệm thu Hera thật.

1. P1 — Corpus KML khách hàng thực: corridor dài/gấp khúc/đa feature, biên tọa độ, self-intersection, holes, Home/MSL/relative/terrain; đối chiếu toán độc lập về chiều rộng/coverage/overlap/ảnh/thời gian. Không suy coverage rộng từ một corridor.
2. P1 — Fault ở ranh giới upload/commit: mất liên kết giữa upload/readback, process restart khi journal pending, sai session/boot/HEAD, thu hồi quyền lúc thao tác. Nghiệm thu unknown/failure rõ ràng, no auto retry/regrant/resume; namespace mới, đủ headroom.
3. P1 — Native standalone: thu hẹp phụ thuộc host compiler/parser/bridge, đưa model/mission compiler đủ kiểm lên Android; UI chọn file KML và diff source→plan→upload, lỗi dễ hiểu, options corridor đầy đủ và kiểm accessiblity/IME/screen sizes.
4. Bench khi có thiết bị/API: HeraHub MCU/HID/calibration/deadman/transport, nguồn video đúng payload và tuổi; Phase One camera/gimbal và quyền hai operator. Hiện chưa có thiết bị/SDK, không gọi engineering APK là bản điều khiển Hera đã nghiệm thu.
5. Gate riêng: source/candidate integration, ký production, resource/thermal/pacing và ENDURE24h. Không tự promote từ PASS93.

Bước kế tiếp đề xuất: corpus KML khách và fault giữa upload/readback/commit trên cùng model, trước khi thêm tính năng demo mới. Không cần HeraHub cho phần chuẩn bị/mock; actual SITL theo admission và ngân sách dữ liệu.
