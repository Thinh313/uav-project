# PREFLIGHT43 · adapter preflight chỉ đọc cho ArduCopter4.7.1

14/10/2026. **DONE trong phạm vi cô lập đã yêu cầu.** Verdict `READY_SCOPED_READONLY_PREFLIGHT43`. R43-01..08 triển khai/kiểm đủ8/8; đây là coverage của adapter/testprofile, không phải tỷ lệ sản phẩm sẵn sàng bay. Một agent lần lượt specification/build/verify; không phải kiểm độc lập. Không tích hợp Fly/native, ký mới hay thay ENDURE.

## Adapter đã làm được gì

Module mới `pilot/preflight43` ghép immutable APSTREAM40framer và FIRMWARE38C-cast decoder với private session/boot/state/cohort mới. Profile43.1 kiểm exactfirmware4.7.1(numeric67568127)/customdbe79216, binarySHA`011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482`, localprocess ownership. Các build/firmware khác chưa được qualified tự động; versionstring đơn lẻ/UID0/ACK không đủ identity hay readiness.

Đọc20namedparameters đúng MAV_PARAM_TYPE, phạm vi/index/count/unit:17trường đã kiểm ở42 và RTL_ALT_TYPE,FENCE_ALT_MAX_TP,GPS_HDOP_GOOD. ARMING_SKIPCHK(int32)=0 giữ mọi check, không dùng ARMING_CHECK đã bỏ hoặc chuyển oldvalue1 sang newmeaning. RTL_ALT_M/RTL_ALT_FINAL_M floatmetres; RTL_ALT_TYPE0 relativeHome vàFENCE_ALT_MAX_TP1 Homeframe. C-cast integer fraction/range/abs>=2^24 không được nhận là số nguyên chính xác. Không cóPARAM_SET/ARM/mode/mission/payload/reboot output; whitelist chỉGCSheartbeat, versionrequest, streaminterval và20namedreads.

Một lượt đọc phải đủ20trường, cùngcount, khoảngcapture<=3s và từngresponse trong1500ms, có writerreceipt. Adapter công bố toàncohort cùnglượt hoặc không công bố; không trộn partialcache để READY. Đây không phải transactionatomic từAP: classicPARAM protocol không có transactionnonce. Sau khi giá trị đã đọc thay đổi, kể cả duplicate/reorderedpacket, cohort/ticket mất hiệu lực và cần fullreread. Foreign/duplicate/reordered không làm dữ liệu mới hơn; conflictfirmware/type/context, writerfailure, host/bootclockregression vàtimeout failclosed.

| Cổng freshness | Giới hạn |
|---|---:|
| Heartbeat usable / hardloss |1500ms / >3000ms |
| SYS/GPS/EKF/globalposition/fence/landed |1500ms |
| Home |3000ms |
| Parametercohort |10000ms từ reply CŨ NHẤT |
| Một request / span của cohort |1500ms / <=3000ms |

TTL từ replycũ nhất nên kết quả READY không mặc nhiên sống thêm10s từ lúc đọc xong. Ticket kiểm tra chỉ có giá trị tới deadline sớm nhất tại lúc cấp và vẫn reassess; dữ liệu mới không hồi sinh ticket đã hết hạn. Ticket là WeakMapprocesslocal, không restore bằng JSON/snapshot/cloning, không chuyển quaowner/profile/session/cohort khác. `armPermission`, `operationalAllowed`, `authenticated`, `hardwareIdentityProven` luônfalse.

## Chẩn đoán preflight và bằng chứng thực

Adapter phân biệt READY_SCOPED_READONLY/BLOCKED/UNKNOWN/INVALIDATED và trả lý do theo nguồn. Kiểm disarmed/landed, bit APprearmhealth, GPSfix/satellite/HDOP, EKFflags/finitevariances, batteryvoltage/profilethreshold, HomeWGS84/MSL+globalMSL/relativealtitude, circlefence config/status, GCSpolicy vàRTLHomeframe. ReservedGPSfix/criticalheartbeat/constantpositionEKF bị chặn hoặcUNKNOWN. Không biến HDOP thành độ chính xác mét, không suy raWh từ voltage/remainingpercentage; không thay APfinalarmchecks hoặc kỹ thuật kiểm máy bay thật.

Theo [MAVLink SYS_STATUS](https://mavlink.io/en/messages/common.html#SYS_STATUS), batteryvoltage có sentinelunknown và có thể mơ hồ khi nhiều pin; profile này chỉ áp cho một pin simulator đã pin. [Parameter protocol](https://mavlink.io/en/services/parameter.html) phân biệt kiểu/encoding và tiến trình đọc; byte/raw/source-specific checks được giữ riêng ởsources-qa.json, hướng dẫn web không thay acceptance.

Finalrun02 dùng exactownedSITL trênlocalhost5798, disarmed toànbộ. Ba TCPsessions, **80namedreads**, khôngflightcommand/parameterwrite:

1. Session01 đọc20typedvalues→READY; heartbeat/telemetry tiếp tục nhưng không đọc tham số, tới age10011ms của replycũ nhất→UNKNOWN(COHORT_STALE), khôngSOURCE_STALE. Full20reread→cohort2 READY, ticketcohort1 không còn hiệu lực; realTCPclose làm ticketmới mất hiệu lực.
2. Session02 discovery/reread20 với profilephủđịnh yêu cầuradius31m, AP thực báoradius30m→BLOCKED(PARAMETER_PROFILE_MISMATCH:FENCE_RADIUS). APconfig không đổi; đây là policycomparison, không phải firmwaređổi sai type.
3. Restart đúng ownedDockerCID: PID22151→23265, StartedAt2026-10-14T14:18:43.049814136Z→14:20:43.134674511Z. Freshsession/discovery/cohort20 mới→READY, tickettrước không chuyển được. Không dùng lệnh rebootfirmware hoặc restorecache.

Một profileREADY chỉ nói20configfields và telemetry hữu dụng khớp testpolicy ở thời điểm đánh giá. Whreserve/calibration/RC/authenticatedradio/polygon/terrain/physicalHera/native/Fly/fullarmingacceptance vẫnNOT_CHECKED. Mấtheartbeat/cohort stale không được giữREADY. Wrongtype kiểm bằng mock và mutationoffline; không nói ArduPilot đã thực phát malformedtypes. Binary/version/source association giữ mức localpinnedmanifest +observedannouncement, không bitreproduciblebuild/cryptographicattestation.

## Kiểm và toàn vẹn

| Phép kiểm | Kết quả cuối |
|---|---|
| Mockcorpus4 |38/38 trạng thái và lý do đúng |
| Edges4 |42/42:20sai type, ACK/unsolicited/prewrite/type/clock/oldcontext/ticket/readonlyTX |
| Currentcoldlifecycle |4/4:writerdeadline/clone receipt/tokenexpiry/outputbound |
| ActualSITL |6/6 trong3sessions,80reads/0writes/0flight |
| Coldraw |884rows,1541APframes,209TX cówrite-return; exact5assessment cùngcohort/profile/context/reasons |
| Adversarialfinal |12/12 mutations bịreject: staleREADY giả, missingwrite/closure/finalPV, type/count/index/skipchecks/profile/session khác |
| Coldregression |36:33/33;37:41/41;38:54/54;39:40/40;40:44/44;41:3actualsessions exact;42:finalrun03 exact |
| Finalverifier |28/28gates ·verification1.json |
| Syntax |13JS +3Python valid; không claim APK/emulator/fullCI/build/lint/typecheck |
| Protectedfiles |13,798paths0missing/changedSHA; ENDURE5,051file inventory giốngbaseline |

Rawreadonlyjournal lưu TXintent/write-return/RX/assessment/close với hashchain; không bỏ frame để đạt performance. Adapter tối đa20000frameevents; writerqueue64/1MiB, capture8MiB/10000rows/session. Lỗi/bound/diskfloor đóng link và không cho incompleteproof PASS. Coldreplay dùng thời điểm tạointent/receipt trên host, sắp theo clockđã ghi với roworder khi bằngnhau; không ghép clockguest–host hay đo one-waylatency. Hashchain/fsync không xác nhận radioauth, physicalpowerloss durability hoặc khả năng bay Hera.

## Hồ sơ phương pháp, tài nguyên và phần còn lại

Mockdriver đầu tiên gặp clockregression rồi introspection trên adapter đãINVALIDATED vẫnthrow; retainedmock-driver-attempt01.json, sửa giữ firstfailure và trạng tháiINVALIDATED. Đồng thời sửa vị trí fixturemargin đúng request trong corpus. BeforeQA run01 bổ sung deadline của bất kỳoutput thiếuwriterreceipt/outputqueuebound; sourcepins trước/sau retained bằng files riêng. Run01 đã đạtbaseline; sau khi mở rộng reservedGPS/criticalstatus/EKFconstantposition guards, giữ nguyên mọi raw và chạy run02 để nghiệm thu sourcecuối. Không ghi đè receipt cũ thành lịch sử khác. Finalactualrunnerpins vàprimarysourceSHA còn đúng.

CPU1/RAM256MiB/log4MiB, source/default/configmountreadonly, isolatedEEPROM16KiB/run, reuse image/binary, khôngpull/install/build/wholeprojectcopy/tmp/SDK/AVD/APK/Nextoutput. Haiownedcontainers đượcstop/auto-remove, alltestsocketsclosed, localhost5798closed, dockerimageprune từngrun; khôngprune/dừng container hoặc volume khác. State nhỏ giữ làm evidence; không có scratchcopy cần xóa.

Finalverifier còn≈22.35GiB; namespace dưới32MiB, finalfingerprint cập nhật sốsaureport. Source/candidate/trust/canonicalSOT/ENDURE không đổi, khôngrestartsoak/selectsoftware/ký mới. SHA cuối là endpointintegrity, không phủ nhận các sự cố đường dẫn gốc từng phải phục hồi ở lịch sửtrước.

Bước tiếp phù hợp: bổ sung bridgepreflight vào native trong namespace cô lập, gắn assessment/profile/cohort/age và lýdoblock vào hành trìnhsurvey→preflight→Flymock→review; snapshot lưu là evidence, khôngrestore quyền. Trước physicalHera cần actualSDK/link/device identity/input/video/profile/calibration vàHIL/flightgates. Safetycoverage rộng hơn(fixedboundary/polygon/altitudefence/no-positionGCSfallback/RC/EKF/battery/AUTOexemptions) vẫn là scope mới. Không tự tích hợp Fly hoặc phát hành/ký theo task43.
