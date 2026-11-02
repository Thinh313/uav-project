# Hai bản bàn giao tại mốc H10

## Định danh

| Vai trò | Repo/tag |
|---|---|
| Bản gốc private của anh | nclamvn/aeris / development-handoff-2026-11-02-h10 |
| Bản public cho nhóm | nclamvn/uav-project / research-handoff-2026-11-02-h10 |
| Candidate H10 host | 5e3c5d69967e415867848208f76e8a9a5b5877a24f36497d2b825d3e64159810 |

Các tag 31/10 và MILESTONE05 giữ nguyên. Source phát triển tiếp từ baseline private `656d694ebf3bb02d13ef9eae956e0eeb8ea2374f` cùng các source H10 đã được kiểm kê. Commit thực của hai repo được ghi trong Git/tag và manifest sau khi đóng gói; không nhầm source baseline với public HEAD.

## Phạm vi đạt

Artifact 20 MiB, metadata 100 MiB đã áp dụng, tăng dự phòng đĩa tương ứng 39 MiB. Root kiểm 10.526 đường dẫn bảo vệ đạt, không có sai byte/mode/SHA trong phạm vi kê khai. Các pin H8/H9/H10 giữ đúng; gói private gốc giữ SHA. Đây là kiểm hiện trạng, không phải chứng minh source/path liên tục nguyên vẹn.

H10 có 140 source, 198 product pins, 257 writer sites, 14 owner và dự phòng 60.686.336 B. 34 phương thức kiểm tập trung trên máy tác giả đạt, gồm wire Node-Python thật với mock metadata budget. Mức chứng minh không tự chuyển sang nghiệm thu Android-SITL.

Source H10 sửa lossless result/ref và normal writer closure. m801 thu đủ raw/SDK closure; đối chiếu riêng xác nhận current native data. Cả bốn cổng Beta-RC01 vẫn chưa được nghiệm thu. Không build/ký APK mới hoặc ký production trong mốc này.

## APK và raw giữ riêng

APK development hiện tại SHA:

`eed4ba7851897af3fb57cd29005a84df41e39a5d97b5ae510baf02321ddc5c17`

Raw m801 SHA:

`3e08bb8f8c23296c5ef6f6f576523b5b293f9d857478c3463cf1fdcfe7adfceb`

Raw có 250.880 B, 83 file/9 thư mục. Lifetime generation 10, record 0; hai journal mới đóng/rỗng, tám archive, không pending. Registry head cuối là observation từ m801 mới; không phải ACK cuối đã giữ trước g105. Các byte gốc và receipt được giữ trong bộ private, không xuất public chỉ để thỏa mock.

## Sự cố và việc còn mở

Sự cố H7 từng ghi qua hardlink vào hai generated asset working H6 đã có hồ sơ, byte lỗi và kiểm phục hồi đúng SHA/mode/inode/device. Candidate đóng băng không bị thay. Atomic COW đã bổ sung. Không khẳng định source/path được bảo toàn liên tục hoặc viết lại lịch sử ENDURE.

Bước tiếp là contract tiếp tục từ trạng thái 83 file và raw m801 có provenance, rồi qualification và G1 mới. Chỉ sau G1 và các lượt ngắn đạt mới G2/G3/G4. Nhóm không tự archive, khôi phục quyền hoặc gửi lại APPLY từ một receipt forensic.
