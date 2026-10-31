# Ma trận nghiệm thu simulator

17 tình huống được lập kế hoạch; chưa chạy runtime SIMTRAIN52. P0 phục vụ hội đồng, P1 là mở rộng/hiệu chỉnh theo plan.json.

## S01 Manual nhập môn

Yêu cầu: R02, R03, R07, R12.

Thao tác: Cất cánh, giữ vị trí, hình số8, hạ cánh bằng input người học.

Oracle/bằng chứng: Input overlay, observed mode, trajectory và landing/disarm; không waypoint animation.

Trạng thái: NOT_RUN.

## S02 Manual nâng cao

Yêu cầu: R02, R03, R06.

Thao tác: Stabilize khi supported, đổi orientation và tiếp quản.

Oracle/bằng chứng: Sai mode/GNSS/neutral bị chặn đúng; không giữ input cũ.

Trạng thái: NOT_RUN.

## S03 Bán tự động

Yêu cầu: R04, R06.

Thao tác: Guided takeoff, chọn điểm, đổi cao/yaw, hold/RTL.

Oracle/bằng chứng: Setpoint với actual path khác nhau và mode quan sát.

Trạng thái: NOT_RUN.

## S04 AUTO mapping

Yêu cầu: R05, R14, R15.

Thao tác: KML polygon→readiness→upload/readback→AUTO→review.

Oracle/bằng chứng: Route và ảnh/metadata được sinh từ scene theo actual pose.

Trạng thái: NOT_RUN.

## S05 AUTO corridor

Yêu cầu: R05, R15.

Thao tác: LineString có khúc cua, hiển thị overscan và transits.

Oracle/bằng chứng: Không nhận mô hình đoạn hiện tại là terrain/airspace clearance; phần chưa hỗ trợ bị chặn.

Trạng thái: NOT_RUN.

## S06 Không tải so với có tải

Yêu cầu: R07, R08, R18.

Thao tác: Hai lượt fresh cùng input/profile nền/seed, chỉ đổi payload đã khai báo.

Oracle/bằng chứng: So gia tốc, stopping distance, hover power, motor headroom; PID có thể bù tải.

Trạng thái: NOT_RUN.

## S07 Tải lệch và gió giật

Yêu cầu: R07, R09, R13.

Thao tác: Một profile off-center, gust có seed.

Oracle/bằng chứng: Attitude/motor/RPM và âm thay đổi tương quan; không đổi CG giữa chuyến để diễn hiệu ứng.

Trạng thái: NOT_RUN.

## S08 Mưa/sương và camera

Yêu cầu: R09, R14.

Thao tác: Giảm visibility/ánh sáng với profile effects rõ.

Oracle/bằng chứng: VFX không tự thành lực; noise/blur sensor có metadata và oracle nếu bật.

Trạng thái: NOT_RUN.

## S09 Tiếp quản AUTO

Yêu cầu: R03, R06.

Thao tác: Pause, manual takeover, xem phần còn lại và xác nhận resume.

Oracle/bằng chứng: Một owner, mode thật, no pose teleport, no command replay.

Trạng thái: NOT_RUN.

## S10 CORS/GNSS suy giảm

Yêu cầu: R04, R15, R16.

Thao tác: Correction age/FLOAT hoặc payload GNSS mất.

Oracle/bằng chứng: Hành động acquisition khác điều hướng; đúng policy, không ép cùng RTL cho mọi lỗi.

Trạng thái: NOT_RUN.

## S11 Video/camera lỗi

Yêu cầu: R14, R15, R16.

Thao tác: Video freeze/ảnh thiếu/full storage trong khi flight telemetry còn.

Oracle/bằng chứng: Cảnh báo riêng; actual inventory/age đúng; không nói drone mất chỉ vì video mất.

Trạng thái: NOT_RUN.

## S12 Input/mạng mất

Yêu cầu: R01, R02, R06, R17.

Thao tác: Unplug joystick, blur, latency/jitter và stale session.

Oracle/bằng chứng: Input cũ không giữ vô hạn; quyền bị thu hồi; remote P1 kiểm riêng.

Trạng thái: NOT_RUN.

## S13 Va chạm/tiếp đất

Yêu cầu: R07, R10.

Thao tác: Ground contact, near-obstacle và crash có kiểm soát.

Oracle/bằng chứng: Collider đúng tỷ lệ; giữ outcome, không tự hồi sinh giữa bài.

Trạng thái: NOT_RUN.

## S14 Overload/restart

Yêu cầu: R18, R19, R20.

Thao tác: CPU/GPU load, queue/disk pressure và owned process kill.

Oracle/bằng chứng: No physics frame drop để làm đẹp RTF; hồ sơ incomplete và restart disconnected.

Trạng thái: NOT_RUN.

## S15 Offline và máy chiếu

Yêu cầu: R11, R12, R21, R23, R24.

Thao tác: Cold start offline, mirror/extend, unplug display.

Oracle/bằng chứng: UI đọc từ cuối phòng, input focus an toàn, không CDN/license surprise.

Trạng thái: NOT_RUN.

## S16 Challenge hội đồng

Yêu cầu: R16, R18, R22.

Thao tác: Người xem chọn target hoặc seed chưa dùng sau khi bắt đầu buổi.

Oracle/bằng chứng: Kết quả live xuất hiện trong trace và review; backup replay được gắn nhãn.

Trạng thái: NOT_RUN.

## S17 Sensor và payload mở rộng

Yêu cầu: R14, R17, R25.

Thao tác: P1: bật từng EO/IR/LiDAR extension với model, provenance và thời gian riêng; remote cùng session/role.

Oracle/bằng chứng: Ground truth và reported data không lẫn; sensor chưa có model bị từ chối hoặc ghi unsupported.

Trạng thái: NOT_RUN_P1.

