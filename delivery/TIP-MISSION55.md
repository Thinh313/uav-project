# MISSION55 · Corpus và oracle theo RAGAS54

15/10/2026. Triển khai B1/B2 trong `pilot/mission55`, bằng chứng trong `evidence/mission55`. Không sửa baseline/candidate, canonical SOT, trust, ENDURE hoặc nghiên cứu RAGAS54; không ký, chạy SITL/emulator mới, build APK hay tích hợp Fly.

| AC | Yêu cầu và cách kiểm |
|---|---|
| AC01 / RG54-01,02,04 | Camera corpus206/2000/2001/2500/2501 giữ tham số/thứ tự, null khác0, flags, identity; phát hiện placeholder, drop, sai target/session; ACK/reported/file tách biệt. Corpus synthetic phải có nhãn. |
| AC02 / RG54-05,06 | So riêng header/editable/executable; polygon/góc/entry/concave/refly/CameraCalc/cachedItems/unknown fields/DO_JUMP đều không bị bỏ ngầm. Giữ bản gốc có SHA. Tái dùng QGC5.1.5 fixtures có provenance; không gọi generated fixtures là QGC exports. |
| AC03 / RG54-07,12–15 | Home/datum/frames/đơn vị/toạ độ, calc terrain khác native terrain; unknown/no-data/stale/reboot phải chặn; Home10→7 vẫn diff. Không sửa Home để so khớp. |
| AC04 / RG54-08–11,16,22 | Oracle analytic và triển khai độc lập: area planar khác area ellipsoid, WGS84 inverse distance, per-leg ETA, camera spacing/count/cadence/GSD, geoid và ridge. Threshold engineering rõ; library/vector pin. Không lấy số dự kiến làm chất lượng ảnh thật. |
| AC05 / RG54-01 | Replay19-item actual-QGC03 readback bằng decoder/comparator mới; rule AP4.7.1 chỉ áp đúng command/field/direction, hash-bound receipt. Không gọi retained replay là chuyến SITL mới. |
| AC06 | Có CLI chỉ đọc, deterministic reports, bounded input/resource; test mutation/metamorphic và fault. Báo NOT_CHECKED cho RAGAS runtime/QGC regeneration/real camera/field. |
| AC07 | Kiểm pin trước/sau gồm RAGAS54 và baseline kế thừa; sàn20GiB; cài/phụ thuộc nếu cần chỉ trong module mới với SHA/license, không copy toàn project hoặc giữ scratch ngoài repo. |

Một agent qua pha Contractor → Builder → Verify; oracle có implementation khác không phải đánh giá viên độc lập. Không có cổng cho phép phát lệnh bay trong module này. Không lấy tuyên bố RAGAS thành acceptance của AERIS. Manifest RAGAS112/tên111 tiếp tục OPEN, không tải binary trong nhiệm vụ này.
