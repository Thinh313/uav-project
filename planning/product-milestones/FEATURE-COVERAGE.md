# Feature coverage cho milestone sau P1

- P2: Phase One đúng model/lens/gimbal của khách, video source/age, cấu hình tới bốn payload theo capability thực; đổi feed không đổi quyền, pilot/payload emergency policy được chốt với RtR. Không suy tên camera thương mại thành API có sẵn.
- P3: offline map/terrain coverage/version/license; airspace/geofence với nguồn/tuổi/miền hiệu lực rõ, không bịa cơ sở dữ liệu vùng cấm; waypoint/survey datum và altitude mode; đủ lệnh camera QGC vào AP; GSD/overlap/blur/boresight/calibration/RTK-PPK evidence; media thật→địa lý→dataset→receiver. Camera gắn gimbal hay fixed phải đánh theo ổn định/calibration/time-sync, không chốt từ marketing. Không tự nâng mock thành mapping đạt chuẩn.
- P4: manual, assisted và AUTO bằng trạng thái vật lý vòng kín; tải lệch/tải treo/motor fault/obstacle sensing phải có model và giới hạn. Asset3D thật có license/source pins, đồ họa và audio cao cấp không thay gate vật lý. Check touch/joystick mock riêng với hardware.
- P5: các input/MCU/video/radio chưa biết giữ unknown; đo trên cấu hình thật, không hardcode BOM như installed truth. Nhiệt/pin/dung lượng/foreground/recovery và dual-operator dùng cùng target.
- P6: AI hỗ trợ chỉ sinh đề xuất có giải thích/validation/operator consent; chưa có runtimeAI không gọi developmentAI là autonomous flight. Khi triển khai AI, bổ sung baseline trực tiếp LLM và tool-agent, tổng công/cost/quality/privacy đúng standard. Hardware/field/bay tự động chỉ theo quyền và gate thực tế.

## Integration gap exposed during P1 verification

The conservative manager1001 ambiguity fence is generation-wide per component/command. One generation can configure one manager request on component154; a second device cannot be configured again through that ambiguous ACK key. P1 verifies device1 in nominal and device2 in the independent loss generation, per frozen A01/A05/A06; this is not simultaneous independent gimbal authority proof. P2 must define and independently verify a multi-device manager lifecycle using device-specific fresh status and explicit consent, without attributing ACK to an invocation or silently removing the fence.
