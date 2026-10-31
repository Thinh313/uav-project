# AERIS SIM-STABILITY03

**NOT READY cho toàn milestone. Lát cắt manual Android–SITL đã kiểm đạt.**

Đã có một chuyến điều khiển bằng giao diện APK thật trên emulator: preflight/Home → cất cánh GUIDED → cấp quyền trung tính → pitch/yaw bằng cần cảm ứng → nhả cần trở về GUIDED → LAND/ground/disarm → đóng review → xuất và nhập SAF. Đây là quad tham chiếu, chưa hiệu chuẩn Hera. Không phải nghiệm thu Xiaomi, HeraHub, chuyến bay thật hoặc bản production.

## Kết quả đã chứng minh

| Hạng mục | Kết quả |
|---|---|
| Chuyến manual được chọn | `rc8f9c0bfcc3a4563b492` (AP04), COMPLETED_OBSERVED |
| Model / thời gian host nhận | 97,3458 s / 97,2773 s |
| Pacing | **1,000696×**, một lượt; chưa suy ra vận hành dài hạn |
| WAL / AP | 116.815 frame liên tục; CRC/chuỗi SHA hợp lệ; không thiếu hoặc trùng stage AP bắt buộc của các frame đã nhận |
| Jitter khoảng nhận frame | p95 5,947 ms; p99 6,864 ms; lớn nhất 78,008 ms |
| Fsync INTENT | p99 0,104 ms; lớn nhất 77,277 ms; fsync trước sensor giữ nguyên |
| Heartbeat | p99 110,552 ms; lớn nhất 205,709 ms; guard 1.500 ms giữ nguyên |
| Đối chứng vật lý | Replay 116.815 PWM qua model Python gốc: **0 khác biệt byte** sensor UTF8 và modelAux |
| Giao quyền manual | Hai lần neutral claim/LOITER; pitch/yaw có RC đúng mục tiêu 42/1; nhả về GUIDED; LAND/ground/disarm quan sát thật |
| Lưu/khôi phục | Review fsync + receipt SHA; cold host restart chỉ đọc lại lịch sử, không phục hồi session/boot/lease |
| SAF | Xuất/nhập qua Android thật; receiver độc lập kiểm hash và từ chối gói sửa byte. Raw lớn chỉ được tham chiếu SHA trên host |

Nguồn chính: [raw audit](../evidence/simstability03/manual-flight-raw-audit01.json), [đối chứng model](../evidence/simstability03/original-model-replay01.json), [ACK/Home/tham số](../evidence/simstability03/manual-flight-evidence-supplement01.json), [receiver SAF](../evidence/simstability03/receiver-saf04.json).

## Nghiệm thu theo yêu cầu

11 tiêu chí: 8 đạt trong phạm vi ghi rõ, 1 lỗi, 1 một phần, 1 chưa kiểm. Không quy đổi thành phần trăm trưởng thành sản phẩm. Ca background AP03 chỉ chứng minh quan sát thu hồi quyền; kết thúc AP03 vẫn FAILED.

| ID | Yêu cầu | Trạng thái | Căn cứ/phạm vi |
|---|---|---|---|
| AC01 | failed lifecycle cleanup and explicit restart | PASS_SCOPED | gateway-fault-tests05.json; actual AP01/AP03/AP05 failed closures; allOwnedClosed; no successful-flight inference |
| AC02 | native preflight/Home/takeoff/manual pitch+yaw/LAND/disarm/review | PASS_SCOPED | AP04 actual ADB touch actions and independently checked raw ACK/HB/RC/WAL |
| AC03 | neutral claim/release/session and boot fences | PASS_SCOPED | AP04 observed two neutral/manual handoffs and GUIDED releases; independent-handoff03.json; fixed TTL200ms/HB1500ms |
| AC04 | background revokes input without restoring authority | PASS_OBSERVATION_ONLY | AP03 background03-revoked.json; held GUIDED reference altitude. AP03 final run failed and is not promoted |
| AC05 | cold host history/restart never restores lease | PASS_SCOPED | cold-host04-before-start.json has null run/session/boot, no input; prior failed history retained |
| AC06 | durable review plus native SAF export/import and receiver | PASS_SCOPED | SAF-manual04 exact SHA; actual Android import; receiver-saf04 tamper rejection; external raw not embedded |
| AC07 | pacing >=1x with complete captured frame/WAL/AP correlation | PASS_ONE_RUN | AP04 RTF1.000696;116815 admitted contiguous frames; no AP required-stage gaps; fsync-before-sensor retained |
| AC08 | optimized sensor/model output matches immutable original | PASS_EXACT_OFFLINE | Original pure-Python replay116815 frames;0 sensor UTF8 or modelAux byte mismatches; not Hera calibration |
| AC09 | consistent bounded300s lifecycle and capture duration | FAIL | AP recorder exhausted on AP03/AP05 before full300s; life() activeAPSeconds keeps advancing after closed. Manual04 remained within short verified capture |
| AC10 | 3D/audio/stale freeze and visual performance | PARTIAL | Actual PBR view and audio gesture observed; no PCM/FPS/photon measurement; reverse removal did not interrupt established socket |
| AC11 | explicit AP reboot fault and recovery in final native build | NOT_CHECKED | Host restart and background tested; AP reboot is not equivalent and was not exercised in final runtime |

## Lỗi chặn và phần còn thiếu

- NOT READY overall. Immutable AP recorder capacity did not support full300s captures in AP03/AP05; a separate bounded capture-capacity solution and actual recheck are required without dropping frames or changing firmware silently.
- Closed-session activeAPSeconds still advances in public state; freeze elapsed time at exact closure and regression-check late callbacks in a new isolated revision.
- Native UI harness must select the actual current page before review navigation; AP05 LAND succeeded, next template mismatch halted driver, then the unclosed session exhausted trace capacity.
- Actual scene-loss/audio mute/freeze, final AP reboot and measured visual FPS/photon latency remain unverified. Removing ADB reverse did not prove an established socket outage. Active AudioFlinger track is not measured audible or calibrated Hera sound.
- Physical Xiaomi/Hera/HeraHub, real gimbal/camera/payload, projector display, Hera mass/aerodynamics/acoustics/environment calibration, AUTO, SDK and production release are outside this slice or NOT_CHECKED.
- Client HTTP input sequence/clock/axes are validated by code/mocks but not directly embedded in raw; wire sequence is a different evidence layer. Generic DJI superiority or training certification is not claimed.

**Phép mất link 3D chưa hợp lệ:** xóa ADB reverse không chứng minh socket đã mở bị ngắt. Ảnh vẫn hiển thị Physics đang cập nhật và ROI thay đổi. Không kết luận stale/freeze/mute PASS hoặc FAIL từ phép tiêm này. Một track AudioFlinger hoạt động sau thao tác bật âm thanh không chứng minh người nghe đã nghe đúng âm hoặc track đã im khi stale.

## Các lượt được giữ nguyên

| Lượt | Revision | Kết quả |
|---|---|---|
| AP01 | receiver01 | Timeout, không ARM; RTF 0,6166; heartbeat mặc định thường vượt guard. FAILED, không gộp thời gian |
| AP02 | receiver02 | Takeoff quan sát được; LOITER chuyển sớm gây hạ trước claim. Phiên đóng được nhưng không đạt manual |
| AP03 | receiver03 | Pitch/yaw, nhả cần và background revoke quan sát đạt; operator quá thời gian recorder, FAILED_INTERRUPTED |
| AP04 | receiver03 | Trọn chuỗi manual → LAND/disarm → review/SAF đạt; raw và model replay kiểm độc lập |
| AP05 | receiver03 | PBR render và thao tác audio quan sát được; mất link chưa được tạo đúng. LAND/disarm đạt; selector review không khớp nên driver dừng, rồi recorder tràn. FAILED_INTERRUPTED |

Đây là các lần thử có sửa source/harness và điều kiện host khác nhau, không phải benchmark đối chứng được kiểm soát. Kết quả mock, quan sát Android thật, raw protocol và replay model được ghi tách biệt. Client HTTP seq/clock/axes chưa được nhúng trực tiếp trong raw; MAVLink wire sequence là lớp khác.

## Gói kỹ thuật và bảo toàn

- Archive: [AERIS-SIM-STABILITY03-NOT-READY.tar.gz](sim-stability03/AERIS-SIM-STABILITY03-NOT-READY.tar.gz), 25,689,903 byte. Gói chẩn đoán **NOT READY**, không phát hành production.
- SHA256 archive: `0b56c97e067e41cb4b633429028f1defa7d4708e4b8606195ba00b404a64d022`.
- Manifest mới: `5f2f33295602c2b535a93feae27f48dbc1d2e73edcc22483b664ddc81257c76a`; parent source03: `df3eb4ec961e2fc83116440ec017796593b36847f2e1a601e7dd0a8b11ec5c8f`.
- Kiểm tất cả 116 member, hash/mode/type/path, BSD tar và parser Python/Node thực trong gói. Không giải nén ra bản project khác.
- APK engineering giữ đúng byte; không build, ký lại hoặc kèm private signing key. Có thể cài APK bằng serial Android xác định theo README; thiết bị Xiaomi/Hera vẫn cần nghiệm thu riêng.
- Host companion chỉ được chứng minh trên macOS ARM và cache Python 3.14/Node/Docker đã khai báo. Không hàm ý Windows/Linux đã chạy được.
- So 17,117 định danh bảo vệ và 650 mục của SIM-VERIFY02: không drift. 165 đường dẫn thiếu từ trước vẫn được ghi nhận; không khôi phục hoặc viết lại lịch sử ENDURE.
- Các tiến trình của tác vụ đã đóng; emulator exit0, host04 exit0, không còn container AP đang chạy. Dữ liệu runtime giữ lại 2.7153 GiB trong ngân sách nội bộ 3 GiB. Gate 20/10 GiB, dự phòng 256 MiB và forecast15s giữ nguyên.
- Docker image prune hoàn tất, thu hồi 0B; không xóa container/volume, evidence hoặc dữ liệu của người dùng. Không tạo bản project trong /tmp.

## Bước sửa tiếp theo

1. Chốt giới hạn recorder theo số frame thật; thiết kế capture theo khối có chain/commit và kiểm đủ frame, hoặc cơ chế dừng có lý do rõ trước khi hết dung lượng recorder. Không âm thầm đổi binary đã pin, bỏ frame hay gán một prefix là chuyến hoàn chỉnh.
2. Đóng băng activeAPSeconds tại thời điểm closure và sửa harness đi theo trang đang hiển thị. Kiểm race/late callback bằng mock trước khi tạo revision cô lập kế tiếp.
3. Dùng fault transport thực sự đóng đúng socket simulator; kiểm stale/audio mute/lease revoke, AP reboot và restart. Chạy lại ngắn trước, rồi mới đo FPS/latency và acoustic output.

Không mở thêm lượt bay trong task này: đã tới giới hạn 4 lần host start và giữ lại cả ca thất bại. Gói bàn giao không tuyên bố hoàn thành toàn milestone.

[Qualification đầy đủ](../evidence/simstability03/qualification-final01.json) · [kiểm bảo toàn](../evidence/simstability03/preservation-final01.json) · [đóng runtime](../evidence/simstability03/runtime-final01.json) · [kiểm đóng gói](sim-stability03/PACKAGING-VERIFICATION.json)
