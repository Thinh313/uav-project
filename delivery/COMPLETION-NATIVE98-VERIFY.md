# NATIVE98: khép kiểm Android–SITL có giới hạn

19/10/2026 · DONE scoped engineering, còn UI-COPY-01 P2 · Không production/Hera.

Một APK Android đã chạy nhiệm vụ KML đã lưu → biên dịch/đối chiếu model → preflight → quyền SITL → upload/readback → arm và xác nhận Home mới → AUTO đồng thời camera/gimbal tổng hợp → hạ cánh/disarm → review. Một phiên riêng kiểm cắt common link khi có owner và capture chờ; review UNKNOWN không bị observer viết lại thành hoàn tất.

## Kết quả thực

| Ca | Chứng cứ | Kết quả |
|---|---|---|
| Nominal `s098c5c41e36548be9071` | 2696 record, 239 cặp TX,16 item, CRC/sequence/compiled-model/routing đối chiếu upstream | PASS scoped; capture/authority/gimbal trong AUTO, ground/disarm cách Home 0.040 m |
| Link loss `s098d5c41e36548be9071` | Owner còn hiệu lực và capture SENT_UNCONFIRMED trước UI cut; mọi role bị thu hồi, capture UNKNOWN_INJECTED_LINK_LOSS96 | PASS; observer GCS failsafe sau 4.911s, RTL khi armed rồi ground/disarm. Review native vẫn UNKNOWN, accepted=false |
| Restart tiến trình + coldboot Android | 20 file raw/workspace SHA giữ nguyên; không tạo phiên raw hay phục hồi quyền | PASS; cùng AVD không wipe, hai PID emulator/boot receipts riêng |
| Bảo toàn | 420 file private Native90–97,9 raw native đã đóng,67.798 đường dẫn bảo vệ | PASS current SHA; không khẳng định đường dẫn hiện diện liên tục |

## Đã sửa và giới hạn kết luận

- APK03 ghi chính xác RX_DELIVERY lag1959ms/giới hạn1500ms; trước đó lỗi chỉ hiện EXPLICIT_SOCKET_CLOSE.
- APK04 thêm timing và encoder hex đối chiếu byte. Trong block lỗi đã đo, WAL+native xử lý khoảng12ms; phần chờ còn lại nằm sau native encode. Không kết luận encoder là root cause hay công bố p99 cải thiện. Lượt này bay/capture nhưng gimbal pitch40° bị guard từ chối, rồi link stale; review gián đoạn và observer ground được giữ.
- APK05 gom tối đa8 envelope cho một lượt WebView, một batch in-flight, giữ từng block/thứ tự ACK, giới hạn64 event/512KiB, không retry. fsync trước consumer/TX, freshness1500ms và speedup1 giữ nguyên. Host tests và hai run thực đạt trong scope, chưa phải reliability benchmark.
- Một lượt APK05 đầu đóng trước arm vì SERIAL0 SITL xen `Init Gyro`/`*` sau binary. Rig mới dùng SERIAL4 cho native, SERIAL5 observer, SERIAL0 bootstrap chỉ đọc/0 TX. Parser tiếp tục từ chối byte lạ; không lọc bỏ byte trong native. Cấu hình rig khác các run cũ và được pin riêng.
- Harness nhập pitch−30° hợp lệ. Có một lỗi số đối số trong harness trước bước payload; đã sửa đúng vùng và tiếp tục phiên hợp lệ, không lặp lệnh đã gửi.

## Kiểm kỹ thuật

27 transport mock/fault,93 core/regression,108 encoder reference/roundtrip,15 batching/scheduler fault. Build05 chạy169 file-gate/archive regression cùng workspace/history/journal checks. Không cộng những lần lặp suite thành ca mới. Sáu requirement NATIVE98 đạt trong phạm vi engineering này. Kiểm bằng một agent; parser upstream/compiler cũ là công cụ đối chiếu, không phải hội đồng QA độc lập.

## Deferred và phần chưa chứng minh

**UI-COPY-01 P2:** sau restart, dòng trạng thái panel payload dùng nhãn disarmed từ giá trị mặc định khi chưa có AP fresh. Header vẫn UNKNOWN và quyền bị khóa. Cần đổi nhãn thành chưa biết trừ khi link mở/AP fresh trước operational bench; chưa sửa/ký lách nghiệm thu trong APK05.

0 ảnh thực, không chứng minh cơ cấu gimbal/camera thật, chưa Phase One/HeraHub/HID/video thật, hai role trong cùng APK không phải hai operator được xác thực qua mạng. Chưa repeated/continuous controls: fence ACK-key vẫn giới hạn một endpoint+command/generation và shared-manager device2 bị chặn. Chưa đánh giá SIM32 pacing hay so sánh DJI/Ragas; không chứng nhận khả năng thương mại hoặc AI tự bay.

## Bàn giao

- APK development05: `native/native98verify/dist/aeris-native98-development05.apk`
- SHA256: `ad97af079cbb37bc9e9df635e0cba9d9a7fed75e0d2ee3c2fa64b19a8b14f8b8`
- Source ID: `e276fb4ce316d379945a7bcc746611fbc457739059a1753480bc309b13a8ddfb`
- Evidence: `evidence/native98verify/final-verification.json`, hai `runs/*/independent-replay98.json`, process/coldboot/private/preservation/cleanup receipts.
- Các lượt03/04/05 thất bại và báo cáo cũ giữ nguyên. Source/candidate/ENDURE/canonical SOT không đổi.
- Đã dừng emulator/SITL/peers; xóa3 APK unsigned do tác vụ tạo, không có scratch ngoài repo. Docker image prune thu0B, không prune volume/container. Dung lượng tối thiểu các run 30.23GiB, cuối 30.38GiB.

## Bước tiếp theo

Sửa nhãn UNKNOWN và tách trường zoom/pitch; sau đó triển khai điều khiển camera/gimbal lặp/liên tục với correlation không mơ hồ, kiểm hai phiên operator độc lập và corpus polygon/corridor chưa dùng. Đây là gap sản phẩm lớn hơn việc mở thêm trang demo. Bench HeraHub/Phase One cần model/firmware/API/thiết bị thật.
