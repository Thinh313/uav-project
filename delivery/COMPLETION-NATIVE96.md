# COMPLETION — NATIVE96

18/10/2026 · PASS engineering trong phạm vi TIP · APK development05 · 6/6 REQ, 20/20 kiểm nghiệm thu cuối. Đây không phải tỷ lệ hoàn thiện toàn sản phẩm.

SPEC → BUILD → VERIFY do cùng một agent thực hiện. Parser upstream, compiler đã đóng băng và receiver riêng là công cụ đối chiếu, không phải nhóm QA độc lập.

## Đã đạt

Android trực tiếp điều hành ArduPilot SITL qua TCP, không qua HTTP GCS bridge. Laptop chỉ chạy AP/physics và observer thụ động; mọi lệnh bay qua các nút UI thật trên APK. AP4.7.1 internal quad, Android13 ARM64/WebView101,1280×800; chưa phải Hera đã hiệu chuẩn.

- Nominal cuối APK05 `s096f2c41e36548be9071`: preflight → upload/readback → arm/Home → AUTO → NAV/RTL → ground/disarm → review. Receiver xác nhận 1644 record native, 235 TX_INTENT và TX_WRITTEN ghép đủ,12 item,24 readback item/hai vòng,4 lệnh camera;0 ảnh thực. CRC, toàn bộ compiled plan/model, quyền30s, vị trí cất cánh và tuyến được đối chiếu riêng. Không suy execution từ ACK.
- Mất link trong AUTO `s096d2c41e36548be9071`: native socket đóng, quyền thu hồi, không reconnect/retry/resume. Observer ghi GCS Failsafe sau 4.583s từ thao tác ngắt, RTL khi armed rồi ground/disarm gần Home. Native review vẫn `INTERRUPTED_UNKNOWN_AIRCRAFT_STATE`,accepted=false,groundDisarmed=false vì native không còn quan sát máy bay; observer không viết lại kết luận này.
- Reboot AP trên mặt đất `s096e2c41e36548be9071` sau verified upload/readback: cùng container nhưng PID/startedAt mới, boot clock giảm; native EOF đóng phiên, không arm/AUTO/regrant/reconnect. Observer sau reboot là epoch riêng,0 MAVLink payload TX, không ghép giả liên tục với epoch cũ. Không phải nghiệm thu reboot khi đang bay.
- Android reboot khi SAF picker pending: giữ nguyên 21 file raw/workspace/staged,không thêm generation direct hay khôi phục quyền. FileOps chuyển UNKNOWN; thao tác recovery-copy có chủ ý ghi đúng từng byte ZIP staged trước reboot,provider đọc lại đúng SHA.

## Gói raw và receiver

ZIP STORED giữ nguyên raw gốc,source-meta và review nếu có; SHA-chain/độ dài/extent CLOSED hoặc prefix/torn được ghi rõ. Không trim/repair nguồn,không tự dọn. Bound raw32MiB/ZIP40MiB,stage128MiB,FileOps32 thao tác. Khi đầy thì từ chối; đây không phải cơ chế lưu trữ vô hạn.

Đã thực hiện ACTION_CREATE_DOCUMENT/Downloads provider thật trên emulator:4 gói completed (nominal04 xuất qua05,loss recovery,ground reboot,nominal05);1 gói CANCELLED retained. Xuất khi direct link còn mở bị native từ chối,stage/ops giữ nguyên byte. Chưa kiểm ACTION_OPEN_DOCUMENT đối chiếu gói gốc và các provider đám mây; nhánh explicit recovery-copy đã kiểm thực tế.

Receiver riêng ràng buộc receiver/nonce/package/manifest,kiểm raw SHA-chain,upstream CRC,compiler AUTO63 đã đóng băng và semantic nhiệm vụ. Receipt bền vững giữ qua process restart; thử lại cùng gói,sai receiver/sai nonce bị từ chối,không đổi ledger.10 ca corpus receiver gồm corruption,CRC camera bị sửa nhưng rehash hợp lệ,path traversal,prefix/torn và replay. Gói và receipt là bằng chứng toàn vẹn,không xác thực mật mã máy bay hay ký gói phần mềm. `sourceAuthenticated=false`,authorityRestorable=false,actualImages=0.

## Quota UI và kiểm

62 kiểm mock/replay trong4 suite:15 raw/quota/Unicode,21 controller fault ở upload/readback/Home/AUTO,16 wire/clock/boot/stale/target,10 receiver. Build05 chạy lại169 kiểm file-gate/archive kế thừa cùng các regression workspace/history/bundle/journal. Không cộng các lần lặp suite thành số ca mới.

Chẩn đoán UI dùng UTF-8 byte thật,≤2MiB/generation,≤16 generation/tổng16MiB;không xóa lịch sử. Actual private có 10 generation,tổng8658683 byte,giữ nguyên các generation cũ. Sampling/dedup đã tách timestamp để không ghi lại frame UI không đổi. Receipt stale bị từ chối; UI self-report không phải runtime attestation. Flight raw là journal riêng.

## Sự cố giữ lại

Run a dừng read-only do observer coi startup ASCII là BAD_DATA; sửa parser chỉ chấp nhận prefix ASCII hữu hạn trước MAVLink đầu,CRC sau đó vẫn strict. Run b có lần arm bị gate chặn vì preflight hết hạn trong harness chậm;không có arm command lúc bị chặn. Sau đọc lại/grant rõ ràng,b mới hoàn thành;không dùng làm bằng chứng APK cuối.

APK02 ghi UI quá dày do timestamp tham gia dedup;quota giữ nhưng cache stale bị harness từ chối. APK04 nominal đã đạt;SAF đầu bị guard symlink-ancestor chặn trên alias Android /data/user/0,không ghi provider. APK05 canonicalize riêng framework files base,giữ guard symlink ở store/raw/stage. Các ca lỗi và nominal cuối đều kiểm trên05; raw04 được xuất bởi05 với sourceId tạo raw và sourceId exporter ghi riêng. Lỗi oracle nominal ban đầu đòi AUTO cả trước lệnh AUTO đã được sửa theo pha bay;không sửa raw.

## Bảo toàn và bàn giao

64,691 đường dẫn bảo vệ qua NATIVE95 khớp SHA;307 file private Native90–95 giữ nguyên. Source/candidate/ENDURE không thay đổi;chỉ xác nhận byte hiện tại,không suy đường dẫn đã hiện diện liên tục trong quá khứ. Không ký production hay khởi động ENDURE mới.

Đã dừng runtime/emulator thuộc96,không còn listener,các bản unsigned/host compile/cache do tác vụ tạo đã dọn;giữ5 APK development và mọi evidence. Docker image prune chạy,không prune volume/container. Dung lượng thấp nhất 37.51GiB,trên sàn20GiB.

- [APK development05](../native/native96/dist/aeris-native96-development05.apk) · SHA `e5c14d82c9a55ac4ad51ecd19ee34704496cfcd761fec09fb6e4cfd93d68cd4d`.
- SourceID `b2a0e264befd8339a5161e8873e50a110ba5818bc3cf5a27ce3c794f20751829`;cert development v2/v3 `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`.
- [VERIFY](../evidence/native96/final-verification.json),[receiver cuối](../evidence/native96/receiver-final05.json),[recovery](../evidence/native96/loss05-restart-verification.json),[private](../evidence/native96/final-private-verification.json),[preservation](../evidence/native96/preservation-final.json),[cleanup](../evidence/native96/cleanup96.json),[TIP](TIP-NATIVE96.md),[ADR111](../docs/ADR-111-NATIVE96-FAULT-RAW-SAF.md).

## Chưa kiểm và bước tiếp

HeraHub/radio/HID/video/PhaseOne/gimbal/nhiều payload/dual-operator thật;airborne AP reboot/Android kill/native IO-power loss đầy đủ;DEM/RTK/photogrammetry;Hera physics/pacing1×/thermal/24h/production. Chưa thể kết luận sẵn sàng bay thật từ các kết quả này.

Ưu tiên tiếp: nối contract payload/quyền đã có vào adapter native cô lập,kiểm discovery/target/correlation/thu hồi quyền bằng mock trước rồi SITL. Khi có thiết bị/API mới bench video/input/payload thật. Giữ candidate đóng băng;không dùng receipt toàn vẹn để cấp quyền hay công bố flight PASS.
