# SIM32-PIPE03 — bàn giao14/10/2026

**PARTIAL — sửa guard/clock và tối ưu RK4 đã có bằng chứng; pacing1× và phiên bản đóng writer/journal cuối chưa nghiệm thu SITL.** Chủ việc yêu cầu bàn giao kết quả hiện có sau khi host thiếu headroom; không chạy thêm SITL, không ký hay tích hợp Fly. Source/candidate đóng băng và ENDURE được giữ nguyên5220SHA. Thực hiện tuần tự Build/Verify bởi một agent, không phải kiểm định độc lập.

## Kết quả đã kiểm trên nguồn được ghi nhận

- Phase A:12test đối nghịch và5probe SITL thật450/550/900/1400/3200ms đạt. Pause3200ms kết thúc epoch trước khi xử lý frame chờ;1400ms xử lý frame đã nhận một lần rồi kết thúc khi thấy duplicate, không cached sensor echo.450/550/900ms tiếp tục cùng epoch. Một nhiệm vụ UI đủ Plan/Home/Preflight/upload/readback/ARM/AUTO/payload/ground/disarm/review đạt13check.
- Nguồn clock có raw packet/peer/nonce, phân loại phản hồi biết trước đến trễ/lặp/out-of-order; nonce lạ/peer sai từ chối. Node/Python/guest có tên miền counter riêng và bracket giữ uncertainty.3test Node listener bổ sung đạt, gồm lỗi ghi evidence không làm callback thoát mất kiểm soát. Raw clock/frame binding kiểm lại trên các run; không suy zero offset/drift hoặc latency một chiều.
- Guest Linux co-location đã build kernel nhỏ từ C bất biến trong image riêng, nhưng **REJECT**: byte gió lệch từ frame10. Không chạy/adopt guest physics vào SITL, không nới oracle. Khác nền Python/libm/compiler được ghi; nguyên nhân số học chính xác chưa cô lập.
- Thay thế bằng gộp4stage RK4 trong C trên host: giữ double precision, thứ tự phép tính/compensated dot, cấm fast-math/FMA contraction, giữ Python normalization/contact/wind/wrench/battery/aux. Đối chiếu nguyên byte sensor và aux trên**1.370.468frame** của corpus đã có oracle gốc, toàn bộ khớp. Microbenchmark đảo thứ tự,3profile×3replicate×2engine×6000step: trung bình26,035→16,758µs/step, giảm**35,63%**. Đây là offline model cost, không phải RTF vòng kín.
- Kernel fused kiểm lại5fault probe SITL và raw/frame/clock binding đều đạt trước khi mở batch UI đối chứng.

Các gate trên thuộc các source snapshot lịch sử cụ thể. Backend/epoch/journal được sửa thêm sau batch; không gán PASS lịch sử cho nguồn cuối.

## Batch đối chứng đã dừng — giữ cả lỗi trong denominator

Kế hoạch12lượt counterbalanced; đã ghi6lượt đầu,6lượt chưa bắt đầu. Cùng offset1kg/gust seed32/survey7m/AP v2 ARM64,2CPU384MiB,rate1200Hz,nominal1×,cap500000µs. Mỗi lượt có UI và instrumentation. Tải host nền biến thiên, không kết luận nhân quả/thống kê từn=1mỗi cell. Lượt cuối có pause controller và dừng chủ đích, không dùng làm mẫu nhiệm vụ hoàn chỉnh.

| Case | Engine | Worker CPU thêm | UI/review | RTF đã ghi | Lưu ý |
|---|---|---:|---|---:|---|
| b01 | native derivative |0|PASS|0,987751|Nhiệm vụ/hồ sơ hoàn chỉnh |
| b02 | fused RK4 |0|FAIL|0,979525|SIGTERM rơi giữa computation, epoch terminal; bước chưa phát được giữ trong aborted-step |
| b03 | fused RK4 |2|FAIL|0,853976|Raw quota128MiB;146610row ghi được, counter146612; **thiếu2raw sensor row**, không thể khôi phục byte gốc |
| b04 | native derivative |2|PASS|0,982992|Nhiệm vụ/hồ sơ hoàn chỉnh |
| b05 | fused RK4 |6|PASS|0,891815|Nhiệm vụ/hồ sơ hoàn chỉnh |
| b06 | native derivative |6|FAIL/cancelled|0,628274|Controller pause/managed stop; raw prefix được seal nhưng nhiệm vụ chưa hoàn tất |

3/6UI đạt,0/6RTF≥1. Không bỏ mẫu lỗi hoặc cộng khoảng gián đoạn.746772raw frame hiện hữu khớp oracle gốc; riêng b03 chỉ có proof prefix INCOMPLETE, không có complete model PASS hay sửa lịch sử. AP trace chứng minh cả frame146610/146611 đã parse nhưng raw sensor bytes không có; retained source/stage/rejected-servo không được dùng để chế lại bằng chứng. b02 có aborted sensor riêng, không biến thành response đã gửi.

Trace ghép bằng frame duy nhất và đo trong từng miền clock: AP transport wait trung bình469–1194µs; host RX→send trung bình112–260µs; kỳ vọng period833,333µs. Các đoạn overlap, không cộng hoặc trừ để quy riêng cho mạng. Chu kỳ servo p99 khoảng6,68–10,92ms, max125–488ms. Debt clip500ms vẫn xảy ra, tổng1,39–37,79s tùy capture. Mô hình không bị tăng speedup/hạ cap hay bỏ bước để tạo RTF đẹp. Giảm kernel cost chưa đủ chứng minh nhịp1×; vòng AP/backend/guest scheduling cần xử lý tiếp có kiểm soát.

## Sửa tiếp sau khi batch đóng — chỉ kiểm offline

1. Managed shutdown: publish DRAINING, chặn adapter/new input, hoàn tất frame đã được nhận hợp lệ nếu vẫn fresh, ghi datagram chờ chưa được admit riêng; giữ stale/clock/duplicate terminal. Không dùng SIGTERM chủ đích để tạo incomplete giả cho một frame có thể đóng đúng ranh giới. Không phục hồi epoch terminal.
2. Journal riêng: tăng bound uncompressed512MiB theo dữ liệu có epoch/domain, thêm hard compressed192MiB để giới hạn disk; vẫn FIFO256. Lỗi writer/queue giữ tối đa258row chưa ghi trong incomplete-tail và báo incomplete. Kiểm lỗi writer ở loop trước khi admit bước mới. Salvage không đổi FAIL thành PASS.10test offline threaded/inline quota, giữ từng row một lần, sticky failure, DRAINING/close và stale-drain đạt.
3. Reclaim phần zero chưa dùng của36trace riêng đã đóng: full SHA/length trước-sau khớp, event/header giữ nguyên; trả lại2.136.506.368byte allocation. Không sửa file bảo vệ hay ENDURE. Attempt đầu F_PUNCHHOLE bị EFAULT do chưa khai báo đúng variadic ABI ARM64; được giữ sự cố, sửa ABI và kiểm SHA sau thao tác thành công.

**Chưa chạy SITL bổ sung cho revision cuối**, gồm graceful stop ở mọi phase, journal overflow/rescue với AP thật, clock/stale regressions sau sửa và matrix12lượt mới. Không bật mặc định fused hoặc triển khai production dựa trên test offline.

## Sự cố và giới hạn tài nguyên

Attempt guard đầu bị collision property`clock` của link; đã đóng PID/container sở hữu, giữ raw/receipt và source cũ, sửa thành`clockCalibration`, dùng IDs mới cho5probe được ghi nhận. Batchstop POST thiếu Origin header bị400; không retry; đóng bằng SIGTERM handler có kiểm PID. Giải thích race ban đầu là giả thuyết sai và có clarification riêng, không rewrite receipt cũ.

Host free space giảm ngoài diễn tiến reserve dự kiến. Sau khi batch đã đóng, đã quan sát**19,87GiB** trước compaction; không được tuyên bố host luôn giữ sàn20GiB. Nguyên nhân tổng giảm dung lượng chưa xác định, không quy cho ứng dụng khác. Mọi SITL mới đã chặn; sau reclaim còn khoảng22–23GiB. Không large build/install/emulator sau breach; người dùng chọn bàn giao thay vì giải phóng thêm. Runtime/image experiment trước đó có admission thực31GiB và full budget; batch có monitor reserve. Một kiểm floor hiện tại không thay cho record thời gian trước.

## Verify và bàn giao

| Requirement | Trạng thái bằng chứng |
|---|---|
| S01 guard epoch/stale |Actual5probe mỗi engine đã đạt trên nguồn lịch sử; managed-close revision cuối offline-only |
| S02 nonce/clock domain |Unit/loopback/Node và raw nonce/bracket qua actual SITL đạt |
| S03 duplicate/gap policy |Actual duplicate terminal/no cached echo, unique prefix/zero-delta checks đạt trước revision cuối |
| S04 fault + healthy UI trước tối ưu |Gate phase-A PASS, đủ raw oracle/binding; không áp cho revision cuối |
| S05 pipeline optimization |Strict host kernel/oracle/microbenchmark đạt; guest REJECT; chưa đạt pacing1× |
| S06 repeated whole-run acceptance |6/12pre-fix capture,3UI fail;12lượt revision mới NOT_RUN theo yêu cầu bàn giao |

Implementation6/6; recorded full gate3/6(S02/S03/S04),3partial(S01/S05/S06); latest runtime **NOT READY**, không dùng tỷ lệ này làm phần trăm sẵn sàng sản phẩm. Python compile/Node parse checks của module cuối đạt; kernel build/oracle đạt;25check offline(adversarial12+Node3+shutdown/journal10) được tách theo revision, không gọi là25live tests.

5220file bảo vệ khớp SHA toàn bộ.18launch source bindings đối chiếu byte trong current/historical snapshots đạt. Source/candidate/trust/ENDURE/SOT/P21/P22/N24/T25/T26/SIM32/INSTRUMENT01/PACING02 gốc không thay đổi. AP SHA`f2be1f…` và builder gốc`e27f…` giữ nguyên. Hash là point-in-time integrity, không phải chữ ký mới, không chứng minh path gốc hiện diện liên tục hay24h acceptance. ENDURE thất bại cũ giữ nguyên; không restart/selection/sign/Fly integration.

Đã đóng18state/run sở hữu, không còn backend/AP/clock/CPU worker/browser/preview riêng; container--rm được dừng, state `.local/sim32-pipe03/<run>` được gỡ theo receipt. `docker image prune -f` trả0B; không prune volume/container, không copy project vào/tmp hay install ngoài repo. Giữ kernel host/Linux và image builder riêng để truy xuất provenance; bản signed/candidate không được tạo.

Evidence: `phase-a-gate.json`, `fused-faults.json`, `integrator-oracle.json`, `linux-oracle.json`, `pre-fix-summary.json`, các raw/binding/clock/bounded-stage proof theo run, `shutdown-journal-tests.json`, `historical-source-verification.json`, `preservation-after.json`, `initial-trace-compaction.json`, `verification.json`, source/evidence fingerprints trong `evidence/sim32-pipe03`. Module riêng tại `pilot/sim32-pipe03`; README nêu gate và helper có ID lịch sử không được dùng lại.

Bước tiếp theo khi được yêu cầu và headroom≥28GiB: pin nguồn cuối → fault/graceful-stop/journal AP thật với IDs mới → oracle/frame/nonce →12lượt đối chứng mới → tách scheduling/transport từ số đo nếu1× vẫn fail. Không thay speedup/cap hoặc physics steps để vượt gate. Hera/HIL/calibration,Android/input/video,24h endurance,Ragas/DJI comparison vẫn có gate riêng.
