# BETAWORKBENCH04: nghiệm thu Beta nội bộ Android–host companion–SITL

Ngày bàn giao: 25/10/2026 (Asia/Ho_Chi_Minh). Timestamp gốc của host/Android được giữ nguyên trong receipt, gồm các mốc UTC ngày 24/10. Trạng thái: **PASS trong phạm vi Beta mô phỏng nội bộ**. Đây không phải nghiệm thu Hera/HeraHub, camera vật lý hay bản production.

## Kết quả cho người dùng

Trong cùng shell Android cô lập, đã thực hiện khảo sát → preflight → upload/readback → xác nhận Home sau arm → AUTO trên ArduPilot SITL thật → review. Trong AUTO đã chọn/cấp quyền payload tổng hợp, đặt góc gimbal mock và lưu JPEG từ video do Android giải mã. Hai ca mất link/reboot khi đang AUTO đều thu hồi quyền và giữ hồ sơ chưa hoàn tất. Sau host/app/emulator restart, ba hồ sơ còn nguyên, quyền không tự trở lại. Xuất raw/media và xuất/nhập workspace qua Android SAF đã kiểm thực tế trên emulator-5582.

## Chính sách dung lượng đã đổi theo yêu cầu

Nguồn chính sách hiện tại: `pilot/betaworkbench04/resource-policy.json`. Admission **20 GiB**, hard floor **10 GiB**, dự phòng đóng/ghi **256 MiB**. Guard dừng sớm khi chạm floor cộng reserve hoặc dự báo giảm trong 15 giây. Giữ cửa sổ admission 31 mẫu/30 giây, giới hạn giảm 256 MiB, quota bằng chứng 1 GiB, thời gian runtime hữu hạn và không tự xóa bằng chứng. Cả controller, AP launcher và nguồn video của bản thử mới dùng chính sách này. Các receipt/source/candidate ENDURE lịch sử không bị sửa để đổi ngưỡng.

`policy-tests01.json`: 7 nhóm boundary đạt, gồm dưới admission, thiếu mẫu, xu hướng giảm, đúng reserve, dưới floor và forecast. Admission thực và guard runtime được giữ trong từng file `controller-admission*.json`, `controller-guard*.jsonl`, `flight/runs/*/admission.json`. Host cuối còn khoảng 33,8 GiB, không cần dọn dữ liệu khác.

## Ma trận nghiệm thu

| Cổng | Kết quả thực tế | Bằng chứng chính trong evidence/betaworkbench04 |
|---|---|---|
| Chính sách 20/10 | PASS, guard/quota/trend còn hoạt động | resource policy, policy-tests01.json, controller-launch06.json |
| Mock/Fault | 8/8 nhóm PASS: polygon/corridor, model binding, close sớm, background, cut/reboot, pending command khi đóng | integration02/results.json |
| Native/SAF busy | Cancel và file sai cấu trúc đều trả lỗi, picker mở lại được; owner gate không bị khóa vĩnh viễn | android-actions01.jsonl, ui-*.xml, saf-*.png, native-final06-verification.json |
| AUTO thật | PASS: upload/readback, Home sau arm, AUTO, thực thi, ground/disarm/near Home, review accepted=true | run s87a25e490da44130aa99: raw.jsonl, review.json, launch.json, closure.json |
| Video Android | 900 mẫu/30.001,4 ms, 29,9986 FPS; P95 upper-bound latency 31,745 ms; fresh-ready 229,9 ms | android04/media/report-01.json |
| Payload/media đồng thời AUTO | PASS: discovery/select/grant/gimbal mock; JPEG tổng hợp có hash và liên kết run/model/plan, tham chiếu host trong AUTO, cao độ tương đối 7,628 m | auto-capture-correlation01.json, auto-video-payload04.png, android04/session/workspace/captures |
| Mất link khi AUTO | PASS cho thu hồi quyền và hồ sơ incomplete; accepted=false, complete=false, raw 2.718 | run s9ad4ec249891427ead46, restart-after-saf06.json |
| AP reboot khi AUTO | PASS: cùng container, PID/StartedAt đổi thực; không reconnect/cấp lại quyền; accepted=false, complete=false, raw 2.718 | run sf349282ead9c41359c30/reboot-observation.json, review.json |
| Native persistence/restart | PASS: generation/HEAD gốc khớp byte sau restart và sau vòng SAF; installed APK khớp artifact; ba host review giữ nguyên, authority=null, leaseCount=0 | native-before-repair, native-final06, native-final06-verification.json, restart-after-saf06.json/png, wal-prefix-final06.json |
| SAF raw/media | PASS: Android create-document/write/readback; file lấy lại từ Downloads khớp HTTP, receiver kiểm 6 file, raw 8.240, WAL/review/JPEG context; gói sửa byte bị từ chối | receiver-android-saf01.json, receiver-android-saf01-verification.json, receiver-http06-verification.json |
| SAF workspace | PASS: xuất JSON 2.313 byte, chọn lại qua picker, kiểm semantic, lưu rõ ràng, restart khôi phục; SHA trùng generation ban đầu | workspace-saf-export06.json, workspace-imported06.png, restart-after-saf06.png |
| Đóng sạch | PASS: host/emulator exit 0, không còn listener trên 8895/8896/5582/5583/5984; AP container đã stopped, không xóa container/volume | controller-closure06.json, closure-final06.json, từng run/closure.json |
| Bảo toàn | PASS theo baseline: 14.025 định danh cũ, 80 file WB02, 358 mục Beta03; frozen dependencies khớp | preservation-after.json, beta03-preservation-final01.json, pins-final01.json |

## Đối chiếu chuyến bay

Firmware ArduPilot 4.7.1 ARM đã kiểm, binary SHA256 `1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41`; cached image `sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84`. Internal quad physics, speedup 1. Không gọi đây là mô hình vật lý Hera/SIM32.

- Nominal `s87a25e490da44130aa99`: 8.240 raw, head `2e3c059966a83c235c3273feab740ab91541a1c7255e1140a9a78c35069c606e`, reached [2,3,5,7], groundDisarmed=true. Takeoff item 1 không phát MISSION_ITEM_REACHED: dùng đúng quy tắc đã có `FIELD02_TAKEOFF01_CURRENT_CLIMB_TRANSITION_V1`, với current takeoff, armed AUTO, climb 19,776/19,987 m tới mục tiêu 20 m và transition sang navigation. Không suy diễn hoàn tất từ ACK.
- Cut `s9ad4ec249891427ead46`: 2.718 raw, head `891dd9182e916cf997a4d5786646f2c388314f67b0213dd37e741ccf4e196aec`, AUTO đã quan sát, incomplete. Native ngắt transport và dừng simulator được sở hữu: kiểm này không chứng minh drone tự RTL khi mất radio.
- Reboot `sf349282ead9c41359c30`: 2.718 raw, head `8d6c627a60055dab8ff4c50cab3a25c2d53feeaa5e64f3727abb99b4eaca655b`. PID AP từ 42442 sang 43051 trong cùng container; không tự reconnect. Chưa quan sát MAVLink boot mới vì session bị thu hồi có chủ đích.

Receiver SAF SHA256 `0aac1d1b1b7c1419306ab1870d0bbf70f26a742428e86c33c13b9ca6502d8bfe`, 5.747.007 byte. Gói ưu tiên review hoàn tất gần nhất, nhãn nút thể hiện lựa chọn này; hai review gián đoạn vẫn còn trong WAL. Đây là gói kiểm toàn vẹn, không phải chữ ký xác thực nguồn hay chữ ký phát hành.

## Các lỗi đã xử lý, giữ nguyên lần lỗi

Đã sửa origin native, fallback chiều cao WebView 101, whitelist port video, exact-byte pin allocation, raw null thay giá trị undefined ở bản mới, lifetime/guard nguồn media, selector/timing UI harness và HTTP Buffer serialization của gói SAF. Không sửa raw/review/receipt đã đóng. Lỗi đầu không cấp container; lượt readonly hết deadline không ARM/AUTO; hai lượt đó được giữ cùng closure/resolution riêng, không cộng thời gian hoặc tính thành ca PASS.

Controller01–05 và run `se8a0ab01927e4119a9ff`/`sd197578b511846c4a4a0` là lịch sử riêng. Controller06 chỉ chạy review/SAF từ workspace đã đóng, không có quyền mở AP mới. Năm AP request đã hết ngân sách của đợt kiểm. Không dùng controller cũ để ghi đè hay tự chạy lại.

`pins-final01.json` đối chiếu 1.547 file không đổi. Năm file hiện hành khác flight pin chỉ thuộc UI export, package/HTTP server, controller review-only và TIP. Các ca bay không được tuyên bố đã chạy lại sau sửa bàn giao; wire-format, native SAF, receiver và restart đã kiểm nhắm đúng phần sửa cuối.

## Giới hạn và công việc còn lại

- Đây là APK development chạy shell với host companion qua reverse localhost, chưa là bộ cài tự vận hành trên HeraHub/Xiaomi. Cần SDK, thiết bị, transport và bench riêng trước bay thật. Không ký production hay tạo candidate phần mềm đóng băng mới.
- Payload discovery/gimbal/camera là mock. RGB/video/JPEG tổng hợp, **ảnh thực 0**, physical exposure time UNKNOWN; geotag là tham chiếu telemetry host, qualifiedForSurvey=false. Không chứng minh Phase One/Sony/thermal, độ phủ ảnh thật, radiometry hay chính xác bản đồ.
- Cửa sổ đo 30 FPS kết thúc trước AUTO. Khung giải mã/chụp trong AUTO được đối chiếu riêng. Chưa chứng minh FPS SLO liên tục khi bay hoặc latency photon/camera thật, app/codec cold-start đầy đủ.
- Review legacy còn chuỗi reason `MOCK_NOMINAL`/`MOCK_CUT_INCOMPLETE`/`MOCK_REBOOT_INCOMPLETE` trên ca actual. Trường source `OBSERVED_OWNED_SITL`, raw và runtime là chứng cứ nguồn; không sửa lịch sử để đổi label. Đây là nợ hiển thị cần xử lý ở phiên bản schema kế tiếp.
- UI vẫn là engineering cockpit: output JSON payload có thể tràn ngang và nội dung panel dài cần cuộn; chưa nghiệm thu UI production/DJI. Publisher có text port cũ mang tính hiển thị. Không nhận đây là sản phẩm hoàn thiện thẩm mỹ cuối.
- Git vẫn ghi nhận 95 tracked paths thiếu. Các đường dẫn thiếu đã được nêu từ Beta03; kiểm bảo toàn so với baseline hiện diện, không khẳng định toàn bộ Git/source gốc đầy đủ hoặc các đường dẫn hiện diện liên tục. Không tự phục hồi ngoài phạm vi tác vụ.
- QA do cùng assistant đổi vai Builder/Verify, receiver là kiểm máy riêng; chưa có người dùng/QA độc lập hay hội đồng nghiệm thu thực địa. Không lấy số test để suy ra DJI parity.

## Bàn giao và vận hành

APK: `native/betaworkbench04/dist/aeris-beta04-development02.apk`, SHA256 `91ae93bc6ba94539a5e880e3a97d29089c73a114b3ea15703ee66039aca6028e`, cert development SHA256 `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`. Source mới chỉ ở pilot/native/planning betaworkbench04 và evidence tương ứng. `final-verification01.json` chứa kết quả máy; `handoff-final01.json` khóa fingerprint bàn giao.

Runtime và tab publisher riêng đã đóng. Giữ AP container/state/log để truy nguyên. Không có project copy trong /tmp; scratch `.build` đã dọn. Docker image prune theo AGENTS.md thu hồi 0 B; không xóa volume/container. Không sửa canonical SOT/ENDURE hay lịch sử các đợt cũ. Không commit/push hoặc công bố ngoài trong tác vụ này.

Bước sản phẩm tiếp theo: đóng gói host-companion Beta để người kiểm tái lập có hướng dẫn; kiểm thêm FPS suốt AUTO, nhiều thiết bị Android và hoàn thiện UI engineering. Sau đó mới mở gate bench HeraHub/camera thật, trước flight readiness/production. Không cần thêm tính năng để coi đợt kiểm này đã đóng đúng phạm vi.
