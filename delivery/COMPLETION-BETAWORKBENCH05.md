# BETAWORKBENCH05: Beta host companion, video xuyên AUTO và cockpit

**Ngày25/10/2026. OVERALL STATUS: READY-with-deferred cho Beta nội bộ trên Mac hiện tại + Android emulator + ArduPilot SITL.** Chưa nghiệm thu HeraHub, camera vật lý, triển khai máy mới độc lập hoặc production.

## Kết quả sử dụng

Có gói thao tác Doctor → Start Beta → Android → Stop, không phải tự ghép các lệnh launch cũ. Launcher kiểm cache/SHA/cổng, giữ guard20/10GiB, tạo thư mục lượt riêng, không tự ARM/retry/resume hay dọn bằng chứng. Luồng Android khảo sát → preflight → upload/readback → Home sau arm → AUTO → payload/video → review → SAF đã chạy thực tế. Receiver kiểm lại gói và kết quả video từ raw, không chỉ đọc nhãn PASS.

Gói này **gắn với checkout/cache trên Mac đang phát triển**, không chứa SDK, Docker image hay toàn bộ source; chưa là installer tự chạy trên laptop sạch. APK development cần host companion. Không có thay đổi source/candidate đóng băng, canonical SOT hoặc lịch sử ENDURE.

## Bắt đầu kiểm

Hướng dẫn: [README](</Users/os/Downloads/AI technique/aeris/delivery/beta05-host-companion/README.md>).

1. Mở `Doctor.command`, sau đó `Start Beta.command`, giữ Terminal chạy.
2. Bật nguồn VP8 tại `http://127.0.0.1:8895/publisher`; mở `Android.command` để dùng emulator-5582 riêng.
3. Làm theo hướng dẫn nhiệm vụ sân thử. Chỉ bắt đầu AUTO sau preflight, cấp quyền, upload/readback và Home sau arm hợp lệ. Đo xuyên AUTO chạy3cửa sổ30s liên tiếp; không tự phát lệnh bay.
4. Review → kiểm video suốt AUTO → xuất raw/media qua SAF. Dùng `Verify Package.command` kiểm JSON lấy về Mac.
5. `Stop Beta.command` hoặc Ctrl+C đóng đúng runtime sở hữu. `Status.command` chỉ đọc trạng thái. `Start Mock Android.command` dùng cho kiểm UI không mở AP; `Start Mock.command` dùng browser bridge mock.

Cổng đều bind127.0.0.1. Không dùng các entrypoint này để kết nối điện thoại/Hera/drone thật. Giới hạn3request AP/host và3container AP Beta05 giữ lại trong đợt kỹ thuật hiện tại, không tự xóa khi đạt quota. SAF còn tên đề xuất legacy workspace02: chọn tên file mới rõ ràng như AERIS-beta05-auto-video.json. Dòng8873 ở trang publisher chẩn đoán là nhãn module cũ; URL thật là8895.

## Ma trận REQ/AC và bằng chứng

| Yêu cầu | Kết quả | Bằng chứng trong evidence/betaworkbench05 |
|---|---|---|
| AC1 Gói host dễ khởi động/dừng | PASS trên Mac hiện tại; Doctor/Start/Android/Stop đã chạy, duplicate launch/stale identity/origin/CSRF bị từ chối | launches/*/doctor.json, admission.json, source-pins.json, closure.json; launcher-http-negative01.json; owner-negative-fixture/result.json; doctor-final02.json |
| AC2 FPS phủ toàn AUTO | PASS:3cửa sổ raw, join bảo thủ vào raw AP, mỗi5s đủFPS, clock/coverage/gap đạt | android-auto-quality01.json; launches/20261025T015900Z-f92a7283/host/media/report-01..03.json; independent-oracle01.json |
| AC3 Cockpit | PASS phạm vi UI đã kiểm: glass, rail48px cân trục, phản hồi gimbal dễ đọc, fault controls tách, nhãn quyền hiện tại, footer không trộn đơn vị khi đổi màn | ui-host-matrix01.json; ui-modal-matrix01.json; android-final-ui01.json; android-footer-navigation01.json; ảnh android-current-*, android-footer-* |
| AC4 Android–SITL/persistence/SAF | PASS: AUTO thật đồng thời payload/video tổng hợp, đóng review, SAF13file, receiver tái tính, native restart giữ model và không trả quyền | receiver-android-saf01.json; receiver-final01.json; native-persistence-final01.json; android-final-ui01.json; closure-final02.json |

REQ coverage:4/4 AC đã triển khai và có bằng chứng theo phạm vi trên. Không cộng4lượt mock thành32ca độc lập: **8nhóm tình huống mock**, lượt cuối có kết quả ở integration04/results.json. Bộ phân tích video có13nhóm analytic/fault + replay read-only; nhãn quyền có7nhóm. QA do cùng assistant đổi vai, không phải người/đội QA độc lập.

## Video suốt AUTO: số đo thực

Run actual `s9bda51d32037456aa787`, host `launches/20261025T015900Z-f92a7283/host`:

| Đại lượng | Quan sát | Tiêu chí |
|---|---:|---:|
| Khoảng AUTO wire → đất/disarm |69.015,176ms | Phải nằm trọn trong các cửa sổ video |
| Khung chắc chắn trong AUTO |2.071 | Đếm theo cận clock, không theo ACK |
| FPS toàn khoảng |30,0079 |≥24 |
| FPS thấp nhất của13bin5s đầy đủ |29,8 |≥24 từng bin |
| P95 source-to-canvas upper bound |24,469ms |≤300ms |
| Gap bảo thủ lớn nhất |78,487ms |≤250ms |
| Tổng thu video |3×900mẫu, khoảng90.004,4ms |3cửa sổ30s liên tiếp |
| Clock unknown / overflow |0 /0 |0 |
| Fresh-ready từ thao tác mở viewer |257,6ms |≤1.500ms |

Phần dư4.015,176ms của AUTO được giữ trong phép tính toàn khoảng, không gộp thành bin5s. Các counter delta apiFailures/decoderErrors/consumerDrops/timestampMisses/unexpectedFreeze đều0 trong từng cửa sổ. Không đổi speedup, bỏ raw frame hay hạ tiêu chí để đạt.

Nguồn VP8 1280×720 tổng hợp, host encode → localhost HTTP/TCP → Android WebCodecs decode → canvas. **Ảnh thực0; physical/photon latency NOT_MEASURED**, backend encoder/decoder UNKNOWN dù yêu cầu prefer-software. Fresh-ready này không chứng minh app/codec hoàn toàn cold-start. Chỉ một nhiệm vụ sân thử ngắn được đo, chưa là thử tải nhiều điện thoại hoặc vận hành dài hạn. Nhiệm vụ vượt phạm vi90s sẽ không được chứng nhận bởi bộ thu này.

Oracle Python triển khai bộ đọc wire/CRC và phép join riêng, không import verifier JavaScript; kiểm668message wire cần thiết và tính ra cùng khoảng, số khung, FPS, P95 và gap. Đây là đối chiếu hai triển khai cùng tác giả, không thay human review hoặc chứng thực nguồn camera vật lý.

## Flight và bàn giao dữ liệu

ArduPilot4.7.1 ARM binary SHA256 `1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41`, image `sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84`. Internal quad, speedup1; chưa là vật lý Hera/SIM32 đã hiệu chuẩn.

Review actual accepted=true, reason=SITL_NOMINAL, raw6.341record, head `29b1f110478091276d2cfac4fa992ed3c5c94fb5a6f64dd6b4fa6cd285c65308`. Hoàn tất dựa navigation/ground/disarm/nearHome cùng quy tắc takeoff đã khóa, không dựa ACK. AP container `7f4e8118f24a1b6c5182e0b5ffc77c97824727cb6c43b008697809a98b652519` đã stopped, giữ state/log/container.

Gói SAF actual13file/7.244.638byte, SHA256 `f38e71a7afd5c34dbfafa05f08579fa0a18bbd6f7f90bb0d58171c9c78295713`, gồm flight raw/review, WAL, JPEG/sidecar/manifest,3raw media report,3binding và kết quả đối chiếu. Android đã ghi rồi đọc lại; receiver riêng kiểmSHA/raw/WAL/context và tái tính FPS. Sửa một byte bị từ chối. Checksum không phải chữ ký xác thực nguồn/phát hành.

Native workspace2.313byte giữ nguyên SHA `fb3584788667e846f876d0033a138600e7d77bac22eac8279b7bc0304e08272d` qua restart; APK cài khớp artifact. Khi start host mới, tạo lượt/workspace host mới; hồ sơ cũ còn theo thư mục/SAF và receiver, chưa có trình duyệt lịch sử host qua nhiều lượt trong UI. Không tự khôi phục quyền hoặc tiếp tục flight.

## Sửa UI và kiểm lại

- Giữ Barlow tiếng Việt, bảng màu RtR trắng/đen/vàng phụ, floating glass và hai rail rời header/footer. Kiểm geometry8màn chính browser,8popup camera/pin–tải–gió/workspace/nguồn ở hai theme; không tràn ngang, nút rail48×48 và cùng tâmY. Có lưu screenshot và kiểm trực quan các màn đại diện.
- Gimbal trả câu readback có pitch/yaw và nhãn tổng hợp thay JSON tràn ngang. Nhóm gián đoạn/quyền nằm trong details riêng; nội dung panel cuộn dưới header.
- Sửa nhãn quyền lấy từ receipt invalidation cũ: dùng snapshot hiện tại bound gateway/run/boot/client epoch; thiếu/sai identity hiển thị chưa xác định. Android đã kiểm cấp1 → thu hồi0 → cấp lại → restart0. Không thay thuật toán cấp quyền.
- Sửa lỗi footer giữ nhãn Fly nhưng render giá trị diện tích/GSD ở Plan/Review. Reset nhãn đồng bộ khi đổi màn; kiểm10lần chuyển màn Android hai theme, đúng nhãn/đơn vị và không tràn ngang. Screenshot cũ sai được giữ làm bằng chứng phát hiện, ảnh android-footer-* là kiểm sau sửa.

Full AUTO/video thuộc flight pins03. Sau đó chỉ sửa quan sát/nhãn/footer, projection guard và Doctor; final pins06. Mock/fault và Android UI được kiểm lại nhắm đúng phần sửa. **Không tuyên bố đã bay lại full AUTO sau các sửa trình bày cuối.** Decoder, clock, collector, verifier video, MAVLink command/readback và vật lý không đổi ở giai đoạn đó.

## Lỗi/giới hạn được giữ rõ

Có6host launch riêng: mock browser, lượt AP lỗi trước allocation, lượt actual AUTO đạt, mock UI thất bại trên inverse guard, mock UI nhãn quyền đạt, mock UI footer đạt. Không cộng/gộp các lượt thành campaign liên tục. Lỗi pin anchor01→02 và lỗi delimiter projection đã sửa có kiểm trước allocation/Doctor mới; giữ mọi console/closure. Một số đánh giá preflight đầu bị chặn đúng khi EKF/Home chưa ổn định; chỉ đánh giá chỉ đọc lại, không bypass và không ARM lúc bị chặn.

Chưa có HeraHub/PhaseOne/Sony/thermal/radio thật, ảnh phơi sáng/thời gian đồng bộ/GNSS thực hay hiệu chuẩn bản đồ. Chưa có production signature, clean-machine installer, signed macOS app, user study hoặc chứng nhận tương đương/vượt DJI. UI vẫn là Beta kỹ thuật và cần kiểm thực địa, găng tay/ánh sáng/thiết bị thật. Gói launcher chưa thay các gate đó.

## Nguồn, tài nguyên và trạng thái cuối

Source mới chỉ trong pilot/native/planning betaworkbench05, delivery/beta05-host-companion, evidence/betaworkbench05. Giữ14.025định danh bảo vệ,80mục WB02,358mục Beta03,2.157mục Beta04 theo từng baseline (các tập có thể chồng nhau, không cộng làm số file duy nhất). Current pins1.547file. Git tracked status không đổi so Beta04, gồm95đường dẫn đã thiếu từ trước; không tự phục hồi hoặc khẳng định hiện diện liên tục.

Gate20GiB admission/10GiB floor +256MiB reserve,31mẫu/30s, forecast15s, runtime45phút và quota1GiB giữ nguyên. Boundary được kiểm bằng mock; không làm đầy ổ thật để thử. Mọi PID/cổng riêng đã đóng; Docker image prune thu hồi0B, không xóa volume/container. Không có project copy trong /tmp, không tải dependency. Scratch biên dịch và cache Python riêng đã dọn, giữ toàn bộ bằng chứng.

VALUE EVIDENCE: thao tác Doctor/Start/Android/Stop/receiver thực đã chạy; giảm ghép lệnh thủ công theo thiết kế, chưa có nghiên cứu thời gian/công sức người dùng đối chứng. Không đưa LLM/agent vào runtime và không tuyên bố lợi thế AI chưa đo.

APK development SHA256 `0a364ba3723887dbe9cdcabdc2c2d6beb6a33c5a1cf7bf09e44576479fba8ea8`, cert SHA256 `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`. Handoff-final manifest và ZIP chỉ khóa checksum bàn giao, không ký production. Không commit/push/công bố ra ngoài.

Bộ kit: [ZIP94,7KB](</Users/os/Downloads/AI technique/aeris/delivery/AERIS-Beta05-host-companion-workspace-kit.zip>),14member, SHA256 `0c1230e3c9636a5c6f4984f6fb48edd3ca9f98d265ae6dbae47415a7be9d4ed4`. Package-verification01 kiểm CRC vàSHA từng thành viên. Source capsule flight03 giữ24file riêng của bản bay đúngSHA pin gốc; một số file được dựng lại bằng inverse patch sau chuyến bay rồi đối chiếuSHA, không sửa đường dẫn gốc hay claim capsule hiện diện liên tục. Current projection dùng ui-projection-handoff06.json, Doctor dùng doctor-final02.json; các file tên final trước đó vẫn là bằng chứng giai đoạn cũ theo handoff-provenance-note.json.
