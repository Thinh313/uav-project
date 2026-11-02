# BETA-RC01: nguồn và mock đã kiểm, admission đang chặn

**NOT READY cho Android–SITL/Beta.** Đã hoàn tất triển khai và kiểm code/mock của bốn cổng. Chưa tạo candidate mới, chưa mở Android/AP hoặc kiểm 10 phút trong milestone này. Không dùng kết quả mock hoặc thời gian chờ làm nghiệm thu runtime.

## Nguồn đã chốt

Runtime HOLD02: `planning/betarc01/runtime/BUILDER-RUNTIME-HOLD02.json`, SHA256 `6561853f6971ec1a555fb0ae7dd567a13a77d8b3c15b97ae5b20e35232c4304d`.

Archive HOLD01: `planning/betarc01/archive/BUILDER-HOLD01.json`, SHA256 `2ee3f533adf6e10c16f90441919efa2df4619d67028e61d7fe8f5ecc25d4ab74`.

Nguồn chọn gồm 129 file runtime, 182 product pin, contract ghi đóng 243 vị trí/14 owner; ngân sách ghi dự phòng vẫn 60.686.336 byte. Tái dùng APK development Native17 đã kiểm, không build/ký APK mới. Candidate cũ, Native17, ENDURE và hai bản bàn giao không được sửa. Đối chiếu trước launch đạt 9.645 đường dẫn tham chiếu; 98 tracked deletion có sẵn giữ nguyên.

## Các cổng đã triển khai, chưa chạy thực

| Cổng | Đường triển khai | Bằng chứng hiện có | Trạng thái thực |
|---|---|---|---|
| G1 | Quan sát APK/dữ liệu lạnh, adoption không cài lại, APPLY, hai phiên native, lưu và đọc workspace | Code, mock, source review độc lập | NOT RUN |
| G2 | Polygon và corridor, preflight, upload/readback, manual/assisted, AUTO, video/payload, review, restart và SAF | Mock orchestration, OnceStore/receipt/TAR, source graph | NOT RUN, phụ thuộc G1 |
| G3 | Mất link, AP dừng/reboot, native restart; quyền bị thu hồi, review incomplete; boot probe chỉ đọc ở context mới | Fault/pipe/StageDrainer mock; source review; không nới require_alive | NOT RUN, phụ thuộc G1/G2 |
| G4 | Khoảng airborne tích hợp 600 giây; cold proof cùng release cho cả bảy loại case | Clock/orchestration và prerequisite mock; không tính idle/bootstrap/export là thời gian bay | NOT RUN, phụ thuộc các cổng trước |

Reboot probe dùng context mới với dữ liệu cold-config riêng, không dùng `-w`, không Activity/input/companion và không khôi phục quyền. Nó không chứng minh EEPROM hoặc nhiệm vụ onboard được giữ qua reboot. Actual CRC, boot clock, frame completeness và vận hành của probe vẫn cần kiểm thực.

## Những sửa chữa kiến trúc quan trọng

- Dự toán số generation trước Activity, có kế hoạch archive và dự phòng hữu hạn. Journal chưa rõ trạng thái không được xoay vòng; không xóa dữ liệu để nhận thêm quota.
- Kiểm đầy đủ P256/STATUS/ACK/RC/clock của hồ sơ đã đóng ở bước offline sau khi actor cũ đóng. Runtime chỉ đối chiếu original inventory và capsule do Root kiểm độc lập, không tạo thêm child ngoài process budget.
- PREVIEW/APPLY cho registry đã enroll có adapter receipt riêng; không dùng nhánh initial unenrolled làm đường tắt.
- Maintenance không khởi động monitor được đóng theo đúng `CLOSED_NO_ACTOR_NOT_ACCEPTANCE`, không gán `durablyDrained=true`. G1 và nhiệm vụ bay vẫn yêu cầu monitor drain bình thường.
- Review khi mất link/reboot đi qua nhánh incomplete, không dùng nút đóng nhiệm vụ hoàn tất.
- AP mới không dùng lại backend/clock/frame của context đã lỗi. Phiên lỗi cũ được giữ nguyên, probe mới chỉ đọc.

## Phạm vi kiểm

Root đã chạy sáu nhóm mock ban đầu và các kiểm delta; reviewer riêng đối chiếu toàn bộ HOLD02, snapshot, archive và đồ thị nguồn. Các kiểm gồm real filesystem/OnceStore với FakePopen không tạo child, orchestration UI, pipe và StageDrainer, 15 ca crypto P256/AJ02/AJZ/RC/clock tổng hợp, các ca registry và cleanup offline. Các bộ có phần trùng và có static assertions; không cộng thành chứng nhận chất lượng sản phẩm.

Receipt độc lập cuối: `evidence/betarc01/qa/INDEPENDENT-FINAL-HOLD02-REVIEW.json`. Không còn P1 được nhận diện trong phạm vi source/mock đã review; điều này không thay nghiệm thu Android/AP thực.

## Refusal trước actor

Pure freeze đã từ chối trước mọi ghi candidate:

| Ngân sách | Dự toán | Trần hiện tại | Vượt |
|---|---:|---:|---:|
| Artifact, tính đủ 11 pool | 11.767.808 B | 11.534.336 B (11 MiB) | 233.472 B (228 KiB) |
| Metadata hiện có + ghi dự phòng | 68.198.400 B | 67.108.864 B (64 MiB) | 1.089.536 B (~1,04 MiB) |

Metadata là ngân sách admission gồm phần dự phòng, không phải tuyên bố runtime đã ghi hết số byte đó. Số liệu này là forecast trước candidate, không phải admission cuối. Đĩa đạt dự toán và nguồn AC đã quan sát; guardian vẫn phải kiểm live trước launch.

Root đã gửi đề nghị ngoại lệ riêng artifact 12 MiB và metadata 66 MiB, giữ mọi guard khác; **chưa coi việc hiển thị câu hỏi là đồng ý**. Không tăng cap, loại pool, xóa bằng chứng hay chạy actor trong lúc chờ.

Hai probe nén filesystem trên fixture riêng không tạo được bằng chứng byte-exact dùng được; không áp dụng lên nguồn/artifact. Mọi fixture riêng đã xóa sau phép thử, các receipt thất bại giữ nguyên. Không dùng nén chưa kiểm để lách admission.

## Tiếp tục sau quyết định

Nếu được cho phép ngoại lệ: sửa đúng hai ngân sách trong nguồn cô lập, cập nhật reserve/forecast tương ứng, kiểm tất cả predicate và cold reader, tạo HOLD/gate mới. Sau đó pure freeze, full load, preservation và admission mới. Chỉ khi đạt mới mở G1; G2/G3 và lượt 600 giây tiếp tục theo prerequisite cùng candidate, không retry kết quả chưa xác nhận.

Nếu giữ trần hiện tại: bàn giao code/mock ở trạng thái NOT READY, bảo toàn hồ sơ và không mở Android–SITL. N02 cũ vẫn `UNCONFIRMED_COMMAND_RECEIPT_NOT_PERSISTED`; không đổi thành cài thành công.

Các giới hạn còn nguyên ở checkpoint này: freshness 250 ms, HostHealth 100 ms, writer 200 ms, input lease 200 ms, speedup 1/cap 500 ms, đủ frame/fsync trước sensor, disk floor 10 GiB + reserve/forecast, native journal 64 MiB, export 192 MiB và các guard nguồn/tiến trình/danh tính. Không HeraHub, SDK, drone thật, production signing hoặc công bố ra ngoài.
