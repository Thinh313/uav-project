# MISSIONINTEGRATED16: nguồn và mock trước kiểm Android–SITL

**Trạng thái: NOT READY cho nghiệm thu thực tế. Đã chuẩn bị và kiểm source/mock; đóng gói đang bị guard artifact chặn. Chưa chạy campaign Android–SITL mới, chưa đạt nhiệm vụ đầu-cuối hoặc beta stable.**

Yêu cầu ngày 01/11/2026 là hoàn tất nhiệm vụ rồi kiểm tích hợp 10 phút với video/payload, mất link, reboot và persistence, giữ nguyên mọi guard và bằng chứng cũ. Đợt này tiếp tục bản gốc AERIS, không thay bản bàn giao.

## Đã triển khai

- Nguồn cô lập trong `planning/missionintegrated16`, dùng lại core WRITERSTAGE15, APK development và ArduPilot ARM đã có. Không build hoặc ký mới.
- Luồng nominal: khảo sát/compile/lưu → consent/preflight → discovery typed39 → cấp quyền/upload/readback → video và payload → ARM/duyệt Home sau arm → AUTO → manual/HELD → hoàn tất/review/replay → Android restart/persistence → SAF và receiver nguyên byte.
- Gate lượt dài yêu cầu receipt Root đã kiểm nhiệm vụ ngắn trên cùng candidate/native/AP/model/profile/media. Nó kiểm SHA và nội dung bảy loại receipt, từ chối disarmed, failed-disposal, video/SAF/closure mâu thuẫn, sai boot, sai candidate hoặc dữ liệu bị thay. Đây vẫn là gate metadata, không thay cold replay thực tế.
- Kịch bản dài kiểm 600 giây airborne/video liên tục, manual ngắn rồi thả cần về HELD, cấp quyền payload và thao tác gimbal/chụp rõ ràng tại các checkpoint. Không tuyên bố 600 giây manual, không tự gia hạn quyền hoặc tạo mẫu input từ host.
- Duration 180/760 được truyền nhất quán tới preview, runtime, guardian và monitor. Đã sửa Inventory còn thiếu slot `l01`; danh sách slot nominal dùng chung và vẫn từ chối fault/slot lạ chưa được triển khai.
- Restart kiểm package khớp manifest, PID/process epoch mới, head/plan được phục hồi và quyền không được phục hồi. Package cũ thực tế đã đúng qua subclass Android; nhận định ban đầu ngược lại đã được đính chính, không coi đó là lỗi sản phẩm.

## Kiểm chứng hiện có

Root chạy độc lập **67 phương thức kiểm**: 19 contract/receipt, 6 hành trình mock, 39 regression writer/guard/cap được áp vào nguồn mới và 3 kiểm preview/scope. Một kiểm cũ chỉ cho phép disarmed được thay bằng kiểm hành trình nominal; không cộng các lượt chạy lại thành kiểm mới.

Hai kịch bản mock/replay bổ sung đạt 9 và 4 assertion: khi injected AP context mất, flight/payload quyền cũ bị thu hồi, lệnh chưa rõ kết quả không bị gửi lại, token cũ bị từ chối và review incomplete; khi nguồn mock còn khỏe, yêu cầu sai boot bị từ chối trước upload/đổi adapter. Đây là mock protocol với wire/clock giả có khai báo, **không phải mất link, AP reboot hoặc bay thực trên SITL**. Giữ các kết quả FAIL trước do fixture/assertion sai, sửa ở phiên bản mới và đã dọn fixture.

9 module JavaScript qua kiểm cú pháp, Python qua AST; source contract đóng 120 file, 209 writer sites, 14 owners, envelope 60.686.336 byte. Các byte core writer/durability/physics và policy số vẫn khớp WRITERSTAGE15.

HOLD02: `87ac35b34d1f6428a4f407f6a6211a227cf3dd594c081e09046ac37b988c9d9b`, 139 file được Root đối chiếu. HOLD01 và đầu vào trước sửa scope được giữ riêng; TIP cũ được phục hồi vào snapshot bằng cách bỏ đúng phần Root vừa append và kiểm SHA, không có tuyên bố đường dẫn cũ hiện diện liên tục.

## Điểm chặn chính xác

| Thành phần artifact | Byte |
|---|---:|
| Tất cả pool hiện có | 10.203.136 |
| Object mới, đã tái dùng object readonly khớp SHA | 278.528 |
| Manifest và namespace dự phòng | 122.880 |
| Tổng dự toán | **10.604.544** |
| Trần đang có hiệu lực | **10.485.760 (10 MiB)** |
| Vượt trần | **118.784 (116 KiB)** |

Builder và Root độc lập nhận cùng refusal trước mọi ghi candidate/actor. Không tạo object rồi lách forecast, không bỏ pool hoặc xóa candidate cũ. Yêu cầu tăng riêng artifact lên 11 MiB đã gửi và **chưa được coi là được phép**. Giữ nguyên HostHealth100ms, writer200ms, freshness250ms, lease200ms, metadata64MiB, floor10GiB/reserve256MiB cùng mọi quota/guard khác.

Pure preview dùng Inventory thật cho cả s01/180 và l01/760 đã qua metadata/disk ở trạng thái trước đóng gói. Nó tắt kiểm candidate vì candidate chưa tồn tại, nên không phải admission cuối. Sau khi có quyết định artifact, phải đóng gói, full-load, kiểm preservation và admission mới trước actor; không dùng con số preview cũ thay kiểm thực tế.

## Chưa nghiệm thu

| Yêu cầu | Trạng thái |
|---|---|
| Source và mock nominal | PASS trong phạm vi nêu trên |
| Nhiệm vụ ngắn Android–SITL hoàn tất | NOT RUN, chặn đóng gói |
| Tích hợp 600 giây với video/payload | NOT RUN, phụ thuộc nghiệm thu ngắn cùng candidate |
| Mất link/AP reboot trên runtime tích hợp | Chưa triển khai fault entry/oracle thực; chỉ có mock thu hồi quyền |
| Persistence/restart và SAF trên Android của bản này | NOT RUN |
| HeraHub/payload/drone thật, production | Ngoài phạm vi đợt này |

Không dùng kết quả WRITERSTAGE15 disarmed hoặc số kiểm mock để công bố nhiệm vụ hoàn tất. Không cộng thời gian các lượt cũ. Các slot fault vẫn fail closed trước actor cho đến khi có implementation/oracle riêng; chúng không thể tạo nominal PASS.

## Bảo toàn và tiếp tục

Nguồn/candidate/ENDURE/handoff cũ giữ nguyên theo các baseline đã có và đối chiếu cuối. 98 đường tracked thiếu từ trước không thay đổi, không stage/restore/xóa thêm. Không commit/push trong task này. Các fixture mock đã dọn, tab `about:blank` dùng kiểm quyền browser đã đóng; không có publisher/runtime mới. Docker image prune thu hồi 0B, không prune container/volume.

Bước tiếp khi được phép đóng gói: source/cap amendment có kiểm riêng → freeze/full-load/admission → một nhiệm vụ ngắn với video/payload và đóng managed → Root cold replay frame/clock/RC/native/video/SAF → mới cho phép lượt 10 phút. Sau đó hoàn thiện fault injection thực, giữ hồ sơ gián đoạn incomplete, kiểm boot và recovery không khôi phục quyền.

Hồ sơ chính: `BUILDER-HOLD02.json`, `ROOT-QA-GATE02.json`, `ROOT-READINESS02.json`, `BUILDER-OBJECT-COSTS02.json`, `qa/ROOT-CONTEXT-LOSS01.json`, `qa/ROOT-BOOT-IDENTITY01.json`, `PRESERVATION-VERIFY02.json`. Tất cả nằm trong `evidence/missionintegrated16`; raw chưa được tạo.
