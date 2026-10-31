# P1 OPERATOR: nghiệm thu Android–SITL

**READY trong phạm vi engineering. 12/12 tiêu chí bắt buộc đạt, không còn P0/P1 trong P1. Toàn bộ AERIS chưa hoàn tất.**

Một APK cô lập đã hoàn tất nhiệm vụ AUTO và điều khiển camera/gimbal lặp trên Fly chính, bàn giao vai có xác nhận, giữ UNKNOWN khi mất link, xuất raw qua Android SAF và giữ hồ sơ qua process restart/cold boot. Không phải khởi động lại kết nối để thực hiện các ý định payload mới hợp lệ.

## Kết quả người vận hành

| Kịch bản | Chứng cứ thực tế | Kết quả |
|---|---|---|
| Nominal, nhiệm vụ 32 item | Android emulator → native MAVLink → ArduPilot4.7.1-dev, cùng socket/generation | 4 capture,2 zoom,2 focus,3 góc gimbal trong AUTO; A bàn giao cho B, B xác nhận và chụp; đủ navigation → về đất/disarm → review accepted |
| Mất link, nhiệm vụ 28 item | Device2 đúng manager154, camera102 và100 đúng route; hai owner còn hiệu lực lúc cắt | Pending capture chuyển UNKNOWN, quyền bị thu hồi; observer riêng thấy GCS failsafe → RTL → ground/disarm. Review vẫn UNKNOWN, accepted=false |
| Xuất gói raw | ACTION_CREATE_DOCUMENT, SAVE và provider readback thật trên Android | 2.824.775 byte provider khớp stage; ZIP/manifest/raw/review/context kiểm độc lập. Toàn vẹn gói không đồng nghĩa nhiệm vụ thành công |
| Persistence | Force-stop/relaunch và cold boot không wipe/snapshot | 23 file raw/workspace cùng SHA và chuỗi hợp lệ; không tạo generation mới, không tự khôi phục quyền |
| Bảo toàn baseline | Đối chiếu current-byte | 468 file private cũ và 68.626 đường dẫn bảo vệ khớp SHA; source/candidate/ENDURE giữ nguyên |

Ảnh thật: **0**. Capture ở đây là ý định/lệnh tới peer tổng hợp. ACK và quan sát không chứng minh thực thi hay ảnh thực. Hai vai A/B hiện nằm trong một cockpit, chưa phải hai operator từ xa được xác thực.

## Gói bàn giao

- [APK development06](</Users/os/Downloads/AI technique/aeris/native/operator01/dist/aeris-operator01-development06.apk>), package `vn.rtr.aeris.operator01`, chữ ký development; không thay gói baseline.
- SHA256: `6a5a9c8a8be1e38baae0664aaedf1c2342c2b83a261b7f62649f8bdc73070ac2`.
- Source ID: `649dd9b276a99439a34a0913bf72e440d0fdf3bd27d8a98168c24c03ecd876ec`;161 source pins và108 assets đã đối chiếu.
- [Contractor Verify JSON](</Users/os/Downloads/AI technique/aeris/evidence/product-milestones/verification-P1-final06.json>), [QA độc lập 12 AC](</Users/os/Downloads/AI technique/aeris/evidence/operator01-qa/final-12ac-disposition06.json>), [Builder Completion](</Users/os/Downloads/AI technique/aeris/delivery/COMPLETION-OPERATOR01-BUILDER.md>).
- [Raw receiver nominal](</Users/os/Downloads/AI technique/aeris/evidence/operator01-qa/run06-01b-nominal-receiver04.json>), [raw receiver loss](</Users/os/Downloads/AI technique/aeris/evidence/operator01-qa/run06-01d-loss-receiver04.json>), [SAF integrity](</Users/os/Downloads/AI technique/aeris/evidence/operator01-qa/saf-package06-outer01.json>), [restart độc lập](</Users/os/Downloads/AI technique/aeris/evidence/operator01-qa/restart06-independent01.json>).

## Nghiệm thu theo TIP đã chốt

| Tiêu chí | Trạng thái | Kết quả trong scope |
|---|---|---|
| P1-A01 | PASS | Same engineering APK/nativegeneration completed compiledmission AUTO→navigation→ground/disarm→acceptedreview while mainFly issued4capture,2zoom,2focus,3gimbal explicit intents. |
| P1-A02 | PASS | Freshness/unknown,units/range and syntheticmedia labels verified by host guards and actualmainFly/restartdisabledstates. |
| P1-A03 | PASS | Every actual payloadintent has currentowner/revision/generation/sequence, exactprepared→wireSHA andoneattempt; no timed retry. |
| P1-A04 | PASS | Delayed/duplicate/wrongACK heldout guards and actualraw keep ACK_UNATTRIBUTED, no intent execution/media promotion; actualImages0. |
| P1-A05 | PASS | Actualdevice1 nominal anddevice2 loss setpoints targetmanager154 with explicitdevice/radians/NaNrates andfreshprimary, matchingexactpeerbytes. |
| P1-A06 | PASS | Heldoutprepare→write authorityloss refusesoldwire; actualAndroidfront transferproposal→explicitlocalrecipientconsent→recipientcapture verifiedraw. |
| P1-A07 | PASS | Heldoutclose/boot/foreground guards plus actualbothpayloadowners+pendingcapture commonlinkcut revoke/freezeUNKNOWN; passiveAPfailsafeRTLground independentlyobserved. |
| P1-A08 | PASS | Admission/quota/WAL/writefaults refusebeforewire; sufficientfsync ordering andnativeheartbeats remain; fullgeometrydiagnostics removedfromflightpaint, optionalUIquotafailure retained. |
| P1-A09 | PASS | Heldoutduplicate/outoforder/contradictory observations preserveunknown; actualfreshcamera/manager/status target/boot/sequence checkedbyupstreamreceiver. |
| P1-A10 | PASS | Frozen unseen8case corpus executedbeforeAndroid; actualnominal+losspinnedAPK/AP raw independentlydecodedCRC/route/units/mission/Home/owner andcounts. |
| P1-A11 | PASS | Process+coldboot retain23raw/workspacefiles,8closedrawchains and2workspacechains withoutnewconnectiongeneration/authority; oldprivate468mapsequal; frozenprotected68626currentbytePASS. |
| P1-A12 | PASS | All precedingmandatoryP1AC have scopedPASS andengineeringlimits; noP0/P1 open in agreedP1scope. |

QA là agent riêng, dùng decoder upstream và kiểm raw/private độc lập. Đây không phải chứng nhận của con người hay chứng nhận an toàn bay thực. Các kiểm mock, module DOM, raw SITL, thao tác Android và toàn vẹn gói được phân biệt trong JSON, không cộng số test làm chứng nhận chất lượng sản phẩm.

## Giá trị và giới hạn

So với giới hạn one-shot đã ghi nhận ở N98verify, P1 chứng minh được thao tác payload lặp trong một mission và một generation. Chưa đo A/B hiệu suất cùng mission với bản cũ, chưa có nghiên cứu usability, A/B Ragas/DJI hay kiểm độ chân thực Hera. Đối chứng LLM trực tiếp không áp dụng cho transport/quyền điều khiển xác định này; chưa đưa AI runtime vào quyền bay.

Mọi lần thất bại được giữ nguyên. Đặc biệt, ca01c đầy quota chẩn đoán và hết lease trước cut không được tính PASS. Ca01d dùng cùng APK/fixture/model đã lưu, bỏ thao tác nhập lại dư thừa, và tự đạt đủ active-owner loss. Không sửa quota, không tự xóa raw hay đổi lịch sử. Bản sửa AUTO phân biệt request với observed bằng deadline1500ms hữu hạn; freshness1500ms/cohort3000ms, fsync trước consumer/send và speedup1 giữ nguyên.

Hai việc P2 cần xử lý: biểu diễn rõ manager1001 đã dùng trong generation, và ngân sách diagnostic UI cho phiên kiểm dài. Native fence vẫn chặn đúng. Chưa có HeraHub/PhaseOne thật, SDK, radio/video thật, hai runtime operator được xác thực, production signature, field flight hoặc nghiệm thu24h từ milestone này.

## Sáu milestone sản phẩm

1. **P1 OPERATOR: đã nghiệm thu engineering Android–SITL.**
2. **P2 CREW: tiếp theo**, hai phiên operator độc lập, xác thực/consent/arbitration, nhiều payload và mất link/partition/reboot.
3. **P3 SURVEY**, khảo sát KML/QGC/corridor, Home/datum, camera và bàn giao dataset trong cùng sản phẩm.
4. **P4 TRAINING**, manual/bán tự động/AUTO với physics vòng kín,3D/audio và đo1×/jitter/fidelity.
5. **P5 HERA BENCH**, thiết bị/SDK/payload thật và HIL; hiện chờ đầu vào phần cứng.
6. **P6 CUSTOMER RELEASE**, ký production, vận hành target/endurance/field/customer acceptance và A/B cạnh tranh.

[Kế hoạch và gate gốc](</Users/os/Downloads/AI technique/aeris/planning/product-milestones/PLAN.md>) giữ nguyên; [trạng thái milestone hiện tại](</Users/os/Downloads/AI technique/aeris/evidence/product-milestones/milestone-status-P1.json>) là overlay mới. Không suy1/6 milestone thành phần trăm hoàn thiện sản phẩm.

Đã dừng sạch các runtime do tác vụ tạo. Đã bỏ6 APK unsigned trung gian sau khi kiểm payload bytes còn nguyên trong APK ký; APK ký và raw giữ lại. Docker prune dangling reclaim0B; không prune container/volume. Không tạo bản copy project trong/tmp. Sàn20GiB được giữ; cuối phiên còn khoảng27.0GiB. Receipt bảo vệ có nhãn cũ throughN97; [clarification](</Users/os/Downloads/AI technique/aeris/evidence/product-milestones/preservation-scope-clarification06.json>) ghi đúng coverage gồmN98verify/accept, không viết lại receipt hay suy đường dẫn tồn tại liên tục.

Fingerprint bàn giao: [module-fingerprints-P1-final06.json](</Users/os/Downloads/AI technique/aeris/evidence/product-milestones/module-fingerprints-P1-final06.json>). Báo cáo HTML đã kiểm cấu trúc/link; xem trước tự động qua file URL bị policy trình duyệt chặn, nên không tuyên bố đã render QA cho trang báo cáo. Việc này không thay kết quả UI Android đã kiểm.
