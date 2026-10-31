# COACH01: Replay training & inspection adviser

25/10/2026. **OVERALL STATUS: NOT READY cho nghiệm thu trọn milestone giao diện. Backend phân tích/replay/report/store đã kiểm đạt; browser UI đã triển khai nhưng NOT_CHECKED vì công cụ vẫn báo Local browser use tắt.** Không gọi phần này là phi công AI, sản phẩm Hera hay bản native đã nghiệm thu.

## Kết quả dùng được

Một lát cắt độc lập cho AI Assisted Training & Inspection: đọc gói SAF Beta05, kiểm SHA/raw/WAL, dựng lại KML/model/plan, giải mã telemetry từ RX wire, phân tích chuyển động, đối chiếu với dải khảo sát, liên kết media và xuất báo cáo có dẫn chứng. Receiver process riêng tái tính toàn bộ từ gói gốc, không chỉ tin nhãn hoặc checksum báo cáo. Không import session/transport bay hoặc tạo kết nối MAVLink.

UI Debrief có bản đồ ENU, đường bay/dải khảo sát, timeline và phát lại, mốc sự kiện, số đo tại mẫu, nút dẫn chứng raw, ảnh tổng hợp, lịch sử hồ sơ, đổi theme và xuất JSON. Giao diện dùng Barlow tiếng Việt, glass, vàng phụ. **Các mô tả này là phần đã implement, chưa là kết quả kiểm browser/pixel/touch/keyboard.** Không có screenshot giả hoặc headless browser dùng thay quyền bị tắt.

Mở [hướng dẫn](</Users/os/Downloads/AI technique/aeris/delivery/coach01-host/README.md>) và [Start Debrief.command](</Users/os/Downloads/AI technique/aeris/delivery/coach01-host/Start Debrief.command>). Preview localhost8897 đã launch PID14533 trong phạm vi task, giới hạn30phút; UI panel open được app trả queued, chưa xác nhận trang thực sự hiển thị. Có thể khởi động lại bằng script khi preview đã đóng. Không kết nối LAN/phone/drone. Không build APK, ký mới, chạy SITL/emulator, tải model hay cài dependency.

## REQUIREMENT COVERAGE

8/8 AC có implementation/biện pháp trong scope; 6/8 có kiểm đầy đủ trong phạm vi đã định, AC5/AC7 còn phần browser chưa chạy. Không cộng tỷ lệ này thành độ trưởng thành toàn sản phẩm.

| AC | Trạng thái | Bằng chứng |
|---|---|---|
| AC1 Nguồn/chuỗi/model | PASS: gói thật đã lưu, bytes và raw/WAL; dựng lại model/plan; từ chối sửa byte và KML đã reseal sai | tests01/results.json, actual-report.json |
| AC2 Wire/clock/freshness | PASS scoped: target/boot/session, CRC message hiểu được; guest regression/gap/stale/foreign/corrupt/tail | tests01/results.json; oracle01.json |
| AC3 Toán chuyển động/địa lý | PASS numerical: vector acceleration, wrapped heading, ENU WGS84, distance tới segment; không qua gap | tests01/results.json; oracle01.json |
| AC4 Media/provenance | PASS: ảnh tổng hợp không thành ảnh thực; vị trí host không thành định vị khảo sát; coverage/GSD/blur/overlap thực UNKNOWN | tests01/actual-report.json; http-tests02/results.json |
| AC5 UI replay | IMPLEMENTED / NOT_CHECKED browser: geometry, thao tác, contrast, phát lại/scrub và download qua UI | static-ui-qa02.json chỉ là kiểm tĩnh |
| AC6 Store/receiver/restart | PASS scoped: source/report/receipt, một writer, idempotency, pending không công bố/xóa, restart, tamper/traversal/symlink | tests01/results.json; http-tests02/results.json |
| AC7 Verify/value | PARTIAL: 16nhóm core; 9nhóm HTTP/store; Python oracle120case toán + replay thực. UI/human value chưa đo | oracle01.json; các receipt trên |
| AC8 Bảo toàn/tài nguyên | PASS so với trạng thái tại lúc vào task, có gap cũ giữ rõ; gate20/10 +256MiB, store256MiB | preservation-before/after.json; http-tests02/results.json |

SCENARIO RESULTS: core16/16 nhóm PASS; HTTP lượt cuối9/9 PASS. Python triển khai riêng kiểm559message wire thuộc loại cần thiết,377mẫu vị trí và120case toán seed20261025. Cùng assistant thực hiện SPEC/BUILD/VERIFY; không là independent human QA. 120case là assistant-authored analytic holdout sau engine, không phải dữ liệu bay thực chưa thấy.

TECHNICAL HEALTH: 5module JS syntax-valid, zsh launcher syntax-valid;33ID HTML không trùng,32ID được JS tham chiếu đều tồn tại. Static import graph35module; không import flight session/gateway/actual transport/net/dgram. Child process duy nhất trong graph là parser KML Python hiện có, có timeout/body/output bound. Không full Android/typecheck/build vì không có đổi APK/native.

## Kết quả replay dữ liệu thật đã lưu

Nguồn duy nhất: evidence/betaworkbench05/android-saf-package01.json, SHA256 f38e71a7afd5c34dbfafa05f08579fa0a18bbd6f7f90bb0d58171c9c78295713,7.244.638byte. Không có chuyến bay mới.

- Run s9bda51d32037456aa787; raw6.341record,377mẫu vị trí;122mẫu armed/AUTO trên2m dùng đánh giá chuyển động.
- Tốc độ mặt đất lớn nhất2,0176m/s; độ cao tương đối Home lớn nhất20,004m.
- Gia tốc vector ngang P95≈0,97848m/s²; heading-rate P95≈17,7°/s trong các cặp đủ điều kiện. Không coi là đánh giá stick hoặc kỹ năng phi công.
-75mẫu đủ điều kiện tham chiếu dải khảo sát; P95 khoảng cách tới dải gần nhất≈15,905m. **Có cả đoạn tiếp cận/chuyển dải; không là sai số bám waypoint hoạt động hoặc bằng chứng nhiệm vụ thất bại.** Không có kết luận định lượng chất lượng bản đồ từ số này.
- CRC của message thuộc dialect hiểu được đã kiểm;358frame không nhận diện không được giải nghĩa để suy tình trạng cảm biến. Unknown không phải clear/safe.
-1ảnh tổng hợp,0ảnh thực. Phơi sáng vật lý UNKNOWN, geotag là host receipt reference, không đủ chuẩn khảo sát. Không tính phần trăm phủ thực hoặc GSD thực.
- Báo cáo policy COACH01_REFERENCE_V2, SHA25609c9a66b3b391a23df78296beb65798ee7836d10cd4b06e93537ec003f32530f. Report hash/chuỗi không phải chữ ký nguồn.

## VALUE EVIDENCE và AI boundary

Phần xác định giao cho code: decode, clock guards, địa lý, integrity, thống kê, báo cáo dẫn chứng. Nhận xét ngôn ngữ là template theo rule được ghi rõ trong JSON/UI. Không có neural controller, learned perception, RL training, provider hay LLM call. Model inference/token/API cost không phát sinh trong runtime module; công phát triển và human review không được coi là0.

Một HTTP import gói7,24MB trên host hiện tại đo229,37ms end-to-end client; analyzer217,87ms. Đây là một phép đo engineering trên file có sẵn, không benchmark cold/warm hay nghiên cứu năng suất. Direct LLM/tool-agent đối chứng và thời gian thao tác người dùng NOT_MEASURED. Chưa tuyên bố lợi thế AI hoặc hơn DJI.

So với xem raw thủ công, workflow đã tự kiểm/tính lại và cho đầu ra report thống nhất, nhưng mức giảm công người chưa đo. Không thêm model chỉ để gắn nhãn AI. Bước sau khi UI đạt: đánh giá shadow-mode trên dữ liệu đầu vào mới, rồi bộ bài tập manual có input/authority/clock và ảnh gốc đồng bộ. Nhánh tự hành/điều khiển motor cần gate riêng, không nối report thành lệnh bay.

## Lỗi và sửa được giữ lại

1. Kiểm preservation đầu gặp file thiếu và symlink tới directory; sửa checker để phân biệt đường dẫn/target, không phục hồi bytes.165đường dẫn unique thiếu ngay lúc vào task, gồm23member Beta05. Cả trước/sau giống nhau;17.117identity unique quan sát không đổi trong task. Không suy nguồn gốc xóa hoặc hiện diện liên tục. Không sửa canonical SOT/history ENDURE.
2. Prototype hình học dùng mặt cầu trong khi plan dùng ENU WGS84. Trước nghiệm thu đã sửa dùng cùng frame WGS84, tăng policy V1→V2. Prototype report/V1 workspace giữ riêng; không ghi đè, final store dùng workspace02. Oracle Python dùng ECEF riêng kiểm kết quả V2.
3. HTTP lượt01 đạt8/9; bước fetch ngay sau restart báo fetch failed. Receipt không giữ nested cause, nên nguyên nhân socket lịch sử chưa chứng minh. Harness lượt02 dùng HTTP connection mới agent:false qua generation mới,9/9PASS. Không coi lượt01 là PASS hoặc gán lỗi này thành mất persistence. Không retry HTTP failure tự động trong product.
4. Import-regex của static checker01 bắt nhầm chuỗi UI; checker02 neo vào statement boundary, kiểm chỉ builtins node và graph35module. Static receipt01 được giữ, không dùng làm gate cuối.

## LIMITS + DISPOSITION

Browser tiếp tục trả Local browser use disabled qua các lần kiểm; người dùng nói sẽ bật nhưng chưa có kết quả tool khả dụng. Do đó thiếu browser E2E import/demo → scrub/play → theme → findings → export → reload/history; thiếu kiểm hình học màn hình, contrast, icon và screenshot. **Milestone chưa được gọi DONE.** Đã tiếp tục toàn bộ phần không phụ thuộc browser và đóng gói phần có thể kiểm, không dùng công nghệ UI khác để vượt quyền.

Nguồn/candidate đóng băng và ENDURE không bị sửa so trạng thái lúc vào; các đường dẫn thiếu cũ giữ nguyên và có hồ sơ. Không khởi động campaign/soak, không sửa baseline hoặc tự khôi phục125/165đường dẫn bằng quyền của danh sách trước.

Gate20GiB admission/10GiB +256MiB floor giữ nguyên, boundary mock không làm đầy ổ thật. Kiểm cuối còn≈44,63GiB. Artifact evidence khoảng59,67MiB trước completion/fingerprint, dưới256MiB. Không whole-project copy/tmp, download/install/build scratch hoặc Docker run, không có scratch cần dọn. Không xóa evidence/user files. Preview được giữ có chủ đích tối đa30phút; mọi server HTTP test8898 đã close. Backend chỉ localhost, không production hardened service.
