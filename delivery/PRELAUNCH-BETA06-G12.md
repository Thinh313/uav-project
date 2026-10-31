# G12: source/mock đạt, chờ nguồn AC

Ngày 23/10/2026, giờ Việt Nam. Chưa hoàn tất nghiệm thu Android–SITL, reboot và persistence.

Đã ghép bản vá thiếu import `os` vào bản thử cô lập `planning/beta06g12/qa-ground-soak.py`. Ngoài namespace G12, đây là thay đổi vận hành duy nhất so với G11. Source/candidate đóng băng, ENDURE và các thế hệ trước giữ nguyên. Không build/cài APK, ký mới hoặc dùng SDK/HeraHub.

Builder kiểm 8 nhóm, QA độc lập kiểm 6 nhóm. Đã gọi effective `collect()` của G12, kiểm constructor metadata, báo cáo từ chối qua finally và khoảng 75 giây mock với 151 mẫu, chuỗi hash journal và hai renewal cho cả publisher/viewer. Đã kiểm lại clock/provider/default và số/thuật toán guard. Đây là thời gian và UI giả lập, chưa phải khoảng chạy thực.

Một MockSocket hiện tại có 947 dòng đã qua đối chiếu canonical/raw, strict WAL, index/outcome/response/history; bốn handler fixture cũng đạt. Các kết quả này được phân biệt với ArduPilot và payload thực.

Gate độc lập: `evidence/beta06/generation12/qa-final-gate01.json`, SHA `b10bc284f1f9a8610e57eeb4fcdc8eddc5930e604f4a038883ba8d915d1a2e1c`. Gate xác nhận 1.141 pin, 25 helper, 18 production sibling, 132 stage file, 5 compiled artifact; 10.217 đường dẫn bảo vệ, 7 symlink và 6.198 entry lịch sử đúng SHA/mode. Fork dữ liệu gốc mới 20 file / 870.221 byte chưa bị writer sử dụng. Không cộng kết quả G9/G11 vào G12.

Fingerprint chính:

- Flight pins: `e21b23318981313577a55691714ac7939c80948f21cd0548ebb84a71c5d6af6d`.
- Native helper freeze: `a56351744aa5e060507e7442b767679f4a5428064b042f264436745c360b5bc1`.
- Source freeze: `79320aafafcfb97b093060ab39472471278e23c98fe26a124a35762450822764`.

Điều kiện còn thiếu là nguồn. Người dùng cho biết sẽ cắm nguồn, nhưng các lần đọc thực bằng `pmset -g batt` vẫn báo Battery Power, 100%, lần cuối ước tính 2 giờ 03 phút. Không coi lời dự định cắm nguồn là bằng chứng máy đã nhận AC. Dung lượng quan sát khoảng 37,1 GiB, trên sàn 20 GiB; chưa chạy admission vật lý 31 mẫu vì chưa đủ điều kiện mở runtime.

G12 chưa mở TTY controller, host, Android, publisher hay AP; không có launch/permit/ledger/first-writer thực, chưa lấy anchor và chưa tiêu thụ hai attempt 24/25. Việc lưu hồ sơ prelaunch không tạo authority hoặc chứng minh nghiệm thu. Không có tiến trình thử G12 cần dừng, không có bản sao project/dependency ngoài repo hay thao tác xóa dữ liệu người dùng. Scratch `evidence/beta06/generation12/codex-tmp-g12-binding-20261023-753_vl_p` đã được Builder dọn theo receipt; các bằng chứng mock được giữ.

Khi nguồn AC thực đạt: kiểm lại nguồn/nắp máy, artifact và fingerprint/đường dẫn bảo vệ, PID/cổng và namespace sạch; sau đó mới mở đúng `/usr/bin/python3 -B planning/beta06g12/qa-root-live24.py` bằng TTY và thực hiện admission mới. Không dựng lại source hoặc ghi đè gate để né điều kiện. Giữ nguyên 2700 giây, tối đa 2 host/4 AP/2 boot, dự phòng 225/240/90 giây, mọi quota, speedup và sàn dung lượng. Boot25 chỉ persistence, không khôi phục quyền. Hướng dẫn đầy đủ ở `planning/beta06g12/BUILDER-NATIVE-HANDOVER12.md` và TIP G12.

SCENARIOS: AUTO/video/payload, mất link, restart host, reboot AP, cold persistence đều **NOT RUN**. Không có FPS/camera thật hoặc chứng nhận Hera từ mock.

OVERALL: **WAITING_EXTERNAL_POWER / NOT READY cho nghiệm thu thực**. Source/mock đã đạt; lượt G12 chưa khởi chạy và có thể tiếp tục sau kiểm điều kiện mới. Không có automation mới được tạo và không có lời hứa tự chạy sau khi chat kết thúc.
