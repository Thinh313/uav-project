# BIG-01: code và APK development, chưa nghiệm thu Operator Alpha

Ngày 21/10/2026. **Trạng thái sản phẩm: NOT READY.** Đã hoàn thiện phần triển khai độc lập, kiểm host/mock, sửa các lỗi được QA phát hiện và tạo APK development PHONE06. Chưa đóng milestone BIG-01 vì chưa có Xiaomi kết nối, chưa thực hiện hành trình Android–SITL hiện hành, qualification manual chưa có bằng chứng thực và kiểm toàn vẹn lịch sử đang có đường dẫn thiếu.

## Đầu ra cụ thể

- [APK development01](</Users/os/Downloads/AI technique/aeris/native/phone06/dist/aeris-phone06-development01.apk>): 3.799.006 byte, package `vn.rtr.aeris.phone06`. SHA256: `0a1423e38f29565b4b22c9c14b1ae1beaffce6dcb46618ee583bd7b2871a9c2b`.
- [Hướng dẫn vận hành BIG-01](</Users/os/Downloads/AI technique/aeris/planning/phone06/RUNBOOK-BIG01.md>): build, USB, launch bằng đúng Intent, admission, operator B, observer, SAF/receiver và đóng phiên. Không tự connect, grant, arm, reconnect hoặc retry mutation chưa rõ kết quả.
- [Entrypoint](</Users/os/Downloads/AI technique/aeris/planning/phone06/entrypoint.py>), [template admission](</Users/os/Downloads/AI technique/aeris/planning/phone06/phase-template.json>) và [receiver độc lập](</Users/os/Downloads/AI technique/aeris/planning/phone06/receiver06.py>). Template không phải giấy phép chạy; các gate thực vẫn bắt buộc.
- [Biên bản APK độc lập](</Users/os/Downloads/AI technique/aeris/evidence/phone06-qa/apk-gate-final01.json>), [QA source07](</Users/os/Downloads/AI technique/aeris/evidence/phone06-qa/verification-source07.json>) và [bàn giao Builder](</Users/os/Downloads/AI technique/aeris/evidence/phone06/builder/BUILDER-HANDOFF07.md>).

APK dùng chứng chỉ development đã có, không tạo khóa ký phần mềm mới. Chỉ có quyền INTERNET; minSdk26/target33, debug=false, backup=false, sensorLandscape. Đây là khai báo và kết quả kiểm package, chưa phải xác nhận ART, Android/HyperOS hoặc phần cứng Xiaomi tương thích. Không ký production, đổi candidate hoặc phát hành ra ngoài.

## Phần đã triển khai và sửa

PHONE06 là một package cô lập, tái sử dụng các dependency đã pin của INTEGRATION03/CREW02. Cockpit, model nhiệm vụ, transport và writer dùng chung được đưa qua overlay có kiểm ngữ cảnh; không sửa các bản nguồn đóng băng để thêm tính năng.

- Input: tách NEUTRAL READY không gửi lệnh khỏi input ACTIVE; kiểm số trước ép kiểu, pointer/sequence/generation/owner/mode, TTL250 ms và tối đa20 Hz. Kiểm lại sau WAL/fsync; lỗi, hủy hoặc neutral không rõ kết quả phải thu hồi quyền/đóng transport đúng nguyên nhân. Không có socket điều khiển bên cạnh writer.
- Admission: vô hiệu binding cũ ngay khi xác thực lại; phản hồi đến muộn không được khôi phục phiên đã hủy; hạn dùng dựa clock cục bộ và RTT, kiểm hết hạn ở cả trạng thái idle. Xác thực mạng không giữ khóa writer.
- Android/public SAF: xuất danh tính công khai và nhập trust có kiểm SPKI/context, giới hạn byte, callback đúng action, commit bền vững; nhập lại cùng policy phải xác nhận lại độ bền, policy xung đột bị từ chối. Không xuất private key hay dùng root điện thoại.
- USB/launch: chọn đúng physical USB, kiểm devpath, không nhận serial mạng/emulator; mapping có receipt sở hữu và kiểm xung đột. Cleanup không bị khóa bởi admission hết hạn và không xóa mapping đã bị thay thế. Launcher dùng đúng `source87=direct`/`owned95`, quote JSON cho remote shell, không tự dừng app đang chạy hoặc tự kết nối.
- Observer: thêm feed localhost chỉ đọc phần WAL đã fsync, token đọc không nằm trong snapshot/log/URL, offset/context bị giới hạn và lifecycle cắt kết nối. Mirror không dùng proxy hoặc theo redirect. Chỉ là prefix; chưa nhận CLOSED không được coi đã xuất đủ raw. Viewer tái sử dụng38 asset/decoder được pin, âm thanh tổng hợp opt-in.
- Receiver: kiểm ZIP, SHA/chuỗi raw, ngữ nghĩa META thực và context bên nhận khai báo độc lập trước khi nhận. Gói nguyên vẹn không tự chứng minh nguồn được xác thực, ảnh thật, quyền điều khiển hoặc nhiệm vụ thành công.

Manual thực vẫn bị khóa với `manualActualQualified=false`. Issuer qualification còn **UNSUPPORTED_PENDING_ACTUAL_PROOF**; không có cờ CLI/config biến tham số đúng thành bằng chứng fallback/LOITER/failsafe. Phần này cần một bước qualification thực có kiểm raw, không chỉ cắm điện thoại là đã hoàn tất.

## Kiểm chứng đã thực hiện

Builder có35 input offline trong phạm vi đã ghi. QA độc lập có23 input:21 PASS scoped và2 PARTIAL, liên quan bằng chứng review/restart thực và Android KeyStore/certificate thực. Không cộng các số này thành tỷ lệ hoàn thiện sản phẩm. Kiểm dùng các lớp native thực với clock/socket/IO fixture được khai báo, không phải chuyến bay hoặc bằng chứng thời gian thực.

QA xác nhận các ca post-WAL mất owner/generation không gửi byte; encoder MANUAL_CONTROL được đối chiếu CRC/trường bằng parser upstream độc lập. Raw receiver đã kiểm bằng ZIP do chính producer native tạo: lỗi source04 được tái hiện, source05 nhận đúng gói dương tính và từ chối sai receiver đúng nguyên nhân. Các lỗi và kết quả trước sửa được giữ nguyên.

Build01 thành công bằng toolchain cache. QA độc lập đối chiếu248 pin closure,182 pin build,115 asset khớp byte và121 ZIP entry, không trùng hoặc thêm asset ngoài dự kiến; chữ ký V2/V3 đúng một signer. DEX có đúng build ID, chưa được QA biên dịch lại độc lập.

- Build source ID: `46f38b12a9e2eec5f461322b6269b781b7142d6f09d0b5951eee3f7e71472cf1`.
- Closure source07: `dad78bd5b0d77605acc73f86aa25c71d011e1a910c82f0fad5992a15ee5af7bd`.

Hai ID mô tả hai tập file khác nhau:182 file cho build APK và248 pin gồm cả host/observer/hướng dẫn. Không thay thế lẫn nhau.

Kiểm browser chỉ xác nhận bố cục và rehearsal offline ở1280×720. Đã sửa overlap2 px giữa cần và rail, đo lại được khoảng hở12 px hai bên, console không có lỗi trong checkpoint cuối. Preview không cung cấp mission, persistence, telemetry hay API Android giả. Không chuyển kết quả này thành nghiệm thu UI Xiaomi, đa điểm chạm hoặc hành trình bốn màn native.

![Preview offline nguồn07, không phải kết quả bay hoặc Android](</Users/os/Downloads/AI technique/aeris/evidence/big01/preview-touch-after07.png>)

## Các gate BIG-01 chưa đóng

| Gate | Hiện trạng |
|---|---|
| P01 bảo toàn nguồn/bằng chứng |160 dependency và248 pin closure hiện hành đạt; lịch sử rộng hơn FAIL do597 đường dẫn thiếu. |
| P02 package development |PASS scoped: build, chữ ký và payload. Chưa cài/ART. |
| P03 USB/admission |Code và ca parser/negative đã kiểm host; USB Xiaomi thực NOT_CHECKED. |
| P04 input native |Policy/writer/touch projection đạt scoped; độ trễ và thao tác cảm ứng thực NOT_CHECKED. |
| P05 UI điện thoại |Chưa kiểm Xiaomi, safe area, popup, gesture hoặc hiệu năng trên thiết bị. |
| P06 KML → preflight → readback → AUTO → review |Code tích hợp và entrypoint đã chuẩn bị; chưa có run hiện hành trên Android–SITL. |
| P07 assisted manual |Issuer qualification chưa hỗ trợ; cần kiểm neutral/RC expiry/LOITER/pose/failsafe thực. |
| P08 hai operator/nhiều payload |Adapter/companion và public trust đã chuẩn bị; chưa kiểm hai phiên, consent, routing và partition trên cấu hình hiện hành. |
| P09 observer/3D/audio |Feed/mock và pin asset đạt scoped; chưa có30 giây airborne cùng UI/SITL, clock/performance/audio thực. |
| P10 sự cố |Chưa kiểm rút USB, app nền, stale, AP reboot và failsafe thực trong run hiện hành. |
| P11 SAF/persistence/restart |Receiver fixture đạt; provider readback, xuất đúng selected run, process restart và reboot Xiaomi chưa kiểm. |
| P12 vận hành/nghiệm thu |Runbook cụ thể đã có; chưa diễn tập và nghiệm thu trọn vẹn với người vận hành. |

## Bảo toàn, dung lượng và giới hạn

Đã khôi phục riêng dependency MAVLink thiếu bằng đúng SHA gốc, có [receipt phục hồi](</Users/os/Downloads/AI technique/aeris/evidence/big01/dependency-recovery-after.json>). Không viết lại lịch sử, canonical SOT, candidate/trust hoặc ENDURE, không chạy soak mới.

Kiểm đầu lượt đọc68.915 đường dẫn bảo vệ phát hiện597 đường dẫn thiếu, không thấy SHA lệch ở các file đọc được. Đây không phải checkpoint đầy đủ71.158 đường dẫn trước đây. Cả597 đường dẫn đó vẫn thiếu khi kiểm lại tập lỗi cuối; nguyên nhân UNKNOWN. Tìm được95 bản chính xác trong Git HEAD nhưng chưa phục hồi chúng trong lượt này. Không tuyên bố bảo toàn toàn bộ lịch sử đạt hoặc đường dẫn hiện diện liên tục. [Receipt kiểm đầu lượt](</Users/os/Downloads/AI technique/aeris/evidence/big01/preservation-before01.json>) và [checkpoint cuối](</Users/os/Downloads/AI technique/aeris/evidence/big01/root-current-checkpoint01.json>) giữ chi tiết phạm vi.

Build có31 mẫu resource admission, thấp nhất26,51 GiB trống, trên sàn20 GiB tại các gate đã kiểm. Đã dọn `.build`, `.mock`, staging preview và staging QA do task tạo; giữ APK ký và toàn bộ bằng chứng. Không cài dependency/image, không dùng emulator, không chạy cửa sổ AP, không tạo mapping USB, không cài điện thoại. ADB cuối lượt vẫn không có thiết bị.

Có một lỗi kế toán ngân sách test: sáu input feed từng bị ghi thành ba nhóm, vượt phân bổ54 input ban đầu thêm ba. Giữ receipt gốc/correction; không gọi đây là tuân thủ hồi tố. Reassessment sau đó chốt58 input (Builder35/QA23), gồm ca receiver dương tính bắt buộc. Các sửa fixture và allowlist verifier cũng được giữ như lỗi bộ kiểm, không gán thành lỗi sản phẩm.

## Bước tiếp theo trong cùng BIG-01

1. Xử lý incident đường dẫn lịch sử bằng bản sao đúng SHA có truy nguồn; không sửa baseline để lấy PASS.
2. Kết nối Xiaomi, ghi model/Android/HyperOS/WebView và kiểm cài/khởi động riêng package development. Kiểm UI, public identity/trust và USB chỉ đọc trước mọi mutation.
3. Khi gate nguồn/tài nguyên/thiết bị đạt, thực hiện run SITL hoàn toàn mới theo runbook: nhiệm vụ, B/payload, observer, fault, SAF/receiver và restart. Không dùng lại acceptance của APK lịch sử.
4. Xác định và kiểm qualification manual dựa trên raw thực rồi mới hoàn thiện issuer hẹp. Không mở khóa bằng metadata hoặc config.

Chỉ đóng BIG-01 khi các gate bắt buộc đạt trên một cấu hình hiện hành. BIG-02 media/geotag, BIG-03 Hera/Phase One/field/production và BIG-04 fidelity huấn luyện vẫn là milestone riêng. Chưa có bằng chứng để nâng chỉ số trưởng thành bằng một tỷ lệ mới hoặc tuyên bố ngang/vượt DJI.

USER OUTCOME: có APK development và bộ code/kiểm/vận hành cụ thể để chuẩn bị Xiaomi–SITL. REQUIREMENT COVERAGE: package và các component đã kiểm scoped; các gate thực ở bảng còn mở. TECHNICAL HEALTH: compile/signature/assets/source và các ca host nêu trên đạt trong phạm vi. VALUE EVIDENCE: partial, chưa đo thời gian/công thao tác hoặc độ tin cậy người vận hành trên điện thoại; không có baseline LLM phù hợp cho deterministic transport. OVERALL STATUS: **NOT READY, chưa DONE BIG-01**.
