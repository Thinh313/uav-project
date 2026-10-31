# AERIS COCKPIT80 — interactive design mock

Current revision: **QA-fix02**, implementing9 findings from the role-separated design review. See [verification](../../evidence/cockpit80/qa-fix02/verification.json) and [completion](../../delivery/COMPLETION-COCKPIT80-QA02.html). Glass01 and the73-check report are earlier revisions, not a fresh full QA02 regression.

On reload there are **no automatic grants**. Open “Mở quyền” / identity chip, manually grant sample flight authority to A and sample camera authority to the current session. Switch A/B in the authority panel to rehearse request/deny/accept. These are two separately addressed sessions within one mock model, not networked controllers.

RTH/sheets are contextual. Telemetry/alerts and Dừng remain accessible. Space pauses the UI mock; Enter or pointer hold1.5s confirms RTH. Scenario lab covers data-loss/reboot, battery, synthetic visual stress and host-only rAF cadence. Numeric invalid mission input blocks the next action; undo never restores approval. Camera currently viewed and mission camera, revision and preflight binding are explicit. History is visually separated from sample live telemetry.


Open [the local mock](http://127.0.0.1:8840/). Server: `node planning/cockpit80/server.mjs` from the AERIS directory. No dependencies or build. This separate concept does not modify the native APK, frozen app/candidate, SOT or ENDURE. No flight API, SDK, hardware, SITL or new signature.

## Duyệt thiết kế

- **Bay:** ảnh camera minh họa toàn vùng; đổi bản đồ/camera bằng ô thu nhỏ. Chọn P1/P2/P3, chụp mẫu, zoom, thu gọn công cụ.
- **Nhiệm vụ:** xem hành lang/khảo sát vùng, chỉnh độ cao tương đối Home và tốc độ; cài đặt camera/tuyến mở theo nhu cầu.
- **Trước bay:** ba xác nhận Home/chuẩn cao độ/tuyến; dữ liệu mẫu và nút xem mô phỏng. Đây chưa phải preflight thật.
- **Hồ sơ:** ảnh mẫu và timeline minh họa; tách khỏi bằng chứng camera/autopilot thực.
- **Tay cầm:** sơ đồ input đề xuất; WASD/IJKL hiển thị hai cần. F1/C1 đổi camera–map, F2/C2 mở nhiệm vụ, Space dừng UI mock, R mở xác nhận quay về. Giữ nút xác nhận1,5 giây bằng chạm hoặc Enter; thả/move ra ngoài hủy. C1/C2/Mode2 chưa được xác nhận trên HeraHub.
- **Concept:** thử mất hình, mất liên kết, pin thấp. Mất liên kết đánh dấu dữ liệu không hiện hành, thu hồi quyền và không xếp hàng lệnh. Mở chip quyền để duyệt A/B; B không được nhận quyền bay.

Chế độ ngày/đêm nằm ở cạnh trái. Focus bàn phím có viền rõ, mũi tên điều hướng và Esc trở lại. Đây là tương tác duyệt UI mẫu, không mô phỏng vật lý hoặc mapping MCU thật.

## Hướng thiết kế

Trắng–đen là khung RtR, vàng chỉ cho điểm chọn/tuyến/hành động chính. Barlow Medium/Semibold/Bold thay chữ mảnh. Camera/map chiếm khoảng77% màn1280×800; bảng chi tiết mở theo ngữ cảnh. Nút chính tối thiểu56px. Thông số bay, liên kết và pin giữ vị trí ổn định.

[Design specification](DESIGN.md) records tokens, input principles and gates. [Asset prompt](ASSET-PROMPT.md) records the generated camera background. Input reference screenshots inform hierarchy and mood; their artwork/branding is not embedded in the mock.

## Verification

`evidence/cockpit80/browser-qa.json`: 73 actual Chromium interaction/layout checks passed, including1280×800,1024×600,1920×1080 and390×844. No external browser requests or JS errors. `font-glyph-qa.json`: all three local fonts contain104 tested Vietnamese Unicode codepoints. `visual-qa.json`: clean captures after visual critique.

First failed receipts remain. The app selector `[data-view]` incorrectly included the body and reset map state on bubbling click; it was narrowed to navigation buttons. An accessibility-selector timeout was fixed by marking decorative arrow/icons aria-hidden. The frame-wait hypothesis was not the root cause; no failed result was silently promoted to PASS.

This is ready for aesthetic/interaction review, not an accepted production design. Native rendering, touch on Hera, gloves, sunlight, real physical buttons/sticks, mapping and latency remain NOT_CHECKED. After review, implement shared native tokens/components, then connect the existing workflow and authority contracts with their regression gates.
