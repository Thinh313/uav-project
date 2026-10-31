# RAGAS 4.0.14 và đường cơ sở kiểm chứng AERIS

15/10/2026. Bản cập nhật nghiên cứu độc lập trong research/ragas54; không sửa đường cơ sở đóng băng. Kết luận: dùng release/binary identity làm mốc, đưa độ đúng mission vào gate trước mở rộng đồ họa. Chưa có phép chạy RAGAS trong đợt này; kết quả cũ của AERIS không chuyển thành bằng chứng RAGAS.

## Những điểm đã đối chiếu

- Release4.0.14 công bố09/10/2026 10:26:59UTC, metadata cập nhật13/10 02:36:25UTC. Android manifest mới tự khai build 112; tag/tên APK vẫn111. Internal APK build và signer chưa kiểm. Ghi FAIL_METADATA_IDENTITY_CONSISTENCY cho release identity; đây không phải kết luận binary lỗi khi bay.
- So snapshot12/10: ghi chú release chỉ khác xuống dòng LF/CRLF; manifest đổi buildNumber111→112; các trường còn lại không đổi. API assetID/digest/size APK/DEB và checksum vẫn khớp snapshot trước. Chỉ manifest Android có ID/hash mới. Không suy tính liên tục của bytes hoặc khẳng định đã hash binary chưa tải.
- 4.0.10 đã công bố3D, sửa lưới QGC, tổng khảo sát, khoảng chụp và giữ thiết lập lưới. 4.0.14 thêm các mục được nêu trong ghi chú như camera-upload, cao độ riêng và terrain-export. Đây là khác biệt nội dung công bố, không chứng minh lần đầu code có tính năng.
- 4.0.8 thiên về UpdateCenter/map/payload responsiveness;4.0.5 và4.0.4 có ghi chú trùng nội dung về đơn vị/editor/payload. Không có benchmark định lượng được coi là đã kiểm. test-linux-u20 là bản test riêng, không lấy làm baseline thương mại.
- README vẫn badge4.0.0build4;3D được công bố cho Android ARM64. CóLinuxDEB không chứng minh3D trênLinux. Main/tag commit của repo phát hành không phải commit source implementation hay chữ ký của APK.

## Bằng chứng cũ dùng lại

QGC03 lưu hai chuyến SITL,30 CAM mô phỏng; QGC 5.1.5 open/save giữ camera/navigation cho hai derivative trong scope. Home10→7 còn OPEN; ComplexItem đã flatten không chứng minh editor regeneration; CMD inventory không phải thời điểm thực thi. Receipt và fixture được hash lại ở reuse.json. GEO14 kiểm nguồn/Home/datum và mô hình terrain giữ lại, không có field certification. MAPPING51 mới mock KML/corridor/thu nhận, actualFiles0. Các báo cáo này không chứng minh parity hay thắng RAGAS/DJI.

## So sánh phiên bản

| Mốc | Nội dung được công bố | Cách dùng làm baseline |
|---|---|---|
|4.0.4-b107/b108 và4.0.5-b109|Ghi chú cùng nội dung editor/đơn vị/payload; takeoff đổi đơn vị cao độ|Giữ fixture đơn vị/formatting; ghi chú trùng không chứng minh binary giống nhau|
|4.0.8-b110|UpdateCenter, map/trajectory và phản hồi payload|Các cải thiện hiệu năng là claim định tính; chưa có số đo RAGAS|
|4.0.10-b111|3D Android ARM64 và nhiều sửa lỗi lưới/tổng khảo sát/roundtrip|Là mốc trước cần benchmark; không tính các mục này là mới riêng4.0.14|
|4.0.14-b111|Giữ15 bullet giống4.0.10, thêm37 bullet trong ghi chú; camera-upload/cao độ/terrain-export nằm trong phần thêm|Khác biệt nội dung công bố; không xác định lần đầu hỗ trợ implementation|
|Metadata13/10 của4.0.14|Android manifest tự khai112; tag/tênAPK111, Linux manifest111; ghi chú chỉ khác xuống dòng so capture12/10|Identity gate FAIL cho tới giải thích/kiểm internalversion; không kết luận chức năng bay FAIL|

release-comparison.json nối từng mục nghiệm thu với nội dung ghi chú của từng bản. NOT_MENTIONED không có nghĩa bản cũ không hỗ trợ.

## Hợp đồng nghiệm thu

verification-matrix.json chứa25 mục, mỗi mục có hành vi, fixture, oracle độc lập, PASS/FAIL, artifact và cách thực hiện terminal-first. NOT_CHECKED vẫn là chưa kiểm, không phải FAIL ứng dụng. FAIL chỉ đặt khi quan sát trái tiêu chí; đây là đề xuất ngưỡng engineering, không phải chuẩn đo vẽ.

Không so riêng file JSON hoặc screenshot. Pipeline đối chiếu phải đi qua ý đồ editable → compiled mission → wire → AP readback → execution → media; mỗi tầng có đối tượng và bằng chứng riêng. Chuẩn hóa chỉ dùng rule theo command/schema đã duyệt, không che thay đổi Home/altitude/target. QGC là oracle tương thích; cần oracle toán/datum khác để phát hiện lỗi chung.

## Gói việc terminal-first cho Claude Code hoặc Codex

1. **B0 — pin và identity (P0):** giải quyết manifest112/tên111 với chủ phát hành; kiểm actual APK version/signature khi có binary. Đầu ra environment.json/asset-manifest.json; giữ tag, fullcommit, artifactSHA, OS/ABI, firmware và QGC pin. Không tự sửa gói hay manifest để qua gate.
2. **B1 — corpus và semantic diff (P0):** dùng lại fixture QGC03 có provenance; thêm góc/concave/multi-survey, camera206/2000/2001/2500/2501, mixedheight, unsupported/fence/rally. Tách editable graph và executable sequence; phát hiện placeholder và Home mismatch. Đầu ra original/expected/observed/diff với fullSHA. Không dùng exporter và importer cùng lõi làm oracle duy nhất.
3. **B2 — oracle toán/địa lý (P0):** shoelace, geodesic, per-leg time, optics/cadence, rounding per-transect, frame/datum/geoid và ridge/no-data; pin thư viện/schema. Đầu ra vectors.json và independently-derived expected. Có thể làm trước khi có HeraHub, không cần APK hay SITL mới.
4. **B3 — QGC/RAGAS A/B + ArduPilot SITL (P0):** chỉ sau pinidentity; cùng fixture/camera/firmware/Home/DEM. Tách cổng capture và decoder; gửi/upload/readback trong SITL cô lập; test camera mutation, loss/reboot/resume. RAGAS3D cần Android ARM64 target phù hợp; Mac/Linux không thay target. Camera responder giả lập không thành payload thực. Đầu ra raw.tlog/DataFlash, missioninventory, execution/capture correlation và report theo từng binary.
5. **B4 — terrain UI/offline (P1):** ray/drag/undo/2D3D/restart/cache và frame-time/input trace. Kiểm bản mission sau thao tác, không chỉ screenshot. Chỉ kiểm engine trên máy chạy; target HeraHub còn chờ thiết bị. Không nhập mock vào Fly hiện hành.
6. **B5 — mapping/payload thực (P0 trước thương mại):** bench camera timing/settings/calibration, ảnh và GNSS/base, thời gian/GCP/checkpoint; field corpus và tiêu chí khách hàng. Terminal hỗ trợ xử lý/đối chiếu, không thay phép đo thực.

Dependency: B0 và B1/B2 chuẩn bị song song về mặt công việc; B3 phụ thuộc identity rõ và B1/B2; B4 cần datum/semantic contract; B5 trước khi kết luận thay RAGAS cho khảo sát thương mại. Không dời SIMTRAIN53 sang production vì bản trình chiếu bay đẹp: mô phỏng huấn luyện và an toàn/độ đúng mission là hai phạm vi nghiệm thu riêng.

## Điều chỉnh ưu tiên sản phẩm

Trước mắt: P0 camera end-to-end, mixedheight/Home/DEM, QGC regeneration/roundtrip và quota/restart integrity. Tiếp theo:3D editor và performance trên target; không chỉ nâng chất lượng rendering. UI cần hiện datum/nguồn DEM/tuổi dữ liệu, mốcHome, trạng thái camera planned/reported/files và khác biệt nhập xuất; không cho status xanh che dữ liệu thiếu. Sau đó mở camera profile thực và nghiệm thu mapping với checkpoint. Chưa thể tuyên bố AERIS thay thế toàn bộ RAGAS hoặc vượt DJI từ các test host/mock hiện có.

Nguồn chính: https://github.com/Real-Time-Robotics/ragas-release/releases/tag/v4.0.14-b111 ; https://github.com/Real-Time-Robotics/ragas-release/releases/tag/v4.0.10-b111 ; https://github.com/Real-Time-Robotics/ragas-release/releases/tag/v4.0.8-b110 ; https://github.com/Real-Time-Robotics/ragas-release/releases/tag/v4.0.5-b109 ; README pin theo main-head.json. URL, thời điểm, SHA và nguồn gốc chung nằm trong sources.json. API/HTML/manifest cùng publisher không được coi là ba kiểm chứng độc lập.
