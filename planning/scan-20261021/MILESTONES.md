# Các task lớn đề xuất sau scan AERIS ngày 21/10/2026

Mục tiêu là thu hẹp khoảng cách từ các thành phần engineering sang một sản phẩm sử dụng được. Đây là đề xuất giao việc theo Vibecode Kit 6.3, chưa phải kết quả triển khai. Giữ nguyên nguồn đóng băng, candidate, canonical SOT, ENDURE và mọi bằng chứng cũ. Các task dưới đây gom việc của PHONE06, INTEGRATION03 và kế hoạch P2–P6; không xóa hoặc sửa lịch sử milestone.

## BIG-01: Operator Alpha trên Xiaomi và ArduPilot SITL

**Kết quả bàn giao:** Một APK development, một manifest nguồn và một entrypoint kiểm thử thống nhất. Kỹ sư dùng điện thoại thật để lập nhiệm vụ, bay AUTO và LOITER hỗ trợ, điều khiển payload, xử lý mất kết nối, xem 3D, review và xuất hồ sơ. Hai operator có phiên độc lập. Tái sử dụng P1 đã đạt đúng phạm vi, không chuyển PASS sang bản mới bằng suy luận.

### Công việc phải gom vào cùng task

1. Khôi phục dependency đang thiếu bằng đúng SHA gốc đã tìm được. Lưu hồ sơ phục hồi và kiểm lại pin; không sửa nội dung hoặc lịch sử. Chốt một đường build hiện hành, giữ các prototype cũ chỉ đọc.
2. Sửa các gap PHONE06: binding admission cũ phải bị vô hiệu ngay khi xác thực lại hoặc xác thực thất bại; cutoff hết hạn đúng; xác thực mạng không khóa writer đang hoạt động; kiểm giới hạn số trước khi ép kiểu; trạng thái sẵn sàng trung tính không tự hết lease trước thao tác đầu; lỗi input hoặc gửi neutral vẫn phải thu hồi quyền đúng.
3. Hoàn tất dịch vụ admission, controller, script build và resource guard; cài APK development qua đúng serial Xiaomi, kiểm SHA/chữ ký và USB reverse. Không root điện thoại hoặc thao tác dữ liệu cá nhân.
4. Nối thao tác cảm ứng qua chính transport, sequence và writer native dùng chung. WAL/fsync trước gửi; kiểm lại owner, mode, generation, admission và tuổi input sau WAL. Không tạo socket gửi lệnh bên cạnh gate. Mất touch, JS đứng, app nền hoặc mất USB phải có kết quả an toàn và bằng chứng từ AP.
5. Khép luồng KML/polygon/corridor/QGC SimpleItems → preflight đúng kiểu và Home → upload/readback → AUTO → ground/disarm → review. Manual chỉ LOITER/Hold/RTL/Land theo quyết định PHONE06. Takeover làm nhiệm vụ tự động bị gián đoạn; không tự chuyển thành survey hoàn tất.
6. Nối operator B độc lập, consent/handover và nhiều payload đúng camera/gimbal/manager. Chuyển nguồn quan sát không được đổi quyền bay. Giữ UNKNOWN cho lệnh chưa rõ kết quả khi mất link.
7. Ghép observer 3D/âm thanh tổng hợp với cùng run/plan/pose, rồi xuất đúng hồ sơ qua SAF và kiểm bằng receiver độc lập. Restart/reboot phải giữ hồ sơ, không tự nối hoặc khôi phục quyền.

### Definition of DONE

- Build tái lập từ manifest hiện hành thành công; không thiếu pin; APK có chữ ký development, SHA nguồn/payload đúng; không còn P0/P1 trong phạm vi.
- Cài và đi hết hành trình trên model Xiaomi, Android/HyperOS và WebView đã ghi nhận. Kiểm layout, hitbox, popup, safe area, theme và input thực; không dùng browser emulation thay kết quả điện thoại.
- Read-only identity, boot, kiểu tham số và freshness đạt trước mọi mutation. Không tự connect, grant, arm hoặc retry lệnh chưa rõ kết quả.
- Neutral/pointer/axis/sequence/owner, TTL 250 ms, rate tối đa 20 Hz và post-WAL checks có negative cases. Đo độ trễ hết hạn thực; không suy bảo đảm real-time từ mock hoặc nới guard để lấy PASS.
- AP override expiry, RC fallback, LOITER, mất link và failsafe được qualification bằng một admission hữu hạn. Không bật manualActualQualified chỉ vì tham số đọc đúng.
- Nhiệm vụ polygon và corridor trên nguồn hiện hành qua readback, navigation, ground/disarm và review. Đủ các cohort và guard 1500/3000 ms của INTEGRATION03, không dùng lại acceptance của APK cũ.
- Hai phiên operator độc lập và các payload trong corpus qua consent, tranh chấp, revoke, partition và pilot loss; không tự khôi phục quyền.
- Observer airborne đủ 30 giây cùng UI/SITL, đúng pose và nguồn, đạt các gate RAF/coverage đã chốt. Các chỉ số này không được gọi là độ trễ camera.
- SAF đúng selected run, provider readback, hash và receiver độc lập; corruption/sai context bị từ chối. Có raw, exit status và closure seal đúng; package nguyên vẹn không tự chứng minh nhiệm vụ thành công.
- Process restart và reboot giữ nguyên hồ sơ; nguồn/candidate/ENDURE không sai pin; owned PID, port, container và mapping được đóng sạch.

**Ngân sách và điểm dừng:** Dùng điện thoại thay emulator. Chỉ dùng toolchain, image và asset đã cache. Giữ sàn 20 GiB; admission build gồm 160 MiB staging và 512 MiB dự phòng. SITL cùng 3D cần tối thiểu 22 GiB ổn định 30 giây, forecast được kiểm và runtime guard 21 GiB. Tối đa ba cửa sổ thực mới, mỗi cửa sổ 900 giây, sau các gate; lỗi chặn các bước phụ thuộc. Bộ mock ban đầu tối đa 48 input riêng biệt. Không xóa bằng chứng hoặc tự retry mutation.

**Phụ thuộc:** Xiaomi kết nối được, tài nguyên ổn định. Không cần SDK Hera để đóng phạm vi mô phỏng này. Giữ lại P1 writer/review/SAF/restart, CREW02 mTLS, compiler/observer INTEGRATION03 và sửa closure lifecycle05.

## BIG-02: Live Media và ảnh gắn định vị trong cùng cockpit

**Kết quả bàn giao:** Người vận hành xem và chuyển đúng RGB/IR, chụp ảnh có nguồn và tọa độ camera/drone lúc chụp, review ảnh trên bản đồ và chia sẻ video tới các thiết bị đã qualify. Đây là task giải quyết trực tiếp ba phản hồi đầu buổi họp.

### Công việc phải gom

- Chốt topology, camera, codec, resolution/FPS/bitrate, đường truyền, số người xem và budget độ trễ/loss/recovery trước khi chọn pipeline. Hiện chưa biết đoạn gây giật.
- Đo từng chặng camera/encode/link/receive/decode/display và fanout. Dùng test stream có frame ID/timestamp để cô lập mạng và decoder trước camera thật; ghi rõ nguồn tổng hợp. Giới hạn queue và thống kê frame trễ; xử lý video không được chặn C2 hoặc WAL. Chính sách bỏ frame video phải riêng, không áp sang mất raw/physics frame.
- Discovery và identity từng feed; selector RGB/IR/PiP theo capability; tuổi frame và trạng thái riêng. Xem thermal và đo nhiệt độ có gate khác nhau. Không tạo °C từ màu, không coi metadata MAVLink là đồng bộ thermal chính xác từng frame.
- Capture pipeline: intent/ACK/capture event/exposure time → file gốc và SHA → GNSS/pose/datum/time uncertainty → EXIF hoặc sidecar có lineage → review/export. Không dùng vị trí lúc download hoặc tọa độ vật thể thay vị trí camera/drone lúc chụp.
- Kiểm clock, reboot, generation và file retrieval. Thiếu GNSS, thời gian hoặc file phải UNKNOWN/quarantine; không điền số 0. Giữ file gốc, đánh dấu bản dẫn xuất nếu sửa metadata. Receiver độc lập và corpus chuyển động/thời gian sai/corruption phải kiểm được quan hệ ảnh–vị trí.

**Definition of DONE:** Một build hiện hành đạt các budget đã chốt trên đúng codec/link/thiết bị, có p50/p95/p99, jitter, FPS, drop, freeze/recovery, CPU/RAM/heat và uncertainty. Thiếu capture clock thì ghi UNKNOWN cho glass-to-glass latency. Ma trận điện thoại/desktop/tablet và fanout được kiểm trên các mẫu thiết bị thực đã chốt. RGB/IR, capture và geotag đúng nguồn, đúng thời điểm; lỗi và frame cũ hiển thị rõ. Có ảnh gốc, metadata và kết quả receiver độc lập. Tách test stream, camera thật và radiometry thành các gate; thiếu camera/model/API thì chưa đóng claim phần cứng.

**Phụ thuộc:** Nối vào active build của BIG-01. Có thể chuẩn bị adapter, corpus và nguồn test stream song song từ sớm. Cần camera/model/firmware/API, ảnh gốc và topology cho gate camera thật. Không dựng thêm ứng dụng demo video rời. Các chỉ tiêu numeric chưa chốt phải được quyết định đầu task, không tự gọi một mức là chuẩn DJI.

## BIG-03: Hera Bench → Field → Customer Release

**Kết quả bàn giao:** Một cấu hình HeraHub/Hera và payload cụ thể đủ điều kiện khảo sát/utility inspection và bàn giao khách hàng; vận hành đêm/tầm xa được chứng minh trong miền hoạt động đã chốt.

**Công việc gộp:** MCU/HID/joystick/nút và calibration thật; SDK/radio/gimbal/camera Phase One/RGB/thermal đúng model; mass/CG/power/thermal/link/endurance budgets; HIL rồi field. Kiểm sensor/video/failsafe ban đêm, khi link yếu, quay về ngược gió, Home/terrain và điểm đáp. Khép dual operator, ảnh thật/geotag, production signing/key custody, update/migration/recovery, SBOM/license, support và customer acceptance.

**Definition of DONE:** BOM/firmware/software/configuration có chủ nguồn xác nhận; trace bench/HIL/field cho nominal và lỗi; range/night/energy margin/media đáp ứng mức đã chốt. Camera, operator và payload thật được kiểm, không suy ảnh từ ACK. Production chỉ khi key/update/rollback/recovery và các gate phát hành đạt. Không coi development PKI là production hoặc phần mềm là chứng nhận NDAA. ENDURE 24 giờ phải đạt campaign nguyên vẹn đúng gate, không cộng interval hoặc elapsed time. Thiếu thiết bị/SDK/địa điểm/nghiệm thu khách hàng phải giữ trạng thái chưa đạt đúng scope.

**Phụ thuộc:** BIG-01/02 và thiết bị/SDK Hera, HeraHub, Phase One, radio; yêu cầu formal của khách hàng. Tầm xa và bay đêm là năng lực cả hệ thống. Không hứa số km hoặc 45+ phút từ mô hình chưa hiệu chuẩn.

## BIG-04: Training Simulator có fidelity được đo, nhánh riêng

**Kết quả bàn giao:** Huấn luyện manual/assisted/AUTO qua chính AERIS, physics vòng kín giữ 1× cùng UI/AP, tải/gió/pin/collision/motor fault bám dữ liệu; có scenario, instructor, replay và đánh giá học viên.

**Definition of DONE:** Có dữ liệu khối lượng/quán tính/thrust/drag/battery/CG/motor failure và đối chứng. Nếu chưa có thì chỉ qualify profile generic, ghi nhãn rõ. Giữ speedup 1, cap 500 ms, full frame và fsync; đo RTF/jitter trên các profile/tải host cùng điều kiện. Collision detection không thay collision response hoặc lực va chạm. Sling, CFD và âm học thiếu dữ liệu không được coi đã hoàn thiện. Model/asset license, pose, cảnh, hiệu suất và âm thanh có nguồn; RPM ước lượng vẫn là synthetic. Scenario và scoring có đối chiếu, chất lượng đào tạo được người vận hành đánh giá.

**Phụ thuộc:** BIG-01 và các component SIM32/SITL76/77/viewer hiện có; fidelity Hera cần measurements. Nhánh training không thay gate field của BIG-03. AI runtime, fleet và VIO chỉ thêm khi có nhu cầu, quality floor và ground truth, không làm chậm mục tiêu inspection trước mắt.

## Cách điều hành

Mỗi task có một manifest đầu ra, Builder thực hiện, QA độc lập bằng case chốt trước và Contractor kiểm output thực. Các sửa lỗi nhỏ là work package bên trong, không báo DONE như milestone riêng. Không đóng task khi mandatory gate còn FAIL/NOT_CHECKED. Không có số đo đủ để cam kết ngày hoàn tất hoặc tổng công từ scan này. LLM/agent trực tiếp không phải baseline phù hợp cho transport native và durability; ưu thế sản phẩm phải đo bằng hành trình người dùng hoàn tất, độ tin cậy, thời gian và công thao tác.
