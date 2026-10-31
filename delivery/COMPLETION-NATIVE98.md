# COMPLETION — NATIVE98 · PARTIAL

18/10/2026. Đã triển khai transport native hợp nhất flight + payload trong package cô lập `vn.rtr.aeris.native98`. Build và mock đạt. **Chưa nghiệm thu nhiệm vụ Android–SITL đồng thời camera/gimbal hoặc thu hồi quyền payload đang sở hữu khi mất link trong bay. Không báo PASS cho các mục này.**

SPEC → BUILD → VERIFY do một agent thực hiện. Parser upstream và compiler cũ là công cụ đối chiếu riêng, không phải nhóm QA độc lập. Báo cáo theo TIP-NATIVE98, không phải tỷ lệ hoàn thiện toàn AERIS.

## Phần đã làm

DirectTransport95 là nơi duy nhất giữ socket, reader, writer, generation và raw journal. Payload không còn socket/heartbeat/journal riêng. Một RX được lưu và fsync trước khi cấp cho cả hai consumer và UI. Mọi TX dùng chung sequencer255/190, kiểm CRC gốc rồi gán sequence/CRC wire; raw ràng buộc byte ý định với byte thực gửi.

WireGate flight vẫn kiểm KML đã commit, kiểu tham số, preflight, quyền tạm thời, upload/readback và xác nhận Home sau arm. Payload giữ hai vai trò local, bundle camera/gimbal, lease/consent/revision/sequence riêng. Payload không cấp quyền bay; raw flight không được gửi lệnh camera/gimbal trực tiếp. Payload chỉ chấp nhận trạng thái armed sau một ARM transmit đã qua gate native trong đúng phiên mô phỏng. Đây không phải xác thực máy bay hoặc hai tay cầm thật.

Cả hai loại gửi dùng chung primitive: fsync TX_INTENT → kiểm foreground/quyền hiện hành → một lần socket write → TX_WRITTEN. Lỗi link/clock/stale/CRC/storage/background đóng cả hai gate, thu hồi role/quyền và giữ kết quả pending UNKNOWN; không tự reconnect/retry/regrant/restore. Đóng riêng payload không kết luận máy bay an toàn.

APK02 bỏ ghi trùng semantic `FOREIGN_IGNORED` ở JS vì mọi byte RX đã nằm trong WAL native. Không bỏ frame raw, không giảm fsync trước apply/gửi. Java gate không đổi so với APK01. Chưa đo được mức cải thiện hiệu suất của thay đổi này.

## Bằng chứng đã đạt

- **93 ca mock có mục tiêu:**38 shared session/send boundary,41 arbiter/protocol,14 biên gửi/lifecycle. Có fsync lỗi trước/sau write, thu hồi trong approval, partial write không retry, sequence/revision/session/clock, CRC, stale, unexpected armed và payload không được ARM. Một ca sequence wrap dùng260 mẫu được parser upstream kiểm CRC riêng; không tính260 mẫu thành260 scenario.
- Replay capture nhiệm vụ NATIVE96 qua core mới:1.159 RX,235 TX, grant/readback/Home/AUTO và kết quả hoàn tất vẫn đạt. Đây là replay capture cũ, **không phải lượt SITL mới**.
- Build02 chạy lại169 ca file-gate/archive kế thừa, cùng regression workspace/history/bundle/journal. APK development v2/v3 hợp lệ; không ký production.
- APK01 thực trên Android13 ARM64/WebView101 và AP4.7.1:3 phiên chỉ đọc,5.409 record native; CRC/SHA-chain/TX pairs/shared sequence và8 discovery camera100/102/101/manager154 đi đúng hai bus được đối chiếu riêng. Mỗi phiên một socket/generation; các role không còn alive sau đóng. Không có grant/ARM/AUTO, không có ảnh thực.

## Vì sao chưa nghiệm thu SITL bay

A: observer ban đầu chiếm SERIAL3, trùng GPS mặc định SITL. Preflight chặn fix0/Home thiếu; không ARM. Đã giữ nguyên raw và chuyển observer sang SERIAL4; các ca sau có GPS/Home.

B: GNSS/Home có trước EKF/prearm khỏe, cohort preflight bị chặn đúng. Sau đó native heartbeat guard đóng phiên khi còn disarmed. Observer có khoảng heartbeat gap tới27,07s. Không tự nối lại.

C: frontend đóng socket trong pha chỉ đọc; raw có42 semantic FOREIGN_IGNORED trên83 record, cho thấy ghi trùng đáng loại bỏ. Không đủ bằng chứng quy toàn bộ khoảng gián đoạn cho log này. Harness cũng từng đọc diagnostic trước khi UI sẵn sàng/chạm vùng bản đồ không phát capture; đã chuyển sang chạm header an toàn và yêu cầu receipt mới sau chạm, tuổi vẫn<2s. Các lượt lỗi được giữ nguyên, không dùng hitbox stale.

D: cài APK02 dừng ở force-stop timeout30s, trước lệnh install. Shell khởi động AP sau lỗi vì thiếu fail-fast; harness phụ thuộc dừng vì launch metadata chưa có. Đã xác minh ca D không có native connection/flight command và dừng đúng controller sở hữu. Các chuỗi tiếp theo dùng fail-fast. Không tính D là đã kiểm APK02.

Khởi động lại emulator sạch, không wipe dữ liệu, vẫn không đạt hạn boot90s. Snapshot host ghi load average85,57/87,21/70,89 và swap dùng5.553MiB trên máy32GiB RAM. Đây là bằng chứng host/runtime không đạt admission, không chứng minh chính xác nguyên nhân từng gap. Không đổi timeout/freshness hay bỏ kiểm để lấy PASS. Mọi runtime sở hữu đã dừng.

## Ma trận nghiệm thu

| REQ | Kết quả | Giới hạn |
|---|---|---|
| R98-1 cô lập/bảo toàn/dung lượng | PASS khi final-verification xác nhận | Kiểm byte hiện tại, không khẳng định đường dẫn hiện diện liên tục |
| R98-2 shared transport/sequence/raw | PASS phạm vi source/mock và APK01 chỉ đọc | APK02 runtime NOT_CHECKED |
| R98-3 hai domain quyền/preflight | PASS mock/replay/source | Chưa có nhiệm vụ bay mới |
| R98-4 durability/thu hồi/no restore | PASS mock và đóng role pha chỉ đọc | Thu hồi owner đang bay NOT_CHECKED |
| R98-5 nhiệm vụ SITL đồng thời payload/loss | PARTIAL | Discovery đạt; các ca airborne bắt buộc NOT_CHECKED |
| R98-6 persistence/bàn giao | PARTIAL | Artifact/cleanup có; kiểm SHA private sau restart NOT_CHECKED vì boot/ADB không sẵn sàng |

4/6 REQ được kiểm đầy đủ trong phạm vi nêu trên;2/6 còn bắt buộc hoàn tất. **Overall NOT READY cho nghiệm thu nhiệm vụ Android–SITL của NATIVE98.** Không dùng tỷ lệ này để quảng bá mức trưởng thành toàn sản phẩm.

## Bàn giao và bảo toàn

Bản mới nhất: [APK development02](../native/native98/dist/aeris-native98-development02.apk), SHA `d6d77f559df570497685b7f65f5602572a9a586d7ac5fda4e46b3a2369b667d9`. Build đạt; chưa xác nhận cài/chạy bản này trên emulator. APK01 và toàn bộ ca lỗi vẫn được giữ.

[VERIFY](../evidence/native98/final-verification.json), [mock shared](../evidence/native98/unified-mock02.json), [read-only replay](../evidence/native98/readonly-independent98.json), [preservation cuối](../evidence/native98/preservation-final.json), [resource observation](../evidence/native98/host-resource-observation.json), [TIP](TIP-NATIVE98.md), [ADR113](../docs/ADR-113-NATIVE98-UNIFIED-TRANSPORT.md).

Final verification đối chiếu67.149 đường dẫn bảo vệ qua NATIVE97, gồm source/candidate/ENDURE. Không sửa canonical SOT, lịch sử ENDURE, selected candidate hay khởi động soak. Snapshot private trước task có420 file của Native90–97; kiểm SHA sau restart chưa chạy được, nên không khẳng định đã đối chiếu lại phần private này.

Đã dọn hai APK unsigned, `.host98`, `native98/__pycache__`; giữ hai APK development, AVD/private data và mọi evidence. Không tạo bản sao toàn dự án trong tmp, không tải SDK/dependency. Docker image prune thu hồi0B, không prune volume/container. Dung lượng runtime thấp nhất được ghi trong VERIFY và cao hơn sàn20GiB.

## Bước tiếp theo đúng gate

Giảm tải host hoặc dùng host kiểm riêng, kiểm boot/độ đáp ứng trước, rồi cài APK02 và xác nhận đúng SHA. Chạy phiên mới từ chỉ đọc với GPS/Home/EKF/prearm đầy đủ; sau đó nominal AUTO có capture/gimbal khi đang bay và review ground/disarm. Một phiên riêng kiểm owner payload còn hiệu lực và pending command lúc cắt socket, observer theo dõi GCS failsafe/RTL; native review phải giữ UNKNOWN sau mất link. Sau cùng kiểm persistence/private SHA và regression; không ký production.

Hai operator vẫn local trong một Activity; chưa có remote enrollment/radio. PhaseOne model/API/lens/calibration, HeraHub/HID/video/SDK, gimbal vật lý/ảnh thực, Hera physics/pacing1×/24h và HIL/bay thật vẫn chưa được nghiệm thu. ACK/phản hồi khớp không chứng minh thực thi payload.
