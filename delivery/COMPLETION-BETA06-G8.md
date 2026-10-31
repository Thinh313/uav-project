# BETA06 G8: chẩn đoán dung lượng và lỗi binding trước Connect

22/10/2026. **NOT READY cho nghiệm thu Android–SITL toàn luồng.** Host và emulator đã qua admission giữ nguyên; Android cùng nguồn video tổng hợp chạy được. Connect bị từ chối trước input/AP vì scanner nhận sai namespace host.

## Kết quả và giới hạn

Chẩn đoán host 181 mẫu trong 180,004939 giây: available giảm 92.598.272 byte; APFS Data tăng 92.614.656 byte, VM không đổi. Các bộ đếm ghi theo PID không xác định chủ sở hữu dung lượng tăng. Không xác định được nguyên nhân biến động lớn G7 trước đó: **UNKNOWN**. Không có bằng chứng để quy lỗi cho một ứng dụng hoặc sửa ngưỡng guard.

Fresh preflight 31 mẫu/30,221562 giây đạt, minimum 39.976.960.000 byte, peak decline 0. Admission host và emulator thực tế G8 sau đó đạt riêng. Android boot một lần, APK development hiện có khớp SHA, không build/cài/ký mới. Minimum free ghi bởi emulator: 39.987.023.872 byte, trên sàn 20 GiB.

Ground video 141 mẫu/75,147590 giây đạt, có ba renewal viewer và ba publisher. Đây là kiểm ground với video tổng hợp, chưa phải FPS/cold-start trong bay hay ảnh camera thật. Native 19 file/34 record được đối chiếu SHA; journal 15.467 byte không append, giữ 13 PENDING và ba thao tác picker còn lại. Cold persistence lần boot thứ hai chưa chạy.

Connect bị `ORIGINAL_COUNTER_CAPACITY_MISMATCH` trước Connect anchor/input hoặc tạo AP. Scanner G8 còn regex `host-app07`, trong khi thư mục thực là `host-app08`; đếm hostProcesses=0 và phân loại sai media/clock/WAL/UI/metadata sang SourceQA. Counter gốc trong Python ghi một host đã tạo. Guard fail-closed đúng; binding source sai. Kiểm source trước runtime chỉ chuẩn hóa namespace và dùng mock output qa-* nên bỏ sót tình huống thư mục canonical này. Giữ nguyên gate cũ và ghi rõ lỗ hổng kiểm chứng, không sửa báo cáo lịch sử.

**AP mới: 0. ARM/AUTO, mất link, reboot: 0.** N1/F1/N2/F2 và cold persistence đều NOT_RUN; không cộng kết quả G6 hay các campaign cũ để nghiệm thu G8. Không có kết luận beta, phần cứng Hera hoặc camera/gimbal thật.

## Bảo toàn và đóng sạch

874 pin source, 23 helper, toàn bộ 8.501 đường dẫn bảo vệ và inventory lịch sử 4.645 entry đã được QA đối chiếu. 20 file workspace gốc và journal prefix nguyên vẹn. Các sự cố phục hồi đúng SHA và 95 đường dẫn thiếu lịch sử tiếp tục ghi riêng; không khẳng định đường dẫn luôn hiện diện.

Đã dừng viewer, publisher và đóng tab tạm. Host, emulator và controller được quan sát exit0; bốn PID không còn và năm cổng không còn listener. Host closure không lỗi payload evidence hoặc close index. Không tự khôi phục quyền. Hai dòng stdin từng xếp hàng sau setup không có Controller approval/intents; cơ chế tiêu thụ hoặc thất lạc chính xác UNKNOWN. Những lệnh native về sau gửi từng dòng riêng sau kiểm không-effect; không retry lệnh bay.

G8 đóng vĩnh viễn cho lượt kiểm này. Bản sửa binding và test real-filesystem cũ-fail/mới-pass được chuẩn bị riêng ở G9. Chỉ cho phép campaign mới sau gate độc lập và admission live mới, không nới guard, không đổi source/candidate đóng băng, ENDURE hay ký phần mềm.

## Chứng cứ

- HOSTDIAG08: delivery/COMPLETION-HOSTDIAG08.md và evidence/hostdiag08/qa-analysis01.json, admission01.json.
- evidence/beta06/generation08/qa-final-runtime-summary01.json: kiểm độc lập, SHA c49b4a16ce427ae04e27cb443cd482436e0f63df2d4d3d32cbdadfd9dd62c9ea.
- qa-closure-summary01.json, android-closure16.json, host-app08/app-closure.json.
- root-controller16-live.jsonl, g8-n1-ground-ground-soak.json, android-store-before-n1-16.json, android-store-after-closed-16.json.
- qa-final-gate01.json giữ nguyên; kết quả runtime hiện tại giới hạn phạm vi PASS source/mock trước đó.

Value evidence: không áp dụng đối chứng LLM cho sửa deterministic này. Kết quả có ích là xác định được lỗi wiring và giữ an toàn trước effect; chưa chứng minh toàn bộ hành trình sản phẩm.
