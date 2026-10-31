# Nội dung bàn giao và đối chiếu

## Phần public

Repo mới có lịch sử Git riêng, lấy snapshot từ source commit
`6ea4f5027bc93d4f67e10da53c098391d9553f2f`, bổ sung các file source chưa commit
ở thời điểm bàn giao. Không sao chép lịch sử private sang public.

Source được đối chiếu theo `handoff/SOURCE-MANIFEST.json`. Manifest không chứa
chính nó hoặc `.git`; khi verify một workspace có dữ liệu runtime thêm vào,
công cụ chỉ chứng minh các file được liệt kê còn đúng byte, không chứng minh
workspace không có file lạ hay đã an toàn vận hành.

Toàn bộ mã sản phẩm, adapter, source Android, compiler, mock và source giả lập
được giữ. Tài liệu/generator gắn trực tiếp với hồ sơ khách hàng được bàn giao
trong overlay private để giữ nguyên dữ liệu gốc. Chín file public chỉ ẩn danh
nhãn khách hàng. Bản gốc của cả chín file có trong ZIP private.

98 đường dẫn thiếu trong checkout cũ được lấy từ Git HEAD cho bản chuyển giao.
Đây là tái dựng source snapshot ở thư mục mới, không khẳng định các đường dẫn
trên máy gốc đã hiện diện liên tục. Dự án gốc không bị sửa hoặc khôi phục tại chỗ.

Hai fixture engineering synthetic cần cho graph/mock/legacy receiver được bổ
sung đúng byte. Không có ảnh camera thực được suy ra từ các fixture này.
Giữ attribution và giấy phép asset, font và thư viện theo `NOTICE.md`.

## Phần private được giao riêng

1. Context ZIP cùng manifest export đầy đủ: mô tả file được tách riêng,
   byte gốc trước ẩn danh, nguồn Git/working tree và SHA256.
2. Engineering replay kit cùng manifest từng file: các lượt VIDLIFE12,
   HOSTDIAG11, IPC10; các candidate pools cần thiết, APK và AP artifacts.
3. Image Docker đã dùng, manifest image ID và checksum archive.
4. Log kiểm bản public, tài liệu này và README tiếp nhận riêng.

Bộ này không chứa khóa ký production. Không upload archive private hoặc
manifest có chi tiết khách hàng vào issue/PR/release public. Giao trực tiếp cho
nhóm được anh chỉ định bằng kênh kiểm soát truy cập.

## Phần không nằm trong gói

- Toàn bộ ổ đĩa, `.venv`, Android SDK/system image/AVD userdata và cache máy cũ.
- Tất cả raw log, campaign và gói dữ liệu lịch sử ngoài các root đã kê khai.
- Thiết bị HeraHub, radio/MCU/SDK thật, camera/gimbal, dữ liệu hiệu chuẩn Hera.
- Một universal installer hoặc một bộ beta đã nghiệm thu production.

Vì vậy, “toàn vẹn” ở đây là source snapshot được kiểm kê và các gói đã kê khai
có checksum, không phải lời hứa rằng mọi lịch sử hoặc máy ảo đã được sao lưu.
Nghiên cứu phần thiếu cần baseline mới; không tạo file giả để thỏa hash/gate.

## Cách nhận

Clone/tag -> verify source -> đọc status -> nhận private archives -> đối chiếu
SHA và manifest -> lập môi trường riêng -> mock -> ghi các prerequisite còn thiếu
-> admission -> kiểm thực ngắn. Người nhận ký biên bản theo các mục đã kiểm,
không ký một câu “đã nhận đủ và chạy được” khi mới clone thành công.
