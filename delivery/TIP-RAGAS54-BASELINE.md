# TIP RAGAS54 · Đường cơ sở RAGAS 4.0.14

15/10/2026 · Nghiên cứu bổ sung trong `research/ragas54`, không thay canonical SOT hoặc phần mềm đóng băng.

Yêu cầu: REQ-RG54-01 kiểm release hiện tại và lịch sử; REQ-RG54-02 lập ma trận độ đúng/an toàn nhiệm vụ; REQ-RG54-03 tách claim và runtime proof; REQ-RG54-04 tận dụng corpus/receipt cũ; REQ-RG54-05 xác định việc terminal-first và thứ tự ưu tiên; REQ-RG54-06 bảo toàn nguồn/candidate/ENDURE.

| AC | Đầu ra và nghiệm thu |
|---|---|
| AC01 / REQ01 | Raw API/manifest/README có URL, timestamp, SHA; pin tag/commit/assets; đối chiếu snapshot cũ và nhiều release trước. Phân biệt binary hash công bố với binary đã tải/hash. |
| AC02 / REQ02 | Mỗi mục có hành vi, test data, independent oracle, PASS/FAIL, artifact và scope thực hiện; đủ camera/QGC/geometry/coordinate/height/terrain/roundtrip. Ngưỡng engineering phải ghi là đề xuất. |
| AC03 / REQ03 | Official claims giữ Refinery sourced; runtime RAGAS chưa chạy giữ NOT_CHECKED. Metadata inconsistency được báo riêng, không kết luận lỗi bay. |
| AC04 / REQ04 | Hash lại fixture QGC có provenance và receipt cũ; giữ Home10→7 OPEN, simulated CAM khác ảnh thật, flatten khác ComplexItem regeneration. |
| AC05 / REQ05 | Chia B0–B5 với dependency và kết quả bàn giao; phân biệt terminal/mock, QGC/SITL, Android và bench/field. Không dùng source RAGAS. |
| AC06 / REQ06 | So pin kế thừa SIMTRAIN53 trước/sau; không sửa app/services/candidate/SOT/trust/ENDURE, không chạy soak/bay/SITL/emulator hoặc ký. |

Thực hiện một agent qua các pha specification → capture/build → verify; không có reviewer độc lập. Chỉ cổng kiểm integrity tự động đã chạy, không phải kiểm binary RAGAS. Không cần tải binary hoặc cài dependency cho phạm vi nghiên cứu này. Giữ sàn 20 GiB; mọi scratch bite có tên task và xóa khi xong. Không phát hành ngoài máy.
