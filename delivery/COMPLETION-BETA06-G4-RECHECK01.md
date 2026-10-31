# BETA06 · Android–SITL · Recheck 01

Ngày 22/10/2026 · **OVERALL: NOT READY**

Đã kiểm lại quyền browser và chạy được luồng Android cockpit → host companion → ArduPilot SITL. N1 hoàn thành AUTO, quay về và disarm gần Home với video và thao tác payload mock cùng hoạt động. Chưa nghiệm thu trọn milestone: hai lỗi kết thúc phiên làm chiến dịch dừng ở một lượt AP; mất link, reboot, N2/F2 và persistence qua restart của lượt này chưa chạy.

## Kết quả thực tế

| Hạng mục | Kết quả và phạm vi |
|---|---|
| Nhiệm vụ AUTO | PASS raw nominal SITL: 17.150 bản ghi, 12 item upload, hai chu kỳ readback khớp, không ghi tham số. Lệnh camera 206 được giữ nguyên. |
| Hoàn tất bay | RTL, gần Home, ground và disarm được xác minh từ raw. Tiêu chí takeoff dùng đúng quy tắc FIELD02_TAKEOFF01 đã đóng băng; không đổi thước đo sau kiểm. |
| Video Android | PASS cửa sổ 30 giây đã chọn: 29,57 FPS; giới hạn trên độ trễ P95 45,41 ms; khởi tạo 220,2 ms; phục hồi sau pause chủ đích 500 ms: 585,8 ms. Không suy rộng thành toàn bộ thời gian bay. |
| Payload đồng thời | Hai sự kiện camera/gimbal mock trong AUTO, có đối chiếu raw tại cao độ tương đối 8,018 m và 10,008 m. 74 điểm quan sát cùng ngữ cảnh; không chứng minh hoạt động liên tục cả cửa sổ. |
| Ảnh và định vị | JPEG tổng hợp 55.091 byte, manifest/sidecar/SHA và journal COMMITTED khớp nguồn, run, boot và nhiệm vụ. Số ảnh thực: 0. Thời điểm phơi sáng vật lý: UNKNOWN. |
| Đóng bay | Container đúng CID đã dừng, exit 0, không OOM, raw/review/log giữ lại; không retry Close hoặc khôi phục quyền. |
| Mất link/reboot | NOT RUN trong chiến dịch này. Không dùng bằng chứng các lượt cũ để thay thế. |
| Android persistence/restart | Snapshot trước/sau trong cùng boot khớp 19 file và 34 bản ghi. Đây chưa phải kiểm restart; 13 PENDING và 3 thao tác SAF còn lại được giữ nguyên. |

## Hai lỗi P1 và bản sửa cô lập

1. **Chờ kết thúc sai phase.** Helper yêu cầu nhãn DISARMED, nhưng UI vẫn phát stage AUTO sau khi armed=false và canonical completion đã hoàn tất. Lượt chờ 120 giây timeout được giữ nguyên là FAIL. Bản sửa pure offline dùng completion cùng telemetry và ngữ cảnh mới, giữ nguyên lớp kiểm dispatch, không suy ra disarm từ nhãn.
2. **Close đã có hiệu lực nhưng UI báo JSON_TYPE.** Review có 842 khóa SHA vượt giới hạn 64 khóa/object của serializer. Flight đã đóng và review riêng đã lưu, sau đó ghi chỉ mục workspace mới lỗi. Bản sửa pure offline tạo tham chiếu nhỏ gắn SHA/byte/path tới review đã seal, giữ đầy đủ execution; nếu chỉ mục lỗi thì báo trạng thái pending, không báo chưa thực thi và không retry tác dụng đã hoàn tất.

Hai bản sửa nằm riêng trong planning/beta06g4r2 và pilot/beta06g4r2. Builder và QA đã kiểm source/mock các biên freshness, identity, quota, mất receipt, seal sai và chống đóng lặp. **Chưa ghép vào app, chưa kiểm lại trên Android–SITL, chưa sửa receipt cũ hoặc journal cũ.** Fixture trước Close là phép chiếu suy ra từ các điểm bằng chứng đã giữ, không phải bản dump toàn trạng thái đồng thời.

QA tổng hợp: PASS trong phạm vi source/mock, không còn P1 chưa xử lý ở hai module mới. Đã tái chạy 15 ca completion, 7 nhóm chỉ mục review và 18 nhóm biên độc lập bổ sung; các số này không thay thế lượt kiểm Android–SITL. Toàn bộ 843 file của N1 đã đóng giữ nguyên SHA.

## Bảo toàn và vận hành

- 5.287 đường dẫn baseline: 5.286 khớp nguyên trạng; chỉ journal workspace02 nối thêm phần được phép, prefix cũ khớp SHA. 16 blob cũ không đổi.
- 653 pin production và source/candidate/ENDURE trong baseline giữ nguyên. Một số đường dẫn lịch sử đã thiếu trước lượt này vẫn được ghi nhận riêng; không tuyên bố cả repository nguyên vẹn hay hiện diện liên tục.
- Emulator, host companion, controller và các cổng sở hữu đã đóng; container và volume giữ lại.
- Dung lượng thấp nhất ghi nhận: **38,42 GiB**, trên sàn 20 GiB. Không build, cài lại hoặc ký APK mới.
- Docker image prune thu hồi 0 byte; không xóa container, volume hay bằng chứng. Các thư mục fixture nhỏ do kiểm mock tạo đã được dọn theo receipt QA/Builder.

## Bước tiếp theo

Đưa hai sửa lỗi vào một bản tích hợp cô lập có pin mới cho chính harness đó, giữ nguyên candidate sản phẩm và ENDURE. Kiểm mock admission trước, rồi lập chiến dịch hữu hạn mới để chạy N1 → mất link/thu hồi quyền → N2 → reboot → review/persistence và SAF trong ngân sách đã duyệt. Không mở lại chiến dịch lỗi hay xóa latch để tiếp tục.

**Giá trị đã đo:** Android điều khiển được nhiệm vụ AUTO SITL cùng video/payload mock trong phạm vi trên. Không có benchmark vượt DJI, phần cứng Hera, camera thực hoặc production acceptance trong lượt này. LLM/agent baseline không áp dụng cho phép kiểm deterministic này.

## Bằng chứng

- [QA tổng hợp hai bản sửa và bảo toàn](../evidence/beta06/generation04/qa-g4r2-correction-independent01.json)
- [QA raw và tương quan Close](../evidence/beta06/generation04/qa-g4r1-n1-closure-correlation01.json)
- [Video độc lập](../evidence/beta06/generation04/qa-g4r1-n1-media-independent01.json)
- [Capture và journal](../evidence/beta06/generation04/qa-g4r1-n1-capture-independent01.json)
- [QA sửa completion](../evidence/beta06/generation04/qa-g4r2-native-boundaries01.json)
- [QA sửa chỉ mục review](../evidence/beta06/generation04/qa-g4r2-sealed-boundaries01.json)
- [Bảo toàn cuối](../evidence/beta06/generation04/g4r1-root-final-preservation02.json)
- [Đóng runtime](../evidence/beta06/generation04/g4r1-root-owned-runtime-closure01.json)

![Android N1 trước khi đóng phiên](../evidence/beta06/generation04/g4r1-n1-ground-close.png)

