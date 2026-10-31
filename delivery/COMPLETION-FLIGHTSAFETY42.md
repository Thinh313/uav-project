# FLIGHTSAFETY42 · preflight, geofence và GCS failsafe trên ArduPilot thật

14/10/2026. **DONE trong phạm vi SITL cô lập đã chốt.** Verdict `READY_SCOPED_REAL_SITL_FLIGHTSAFETY42`. Bảy yêu cầu R42-01..07 đã triển khai và kiểm đủ7/7; đây là coverage của lượt kiểm, không phải tỷ lệ trưởng thành sản phẩm. Một agent lần lượt làm specification/build/verify; không gọi là kiểm độc lập. Chưa tích hợp vào native/Fly hay xác nhận Hera thực.

## Hành vi đã quan sát

Dùng đúng binary ArduCopter4.7.1, custom commit`dbe79216`, SHA256`011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482`, cùng binary của41. Fullsource commit đối chiếu là`dbe792162d06cab66c3475fd5556bf7a120f119e`. Quan hệ binary/version/source dựa trên metadata gốc, manifest sở hữu và thông báo thực; không phải build tái tạo byte hay attestation mật mã.

| Tình huống | Kết quả thực trong run03 |
|---|---|
| Preflight quan sát | GPSfix>=3, >=10satellites, EKF attitude/absolute horizontal position, Home và vị trí/battery/17 kiểu tham số đọc được |
| Ngưỡng arm pin không đạt | BATT_ARM_VOLT50V: arm result4(FAILED), text Battery1 below minimum arming voltage, heartbeat mới vẫn disarmed |
| Fence không hợp lệ | Margin40m >radius30m: arm result4 và textFENCE_MARGIN, heartbeat mới vẫn disarmed |
| Khôi phục preflight | Readback pin0V vàmargin2m, ARMING_SKIPCHK0; hai lượt normalarm/cất cánh10m, heartbeatarmed/altitude/in-air thực |
| Guided ngoài vùng | Lệnh mục tiêu100m không làm drone đi quá5m trong cửa sổ5s; đây là quan sát kết hợp source, không chứng minh nguyên nhân bằng im lặng/ACK |
| Bay tới điểm trong vùng | Drone đi18–25m, modeGUIDED, trong circle30m |
| Geofence thực thi | Fault đổi radius30→10m khi đang bay: FENCE_STATUS circlebreach(count/type/status), textbreach, tự modeRTL, về Home/hạ cánh/disarm |
| GCS failsafe thực thi | FS_GCS_ENABLE1, timeout5s, FS_OPTIONS0 đọc lại; dừng TXheartbeat trong khi RX tiếp tục → GCSfailsafe text +armedRTL |
| Khôi phục GCS/kết nối | Heartbeat restored→cleared text; quan sát>=5s và>=2 heartbeat MỚI vẫnRTL; close TCP thật, lease cũ mất hiệu lực; reconnect discovery/17reads mới, về Home/hạ cánh/disarm |

Home quan sát là10.8539999°N,106.807°E, altitude10100mm MSL. GLOBAL_POSITION_INT giữ riêng altMSL(mm) vàrelative_alt(mm); lệnh takeoff/position10m relative-to-Home, RTL_ALT_M10m. Ở marker hạ cánh, flightfence cáchHome≈0.011m, relative_alt−5mm; flightGCS≈0.022m,−23mm; cả hai landed_state1, armedfalse, mode6. Đây là kết quả simulator, không phải độ chính xác Hera/GNSS thực. `observed-summary.json` cuối session01 là lúc chuyến GCS đangRTL; dùng `flight-endpoints.json` để xem kết thúc từng chuyến, không nhầm sessionend với flightend.

ArduPilot theo dõi heartbeat GCS và khi kết nối khôi phục giữ modefailsafe; nguồn hướng dẫn chính thức [GCS Failsafe](https://ardupilot.org/copter/docs/gcs-failsafe.html). Hướng dẫn [Fences](https://ardupilot.org/copter/docs/common-geofencing-landing-page.html), [Pre-arm checks](https://ardupilot.org/copter/docs/common-prearm-safety-checks.html) và [Guided commands](https://ardupilot.org/dev/docs/copter-commands-in-guided-mode.html) bổ sung ngữ cảnh; chúng là externalclaims, không thay raw/version-specific sourcechecks. Hash sourcefiles và mapping ởsources-qa.json.

## Khoảng trống firmware đã tìm và xử lý trong namespace mới

4.7 bỏ ARMING_CHECK, chuyển ARMING_SKIPCHK với ý nghĩa đảo ngược:0 skipnone. Không gửi oldvalue1 sang newparam; không disablechecks/forcearm. RTL_ALT/RTL_ALT_FINAL centimetres đã chuyển RTL_ALT_M/RTL_ALT_FINAL_M floatmetres. Mapping mới có readback loại/value thật, không sửa FIRMWARE38 hay lịch sử version cũ. UID0 và UART bootpreamble giữ exception hẹp trong simulator sở hữu, không chuyển thành identity Hera.

## Kiểm bằng chứng và sức khỏe kỹ thuật

| Kiểm | Kết quả / receipt |
|---|---|
| LiveQA cuối |17/17, 2flights/2TCPsessions ·run03/qa.json |
| Named readbacks/configsets |57reads +6sets,17names/types ·raw-replay2.json |
| Raw replay từ bytes |1024rows,1990APframes,226TX intents cówrite-return;13/13 semanticgates |
| Unit/fault |56/56 unit3 +9/9 focusedguardfaults1 |
| Adversarial evidence |14/14 rejected ·bites1; các mutation ngữ nghĩa tái tính hashchain vẫn phải bị chặn |
| Cold regressions |36:33/33,37:41/41,38:54/54,39:40/40,40:44/44;41:3actualsessions exact, không ghi output cũ |
| Final verifier |26/26 gates ·verification1.json; freshprocess replay exact |
| Syntax |8JS +3Python valid; không claim fullbuild/typecheck/lint/emulatorCI |
| Bảo toàn |13,708 protectedpaths,0missing/changed; ENDURE5,051file inventory cùng SHA |

TX whitelist chỉ GCS255/190→AP42/component1; không broadcast, forcearm, missionupload, payload, termination, firmware reboot hoặc automaticretries. ACK được lưu như phản hồi; mọi kết luận thực thi có telemetry/raw bổ sung. Weak locallease không restore bằng serialization; loss/stale/framing/clock/conflictingversion làm mất hiệu lực. Harness chỉ localhost5797/container sở hữu, chưa là command authority cho ứng dụng.

## Các lần thử và giới hạn được giữ nguyên

Run01 timeout tên ARMING_CHECK đã bị bỏ, trước mọiset/arm/flight. Source/config/raw/failure/cleanup gốc retained. Run02 live17/replay13 ban đầu đạt nhưng semanticbite phát hiện cửa sổ321ms saurestore không có heartbeat mới, không đủ kết luận modepersistence. `verification-gap.json` giữ sự cố và đánh dấuNOT_FINAL_ACCEPTANCE; không sửa cácreceiptPASS cũ thành lịch sử khác. Run03 là acceptancecuối sau tiêu chí>=5s/newheartbeats, post-negative disarmed heartbeat và observer failclosed. Lỗi focusedfaultfixture ban đầu thiếu13byte signaturetrailer được giữ riêng và sửafixture, không đổi runtime để nétest.

GCS blackoutmarker→RTLmark là4429ms host; lastheartbeatTXintent→RTLmark5243ms. APtimeout5s tính từ APnhận heartbeat, không phải lúc bắt đầu marker; TXintent không phải APreceipt. Không suy ra one-waylatency, jitterhay1× từ các con số này. Clockhost–guest không ghép/scaled.

Geofenceca là boundaryupdatefault, chưa chứng minh crossing ranh giới cố định/polygonupload/altitudefence/avoidance. NgoàiGPS/EKF quan sát vàbatteryprearm, chưa kiểm activebattery/RC/EKFfailsafe, Landfallback khi mấtposition, AUTOmissionfailsafe exemptions, actualradioimpairment hay simultaneousfaults. Ảnh/media/payload, SDK/Hera/HeraHub, APK/Android/emulator, native/Fly integration, AIflight, endurance24h và software release/signature đềuNOT_CHECKED trong bước này. Không so chất lượng bay vật lý với DJI từ simulator.

## Tài nguyên, closure, bàn giao

Runtime reuse imageSHA`534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`, CPU1/RAM256MiB/log2×2MiB, source/defaults readonlymount, EEPROM16KiB/run riêng. Staticx86_64binary chạy qua DockerDesktopemulation trên host; không install/pull/build dependencies. Threeownedtestcontainers đã stop/auto-remove; cuốiport5797closed, alltestsocketsended, dockerimageprune receipt mỗirun. Không prune container/volume khác. State nhỏ giữ làm evidence; không có bản copy dự án/tmp/AVD/APK/Next outputs cần xóa.

Finalverifier còn≈24.19GiB và namespace mới dưới64MiB; finalpreservation/fingerprint receipt cập nhật số chính xác saureport. Nguồn/candidate/trust/canonicalSOT và mọiENDUREevidence không đổi, không restart/selection/24hclaim. SHA cuối chứng minh tính toàn vẹn tại thời điểm kiểm, không chứng minh hiện diện liên tục của các đường dẫn từng phục hồi ở bước trước; fsync/journalhash không phải kiểm powerloss vật lý hay radioauthentication.

Bước tiếp phù hợp: adapterpreflight theo firmware4.7 với freshness/configtyped và policyđược version hóa; tích hợp chỉ sau scope/gate mới. Để mở rộng safetycoverage: fixedboundary/polygon/altitudefence, GCS/no-position fallback, battery/RC/EKF/AUTO exemptions rồi faultcombinations. Chưa có ủy quyền tự sửa frozenapp/candidate, chạy ENDUREmới hay kýrelease trong task này.
