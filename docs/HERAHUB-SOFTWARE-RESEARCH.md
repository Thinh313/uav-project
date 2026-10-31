# HeraHub · Nghiên cứu nền tảng phần mềm

12/10/2026 · HERA02 · Ưu tiên: khảo sát và lập nhiệm vụ bay.

**Đủ căn cứ để đi tiếp với phần mềm cho HeraHub nền Android/ARM64, qua lớp adapter phần cứng và kiểm khả năng lúc chạy.** Điểm thiếu ảnh hưởng tích hợp thật là SDK/giao thức đầu vào, firmware thực, endpoints và cấu hình luồng; không phải chênh lệch số nits. HeraLink là tên cũ, HeraHub là tên hiện tại theo chủ việc. Độ sáng được coi là đủ cho dự án theo quyết định của anh; đây là ràng buộc làm việc, không phải kết quả đo độ sáng.

## Nền tảng và phạm vi nguồn

[Trang HeraHub nền Intel](https://rtrobotics.com/commercial/herahub) công bố i7 và tám luồng; [HeraHub v2](https://rtrobotics.com/commercial/herahub-v2) công bố QCS8550, Android 13, Adreno 740, bốn joystick và sáu luồng 1080p. Phải tách thế hệ khi tìm tài liệu. Tên đổi không chứng minh tương thích firmware, SDK hay cách đấu dây.

[Tài liệu Qualcomm](https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/Qualcomm-Application-Processors-for-IoT-Selector-Guide.PDF), trang 2, xác nhận cấu trúc octa-core của QCS8550. Khả năng silicon không là ngân sách decode/thermal của controller. Các khác biệt dung lượng giữa public spec và master nội bộ được xử lý bằng quota và truy vấn dung lượng thật, không khóa cấu hình ứng dụng theo một brochure.

[Manual RAGAS](https://rtrobotics.gitbook.io/real-time-robotics/ragas.md) tự ghi 4.0.0 build 4. [Release công khai](https://github.com/Real-Time-Robotics/ragas-release/releases/tag/v4.0.14-b111) mới nhất trong capture phát hành ngày 09/10/2026; [manifest Android](https://github.com/Real-Time-Robotics/ragas-release/releases/download/v4.0.14-b111/manifest-prod.json) ghi 4.0.14 build 111, ABI arm64-v8a. Chưa biết bản trên controller. Chưa kiểm package name, signing certificate, min/target SDK hay nội dung APK. Public binary/manual không cung cấp source RAGAS hoặc SDK HeraHub có thể build lại trong tập nguồn đã chọn.

## Điều tìm được và tác động triển khai

| Mảng | Bằng chứng đúng phạm vi | Quyết định cho phần mềm |
|---|---|---|
| Cài đặt và lifecycle | [Installation](https://rtrobotics.gitbook.io/real-time-robotics/getting-started/installation.md): APK, kiểm overlay và exemption tối ưu pin; OEM có thể cần thêm autostart setting | Kiểm installed/target SDK, quyền và hành vi OEM. Thiết kế reconnect/lưu phiên; không coi quyền overlay là bảo đảm dịch vụ luôn chạy |
| Joystick và phím | [RC Settings](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/settings/rc-settings.md): 12 **chức năng** gán được, calibration và live channel | Tách physical input, mapping, calibration và semantic action. Không đọc “12 chức năng” thành 12 nút hay gán L/R theo hình |
| Điều khiển lịch sử | [HeraSight control](https://rtrobotics.gitbook.io/real-time-robotics/payloads/herasight-2/remote-controller-operation.md) mô tả wheel/dial cho EO/IR/gimbal; [setup](https://rtrobotics.gitbook.io/real-time-robotics/payloads/herasight-2/setup.md) dùng tên HeraLink | Dùng để hiểu intent thao tác. Không kế thừa channel ID, keycode hay default TCP từ tài liệu cũ sang v2 |
| Telemetry/link | [Transmission Settings](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/settings/transmission-settings.md): MAVLink signing, forwarding, heartbeat và thống kê; [Top Bar](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/flight/top-bar-status.md): chi tiết từng link | Mỗi link có identity, freshness và counters. Đổi link không được tạo nhiều owner phát cùng command; ACK và trạng thái quan sát phải riêng |
| RTK | [RTK Settings](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/settings/rtk-settings.md): NTRIP profile/reconnect, VIO origin; [GPS_RTCM_DATA](https://mavlink.io/en/messages/common.html#GPS_RTCM_DATA): carrier correction chuẩn | Tách caster connection, tuổi correction và fix trên máy bay. Connected không tự đồng nghĩa RTK Fixed |
| Offline | [Offline Map](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/map/offline-map.md): region/cache/progress; [Terrain](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/mission/mission-terrain.md): elevation cache | Một gói nhiệm vụ chứa vùng phủ map/terrain và báo đủ/thiếu trước khi ra hiện trường |
| Storage | [Storage](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/settings/storage.md): phân loại map, terrain, log, media và preview khi xóa | Quota theo free bytes thực, log có giới hạn, dọn cache có preview; tránh hardcode 256/512GB |
| Pin và update | [Top Bar](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/flight/top-bar-status.md) nói pin máy bay. [OTA Update](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/settings/ota-update.md) nói firmware **payload**, disarmed và pin controller ≥50% | Ba luồng cập nhật app/BSP/payload tách riêng. API hai pin controller còn thiếu; không gán pin máy bay thành pin controller |
| Payload/UI | [Capability matrix](https://rtrobotics.gitbook.io/real-time-robotics/reference/capability-matrix.md) phân biệt tính năng theo payload; [RAGAS website](https://rtrobotics.com/commercial/ragas) quảng bá REST/WebSocket | UI dựa trên capability đã khám phá. API quảng bá chưa đủ làm transport contract; endpoints, auth và schema còn null |

## Video: chọn theo luồng thật

[Media3 RTSP](https://developer.android.com/media/media3/exoplayer/rtsp) liệt kê H.264 với SPS/PPS trong SDP, UDP unicast và interleaved TCP; không liệt kê H.265 trong bảng hỗ trợ chụp được. Không mở rộng điều này thành nhận định mọi module Media3 đều không hỗ trợ H.265.

Spec HeraSight61 nội bộ `Sheet1!C17` nêu RTSP/UDP/RTMP; `C42` nêu H.264/H.265 ở **định dạng phim** ([master](</Users/os/Downloads/RTR-Specification/RTR Master Specification/HeraSight61-Standard/HeraSight61-standard-MASTER-v1.0.xlsx>)). Đây chưa phải codec của stream trực tiếp. Bước đầu phải lấy URL/SDP thật, codec, profile, resolution, fps và transport. Nếu luồng không phù hợp Media3 RTSP, thử adapter native/SDK hoặc [GStreamer rtspsrc](https://gstreamer.freedesktop.org/documentation/rtsp/rtspsrc.html) và [H.265 depayloader](https://gstreamer.freedesktop.org/documentation/rtp/rtph265depay.html); depayloader chỉ tách RTP, vẫn cần decoder.

[Android CodecCapabilities](https://developer.android.com/reference/android/media/MediaCodecInfo.CodecCapabilities) có query low-latency feature và max instances; số instances là gợi ý giới hạn trên, không bảo đảm chạy đồng thời. Đề xuất đo một luồng chủ đạo trước, tăng số luồng theo workload thật; ghi dropped frames, thời gian decode/present và thermal. Chưa đặt số latency nghiệm thu từ marketing.

## Workflow khảo sát: thứ tự thực hiện

[Mission manual](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/mission.md) tách lưu local, upload và thực thi. Điều này phải xuất hiện rõ trong UI: chỉnh sửa plan không tự thay mission đang trên máy bay; upload có thể thay mission đã có. [Waypoints and Patterns](https://rtrobotics.gitbook.io/real-time-robotics/user-guide/mission/waypoints-and-patterns.md) là nguồn intent thao tác và camera; chưa là file format/giao thức upload.

Release 4.0.14 báo sửa grid QGC `.plan`, số liệu area/time/photo, chuyển lệnh camera tới ArduPilot, chặn export khi thiếu terrain và resume ở waypoint cuối đã tới. Đây là **release claims**, cần fixture và SITL để xác nhận; không dựa vào số ảnh hoặc quỹ đạo của bản cũ làm đáp án. Nguồn: [release manifest](https://github.com/Real-Time-Robotics/ragas-release/releases/download/v4.0.14-b111/manifest-prod.json).

Các acceptance case đề xuất:

1. Polygon thực và camera profile có đơn vị rõ; GSD, footprint, overlap và speed hợp lệ. Không có footprint/trigger model thì photo count unavailable.
2. Fixtures QGC cố định phiên bản: góc/phase/lượt tuyến, polygon lõm, entry corner, round-trip và phép tính trên toàn mission. Tránh tự tuyên bố tương thích trước khi đối chiếu format nguồn.
3. Chọn frame độ cao rõ: relative launch, terrain hoặc AMSL. Terrain thiếu hiện dữ liệu cần tải; cache sẵn dùng offline. Không xuất cao độ suy đoán.
4. Lưu → kiểm plan → upload → xác nhận nội dung trên vehicle → thực thi. Mỗi bước có lỗi và khôi phục riêng; cần command ownership và telemetry observed.
5. Báo ảnh planned/aircraft-reported riêng; ảnh reported chưa chứng minh file ảnh đã lưu đủ hoặc vùng phủ đạt chất lượng.
6. Pause/resume lưu tiến độ và vùng chưa phủ; test không bỏ sót, chấp nhận refly vùng biên theo chính sách được kiểm.

Đây là yêu cầu cho bước phát triển, chưa là tính năng đã chạy trong workbench hiện tại.

## Contract tích hợp và khoảng trống

Kiến trúc đề xuất: UI Plan/Fly → dịch vụ mission/session/video → adapter Android, input, payload, telemetry, RTK và power. Các adapter công bố capability và trạng thái unavailable; không dựng giả dữ liệu phần cứng để UI có vẻ đầy đủ. Giữ giao diện trắng/đen, vàng nhấn ít theo branding; calibration/setup nằm ngoài màn hình tác nghiệp, status quan trọng ổn định.

[Android controller events](https://developer.android.com/games/sdk/game-controller/controller-input) áp dụng nếu Hera xuất thiết bị tương thích; cần inventory để biết HID, UART hay SDK hãng. [MANUAL_CONTROL](https://mavlink.io/en/services/manual_control.html) định nghĩa trục chuẩn nhưng chưa chứng minh đó là đường RC đang dùng. [Redundancy guidance](https://mavlink.io/en/guide/redundancy_deduplication.html) chỉ ra seq theo từng channel không dùng dedup liên link; [signing](https://mavlink.io/en/guide/message_signing.html) là cơ chế xác thực, không đủ làm bằng chứng có kênh mã hóa.

[Android background restrictions](https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start) phụ thuộc API/target SDK và ngoại lệ. Cần thử boot, screen-off, suspend, process restart và reconnect trên đúng firmware; không áp máy móc quy tắc Android 14+ cho Android 13.

| Chưa biết trong tập nguồn đã chọn | Ảnh hưởng | Có thể làm ngay |
|---|---|---|
| SDK/license, method signatures, native ABI/dependencies | Chặn adapter hãng thật | Contract adapter và replay harness |
| Input transport/keycode/axis/channel map, ownership calibration | Chặn gán phím/RC trên Hera | Inventory read-only, event trace và simulator input |
| Build fingerprint, density/insets/target SDK/package signer | Chặn chứng nhận APK cài đúng controller | Capability schema, layout review và lifecycle test plan |
| Radio modules, link endpoints, heartbeat/failover và crypto policy | Chặn kết nối field | Mô hình link/command state và fault replay |
| Video URL/SDP, live codec, decoder/thermal budget | Chặn chọn player production | Stream descriptor, reconnect semantics và probe design |
| RTK route, caster config, GNSS role và age/fix messages | Chặn phép đo RTK tích hợp | Phân tách correction delivery với aircraft fix |
| Controller battery A/B API, hot-swap event, BSP update/recovery | Chặn power/update HIL | Session recovery và power-state contract |

Nguồn công khai không tìm thấy trong phạm vi nghiên cứu không có nghĩa SDK không tồn tại. Không gọi các URL/IP ví dụ của manual để thử thiết bị. Không thay đổi stack production trước khi audit source và adapter; workbench web hiện vẫn là prototype review.

## Độ sạch và kiểm chứng

45 yêu cầu public, 44 raw capture thành công, hai text dẫn xuất; 59 claim thuộc 18 entity và năm origin. Một URL trả 404 được ghi unavailable. Registry có hash/span, ambiguity gate và no-inferred gate; unknowns giữ null, không có coverage denominator. RtR website/GitBook/GitHub chung một origin. Tài liệu nội bộ giữ ở profile riêng, không tự nâng claim công khai thành đo kiểm.

Báo cáo audit cuối và manifest nằm tại `evidence/hera02`; các kiểm máy xác nhận tính toàn vẹn và consistency, không chứng minh semantics, độ trễ hay an toàn bay. Chi tiết nguồn tại `research/herahub-software-20261012`. Công việc kế tiếp đã chuyển thành [integration backlog](</Users/os/Downloads/AI technique/aeris/docs/HERAHUB-INTEGRATION-BACKLOG.md>).
