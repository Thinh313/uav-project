# G5: tương thích đóng review Fly mock cũ

Ngày 22/10/2026. **ĐẠT trong phạm vi source/mock/protocol replay. Beta sản phẩm: NOT READY.**

Đã bổ sung entry cô lập `pilot/beta06g5r1/entry.mjs`, sửa luồng đóng và lưu review của Fly mock cũ. Không sửa byte source/candidate đã đóng băng hay bằng chứng ENDURE; không tích hợp hoặc khởi chạy Android–SITL, listener, build, cài APK hay ký mới.

## Kết quả và nguyên nhân

G5 cũ áp hợp đồng đóng hồ sơ SITL cho run mock. Mock dùng run `m…`, nguồn `MOCK_PROTOCOL_REPLAY_NOT_AP`, không có owned AP closure; vì vậy review hợp lệ bị coi là chưa xác minh. Entry mới dùng `FLIGHT_REVIEW_MOCK_REF` riêng, trả `CLOSED_REVIEW_INDEXED` tương thích phân loại thành công của UI G5, và đọc lại được qua strict Store/lịch sử sau reload. UI và entry G5 gốc vẫn giữ nguyên.

Bản sửa ràng buộc đúng run, workspace, session, model, plan, review và chuỗi SHA raw. Không tạo closure giả, không đổi mock thành SITL. Lỗi index, quota/fsync, mất receipt, ghi outcome/journal hay phản hồi sau effect giữ trạng thái pending/unknown, chặn tiếp tục sau reload, không tự retry effect hoặc khôi phục quyền. Dấu host `res.end` đã trả về không được coi là client ACK hoặc bằng chứng giao tới thiết bị.

## Ma trận nghiệm thu

| Yêu cầu | Kết quả | Bằng chứng |
|---|---|---|
| Luồng protocol mock qua handler thực | PASS | QA run `m4129ecd1b1e6498a9409`: connect → preflight → cấp quyền → upload/readback → arm/duyệt Home → AUTO → về đất mock → close |
| Đóng review, strict Store, history/reload | PASS | Một `FLIGHT_REVIEW_MOCK_REF`; 947 dòng raw; 26 file bằng chứng giữ lại; quyền không tự khôi phục |
| Đối chiếu raw độc lập | PASS trong mock | Canonical replay: 420 RX, 93 TX, 12 mission items, hai chu kỳ readback; ảnh thực = 0 |
| Manifest/source/compiled boundary | PASS, 11 nhóm | Sai pin, cache, recipe, đường dẫn hoặc manifest bị từ chối trước app writer |
| Chống review/raw/identity bị sửa hoặc nhầm mode | PASS, 23 nhóm | Mutations có tính lại SHA vẫn bị kiểm semantic/context phát hiện |
| Lỗi sau đóng và restart/reload | PASS, 5 kịch bản | Abort protocol mock thực; fault injection quota/fsync/mất receipt/outcome/response; không lặp effect |
| Nhánh đóng SITL cũ và phân tách mode | PASS, 9 nhóm | So sánh thuần archival với G5/R2 nguyên bản, dùng sealed bytes cũ/result stub, không chạy SITL mới |
| Bảo toàn baseline | PASS | 6.770 đường dẫn đối chiếu chính xác lstat/mode/link/bytes/SHA; 700 pin cũ + 5 module mới; 3 compiled artifacts và 16 file freeze khớp |
| Android, browser delivery, SITL mới, thiết bị thật | NOT_CHECKED | Chưa chạy theo phạm vi người dùng yêu cầu |

QA độc lập: 50 nhóm gồm hành trình đầy đủ, canonical replay và 48 nhóm kiểm chuyên biệt trên overlay08 cố định. Builder còn có 35 nhóm kiểm riêng; không cộng các số này thành chứng nhận chất lượng sản phẩm hay độ tin cậy ngoài thực địa. Các fault là chèn lỗi có kiểm soát, không phải sự cố ổ đĩa thật.

## Giới hạn và lỗi được giữ lại

Một lượt QA đồng thời hết hạn heartbeat ở preflight; raw và receipt lỗi được giữ, nguyên nhân thiếu các renewal thành công chưa được chứng minh. Lượt tuần tự cuối bổ sung ghi đo renewal và heartbeat rõ ràng trước thao tác bên cạnh timer 750 ms; source và TTL 3.000 ms không thay đổi. Lượt này đạt; không suy ra bảo đảm timing/tải đồng thời. Các lượt cũ khi source/pin đang đổi cũng được giữ riêng, không gộp vào PASS overlay08.

`accepted` và `executionVerified` chỉ có ý nghĩa protocol mock. Chưa chứng minh AP execution, độ đúng vật lý, ảnh/video thực, điều khiển Hera, UI Android hay beta. Entry hiện chỉ dành cho kiểm in-process; chặn listen và actual SITL connect/action. Kiểm Android–SITL đồng thời video/payload, mất link/reboot và persistence vẫn là gate tiếp theo khi được phép chạy runtime; task này chưa mở gate đó.

Baseline có 95 đường dẫn tracked thiếu từ trước, đã ghi riêng trong preservation; không khôi phục và không khẳng định toàn bộ repository từng hiện diện liên tục. Prepared workspace G5 (20 file/870.221 byte) vẫn chưa bị tiêu thụ, không thêm first-writer/SAF claim. Không dùng LLM baseline cho sửa tương thích tất định này.

## Định danh và bàn giao

- Overlay: [overlay-pins08.json](../evidence/beta06/generation05-mockcompat01/overlay-pins08.json), SHA `f88475606fc8eae8e8136c4f4e8056f9f0692c4e7bf0e6c8c94ef581f987be6e`.
- [QA gate độc lập](../evidence/beta06/generation05-mockcompat01/qa-independent-gate01.json), SHA `b63d11d155740362d778ecea42019e89f202d2e923c492bb91250ce7f9087e1f`.
- [Handover kỹ thuật](../planning/beta06g5r1/BUILDER-HANDOVER01.md), [TIP](../planning/beta06g5r1/TIP-MOCK-REVIEW-COMPAT01.md), [ADR](../planning/beta06g5r1/ADR-MODE-AWARE-REVIEW01.md).
- [QA preservation](../evidence/beta06/generation05-mockcompat01/qa-final-preservation01.json) và [Root corroboration](../evidence/beta06/generation05-mockcompat01/root-final-preservation01.json).
- Nguồn đóng băng: [builder-source-freeze01.json](../evidence/beta06/generation05-mockcompat01/builder-source-freeze01.json); SHA `7b9488c58258db16d726ad671ea1824c27235d1f50eee4b56d52b5505b946a2f`.

Kiểm entry nguồn: `node planning/beta06g5r1/verify-overlay01.mjs evidence/beta06/generation05-mockcompat01/overlay-pins08.json` trả PASS_SOURCE_OVERLAY_ONLY. Lệnh này không chạy hành trình UI hay AP.

Dung lượng tại chốt báo cáo: 34.75 GiB, trên sàn 20 GiB. Không tạo project copy, dependency install, build cache hay Docker image. Đã xóa riêng fixture âm tính của task và script tạm; giữ bằng chứng dương tính và lỗi thật. Danh sách đường dẫn đã dọn:

- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/flight/runs/m2beb8599d6994b0abbc5`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/flight/runs/m38760de7429143e4946d`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/flight/runs/m44d85970fbfe4cd7b11b`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/flight/runs/m56a038004d094b849dd9`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/flight/runs/mfdda65cbec9f4ee1ab6a`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-mock-seal-negative-scratch01`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-mock-seal-negative-scratch02`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-overlay-negative-scratch01`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-overlay-negative-scratch02`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-reload-scratch-lost-receipt`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-reload-scratch-outcome-write`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-reload-scratch-response-end-marker-write`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-reload-scratch-zero-row-fsync`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-reload-scratch-zero-row-quota`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-scratch-lost-receipt`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-scratch-outcome-write`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-scratch-response-end-marker-write`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-scratch-zero-row-fsync`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-pending-scratch-zero-row-quota`
- `/Users/os/Downloads/AI technique/aeris/evidence/beta06/generation05-mockcompat01/qa-sitl-delegation-scratch01`
- `evidence/beta06/generation05-mockcompat01/codex-tmp-mockcompat-tests-20261022`
- `/private/tmp/codex-tmp-mockcompat-write-20261022.py`
