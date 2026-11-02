# BETA-RC01: kiểm SDK và bản sửa H5

NOT READY. Chưa nghiệm thu BETA-RC01 hoặc beta stable. Đã thực hiện kiểm Android SDK, sửa nguồn cô lập và kiểm mock; chưa chạy AP/SITL hay gửi lệnh bay trong milestone này.

Kết quả thực tế

m301: một lần cài đúng APK development hiện có bằng push/no-incremental, guest sync thành công, SDK exit 0. m302: kernel boot mới; package/UID10141/SHA đúng tại mốc 0 và 30 giây; TAR dữ liệu riêng vẫn đủ 70 file và 5 thư mục, khớp nguồn N02. Tuy nhiên SDK abort khi đóng, exit -6. Owner exit 0 không phải SDK đóng sạch. Crash dump được giữ đúng byte và gắn PID41369; nguyên nhân SIGABRT chưa xác định.

Sửa đã hoàn tất ở mức source/mock

Helper H4 chủ động chuyển quan sát thành công sang fail_case nên không kiểm nhánh đóng SDK bình thường. H5 dùng đóng quản trị có chứng cứ từ raw command/TAR, monitor NO_ACTOR và guardian bình thường; không khai pendingTransactions=0, không giả bằng chứng bay. QA còn bắt lỗi tên báo cáo closing không hợp lệ; đã sửa thành owner-terminal.json với bốn tham chiếu và giới hạn 4096 byte. Sáu phương thức mock cuối của Builder đạt; Root kiểm thêm đường dữ liệu/giả mạo và lời gọi writer thật. Đây là kiểm chồng phạm vi, không cộng thành số ca sản phẩm độc lập. QA độc lập H5 HOLD02 không còn P1 trong phạm vi đã rà. Hai lượt SDK mới m401/m402 chưa chạy; chưa chứng minh H5 xử lý được SIGABRT.

Giới hạn tài nguyên đang chặn

Đã áp dụng đúng quyền artifact 12 MiB và metadata 66 MiB. Dự toán nguồn H5 đã kiểm: artifact 12,697,600 byte so với cap 12,582,912, vượt 114,688 byte (112 KiB). Metadata hiện tại 8,904,704 + future owner envelope 60,686,336 = 69,591,040 byte so với cap 69,206,016, vượt 385,024 byte (376 KiB). Báo cáo/QA cuối này còn phải được tính thêm trong admission kế tiếp. Đủ cả 11 pool cũ; không bỏ lịch sử để giảm số. Disk khoảng 25 GiB, disk admission đạt. Không cần dọn ổ đĩa cho điểm chặn này. Chưa freeze H5, chưa tạo actor/slot m401/m402. Gate05 draft dùng nhầm số lượng product pins đã bị validator từ chối trước mọi mutation; Gate06 dùng đầy đủ mapping 188 pin và mới được dùng cho dự toán.

Phạm vi bảo toàn

Đối chiếu cuối 9.981 đường dẫn baseline về byte/kích thước/mode. Source/candidate cũ và ENDURE giữ nguyên; không tuyên bố đường dẫn luôn hiện diện liên tục trong lịch sử. H5 gồm 132 source file, 188 product pin; 14 owner và future envelope 60.686.336 byte giữ nguyên. H4 nguồn, helper, candidate và raw lỗi được giữ. Các byte H5 HOLD01 bị thay khi sửa P1 đã được lưu trong HOLD01-TERMINAL-WRITE-ORIGINALS.tar.gz trước khi ghi HOLD02. Không build hoặc ký APK mới, không commit/push, không sửa hai bản bàn giao. Giữ freshness250ms, HostHealth100ms, writer200ms, input lease200ms, speedup1/cap500ms và sàn đĩa10GiB.

Bước được chuẩn bị để tiếp tục

Cần quyền tăng riêng artifact lên 13 MiB và metadata lên 68 MiB cho bản cô lập để vượt dự toán hiện tại, giữ mọi guard còn lại. Sau quyền mới phải cập nhật policy có nguồn, kiểm regression và tính lại toàn bộ trước freeze; các con số đề xuất không thay admission thực tế. Sau đó: hai cold boot mới không cài lại, mỗi lượt kiểm package/UID/SHA/private và normal SDK exit0; QA độc lập mới cấp proof cho G1. Tiếp theo mới mở G2 hai dạng nhiệm vụ, G3 fault/restart, rồi G4 600 giây đang bay. Bất kỳ crash/unknown/forced kill hoặc guard fail đều từ chối nghiệm thu, giữ nguyên raw và không tự retry. Chưa thể xác nhận điều khiển Hera, camera/gimbal thật hoặc phát hành production.

## Bốn cổng nghiệm thu

| Cổng | Trạng thái | Phạm vi |
|---|---|---|
| G1: vòng đời native và SDK | BLOCKED | APK giữ đúng qua cold boot; SDK m302 SIGABRT (-6). H5 mới chỉ qua source/mock. |
| G2: polygon và corridor đầu-cuối | NOT RUN | Chờ G1 thật; cùng candidate, Android public UI và SAF. |
| G3: mất link, AP reboot, native restart | NOT RUN | Chờ cả hai nhiệm vụ G2; không tự khôi phục quyền. |
| G4: tích hợp 600 giây đang bay | NOT RUN | Chỉ mở sau mọi gate ngắn đạt; không cộng thời gian idle hoặc nhiều lượt. |

## Hồ sơ

- [H5 HOLD02](/Users/os/Downloads/AI technique/aeris/planning/betarc01/runtime-h5/BUILDER-RUNTIME-H5-HOLD02.json)
- [QA độc lập H5](/Users/os/Downloads/AI technique/aeris/evidence/betarc01/qa/INDEPENDENT-H5-HOLD02-REVIEW.json)
- [QA thực tế m301](/Users/os/Downloads/AI technique/aeris/evidence/betarc01/qa/INDEPENDENT-M301-PUSH-SYNC-COLD01.json)
- [QA thực tế m302](/Users/os/Downloads/AI technique/aeris/evidence/betarc01/qa/INDEPENDENT-M302-COLDBOOT01.json)
- [Crash dump m302 và định danh PID](/Users/os/Downloads/AI technique/aeris/evidence/betarc01/qa/ROOT-M302-SDK-CRASH20.json)
- [Dự toán đầy đủ, chưa freeze](/Users/os/Downloads/AI technique/aeris/evidence/betarc01/ROOT-H5-PURE-FREEZE-METADATA04.json.gz)
- [Đối chiếu cuối](/Users/os/Downloads/AI technique/aeris/evidence/betarc01/qa/ROOT-H5-FINAL-PRESERVATION24.json)

Lập lúc 2026-11-01T14:37:22.339314+00:00. Tổng trạng thái: **NOT READY**.
