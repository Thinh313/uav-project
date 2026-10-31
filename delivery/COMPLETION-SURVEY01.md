# Completion · SURVEY01 / Hera project SOT

12/10/2026 · Software 0.3. **DONE cho workflow prototype và SOT nội bộ được giao.** Chưa hoàn thành GCS Android/native, source RAGAS hoặc tích hợp bay. Single-agent implementation/review; không tự nhận phản biện độc lập.

## Kết quả

Plan chuyển từ rectangle cục bộ sang polygon WGS84/ENU có edit tọa độ, kéo/vẽ đỉnh bằng chạm, heading, camera tùy chỉnh/mẫu, target GSD, overlap và frame độ cao distinct. Save/library/export/import AERIS v2 tính lại geometry. Dirty inputs ẩn số liệu/tuyến cũ và chặn export/upload bản cũ. Thiếu camera/terrain/AGL giữ kết quả unknown; bản nháp lưu được, readiness không đạt.

Fly có mission upload/ACK/readback SHA-256, run/pause/resume/abort/progress trong mô hình. ACK không cho start; sửa draft không đổi onboard mission; reload kiểm digest và không tự nhận vehicle execution. Legacy flight/rectangle cores và test fixtures giữ nguyên. Capability/Input adapter seams có context và explicit mapping; chưa có channel/SDK giả.

BOM owner original giữ byte; mirror 1.571.857 bytes trong canonical. Đọc 41 sheets gồm hai master ẩn, 135.315 cells, 7.617 công thức; 32 cached error cells có sẵn và không missing formula cache. 6.483 sheet-scoped BOM rows không phải unique parts hoặc số linh kiện trên một chiếc Hera. Header Master (2) khác được xử lý riêng; không cộng master/variant/history columns.

Project SOT mở rộng tại `sot/`: 51 facts = 10 confirmed intents, 3 proposals, 9 unknowns, 28 BOM document claims, một flagged error set. Curated IDs theo variant+internal PN; raw full-BOM row IDs theo sheet/row/PN của snapshot. BOM part quantity/API/capability không được tự nâng verified. HERA v1.1/Getac/radio variants không nhập vào HeraHub v2 Android as-built. SOT view `sot/exports/project-sot.html` được review và copy qua publish gate nội bộ, chưa publish ra Internet.

## Acceptance và bằng chứng

| AC | Kết quả | Bằng chứng trong `evidence/survey01/` |
|---|---|---|
| AC-B1 · BOM integrity/scope | PASS | `bom-original-integrity.json`: fresh two-pass comparison 135.315 cells; `bom-integrity.txt`: original/mirror/locators/claim status và adapter; original hash unchanged |
| AC-S1 · live owned SOT | PASS | `truth-review.json`, baseline 3 files, A3 0 violation, 6 kernel bites, current gate/status; `sot-view-qa.json` 51 rows rendered |
| AC-G1 · geometry/camera/readiness | PASS cho declared model | `unit-tests.txt`: analytic rectangle, 24 headings, hemispheric round-trip, concave splitting/connectors, polygon/extent/camera/workload bounds và missing terrain/AGL |
| AC-U1 · end-to-end reference UX | PASS kỹ thuật, owner aesthetics pending | `browser-qa.json`: 19 checks; Plan/Fly screenshots ở Hera reference 1280×800, desktop1440×900/1280×720 và mobile390×844; drag/draw/edit/library/export/import |
| AC-I1 · session/adapter semantics | PASS local/replay | Unit và browser ACK→readback, mismatched/racing/aborted transaction, progress/resume/reload; capability browser refusal, explicit mapped input/attachment |
| AC-V1 · verification/handoff | PASS | 50 unit tests, syntax, 17 evidence checks; 68 public captures hashed; new method-reference domain build + 6 applicable fault checks PASS/10 N/A; cleanup/source manifests |

Bản browser QA đầu tiên gặp float display `36.480000000000004`; đã sửa hiển thị độ cao và step validity, giữ receipt `browser-qa-first-run.json`. Visual review phát hiện mobile telemetry bị cắt, đã tăng vùng và căn baseline; notification được chuyển để không che thao tác. Một lượt QA cuối bắt gặp phép kiểm nhập file đọc DOM trước khi async handler hoàn tất; QA đã bổ sung chờ trạng thái đã nhập, giữ receipt `browser-qa-import-timing.json`. Browser cuối không runtime errors hay external requests. Tests không chứng minh ưu thế UX trước operator/đối thủ.

## Giới hạn còn lại

NOT_CHECKED: actual Hera/Android window/input/RF/power/video/thermal/latency, RAGAS source/license/build, version-pinned QGC parity, terrain/geoid/camera quality, real MAVLink mission/capture commands, SITL/HIL/flight. Polygon coordinates là thật trong hệ WGS84, nền hiển thị hiện chỉ là grid tọa độ; site/camera mặc định đều mẫu. Gói AERIS v2 operational=false, không dùng trực tiếp cho autopilot. Khoảng 5–120m/3km là giới hạn prototype, không là quy định hoặc giới hạn certified Hera.

Độ sáng đủ theo chủ việc, không chặn phần mềm. 32 lỗi nguồn BOM còn flagged; gate PASS nghĩa provenance đúng và sources khớp, không có nghĩa lỗi nguồn được giải quyết hay mọi fact đã đo kiểm.

## Disk và bàn giao

Đã kiểm 44GiB trống; không cài dependency, tải binary lớn, copy project, tạo Next distDir hoặc Docker image. Chỉ copy BOM 1,5MiB làm canonical deliverable; extract khoảng 26MiB được giữ làm nguồn tra. Đã xóa scratch `/private/tmp/codex-tmp-aeris-survey01-20261012` trong finally và `/private/tmp/codex-tmp-survey-ui-20261012.py`; browser profiles tạm được Playwright dọn. Server loopback 8788 giữ để chủ việc review.

Điểm vào: `README.md`, `sot/README.md`, SOT HTML, `docs/SURVEY01-CONTRACT.md`. Bước tiếp: map/terrain offline package + version-pinned QGC/camera compiler, source/SDK audit và adapter native trên cấu hình được xác nhận.
