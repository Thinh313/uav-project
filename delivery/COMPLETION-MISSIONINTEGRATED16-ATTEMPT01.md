# MISSIONINTEGRATED16: artifact11 và lượt Android đầu tiên

**NOT READY cho beta hoặc nhiệm vụ bay.** Đã áp dụng artifact11MiB trong đúng phạm vi được phép, đóng gói và chạy một lượt Android. Lượt này thất bại trước khi ArduPilot khởi động. Chưa chạy lại s02 hoặc kiểm 10 phút.

## Đã hoàn tất và kiểm chứng

- User cho phép riêng artifact10→11MiB; Root đối chiếu đúng một hằng cap, hai nhãn lỗi và 11 giá trị reserve/peak/requiredFree tăng1MiB. Mọi giá trị policy khác khớp nguyên bản. HostHealth100ms, writer200ms, freshness250ms, lease200ms, metadata64MiB và guard nguồn/disk/physics/frame/durability giữ nguyên.
- Bộ kiểm áp cho bản11MiB: **58 phương thức đạt** (19 contract, 6 hành trình mock, 3 preview thật, 4 cap11, 26 IO/guard giữ nguyên). Các kiểm cũ phụ thuộc cap10 đã được thay đúng phạm vi, không cộng lại thành số kiểm mới. Hai kịch bản mock quyền/boot có thêm 9 và 4 assertion, không cộng chúng vào số phương thức.
- Metadata từng từ chối trước runtime. Nén filesystem APFS cho các file QA tĩnh của riêng E16 giảm **303.104 byte phân bổ thực** qua hai receipt; byte/SHA/mode/mtime giữ đúng. Không nén/sửa old source, candidate hoặc raw. Quota64MiB không thay đổi; giữ hồ sơ và không tuyên bố inode/đường dẫn cũ hiện diện liên tục.
- HOLD03 SHA `d252426538b5cd62502ca51f41f06f28a76f48dfef47c91d5332d188fb698988`: 140 file giữ nguyên sau kiểm. Source contract120 file,209 writer sites,14 owners.
- Candidate `9e01e2dc55f4c1545388204674b236bb1babf1a6da97fcbc57d383ffaac0190c` đã freeze/full-load. Artifact thực **10.571.776 / 11.534.336 byte**, tính đủ mười pool. Dùng lại APK8bc0a7… và AP/imageARM đã kiểm, không build/ký mới.

## Lượt thực s01

Run `mission16-nominal-short01`, Root owner PID71329, thời gian host44,6451giây gồm khởi động và đóng; exit1. Thu đủ stdout153byte và stderr2.630byte, có SHA và EOF. Android OS đã sẵn sàng; companion có READY, nhưng native producer chưa được nhận. Không AP, ARM, AUTO hoặc bay; không có video publisher thực sự chạy.

Primary quan sát: `PRODUCT_NATIVE_DTO_SIGNED_NATIVE_PRODUCER_SCOPE` trong native.start→status.validate. Terminal giữ FAILED_PHYSICAL_DISPOSAL, không nhận thành normal closure hay PASS; secondaryErrors rỗng. Guardian/emulator/helper đã đóng, không còn PID/cổng của lượt. S01 đã đóng baseline **57file**, giữ nguyên toàn bộ raw và receipt.

Root thử mở nguồn video một lần sau companionREADY, nhận ERR_CONNECTION_REFUSED vì owner đã dừng và đóng server. Đây là hậu quả của lượt thất bại, không phải bằng chứng nguồn video đã chạy hay một lỗi quyền browser. Không reload/retry publisher. Tab lỗi id5 không đóng được bằng API do URL policy chặn trang lỗi data:; tab không có nguồn video/runtime đang chạy. Không đổi firewall hoặc quyền trình duyệt.

## Nguyên nhân được đối chiếu

DTO gốc đúng nonce/PID/APK/source/protocol nhưng là nhánh actor-absent: `actorCreated=false`, `configured=false`, `failed=true`, không có producerPublicKey/signature scope và geometry rỗng. Validator từ chối là đúng; không được dựng khóa giả hay bỏ bước kiểm.

Backup native trước mở Activity có đúng **8file AJ02**, mỗi file23byte và chỉ chứa magic `AERIS_INPUT_JOURNAL_V2`. Java nguồn được giữ cùng APK từ chối `all.length>=8` bằng `INPUT_JOURNAL_GENERATION_QUOTA` trước khi tạo journal/khóa thứ9. Activity bắt lỗi và trả về trước khi gán currentInput, phù hợp DTO đã quan sát.

Đây là đường nguyên nhân có precondition thật và source khớp receipt. Chưa thu trực tiếp fatal stack/thông báo màn hình, nên không loại trừ tuyệt đối một lỗi khởi tạo sớm hơn. Tuy vậy, thời gian chờ dài hơn không thể gỡ điều kiện8file đang có. Không dùng slot s02 cho một retry khởi động chưa có cơ sở.

Chi tiết độc lập: `qa/DIAGNOSTIC-S01-NATIVE-START01.json`,7.361byte,SHA `7e3e318f00f8262f2dbe21d4e6f7e1f9b771f7a377f705d8d906e85fbf2534a2`.

## Quyết định tiếp theo

Đã lập `planning/missionintegrated16/NATIVE-JOURNAL-LIFECYCLE-PROPOSAL.md`: archive/rotation có kiểm, giữ nguyên mọi byte và bộ đếm, quota tổng vẫn hữu hạn, không tự xóa, không phục hồi quyền; cần APK development cô lập và kiểm migration/restart/fault trước lượt mới.

Phương án đổi cách tính giới hạn8journal toàn lịch sử thành mô hình live/archive hữu hạn. Vì user yêu cầu giữ các guard còn lại, **chưa triển khai thay đổi này hoặc xóa/di chuyển journal trên Android**. Câu hỏi xin quyết định phạm vi lifecycle/APK đã gửi; không coi thời gian chờ là đồng ý. S01/candidate và các bản gốc/ENDURE/handoff tiếp tục được giữ nguyên.

Nghiệm thu ngắn đầu-cuối,600giây, mất link/AP reboot và persistence/SAF của bản tích hợp vẫn chưa đạt/chưa chạy. Artifact11 đã được giải quyết; điểm chặn tiếp theo là vòng đời journal native, không phải một kết quả beta hoàn tất.
