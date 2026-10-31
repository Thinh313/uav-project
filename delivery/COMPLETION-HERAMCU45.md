# HERAMCU45 · completion · 2026-10-15

STATUS: DONE trong phạm vi chuẩn hóa contract và kiểm host mock/replay. OVERALL: READY để review phần chuẩn bị tích hợp; **chưa sẵn sàng kết nối MCU HeraHub thật**. Một agent tách bước specification/build/verify, không phải kiểm định độc lập.

## Kết quả

`pilot/heramcu45/contract.json` revision45.2 giữ 16 nhóm message và21 nhóm enum từ DOCX, có nguồnSHA/block literal. Tách document claim, unknown và policy mock; 16 vấn đề còn thiếu giữ UNRESOLVED. XML dialect/ID/CRC_EXTRA/USB/addressing/firmware chưa rõ nên codec vật lý luôn từ chối. Không tự gán ID, sửa trimuint8 hay diễn giải hệ sốmapping chưa có nghĩa. Cổng RF và RC output là namespace riêng; quan hệ của chúng trong mock chỉ là topology đề xuất.

Handshake, calibration9nhóm, mapping2cổng/16kênh, SAVE→readback, mất USB/reboot/sai nguồn/ACK trễ/trùng, deadline và guard tài nguyên đã kiểm bằng JSON logicalmock. Nguồn pin/RF/kênh có tuổi dữ liệu; ACK không thay kết quả calibration hoặc bằng chứng lưu. Sau restart phải handshake/readconfig mới; historical replay không cấp controller hoặc quyền input. Thay cấu hình mới xóa cờ readback thành công cũ. Không tích hợp native44/Fly hoặc bất cứ transport thật nào.

## Verify và coverage

R45-01..08: 8/8 trong phạm vi mock được giao; không phải tỷ lệ trưởng thành sản phẩm.

| Requirement | Kết quả và evidence |
|---|---|
| R45-01 | 14.074 đường dẫn bảo vệ, inventoryENDURE5.051 và SHA nguồn chụp; floor20GiB/budget16MiB, `verification1.json` |
| R45-02 | source-manifest, DOCX/XML/sáu sơ đồ, blocks và contract; 16unknown/16message/21enum, provenance QA |
| R45-03 | `corpus5.json`, `mock5.json`: identity/config transaction, deadline, sai target/session/boot, rediscovery |
| R45-04 | calibration9nhóm, ACK≠result, min/trim/max/pressed-mask, cancel/timeouts/partial-result retention, saved readback |
| R45-05 | mappingtyped/bounds/ports/invert, ACK/save/readback faults, freshsession after mockreboot; `mock-reboot-readback4.json` |
| R45-06 | pin/RF/channel freshness, duplicate/reorder/clock/boot/USB loss, portscope; no automaticretry or failover |
| R45-07 | 76/76 corpus, 50/50 supplemental in `qa4.json`: UTF8/chunks/EOF/bounds, rehashed adversaries, seal and expected externaldigest |
| R45-08 | 115/115 prior native33/35 tests; cold43 corpus38+lifecycle4+3actualtrace sessions, cold42 actual13; syntax/finalpreservation/fingerprints/report |

Technical health: verifier41/41, JS syntax9/9, 0 syntaxerrors; 76/76 corpus và50/50 supplemental PASS.

Build APK/native/firmware không chạy; không có typechecker/linter mới hoặc dependency install. JS syntax được verifier kiểm trên toàn module; số kiểm metadata/syntax tách khỏi126 ca corpus/supplemental và115 regressions. Không cộng các run cũ để tăng số PASS.

## Lịch sử lỗi và giới hạn integrity

Giữ nguyên corpus1/mock1 75/76: test dừng ở254events, trong khi lần255 mới bị guard chặn. Đã bổ sung lần thử còn thiếu; không nới giới hạn. QA1 giữ lỗi oracle xóa một event không đổi state rồi đòi replay phải phát hiện; hồ sơ prefix semantic hợp lệ không thể bị coi là sai chỉ vì thiếu event vô tác dụng nếu không có expected history. Thêm replay schema2 seal/count/tail/bodySHA và phép so expected digest; test đổi sang xóa final configuration readback, đồng thời kiểm prefix re-sealed phải không khớp digest gốc. Hash/seal không phải chữ ký hoặc xác thực. Không tuyên bố phát hiện mọi lịch sử giả nhưng tự nhất quán khi không có digest đáng tin từ bên ngoài.

Các run trung gian corpus2..4/QA2..3 giữ nguyên theo contract/source tại lúc chạy. Current acceptance dùng corpus5/mock5 +QA4 và source cuối. Verification pin source và fingerprint tập evidence, không ký phần mềm.

Tài liệu gốc ở ba đường dẫn Downloads đã thiếu tại lượt trước. Bản chụp ba file đúng SHA vẫn có trong `evidence/heramcu45/sources`; verifier ghi riêng tồn tại đường dẫn gốc và tính toàn vẹn bản chụp. Không khôi phục hay thay file gốc trong task này, không suy ra đường dẫn gốc hiện diện liên tục. Hera16,5kg/H và request3,5kg giữ tách ngữ cảnh, không tạo profile vật lý đã hiệu chuẩn.

## Bảo toàn, dọn dẹp và bước tiếp

Không sửa source/candidate/SOT/trust/ENDURE; không retry campaign, tạo chữ ký/APK, chạy SITL/emulator/server, càiSDK hay gửi lệnh bay. Không tạo scratch/projectcopy/tmp/install/runtime riêng; không có tiến trình để giữ lại hoặc thư mục scratch để xóa. Giữ toàn bộ thất bại và evidence nhỏ. Disk từng xuống dưới sàn ở lượt trước đã được báo/PARTIAL; không tuyên bố liên tục đạt sàn qua khoảng đó. Lượt tiếp tục có admission thực và kiểm floor trước các batch/receipt; số free/allocated cuối nằm trong verifier.

Bước kế tiếp cần dữ liệu: XML/generated headers đúng MCU firmware, firmware/hash/compatibility HeraHub, USB descriptors và capture handshake/config/broadcast; xác nhận 16unknown trước khi làm codec/transport thực. Trong lúc chưa có dữ liệu có thể dùng module này làm contract harness, nhưng không gắn vào input điều khiển thật.
