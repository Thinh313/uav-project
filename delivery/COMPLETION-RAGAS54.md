# RAGAS54 · Đối chiếu release và đường cơ sở kiểm chứng

15/10/2026 · **DONE_FOR_RESEARCH_SCOPE**. Đã kiểm metadata và cập nhật baseline nghiên cứu bổ sung; chưa chạy hoặc nghiệm thu runtime RAGAS. Một agent thực hiện specification → build → verify, không phải đánh giá viên độc lập.

Mở [báo cáo và ma trận 25 mục](../research/ragas54/index.html), [phân tích/thứ tự triển khai](../research/ragas54/assessment.md), [ma trận máy đọc](../research/ragas54/verification-matrix.json) và [so sánh phiên bản theo chức năng](../research/ragas54/release-comparison.json).

## Kết luận có ích cho AERIS

- RAGAS 4.0.10 đã công bố 3D và nhiều sửa lỗi khảo sát/QGC. Trong phần bullet được đối chiếu, 4.0.14 giữ 15 mục giống hệt và nêu thêm 37 mục; không suy lần đầu implementation có tính năng từ lần đầu ghi chú nhắc đến.
- Release 4.0.14 công bố ngày 09/10 10:26:59 UTC; metadata cập nhật 13/10 02:36:25 UTC. So snapshot 12/10, nội dung ghi chú chỉ khác xuống dòng. Android manifest đổi buildNumber 111→112, trong khi tag/tên APK vẫn111. API assetID/SHA công bố/size APK và DEB khớp snapshot cũ. Đây là **FAIL_METADATA_IDENTITY_CONSISTENCY** theo gate nghiên cứu đề xuất, không phải kết luận RAGAS bay lỗi. Internal APK build và signer còn NOT_CHECKED; không tải binary.
- README vẫn badge 4.0.0 build4. Bản 3D được công bố cho Android ARM64; có DEB không chứng minh 3D trên Linux. Commit repo phát hành không tự chứng minh source implementation hay signer binary.
- Độ đúng camera phải qua intent → compiled mission → wire → AP readback → execution → file. ACK, inventory CMD, CAM mô phỏng và file ảnh thực là các tầng khác nhau.
- Dùng lại QGC03 với11 fixture có provenance và7 receipt đã hash lại. Hai chuyến SITL/30 CAM là bằng chứng lịch sử AERIS; Home10→7 còn OPEN và flatten không chứng minh tái sinh editable Survey. GEO14/MAPPING51 giữ giới hạn mô hình/mock và field quality chưa kiểm.

## REQ/AC và kiểm đã chạy

| AC theo TIP | Kết quả |
|---|---|
| AC01 phiên bản/nguồn | PASS cho thu thập/đối chiếu:13 release,22 snapshot metadata/spec, URL/timestamp/SHA, tagcommit/README head và asset delta. Bất nhất manifest được phát hiện riêng. |
| AC02 ma trận | PASS cho hồ sơ:25 mục có hành vi, dữ liệu, oracle, PASS/FAIL, evidence, terminal-first và published-note presence. Các ca runtime là NOT_CHECKED. |
| AC03 claim/proof | PASS:30 claims Refinery sourced; runtime/installed version là null; một publisher không thành nhiều nguồn corroborated. |
| AC04 tái dùng | PASS:11 fixture và7 receipt hash khớp, giữ các giới hạn Home/ComplexItem/camera. Không chạy lại test cũ rồi cộng vào tổng. |
| AC05 thứ tự triển khai | PASS: B0identity → B1corpus/B2oracles → B3QGC/RAGAS/SITL → B4terrainUI → B5bench/field; phân biệt phần terminal tự làm và phần cần target/dữ liệu thực. |
| AC06 bảo toàn | PASS:20.555 pin kế thừa SIMTRAIN53 khớp ở kiểm trước và sau; không sửa source/candidate/SOT/trust/ENDURE hoặc chạy lại chiến dịch. Không suy hiện diện liên tục hoặc ENDURE PASS từ hash. |

`research/ragas54/verification.json`: **131 PASS, 0 FAIL** trong phạm vi integrity/provenance/schema/static links và injected faults; không phải 131 chức năng RAGAS đạt. Refinery digest `b7e843d7ffdec689`, auditor/idempotent và các bite áp dụng đạt. Các gate không áp dụng ghi N/A. Đề xuất oracle độc lập không có nghĩa các phép oracle runtime đã chạy.

Kiểm trình bày browser bằng file URL bị policy từ chối; không dùng đường vòng. Báo cáo chỉ được kiểm HTML/static link, chưa xác nhận layout bằng browser. Đầu ra JSON/Markdown đọc độc lập được. Không có RAGAS runtime, QGC UI mới, APK/DEB inspection, SITL/emulator, SDK/HeraHub, ảnh/calibration/checkpoint thực hoặc benchmark DJI trong nhiệm vụ này.

## Dung lượng và dọn scratch

Host cuối khoảng37 GiB trống, trên sàn20 GiB; thư mục nghiên cứu khoảng1 MiB. Không cài dependency, không tải APK/DEB, không copy toàn project, không tạo build output/Docker image. Đã xóa13 thư mục scratch bite tên `codex-tmp-ragas54-20261015-*`; danh sách đầy đủ và kiểm không còn tồn tại nằm trong `verification.json → scratch_removed`. Không xóa dữ liệu/bằng chứng người dùng.

## Bước hợp lý kế tiếp

Làm B1/B2 trong module cô lập: mở rộng corpus camera/ComplexItem/mixedheight và semantic/numeric oracle. Đồng thời chốt gói RAGAS chuẩn cho A/B sau bất nhất112/111; không tự sửa manifest để qua gate. Sau đó chạy cùng corpus qua QGC/RAGAS và AP SITL với raw capture/readback. Chưa tích hợp vào Fly đóng băng hoặc tạo bản ký mới. 3D simulator huấn luyện tiếp tục có gate riêng; hình đẹp không thay bằng chứng độ đúng nhiệm vụ hoặc mapping thương mại.
