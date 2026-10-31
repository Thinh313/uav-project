# COACH01 UI repair01: sửa lỗi bằng rà soát code và mock

25/10/2026. **READY trong phạm vi sửa code và kiểm mock được người dùng cho phép. Nghiệm thu UI trực quan đầy đủ vẫn NOT_CHECKED.** Không đổi kết luận lịch sử của completion COACH01 gốc, không coi Node mock là browser E2E. Một assistant thực hiện Contractor → Builder → Verify; không là human QA độc lập.

## USER OUTCOME

Các lỗi UI có thể xác định từ code đã được tái hiện và sửa: đồng bộ slider/mẫu/clock khi mở hồ sơ, state chờ/phiên server mới, phục hồi thao tác lỗi, export an toàn và logic replay/render. Mở http://127.0.0.1:8897 sau refresh trang để lấy app mới. Preview bản sửa đã khởi động PID25010, chỉ localhost, tối đa30phút; hết thời gian mở lại delivery/coach01-host/Start Debrief.command. Giữ workspace02 hiện có; không clear dữ liệu.

Không có thao tác browser nào được chạy trong increment này, theo yêu cầu chuyển sang code/mock khi browser bị chặn. Không dùng browser/headless hoặc công nghệ UI khác để né quyền. Không có ảnh chụp màn hình hay claim UI đã hiển thị đúng.

## Các lỗi đã sửa và đối chứng

| Phát hiện từ source/mock | Sửa | Kiểm cuối |
|---|---|---|
| Demo/import có thể chạy trước bootstrap, hoặc dùng CSRF cũ sau restart | Chặn mutation khi bootstrap đang chờ; lấy lại state chỉ đọc trước mỗi POST do người dùng chủ động. Không auto retry POST | Bootstrap pending/error, restart token, explicit retry |
| Mở hồ sơ mới giữ slider cũ dù clock/marker đã về0 | Reset slider/at cùng lúc, chỉ commit report sau kiểm checksum client | Mở report khác sau seek50s, giá trị về0 |
| File bị từ chối không reset, chọn lại cùng file có thể không tạo change | Clear file input trong finally cho cả thành công, lỗi và cancel | File quá32MiB không POST và value rỗng |
| Export dùng location.href, có thể rời app tới JSON/lỗi409 | GET có xử lý lỗi → kiểm scope/SHA/context → Blob download; không điều hướng; thu hồi Blob URL | HTTP lỗi, sửa byte, report khác có checksum hợp lệ, pagehide |
| Các control khác vẫn hoạt động giữa lúc tải/export | Disable các action xung đột, giữ theme độc lập; aria-busy; một tác vụ tại một thời điểm | Busy import, play/seek/export/history không chạy xen |
| Lỗi refresh history khiến thành công import bị gọi là thất bại | Giữ report đã lưu, báo lỗi phụ rõ; thêm Làm mới hồ sơ | Import thành công/history lỗi vẫn xem và xuất được |
| Replay seek event/raw chưa pause; callback cũ có thể chạy sau resume | Pause tại mọi thao tác seek; epoch loại RAF cũ; đồng bộ end/reset, rate và background | Event/raw, stale callback, end/replay, hidden document |
| Khoảng gap có dung sai50ms, vô tình hiển thị số như còn dữ liệu | Chọn mẫu theo tS trực tiếp/binary search; toàn khoảng giữa hai mẫu có break là unavailable | Biên gap ở .500001/.999999s; không nội suy |
| Canvas gán width/height ở mỗi draw gây reset/cấp phát lặp | Chỉ resize khi kích thước/DPR đổi; setTransform và clear mỗi frame | Allocation không tăng theo replay; DPR2 không nhân scale chồng |
| Biểu đồ ép cao độ âm về0; fit có scale tối thiểu có thể cắt trace | Range có min âm; fit giữ điểm trong rectangle với margin co giãn, không chặn scale tối thiểu | Negative Home height và viewport800×460/320×200/100×60/5×5, trace cực trị |
| Theme và lựa chọn hồ sơ mất sau reload | Lưu riêng theme/report SHA; restore report chỉ khi có trong danh sách và qua verified GET, paused; storage lỗi không chặn app | Simulated reload, invalid preference, storage denied; không POST/quyền |
| Accent/focus vàng trên nền sáng có tương phản token thấp; event/ref control thấp44px | Dùng path accent tối ở theme sáng, min-height44px, timeline đủ chiều cao; guard short landscape; aria-pressed cho layer | Token math và source review; geometry/touch thực NOT_CHECKED |

Timeout8s nay bao trọn fetch headers và tiêu thụ response body, không chỉ thời điểm có headers. Mock fault injection body stalled xác minh busy được giải phóng, report cũ còn nguyên và không tự POST lại. Đây là thời hạn network read, không là bảo đảm mọi CPU operation hoàn tất trong8s.

## REQUIREMENT COVERAGE / SCENARIO RESULTS

7/7 AC của TIP UI repair có triển khai và kiểm trong phạm vi code/mock/API. AC về geometry/browser đầy đủ không nằm trong phạm vi nghiệm thu mock được cho phép và vẫn ghi NOT_CHECKED.

- **12/12 nhóm mock chính đạt**, sau khi bản gốc tái hiện10FAIL/2PASS bằng harness đã sửa. Dùng ui-before02.json và ui-after02.json; không cộng lượt trước thành ca mới.
- **13/13 nhóm mock bổ sung đạt**, gồm body timeout, busy concurrency, history partial error, restore preference, stale RAF và export wrong context. Gate dùng ui-extra02.json.
- **6/6 nhóm toán/client-digest/token-color đạt**. Token accent light trên panel/map composite tham chiếu tăng từ≈1,57:1 lên≈5,51:1; fg≈15,17:1, muted≈6,16:1. Đây là toán trên màu khai báo, không là pixel đo thực hoặc chứng nhận accessibility.
- **3/3 nhóm HTTP thực đạt**: server phục vụ module replay mới, import/export gói gốc vẫn tái tính đúng digest, restart giữ report và từ chối stale CSRF. Test dùng connection mới agent:false, không retry ngầm; port8898 đã đóng.
- JS6module syntax-valid; HTML35ID không trùng,34ID JS tham chiếu đều có. Không build/typecheck Android vì không sửa native/APK.

Tổng31nhóm mock/toán ở ba suite khác nhau; 3nhóm API là bằng chứng localhost thực, không phải browser. Harness chạy source app thực trong Node VM với DOM/canvas/fetch/RAF/storage test doubles, không dùng rendering engine hoặc giao diện máy tính. Canvas spy chỉ xác minh call/allocation logic, không đo GPU/FPS/mượt hay font layout. Seed/fixture là assistant-authored hoặc clone report gốc cho negative cases, không phải dữ liệu thực chưa thấy.

Hồ sơ Android–SITL cũ vẫn giữ policy COACH01_REFERENCE_V2 và report SHA256 `09c9a66b3b391a23df78296beb65798ee7836d10cd4b06e93537ec003f32530f`. Receiver đã tái tính từ raw gốc. Không chạy chuyến bay mới, không suy lệnh camera thành ảnh thực hoặc AUTO thành kỹ năng phi công.

## Lỗi harness và giới hạn provenance giữ lại

- ui-before.json lần đầu vô tình tạo token restart cùng giá trị ban đầu, khiến ca restart PASS giả trong mock. Đã tách bootGeneration khỏi counter RAF/Blob; ui-before02.json mới là red baseline được dùng. Không xóa lượt đầu.
- ui-extra01.json có một ca đặt tên wrong context nhưng thực tế kiểm successful export của report hiện tại. Đã thêm response khác có checksum hợp lệ và assert không download; ui-extra02.json mới là gate. Không dùng kết quả mislabeled để chứng minh negative cũ.
- ui-after01.json là lượt12ca đạt sớm; sau đó rà soát thấy timeout bị clear khi mới có headers. Sửa bao trọn body và dùng ui-after02.json + ui-extra02.json kiểm cuối. Không coi lượt xanh sớm là nghiệm thu tất cả.

## Bảo toàn / kỹ thuật

Chỉ sửa4file được phép: pilot/coach01/app.mjs, index.html, style.css và server.mjs (asset map thêm replay.mjs). Byte gốc4file lưu trong evidence/coach01/ui-repair01/source-before với SHA. Thêm replay.mjs và harness/planning/evidence/report riêng; **core.mjs/store.mjs và policy phân tích không đổi**. 49member còn lại của handoff COACH01 gốc khớp. Không sửa completion/handoff cũ để che thay đổi được cho phép trong4file.

Bộ bảo vệ trước/sau vẫn cùng17.117identity được quan sát,165đường dẫn đã thiếu từ trước giữ nguyên trạng và có receipt; không phục hồi, không suy nguyên nhân hoặc hiện diện liên tục. Source/candidate đóng băng, canonical SOT và ENDURE không đổi. Không signer, APK, SITL/emulator, SDK/HeraHub, Docker, dependency install hay network external trong runtime/test.

Gate20GiB admission,10GiB +256MiB write reserve giữ nguyên. Kiểm cuối bảo toàn còn khoảng40,44GiB. Evidence cho repair nằm trong64MiB budget; test không làm đầy ổ thật. Không project copy/tmp/build scratch; không có scratch cần dọn. Các file pending/source/report của ca kiểm là bằng chứng có chủ đích và được giữ, không auto cleanup.

## VALUE EVIDENCE / LIMITS + DISPOSITION

Measured: các lỗi hành vi đã được tái hiện trên source cũ và kiểm lại source sửa trong mock; report raw vẫn tái tính đúng qua HTTP thực. Không có model/LLM runtime; không claim lợi thế AI hay hơn DJI. Human productivity, actual input latency, rendered FPS, crash-recovery download và physical device quality NOT_MEASURED.

Chưa kiểm trực quan: native file chooser/cancel/reselect trên browser, browser download thực và quyền lưu file, reload thật/localStorage policy thực, font/line wrap, overflow/overlay, focus order/keyboard/touch, blur compositing, projector/Android, contrast trên pixel thật. Không gọi toàn UI COACH01 đạt chỉ từ mock hoặc token math. Cần chạy lại browser checklist khi công cụ có quyền; không yêu cầu người dùng lặp bật/restart trong task này.

Bằng chứng: evidence/coach01/ui-repair01/ui-before02.json, ui-after02.json, ui-extra02.json, math01.json, http01/results.json, static01.json; preservation-ui-repair01-before/after.json nằm cùng evidence/coach01. Source/hash handoff repair được lưu riêng sau báo cáo.
