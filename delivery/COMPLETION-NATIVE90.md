# Completion NATIVE90

18/10/2026 · PASS trong phạm vi cockpit Android offline/mock, không phải nghiệm thu Hera hay phần mềm production. Một agent tách SPEC/BUILD/VERIFY theo MethodBox hiện hành; receiver Python đối chiếu thuật toán riêng, không tự nhận nhóm QA độc lập.

Đã đưa video local tổng hợp và chẩn đoán input vào cockpit native cô lập, giữ blur glass/Barlow. Mục Tay cầm mở bảng chẩn đoán; video có nhãn nguồn và nút phát cố định, không tự chạy hoặc khôi phục. Input chẩn đoán không nối quyền Fly hoặc lệnh bay. Bản này không có permission Android nào, source chỉ mock; phần SITL đã nghiệm thu ở Native88 được giữ nguyên riêng.

## Nghiệm thu thực tế

| REQ | Kết quả | Bằng chứng |
|---|---|---|
|90-01 Cô lập/offline/bảo toàn|PASS: namespace90,0permissions;57.176đường dẫn trước đó khớp SHA|build08,installed08,preservation-before/after|
|90-02 Local video/generation/stale|PASS: Android WebView decode thật,2lượt kết thúc22callback/lượt; freeze bị chặn ở545ms; dừng khi ra nền|diagnostics08-final.tar,trace-verification-final|
|90-03 Input|PASS:33guard checks trên JVM và ART cùng bộ ca;4KeyEvent callback và1joystick callback do ADB injection, stale/focus thu hồi|host-tests08,raw trace|
|90-04 Journal/review/restart|PASS: fsync SHA-chain, tham chiếu đúng HEAD r15/mission; giữ nguyên mọi byte workspace qua app restart, Android reboot và recreation|persistence-verification,journey-verification|
|90-05 Hành trình/UI|PASS: khảo sát31m/1,1m/s → preflight → Fly mock2điểm → COMPLETED_MOCK → review; ACK không tăng tiến độ. Hai kích thước, ngày/đêm, nút mới≥48px, không đè nhau trong mẫu kiểm|screenshots,ui-verification|
|90-06 Receiver/closure|PASS:295events/10traces,6traces thuộc source08 được tính coverage13nhóm;14mutant bị chặn; source/APK parity và runtime đóng|negative-verification,source-final,runtime-closure|

Bộ kiểm bổ sung:15ca journal host;16workflow;31controls;22resource-policy;31draft-store và4archive-edge. Không cộng các lần chạy lại hoặc33ca ART/JVM thành các ca độc lập khác nhau. Các suite kế thừa workspace/file/bundle cũng chạy đạt trong build08.

Workspace hoàn tất: `initial`, r15, HEAD `02c69710797908907c86940904c1daa330860972287890ba432afdc9e388b7d8`; mission `0223662ab83267e661336c54e89fb8d6c67582b9393d7bcac55dbca60e213d79`. Semantic replay xác nhận3snapshot preflight, start-intent/handoff,2điểm quan sát và LANDING_OBSERVED. Tất cả vẫn operational=false,authorityRestorable=false,ảnh thực0.

## Bản bàn giao

- APK: `native/native90/dist/aeris-native90-development08.apk`.
- SHA256: `93095ee7ec4645dce34f758fb2d17b176525b6989f2e69c45a93c69cb1430c64`.
- Source ID: `4286cbc93c96e1bc5b616c5a6f674287b7e8aa0c3dbe53879faa55fb66f977e1`.
- V2/V3 development signature đã kiểm, cùng certificate engineering trước đây; APK cài trên emulator được đọc lại và khớp SHA. Không ký production/candidate mới.
- Android33 ARM64, WebView101.0.4951.61. Bản01–07 giữ để truy vết; chỉ08 là bản bàn giao đã nghiệm thu.

## Giới hạn và sự cố được giữ

Clip này là pattern kiểm decoder640×360, không phải hình camera cao cấp hoặc hình bay.22callback không chứng minh23mẫu nén đều lên màn hình; không có số latency camera/scanout, hardware mapping hoặc real photos. Memory snapshot chỉ là quan sát app process, chưa gồm toàn bộ renderer và không đóng thermal/leak/performance gate. Không chạy SITL mới hoặc nghiệm thu ENDURE24h.

UIAutomator trên WebView101 đôi lúc chỉ trả root/subtree rỗng, cả khi đổi aria-modal/region; giả thuyết nguyên nhân aria ban đầu chưa được chứng minh. Đã dùng ảnh hiện tại/tọa độ được thấy, xác nhận tác động bằng raw journal; không dùng XML cũ, DOM injection hay WebView debugging. Đây vẫn là giới hạn cần kiểm accessibility tiếp trên runtime/hardware đích. QA geometry chỉ áp các control mới được thấy ở kích thước/màn đã nêu, không chứng nhận mọi pixel của toàn AERIS.

Đã sửa race chuyển Plan→Fly và callback stop cũ hủy generation mới, timeout prepare, read-only snapshot không nuốt sự kiện stale, joystick dispatch trước WebView. Một lần bấm điểm quá nhanh khi fsync còn bận chỉ commit1điểm; giữ capture RUNNING, không suy hoàn tất từ tên tệp. Capture `completed-final` mới là hồ sơ hoàn tất.01–07 và các incident/raw được giữ nguyên.

Trace chẩn đoán được liên kết riêng với workspace HEAD, **chưa được kèm trong ZIP workspace qua SAF**. Không khôi phục player/input hay quyền từ lịch sử.

## Bảo toàn và vệ sinh

Source/candidate/ENDURE/canonical SOT và các module trước đến Native89 giữ nguyên57.176đường dẫn. Chỉ kiểm hiện tại, không suy đường dẫn tồn tại liên tục trong lịch sử. Emulator/controller riêng đã dừng,5582/5583 trống; nguồn/RAM/đĩa emulator được đóng. Thấp nhất31,98GiB trống trong runtime, cao hơn sàn20GiB. Đã xóa8APK unsigned và1cache Python riêng,26.612.896bytes; giữ signed APK/raw/AVD. Không copy dự án sang tmp, không cài dependency/SDK. Docker image prune thu hồi0B, không prune volume/container.

Bước tiếp hợp lý: xuất đủ diagnostic trace kèm manifest/HEAD qua Android SAF và kiểm receiver độc lập, rồi nghiệm thu đồng thời cockpit này với đường SITL đã đạt ở Native88; video vẫn ghi rõ tổng hợp. Bench HeraHub/HID/video thật chỉ mở khi có target/SDK và budget đo được duyệt.
