# AERIS — tiêu chuẩn chất lượng sản phẩm và mục tiêu vượt DJI

Quyết định chủ việc,13/10/2026: tập trung giải pháp hiện tại; yêu cầu khắt khe về thuật toán, hiệu suất, đồ họa và mô phỏng. AERIS là sản phẩm cạnh tranh với và hướng tới vượt DJI, đồng thời thay Ragas theo workflow được nghiệm thu. Đây là yêu cầu thiết kế của chủ việc, không phải kết quả benchmark.

Tài liệu này là chỉ dẫn làm việc bền vững cho SIM32 và các increment sau. Đọc trước khi lập TIP, chọn stack, tối ưu hoặc bàn giao. Được lưu ngoài canonical SOT/source/candidate đang đóng băng; không sửa hay thay thế baseline lịch sử.

## Chuẩn bắt buộc

1. **Một hành trình sản phẩm chạy thật trong phạm vi simulator.** Khảo sát → kiểm Home/độ cao/profile → upload/readback → bay SITL → camera/gimbal → kết thúc → review/bàn giao. Một lần thao tác phải truy được request/session/aircraft/target và phản hồi. Không tính ACK, playback hoặc hoạt ảnh theo waypoint thành execution.
2. **Vật lý tạo ra trạng thái; đồ họa thể hiện trạng thái.** Autopilot SITL và model động lực học đóng vòng kín. Renderer/audio không ghi vị trí, thái độ hoặc tiến độ nhiệm vụ để làm cảnh đẹp. Điều khiển qua adapter simulator riêng, không qua inspector replay hoặc đường radio thật.
3. **Thuật toán có phép chứng minh/đối chứng phù hợp.** Ghi đơn vị, hệ tọa độ, timestamp, datum và giới hạn số. Kiểm trường hợp biên, nghiệm tham chiếu, sai số, tính hội tụ theo bước thời gian, tính lặp lại và miền mô hình. Tối ưu có số đo trước/sau, giữ độ đúng và corpus; không tối ưu bằng bỏ kiểm hay hạ độ chính xác âm thầm.
4. **Profile tải có cơ sở vật lý.** Mass, CG, inertia tensor, vị trí payload, thrust/torque curve, response lag, drag và battery model có đơn vị, version và provenance. Thay tải phải cập nhật các đại lượng liên quan. PID có thể bù tải; không mặc định tải nặng luôn làm mọi chuyển động chậm hơn. Giới hạn actuator phải được mô hình và quan sát.
5. **Môi trường có miền hiệu lực.** Wind/gust/turbulence dùng seed và clock đã ghi. Terrain/collision dùng mét thật và datum rõ; không phóng đại mesh dùng cho physics. DEM không tự chứng minh vật cản nhỏ. Va chạm, propwash, ground effect, tải treo, mưa tác động động cơ hoặc khí động học phức tạp chưa có model thì ghi UNSUPPORTED, không dùng hiệu ứng hình ảnh làm bằng chứng.
6. **Âm thanh có provenance.** Tổng hợp theo RPM/model motor, số rotor/cánh, tải, khoảng cách và chuyển động người nghe. RPM ước tính khác RPM quan sát. Âm thanh tổng hợp chưa phải âm Hera đo thực; calibration cần bản ghi tham chiếu cùng cấu hình và điều kiện đo. Mức âm lượng speaker không phải SPL vật lý đã hiệu chỉnh.
7. **Ngân sách hiệu suất được chốt theo workload và máy.** Ghi CPU/GPU/RAM/OS/build, chế độ nguồn, compiler, simulator và renderer hashes; cold/warm, resolution, số payload/stream/waypoint, dt và seed. Thu p50/p95/p99/max và phân bố, deadline misses, frame age/drops, queue depth, RSS/CPU/GPU và disk. Control/logging không phụ thuộc render FPS; queue có giới hạn và hành vi overload. Không tuyên bố hard real-time từ p99 hoặc host emulator.
8. **Đồ họa cao cấp phục vụ vận hành.** Branding trắng/đen, vàng làm nhấn phụ; thông tin, mức ưu tiên và vị trí hành động ổn định. Tỷ lệ/đơn vị ánh xạ đúng; camera không che lỗi model. Verify screenshot và walkthrough đủ Plan/Preflight/Fly/Review, tải/gió/mất link, touch/keyboard/window. Native48dp không được suy ra từ48CSSpx. Video frame age và nguồn mô phỏng phải nhìn thấy.
9. **Evidence và authority không bị đánh đổi cho tốc độ.** Không mất hồ sơ âm thầm, không hoàn tất giả, không duplicate command ngoài policy; mất focus/restart không tự cấp lại quyền. Header/source/profile/clock/seed/raw trace và hashes đi cùng kết quả. Synthetic, simulator-observed, imported và physical giữ riêng.
10. **Tài nguyên là gate thật.** Giữ sàn host20GiB; admission tính peak archive + full uncompressed output + runtime + AVD + evidence + host margin, không chỉ dung lượng cuối. Theo dõi trước và trong từng bước, dừng tiến trình sở hữu rõ khi headroom không đủ. N31 từng vi phạm sàn trong giải nén; receipt giữ FAIL, không lặp giả định sparse. Không large install/emulator ở dung lượng hiện tại; không whole-project copy hoặc xóa dữ liệu không liên quan.

## Các mục tiêu kỹ thuật khởi đầu — chưa phải số đo đạt

| Mục | Mục tiêu đề xuất cho workload đã khai báo | Cách nghiệm thu |
|---|---|---|
| Viewer3D |60FPS nominal ở1280×800; p95 frame time≤16.7ms, p99≤33.3ms | Frame traces trên cấu hình reference có GPU; chạy cùng tải telemetry/payload. Phải công bố drops, sample denominator và fallback. Không coi headless software render là native GPU benchmark. |
| UI feedback local |p95≤100ms cho input→feedback nhận thao tác | Đo từng thao tác/render path; tách khỏi ACK/vehicle response và latency đường truyền. |
| Physics |Real-time factor≥1 cho tốc độ1× trên máy reference; convergence theo dt/2 và dt/4 | So nghiệm quỹ đạo/trạng thái theo scenario cố định; tolerance vật lý phải chốt theo model và dữ liệu hiệu chỉnh trước gate fidelity. Không silently bỏ physics steps để giữ FPS. |
| Thuật toán mission |Đúng schema/geography/datum/camera invariants; budget runtime/RAM chốt theo corpus | Benchmark theo số vertex/waypoint và pattern, worst-case/invalid inputs. Không đặt một số runtime chung khi chưa có workload. |
| Control/video |Budget từng đoạn, jitter/freshness/deadline, overload/failure recovery | Ngưỡng theo transport, firmware và stream thực; chưa có dữ liệu thì OPEN, không gán số của host thành Hera. |

Các số trong bảng là engineering targets đề xuất, không được ghi thành owner-approved numerical thresholds hoặc performance PASS. Sau calibration/reference benchmark, chốt cấu hình và budget trong contract version mới, giữ nguyên bản cũ. Đạt mục tiêu FPS/latency không đủ nghiệm thu sản phẩm nếu gate độ đúng, authority, bằng chứng hoặc chất lượng khảo sát thất bại.

## Đối chứng cạnh tranh

- **Ragas:** khi khả thi, cùng HeraHub/Hera/firmware/payload/mission/environment/operators, pin binary versions/hashes và counterbalance thứ tự. Theo PAYLOAD21-AB-PROTOCOL; runtime hiện NOT_CHECKED.
- **DJI:** chọn chính xác platform/controller/Pilot version/payload và workflow, không dùng “DJI” như một baseline duy nhất. Không giả định phần mềm DJI chạy trên HeraHub. So hệ thống tương đương theo nhiệm vụ, điều kiện, output quality và cách đo; ghi khác biệt hardware, transport, camera và training để giới hạn suy luận về riêng phần mềm.
- Chốt trước collection: task completion, lỗi thao tác và lỗi nghiêm trọng, thời gian/workload, latency/frame age, recovery, coverage/GSD/blur/geographic accuracy, output integrity và tổng tài nguyên. Failed/aborted/missing samples giữ trong denominator. Phương pháp, cỡ mẫu và ngưỡng chưa chốt thì benchmark OPEN.
- Chỉ công bố vượt ở workflow/cấu hình/metric có phép đo và kết luận thống kê phù hợp, trong khi các gate không được phép suy giảm đã đạt. Full replacement cần đầy đủ phạm vi đã cam kết; simulator đẹp hoặc test count không chứng minh vượt DJI.

## Ưu tiên sản phẩm kế tiếp

SIM32: một multicopter reference, không tải/tải giữa/tải lệch; gió tĩnh/gió ngang/gust có seed; AERIS simulation workspace độc lập nối autopilot SITL; viewer/audio bám physics; camera/gimbal synthetic; mission/review lineage và fault scenarios. Profile Hera ban đầu là provisional, chưa calibrated. Bắt đầu từ physics/control và oracle, sau đó viewer/audio, cuối cùng benchmark vòng kín; không hoàn thiện cảnh trước để che đường điều khiển chưa có.

Android runtime, SDK/HeraHub bench, HIL, flight và so sánh thực vẫn có gate riêng. ENDURE thất bại không được đổi thành PASS; không restart, ký release/candidate mới hay tích hợp vào Fly đóng băng bằng tiêu chuẩn này.
