# CLOCKVIDEO05: clock video và harness UI

Ngày 22/10/2026. **Trạng thái tổng thể: NOT READY.** Đã sửa và kiểm được clock video, bố cục thao tác Android và một cửa sổ chạy đồng thời AUTO + payload mock + video. Chưa nghiệm thu trọn nhiệm vụ tới hạ cánh/disarm; chưa chạy ca reboot riêng và chưa kiểm được persistence sau chuyến bay.

## Kết quả cho người vận hành

| Yêu cầu | Kết quả đã có | Phân loại |
|---|---|---|
| Clock video không áp dụng callback của phiên cũ | Tách epoch/config, single-flight, hủy callback cũ; gia hạn lỗi giữ đúng hạn mapping gốc; không hồi sinh mapping hết hạn | Mock/VM độc lập đạt; không xác định ngược nguyên nhân sự cố live cũ |
| Clock hoạt động khi Android nhận video từ host | Cửa sổ VP8 thực đạt; trace clock giữ hạn 60.000 ms và các phép gia hạn đã đối chiếu | Đạt trong phiên/cửa sổ đã đo, chưa chứng nhận mọi thiết bị |
| Nút/UI thao tác chính xác | 9 nút flight và 6 nút payload đủ kích thước, nằm trọn vùng thao tác, không bị che; receipt điều hướng thực khớp | PASS trên Android emulator 1280 × 800, WebView 1280 × 716 |
| Harness không bấm tiếp khi bằng chứng sai | Tương quan document/client/run/boot/config/model/plan, ánh xạ inset thực 24 px; đợi snapshot/paint trong hạn; không lặp input | Mock đối kháng và thao tác UI thực đạt trong phạm vi đã kiểm |
| Upload/readback nhiệm vụ và camera | 12 item upload, 24 item readback trong 2 vòng, 4 lệnh camera 206 được giữ, 0 PARAM write | Đạt đối chiếu byte/semantic đã chọn; không thay nghiệm thu toàn chuyến |
| AUTO + payload/video đồng thời | AUTO thực qua ArduPilot 4.7.1; chụp JPEG tổng hợp và gimbal mock có 2 điểm hành động đủ điều kiện trong cửa sổ video | PASS cho các điểm quan sát; không suy ra cả cửa sổ luôn airborne |
| Hoàn tất nhiệm vụ | Raw kết thúc khi vẫn armed; không có bằng chứng ground-disarm hoàn tất | FAIL nghiệm thu chuyến: runtime AP chạm giới hạn 540 s |
| Reboot với lease đang còn hạn, thu hồi quyền | Chưa chạy ca riêng; chỉ tạo 1 trong 2 request AP được dự trù | NOT CHECKED |
| Persistence/restart sau chuyến bay | Có snapshot trước và các lần mở lại trước bay; lần thu snapshot sau bay gặp ADB `error: closed` khi emulator hết hạn | NOT CHECKED sau bay; không công bố bảo toàn native sau restart từ dữ liệu thiếu |

## Video thực đã đo

Nguồn: Chrome host tổng hợp RGB → WebCodecs VP8 720p30 → HTTP/TCP loopback → Android chỉ nhận/giải mã. Đây không phải camera vật lý hoặc phép đo photon-to-screen.

- 867 frame trong 30.001,2 ms: **28,898844 FPS**.
- P95 cận trên độ trễ nguồn tổng hợp tới canvas: **54,652917 ms**.
- Từ yêu cầu mở viewer tới khung mới đủ điều kiện: giá trị báo cáo **331,5 ms**; trace phase giữ lại cho cận bảo thủ **332,1 ms**, cùng config.
- Ngắt relay 500 ms: phục hồi khung mới sau **565,9 ms**, có kiểm thời điểm source sau resume.
- 74 điểm AUTO quan sát và **2 điểm payload thành công** nằm chắc chắn trong cửa sổ theo cận clock; không có đổi context trong cửa sổ.
- JPEG mới 53.609 byte đã đối chiếu hash/manifest/sidecar và tham chiếu telemetry raw. **Ảnh vật lý: 0.** Gimbal là mock; thermal/radiometry không được nghiệm thu.

Bộ replay ban đầu thiếu binding startup do `decoderLifecycle` đã cắt sự kiện cũ. QA tìm được `startupPhases` còn nguyên trong chính raw report và bổ sung binding độc lập, giữ nguyên báo cáo ban đầu. Không sửa số đo hoặc hạ tiêu chí. Cold-start toàn ứng dụng/codec chưa được chứng minh.

## Lỗi còn chặn và thay đổi kế tiếp

Phần chuẩn bị UI/video kéo dài làm thời gian bay còn lại không đủ trước deadline AP 540 s. Raw và closure giữ nguyên `OWNED_SIMULATOR_DEADLINE`, `TRANSPORT_CLOSED`, accepted=false. Verifier nghiệm thu chuẩn vẫn từ chối closure; kết quả semantic/Takeoff chọn lọc được báo riêng, không nâng thành flight PASS.

Lượt tiếp theo phải hoàn tất staging/source/config/reference trước giai đoạn có hạn, dành đủ ngân sách kết thúc bay và thu native store trước deadline. Guard dự phòng thời gian được chuẩn bị riêng bằng mock; chưa được dùng hoặc chứng minh trên lượt vừa chạy. Sau đó cần kiểm hai lát cắt riêng: nhiệm vụ nominal hoàn tất; reboot airborne với lease còn hạn, kiểm mất quyền và một probe context cũ. Cuối cùng mới kiểm native restart/persistence. Không tăng speedup, không nới freshness, không bỏ frame hoặc ký mới để vượt gate.

## Bảo toàn và giới hạn

- Source/candidate gốc, ENDURE và các baseline bảo vệ được QA đối chiếu không lệch SHA trong phạm vi manifest: 1.486 protected, 7 native, 1.496 bằng chứng trước, 93 source hiện tại, 431 artifact COCKPITVIDEO04. Các tập có phần giao nhau, không cộng thành tỷ lệ chất lượng.
- Hai thế hệ CLOCKVIDEO05 trước được lưu đủ 37 byte-source mỗi thế hệ, kèm manifest/freeze cũ. Pins03 gồm 226 file; SHA `02b532462598893f384a3af7fe83771c2d30daae612ad7cff26bb4387b1adb26`.
- 10 request SITL lịch sử giữ nguyên; chỉ thêm `s7259d4c019bb4c409f8b`. Request thứ 12 chưa chạy. Không thay source/candidate đóng băng, trust/selection hay lịch sử ENDURE.
- Một lần thay host được Contractor ghi rõ trong quyết định L2, cùng emulator02 và hạn 20 phút ban đầu; không thêm coldboot hoặc thời gian. Các gate pixel thất bại trước đó và receipt muộn đều được giữ.
- Dung lượng tối thiểu emulator02 lấy mẫu: **37.000.515.584 byte, khoảng 34,46 GiB**, cao hơn sàn 20 GiB. Đã dừng host/emulator/container test. Không build/cài/ký APK mới; APK development đã cài giữ nguyên SHA.
- Đã dọn riêng `.stage` sinh ra của CLOCKVIDEO05: 132 file, 4.716.328 byte. Docker image prune thu hồi 0 byte; không prune container/volume, không xóa bằng chứng hay dữ liệu khác.
- 95 đường dẫn Git thiếu đã tồn tại ở baseline vẫn là giới hạn cũ, không phải tuyên bố toàn bộ repository đầy đủ. Một số baseline dùng SHA của nội dung symlink sau dereference; không chứng minh toàn bộ thuộc tính liên kết.

## Hồ sơ kiểm chứng

Các đường dẫn dưới đây là hồ sơ cục bộ trong dự án:

- `planning/clockvideo05/TIP.md`, các quyết định generation02/03 và runbook.
- `evidence/field02/clockvideo05/qa-generation03-pre-runtime-gate01.json`: source/mock gate.
- `evidence/field02/clockvideo05/qa-ground-gen03-independent01.json`: pixel, target và receipt thực.
- `evidence/field02/clockvideo05/qa-receipt-poll03.json`, `qa-readiness-wait01.json`: guard harness đối kháng.
- `evidence/field02/clockvideo05/qa-media-nominal03.json`, `qa-media-nominal03-supplement01.json`: số đo video và binding startup.
- `evidence/field02/clockvideo05/qa-overlap-nominal03.json`, `qa-capture-nominal03.json`: hai điểm payload và JPEG tổng hợp.
- `evidence/field02/clockvideo05/qa-raw-nominal03.json`: verifier chuẩn từ chối closure.
- `evidence/field02/clockvideo05/qa-raw-incomplete03c.json`: chẩn đoán chain/wire/semantic chọn lọc, không nghiệm thu hoàn tất.
- `evidence/field02/clockvideo05/qa-final-preservation01.json`, `root-runtime-disposition03.json`: bảo toàn và những phần chưa kiểm.

**USER OUTCOME:** video và các nút điều khiển chính đã có lát cắt Android–SITL thực; chưa có bộ demo end-to-end hoàn chỉnh được nghiệm thu.

**VALUE EVIDENCE:** measured trong phạm vi video/điểm payload nêu trên; chưa đo lợi thế tổng thể so với sản phẩm khác. Công việc xác định dùng code; không có claim AI/LLM cần benchmark ở thay đổi này.

**DISPOSITION:** giữ bản cô lập để kiểm tiếp. Không đưa vào production, không tuyên bố READY hoặc thay thế Hera/SDK thật.
