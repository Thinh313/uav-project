# AERIS Integrated Mission Beta01

26/10/2026 · **NOT READY – chưa nghiệm thu beta tích hợp**

Đã triển khai một bản cô lập gồm cockpit Android, launcher host, hành trình KML → preflight → upload/readback → Home sau arm → AUTO → payload/video → review và bàn giao SAF. Một lượt polygon thực trên Android–ArduPilot SITL đã hoàn tất điều hướng, HOLD/resume và chụp JPEG tổng hợp. Tuy nhiên video còn các đợt trễ dài, nên campaign dừng ở lượt đầu. Không báo DONE, không tính 5 lượt còn lại là đã kiểm, không công bố bản production.

## Kết quả nghiệm thu

| Yêu cầu | Bằng chứng và kết quả | Đánh giá |
|---|---|---|
| Native shell và một lối mở runtime | APK development cài/chạy trên emulator-5582; launcher chờ Android boot, kiểm pins, admission và sở hữu tiến trình; không tự gửi lệnh bay | Đạt phạm vi engineering, phụ thuộc workspace/cache hiện tại |
| KML/model dùng chung | Polygon và corridor qua compiler/model/preflight/upload/readback; mock workflow 15/15. Polygon source07 đã bay thật trong SITL; corridor source07 dùng trong ca reboot | Chưa đủ lặp nominal thực |
| Home và quyền điều khiển | Home sau arm có hash và TTL10s; giữ/tiếp tục cần quyền, session/boot/model/freshness. Resume đọc MIS_RESTART=0 đúng kiểu. Raw kiểm TX + ACK + heartbeat | Đạt lượt polygon thực; RTL sớm mới kiểm mock |
| Cất cánh | RuleV2 xử lý CURRENT3 trước mẫu độ cao thứ hai trong cùng RX record, không mở rộng sang record khác; giữ ngưỡng750/1500ms và0,5m. Bốn nhóm replay/đối chứng đạt; lượt mới xác nhận proof hợp lệ | Đạt phạm vi rule đã khai báo |
| Payload và media | Discovery → chọn RGB mock → cấp lease → gimbal mock readback → JPEG từ video host → sidecar tham chiếu telemetry → review | Đạt trên Android với payload tổng hợp; **0 ảnh camera thực** |
| Video xuyên AUTO | Sáu cửa sổ30s được giữ đầy đủ; đối chiếu toàn khoảng AUTO bằng JS và Python riêng | **FAIL maximum gap** |
| Mất link và reboot | Cut khi airborne/lease1 trên source04: lease→0, review gián đoạn. Reboot source07: PID35103→35854, lease→0, không reconnect/khôi phục quyền | Đạt phạm vi fault; không phải nghiệm thu discovery MAVLink sau boot mới |
| Workspace/persistence Android | Save → SAF export → force-stop/cold restart → export byte-identical; đổi sang polygon rồi nhập lại corridor qua SAF và xuất đúng byte ban đầu | Đạt |
| Hồ sơ lịch sử và SAF raw | 6 review giữ nguyên run/rawHead/plan sau Android restart; cold receiver sau khi host dừng kiểm lại6 hồ sơ. Gói raw chọn đúng run xuất SAF11.278.026 byte, SHA giống archive, receiver tái tính | Đạt toàn vẹn trong phạm vi host; không xác thực danh tính nguồn bên ngoài |
| UI | 4 màn hình ×2 theme +2 modal workspace trên1280×800; không overflow ngang, target quan trọng≥48px; hai toolbar cùng trụcY; sun/moon đổi đúng | Đạt kiểm hình học có giới hạn; còn2 phát hiệnP2, chưa có human QA/HeraHub/Xiaomi |
| 3 polygon +3 corridor cùng bản khóa | Polygon1: điều hướng đạt, video fail. Polygon2/3, corridor1/2/3 không chạy sau stop | **0/6 qualified integrated nominals; NOT READY** |

“Hoàn tất” trên card review hiện nói về điều hướng nhiệm vụ. Nó không thay kết quả video, toàn vẹn hay nghiệm thu beta. Package giữ riêng `accepted` của điều hướng và `videoQuality: FAIL`.

## Số đo thực của lượt source07

Run `s2e2c548222f5419788da`, ArduCopter4.7.1 ARM, internal quad, speedup1, fixed simulated system42/component1. Đây là profile sân thử phẳng, Home AMSL10m tổng hợp và cao độ relative Home; không phải cấu hình Hera đã hiệu chuẩn.

| Chỉ tiêu toàn khoảng AUTO | Thực đo | Gate |
|---|---:|---:|
| Khoảng quan sát | 74,934s | Phủ toàn khoảng AUTO |
| Frame hiển thị được nối với clock/raw | 2.177 | Không cắt đoạn để cải thiện số |
| FPS trung bình | 29,052 | ≥24: PASS |
| FPS nhỏ nhất trong các bin5s đầy đủ | 27,0 | ≥24: PASS |
| P95 upper source→canvas | 68,766ms | ≤300ms: PASS |
| Gap bảo thủ lớn nhất | **489,086ms** | ≤250ms: **FAIL** |

Python giải mã/kiểm CRC1.161 message thuộc nhóm dùng để xác định khoảng bay, nối lại6 report gốc và thu được đúng kết quả JS. Số đo là nguồn video tổng hợp720p → canvas call trên Android WebView, không phải camera exposure→photon, không phải độ trễ radio/Hera thực. Encoder/decoder backend thực chưa được chứng thực. Các counter source drop/recovery vẫn được giữ, không tuyên bố zero frame loss của toàn pipeline.

Phân tích giữ lại6 gap vượt250ms trong khoảng AUTO. Dữ liệu cho thấy nhiều dạng trễ ở source/relay/HTTP/decoder, chưa cô lập được một nguyên nhân duy nhất. Không quy kết tất cả cho filesystem, host scheduling hay decoder. So sánh khoảng18FPS ở thử cũ với khoảng29FPS ở bản batch là hai quan sát trên điều kiện host khác nhau, không phải benchmark A/B có kiểm soát.

## Phần đã triển khai và sửa

- Namespace riêng `pilot/missionbeta01`, `native/missionbeta01`, `planning/missionbeta01`, `evidence/missionbeta01`, `delivery/mission-beta01`. Tận dụng code đã có và khóa dependency thực thi, không sao chép toàn dự án.
- HOLD/resume/RTL có context và mode proof; thu hồi quyền khi mất client/link/boot. RTL sớm không biến khảo sát thiếu thành hoàn tất.
- Refresh tham số chỉ đọc trước cấp Home và AUTO/resume; không nới freshness/TTL, không ghi tham số để vượt gate.
- Takeoff chỉ khởi tạo ở AUTO đầu tiên. Tương quan cùng RX record được ghi rõ trong proof, raw giữ nguyên thứ tự. Hồ sơ source06 cũ vẫn INCOMPLETE, không sửa lịch sử để chuyển thành PASS.
- Video dùng envelope tối đa4 packet/lượt HTTP, giữ byte/thứ tự và kiểm từng packet, decoder pressure và clock. Unit codec, malformed/torn input và route loopback với target sai đã đạt. Bản batch chưa vượt gate jitter thực.
- Archive original package/receipt bền vững, catalog nhẹ cho heartbeat, kiểm sâu khi đọc/xuất; review chọn run cụ thể để SAF xuất đúng hồ sơ. Không đưa quyền từ lịch sử vào phiên mới.
- Lỗi runtime đã dừng với ownership rõ được ghi review INCOMPLETE; trạng thái không rõ vẫn bị chặn. Admission từ chối trước launch lưu đủ mẫu và receipt “not allocated”, kiểm lại lý do trước khi một thao tác connect mới được phép xét admission.
- Harness chờ geometry ổn định sau scroll và kiểm ngay trước tap; chờ Home UI mới. Các lần thất bại trước sửa được giữ nguyên.

## Gói bàn giao

- [Launcher và hướng dẫn](</Users/os/Downloads/AI technique/aeris/delivery/mission-beta01/README.md>): mặc định owned SITL, có chế độ mock rõ ràng. Một launcher mở host + emulator + APK; nguồn video cần thao tác Start riêng. Không tự ARM/AUTO/retry/resume.
- [APK development](</Users/os/Downloads/AI technique/aeris/native/missionbeta01/dist/aeris-missionbeta01-development01.apk>):37.267 byte, package `vn.rtr.aeris.missionbeta01`.
- APK SHA256: `0d80c89c05981934d150cebbe5d89f67e0907ddaef1b39e2b665551fed4d4f28`.
- Cert development SHA256: `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`; APK v2/v3 verify đạt. Không có production signature hay key material trong handoff.
- [Source/dependency pins07](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/source-pins07.json>):1.008 entry khớp SHA lúc kiểm cuối. Android shell dùng web source từ host, không phải APK độc lập đã sẵn sàng cho Hera thật hoặc máy mới chưa có cache.
- [Raw SAF đã nhận](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/android-saf-raw-s2e2c548222f5419788da.json>) và [receiver](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/android-saf-receiver01.json>):SHA `9684a336e16a73acffd8d03e5b299151206957570841ef61299111316962dbea`.

Một số diagnostic label `BETA05`/`CLOCKVIDEO05` được giữ từ subsystem tiền nhiệm. Namespace, package ID và pins07 là định danh build của handoff này.

## Bằng chứng chính

- [Mock workflow15/15](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/integration04/results.json>), [package/history/video analytical5/5](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/unit01/results.json>), [runtime closure3/3](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/repair-tests01.json>).
- [Batch transport3 nhóm](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/batch-unit03/results.json>), [admission rejection3 nhóm](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/preallocation-tests01.json>), [same-record takeoff4 nhóm](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/correlation-tests07.json>).
- [Kết quả Python độc lập với JS](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/oracle-result-s2e2c548222f5419788da.json>), [gap analysis](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/gap-analysis07.json>), [campaign stop](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/final-campaign05.json>).
- [Cut airborne](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/inflight-cut01.json>), [reboot airborne](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/inflight-reboot01.json>). Reboot chứng minh đổi PID trong cùng container; `mavlinkNewBootObserved=false`, không ngụ ý đã reconnect/discover lại.
- [Workspace restart](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/workspace-restart01.json>), [SAF import](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/workspace-import-verified01.json>), [workspace receiver](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/workspace-receiver01.json>), [raw SAF](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/android-saf-raw-verification01.json>), [SAF cancel/reopen](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/android-saf-cancel01.json>).
- [Android review restart](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/review-after-android-restart01.json>), [cold history sau dừng host](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/cold-history-after-host-stop01.json>), [UI geometry và visual review](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/android-visual-review01.json>).

Một assistant thực hiện Builder và Verify ở các lượt tách biệt. Python là triển khai đối chiếu thứ hai, không phải người QA độc lập. Các kiểm mock/replay, UI Android, ArduPilot thực trong SITL và phần chưa kiểm được ghi riêng; không cộng số test thành phần trăm chất lượng sản phẩm.

## Bảo toàn và dọn dẹp

[Kiểm trước/sau](</Users/os/Downloads/AI technique/aeris/evidence/coach01/preservation-missionbeta01-after.json>) giữ nguyên17.117 identity quan sát và165 đường dẫn thiếu từ trước. Không có phục hồi file, không tuyên bố các đường dẫn hiện diện liên tục. COACH02:133 entry và BETAOPS01:137 entry vẫn khớp, kể cả symlink được kiểm theo target. Không sửa candidate/SOT/corpus/ENDURE cũ, không chạy lại soak, không selection hoặc ký phần mềm production.

Gate vẫn20GiB admission /10GiB floor +256MiB reserve,31 mẫu/30s, giới hạn decline256MiB và forecast15s. Host từng dừng đúng forecast và AP admission từng từ chối trend; log giữ nguyên. Có quan sát swapfile tăng cùng thời gian, chưa xác nhận tác nhân duy nhất của biến động dung lượng. Không yêu cầu người dùng dọn thêm ổ và không xóa dữ liệu của người dùng.

Cả8 host attempts và mọi failure receipt được giữ. Có7 container AP đã dừng, được giữ nguyên; một connect bị từ chối trước allocation. Scratch `native/missionbeta01/.build` đã được build helper dọn; không tạo whole-project copy/dependency install ngoài repo. `docker image prune -f` thu hồi0B; không xóa container/volume. [Cleanup receipt](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/cleanup01.json>).

## Việc bắt buộc trước khi gọi beta dùng được

1. Giảm các đợt trễ dài bằng trace xuyên source render/encode/publish → relay/HTTP → decode/output/canvas, đồng thời đo event-loop/writer và clock. Giữ trace trọn khoảng theo block có hạn mức; không chỉ giữ latest128 khi cần truy nguyên gap. Chỉ cô lập worker/process ở đoạn đã có chứng cứ gây trễ; không đoán một root cause.
2. Làm rõ từng trạng thái điều hướng/video/toàn vẹn của hồ sơ đang chọn. Hoàn thiện control nhập file thay giao diện `Choose File` mặc định. Hai phát hiệnP2 này được ghi trong visual QA, không quảng cáo UI đã đạt đánh giá thương mại cao cấp.
3. Trên cùng một source/dependency pin mới, đạt3 polygon +3 corridor với AUTO + payload/capture + video, mọi bin5s≥24FPS, P95upper≤300ms, maxgap≤250ms; lặp link/reboot, SAF và restart. Không lấy raw replay hoặc FPS trung bình thay cho campaign thực.
4. HeraHub, RC/HID vật lý, radio/video thật, Sony/Phase One/thermal, độ đúng exposure/geotag, hiệu năng phần cứng, an toàn vận hành và production vẫn có gate riêng. Các phần đó chưa được chứng nhận bằng handoff này.

![Android thực trong SITL, video và payload tổng hợp](</Users/os/Downloads/AI technique/aeris/evidence/missionbeta01/journey-175-video-capture.png>)
