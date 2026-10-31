# DUAL67 · Hai phiên cockpit độc lập

16/10/2026 · **DONE trong phạm vi hai client mock; READY_WITH_DEFERRED_RESPONSIVE.** Chưa nghiệm thu Android/HeraHub, hai trạm/radio thật hoặc production authentication. Không SDK, APK/build, ký, SITL/emulator, lệnh bay hoặc thay đổi ENDURE.

Mở [Pilot](http://127.0.0.1:8822/pilot) và [Payload](http://127.0.0.1:8822/payload). Hai tab có role, token và lựa chọn riêng, dùng chung bộ phân xử serial. Preview cuối PID56099; bàn giao với cả hai phiên ngắt, không có owner hoặc tự nối lại. Không sửa COCKPIT66/CYBER65/candidate; source mới ở `native/dual67`, evidence mới ở `evidence/dual67`.

## Coverage và nghiệm thu

**Implementation:8/8 REQ,100%. Full AC verification:7/8,87,5%; D67-07 còn responsive NOT_CHECKED.** Một agent tách BUILD/VERIFY, không gọi đây là kiểm định độc lập bởi bên khác.

| REQ | Kết quả | Evidence chính |
|---|---|---|
| D67-01 phiên độc lập | PASS_HOST_MOCK: role/session/token riêng, lựa chọn độc lập; server không nhận actor/sid giả trong action | browser-qa02, HTTP QA02 |
| D67-02 tranh chấp/fencing | PASS: một người thắng CAS cùng revision; boot/sequence/revision cũ bị từ chối; không tự retry | Unit04, corpus02, HTTP QA02 |
| D67-03 bàn giao | PASS: freeze cả bộ, đúng người nhận xác nhận; decline/expiry/partial commit/loss không để quyền một phần | Unit04, corpus02, hai tab browser |
| D67-04 mất kết nối | PASS_HOST_MOCK: explicit disconnect và silent timeout; peer còn hoạt động, reconnect phiên mới không tự cấp quyền | HTTP clock-injected; browser host clock thực; raw47-event replay |
| D67-05 payload contract | PASS_MOCK: pinned CYBER65/P22/T25; target rõ, ACK-only/sai mục tiêu giữ uncertainty; Phase One unknown, LiDAR khóa, actualImages0 | Corpus22, browser Thermal/Phase One, source/dependency pins |
| D67-06 replay/bounds | PASS_NODE: replay SHA/semantic; forged actor/time/state/receipt bị từ chối; UTF8 byte/quota/core history/clock guard, không silent eviction | Unit30, corpus22, replay47+948 events |
| D67-07 UI/QA | PASS desktop1280×720, hai client và HTTP; **PARTIAL_QA** cho responsive1024/390 | Browser02, screenshot/runtime02, viewport limitation trong browser01 |
| D67-08 preservation | PASS_ENDPOINT_SHA:24.640 đường dẫn bảo vệ và kiểm riêng ENDURE5.051 khớp, không missing/dataless | preservation-before/after, source/artifact pins |

Hai tập preservation có phần giao nhau, không cộng thành số file duy nhất. Hash endpoint không chứng minh đường dẫn hiện diện liên tục hoặc ENDURE đạt24h.

## Kết quả định lượng

- **30/30 unit** cuối đạt, gồm tranh chấp, wrong recipient, partial commit, stale proposal/boot/sequence, silence/loss, core quarantine, Unicode byte bound và core-history bound trước eviction.
- **22/22 corpus** có final-state assertions và deterministic replay; **25/25 HTTP checks** cuối đạt, có đồng thời hai client, spoof/replay, lost-reply deliberate duplicate, sai target và service-instance restart.
- **7/7 quan sát browser trên runtime cuối** đạt; run trước16/16 được giữ riêng, không cộng chúng thành coverage chức năng độc lập. Hai nguồn chọn riêng, quyền chuyển theo consent, owner cũ khóa, mất heartbeat thu hồi và không auto resume.
- Raw browser cuối **47 events** tái thực thi trong engine instance thứ hai đạt; run trước **948 events** cũng được kiểm lại bằng engine cuối. Không có owner/active station ở snapshot bàn giao; core historyComplete=true, ảnh thực0.
- **6 module syntax checks**, HTML ID unique/client references resolved, console browser cuối không error/warning. Không chạy Android compiler, build, linter/typechecker; không ghi chúng thành0 lỗi.
- Desktop: không tràn ngang, nút≥44px, cặp nút cùng hàng/cỡ, nút kết nối hiện trong viewport, hình SVG không chồng phần chú thích. Request viewport1024/390 qua CUA vẫn trả actual1280×720, kể cả tab kiểm mới: **NOT_CHECKED**, các ảnh tên cockpit-1024/cockpit-390 chỉ là attempt. Viewport đã reset, tab kiểm tạm đã đóng.

Giữ riêng unit01 chưa đạt do fixture nhầm biên3000ms, fixture corpus trước sửa enum quarantine, ảnh bố cục ban đầu và source trước sửa nhãn loss. Các refine UI gồm nút kết nối dưới fold, hình vượt khung, nhãn owner chưa xét session/loss. Không sửa receipt cũ thành PASS. Preview01 dừng riêng sau lưu/replay evidence để harden UTF8 byte accounting; HTTP/corpus/unit và hai-tab flow đã kiểm lại trên preview02. Không có source hash runtime01 được chụp trước patch; không suy diễn có pin đó. Run cũ vẫn replay được bằng source cuối, run mới có pins và boot mới.

## Giới hạn và bước tiếp

Outer timeout3000ms/proposal8000ms là policy phối hợp mock; core vẫn explicit-step20ms/intent+10ms/feedback và deadline1400/800ms nguyên gốc. Kiểm browser xác nhận mất phiên được xử lý, không đo hoặc bảo đảm latency deadline vật lý/cứng. Chưa có emergency override/flight failsafe policy được thống nhất.

Role tự chọn localhost và token in-memory không thay trusted enrollment/production security. Hai JavaScript contexts không chứng minh OS isolation, hai máy/tay cầm hoặc radio. Core bytes chỉ đi qua MockTransport; ACK/metadata không chứng minh exposure/file. SVG tổng hợp không phải video hoặc mô phỏng3D.

Review volatile: cần xuất trước shutdown; server restart tạo boot/authority rỗng, không restore từ capsule. Đây không phải durable command journal hoặc nghiệm thu crash recovery. Heartbeat dùng quota; preview bounded không dành soak. Phase One model/API và thiết bị thật vẫn unknown.

Bước tiếp: đóng gate responsive bằng viewport hiệu lực; review policy operator/loss và định danh với kỹ sư; chuẩn bị durable audit và transport hai station riêng trước Android/HeraHub/HIL. Roadmap overlay mới tại `delivery/ROADMAP-DUAL67.md`, giữ SOT/roadmap/acceptance cũ nguyên trạng.

Canonical receipts: `verification.json`, `unit04.txt`, `corpus-replay02.json`, `http-qa02.json`, `browser-qa02.json`, `browser-runtime02-review.json`, `browser-runtime02-replay.json`, `browser-live-replay02.json`, `technical-health.json`, `runtime02-source-pins.json`, `source-pins-final.json`, `preservation-after.json`, `artifact-fingerprints.json`. Source/code usage trong `native/dual67/README.md`.

Sau lưu/replay snapshot47 events, đã reset transport mock explicit qua Pilot và ngắt phiên để anh có thể thử khóa capture mới. Snapshot QA trước giữ nguyên; tape không bị xóa. `handoff-ready-review.json`, `handoff-ready-replay.json` và `handoff-ready-ui.json` kiểm trạng thái cuối: transportEpoch2, không owner/active station/transaction, không auto resume. Đây chỉ là reset preview mới của task, không reset ENDURE hoặc source/candidate.

Cuối kiểm còn khoảng24,83GiB, trên sàn20GiB; toàn bộ phần mới dưới32MiB. Không dependency install, project copy/tmp/build leftovers hoặc xóa dữ liệu. Preview mock được giữ làm deliverable; chỉ tab kiểm tạm và service QA riêng đã đóng.
