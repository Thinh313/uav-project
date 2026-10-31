# HOSTDIAG08: chẩn đoán dung lượng host

22/10/2026. **Đã đủ điều kiện chuẩn bị và chạy admission mới; chưa phải nghiệm thu Android–SITL.** Guard giữ nguyên. Không đổi hoặc xóa dữ liệu của người dùng, không dừng tiến trình khác, không đổi cấu hình APFS/swap/backup.

## Đo và kết luận

- 181 mẫu trong 180,004939 giây, hash chain đối chiếu độc lập đạt. Dung lượng available giảm 92.598.272 byte (88,31 MiB), còn tối thiểu 37,24 GiB.
- Container APFS giảm 92.614.656 byte; volume Data tăng đúng số đó. Các volume khác, gồm VM, không tăng. Swap used không đổi ở 6.580,94 MiB trong cửa sổ này. Biến động mới quan sát phù hợp với tăng phân bổ trên Data, chưa có bằng chứng swap gây ra đợt giảm mới.
- Các tiến trình đọc được có ghi đĩa: ChatGPT 49.954.816, codex 46.039.040 và Chrome 17.473.536 byte. Đây là bộ đếm I/O, có thể gồm ghi đè/cache; không phải lượng dung lượng mỗi tiến trình chiếm thêm. Có tiến trình bị từ chối quyền đọc hoặc đã thoát. Không quy toàn bộ delta cho một tiến trình từ các số này.
- Không có snapshot trên volume Data hoặc backup Time Machine đang chạy tại thời điểm kiểm ban đầu. Không thấy file đã unlink còn mở lớn từ 64 MiB trong phạm vi lsof đọc được. Log kernel/swap đúng khoảng admission G7 cũ không có thông tin hỗ trợ quy nguyên nhân; sự vắng mặt log không bác bỏ hoạt động swap hay writer khác.
- **Nguyên nhân lịch sử của đợt giảm 1.416.642.560 byte tại G7 vẫn UNKNOWN.** Không coi dữ liệu hiện tại là bằng chứng hồi tố. Repo, root và Data cùng available ở phép đối chiếu; khác mount path không giải thích lỗi G7.

## Giữ nguyên guard và admission mới

Ba cửa sổ diagnostic cố định có 31 điểm nhưng span thực nhỏ hơn 30 giây vài mili giây. Guard cũ từ chối `STABLE_31_SECONDS_REQUIRED` đúng như mã nguồn; không sửa timestamp hoặc chọn lại cửa sổ cho vừa PASS. Các cửa sổ này là quan sát, không phải admission.

Sau khi observer kết thúc, Root lấy riêng 31 mẫu mới bằng sleep1s và gọi nguyên hàm `budget_decision` của helper G7 bất biến. Kết quả **PASS**, span30,221562 giây, min37,231445 GiB, peak decline0. Có đủ headroom29GiB và ngưỡng256MiB giữ nguyên. Đây là preflight host; campaign mới vẫn phải chạy lại admission trực tiếp ở host/emulator/Connect và runtime guard28GiB/forecast15s giữ sàn20GiB.

## Phạm vi và bước tiếp

Chỉ chuẩn bị G8 trong namespace mới, không resume G7. Reuse APK development và ARM artifact đã kiểm, không build/cài/ký mới. Root chỉ launch sau source gate độc lập và admission trực tiếp đạt. Mọi AUTO/video/payload/mất link/reboot/cold persistence cần bằng chứng mới riêng; không lấy preflight host hay mock để báo PASS sản phẩm.

Observer read-only không tạo scratch/venv/build/cache. Bằng chứng giữ ở `evidence/hostdiag08`: `samples01.jsonl`, `collection01.json`, `qa-analysis01.json`, `admission01.json`, `open-unlinked01.json`, `historical-kernel01.json`. SDK ABI thực được đối chiếu: UUID16 +35uint64=296 byte; process identity dùng pid+start. Không benchmark LLM vì đây là chẩn đoán deterministic hệ điều hành.
