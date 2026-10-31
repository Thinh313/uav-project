# NATIVE89 — Android input/video bench

**DONE / READY trong phạm vi companion Android mô phỏng. Chưa nghiệm thu HeraHub.** Ngày18/10/2026.6/6REQ đã triển khai và kiểm trong phạm vi TIP-NATIVE89;100% là coverage của6REQ này, không phải phần trăm hoàn thiện AERIS.

Companion `vn.rtr.aeris.native89` tách khỏi APK cockpit Native88, không có permissions Android, không network/flight/SDK transport. Không thay source/candidate/canonical SOT hay ENDURE. Dùng SDK86 và certificate development sẵn có, không tải SDK/image hoặc tạo khóa/chữ ký production.

## Đã kiểm thực trên Android

- Android33 ARM64, owned emulator-5582/AVD89. APK development02 đã đối chiếu đúng byte cài đặt và assets/source của build; signature v2/v3 đạt, permissions trống.
-31kiểm mô hình chạy được trong ART qua nút Self-test: calibration/deadzone/neutral/deadman, invalid/foreign/stale input, focus/device loss, video generation/clock/metadata và late callback. Cùng31ca cũng chạy trên host JVM; không cộng hai lần thành62năng lực.
- Replay mock đã có3mẫu trung tính, deadman và nhận quyền mock rõ ràng, rồi stale/invalid axis thu hồi. Một ca xuống nền xảy ra4ms sau snapshot còn mockOwned=true; resume không cấp lại. Không có quyền bay hoặc đầu ra điều khiển.
- Android nhận7KeyEvent callbacks qua ADB và1joystick MotionEvent qua system input dispatcher. Đây là sự kiện mô phỏng, không phải HID/HeraHub thật. Raw joystick được giữ unmapped; không suy calibration hoặc độ trễ RC từ callback này. p95dispatch4ms chỉ mô tả số mẫu injected này trong clock uptime Android, chưa có budget phần cứng được duyệt.
- MediaExtractor đọc đúng clip VP8 tổng hợp SHA `317747904d0dba4d52afd987b92f19acab70d99766ac0db1f8d2134b8acd9a18`:640×360,23mẫu nén,1474595us. MediaPlayer/TextureView đã thực sự phát; các lượt danh nghĩa quan sát22hoặc23callback. Không đồng nhất mẫu nén/callback/scanout, không kết luận mọi frame được trình bày.
- Pause player có chủ ý để giữ frame: watchdog khóa freshness tại tuổi callback544ms, không tự hồi phục. Sau background khi video đang chạy, player bị dừng; resume giữ trạng thái chưa phát. Phát lại có chủ ý mở generation mới. Tuổi camera và camera→display latency luôn null/chưa biết.
- App force-stop/restart và Android reboot giữ SHA mọi trace cũ, tạo phiên mới không phục hồi ownership/player. Replay Python cuối kiểm5trace /245events,12nhóm chứng cứ phần mềm. Đây không phải powercut vật lý hay source authentication.

## QA và bằng chứng

| REQ | Kết quả trong scope | Evidence |
|---|---|---|
|89-01 companion/asset/UI/bounds | PASS | build02, installed-final02, ui-verification |
|89-02 input mock + Android dispatch | PASS mô phỏng; physical mapping NOT_CHECKED | host-tests02, trace-verification-final, joystick-dispatch-result |
|89-03 Android local video | PASS synthetic VP8; remote camera NOT_CHECKED | trace-verification-final, screenshots |
|89-04 lifecycle/restart | PASS emulator | process-restart-verification, android-reboot-verification |
|89-05 journal/receiver/fault | PASS scoped | host-tests02, negative-verification |
|89-06 preservation/closure | PASS | preservation-final, runtime-closure, source-final |

15ca storage trên JVM: writer lock, append/hash, clock/size/count/quota, symlink, evidence retention và không viết sau fail.12mutant trace bị từ chối, gồm torn/hash/duplicate, foreign session, claim physical/latency, mixed key clock, ART verdict sai, frame count sai và frame cũ sau stale. Một số mutant được tính lại SHA để chứng minh integrity byte không thay thế kiểm ngữ nghĩa. Không tạo receipt nguồn đã xác thực từ các kiểm này.

8nút native đạt bounds≥48dp, không chồng nhau ở1280×800,1280×640 và1024×600; ảnh đã lưu. Không chứng nhận mọi pixel, touch phần cứng hay FPS. Development01 phát clip được nhưng UIAutomator fresh dump thất bại sau cập nhật metric liên tục; không dùng XML cũ. Development02 chỉ đổi TextView khi text thay và không chạy age counter sau khi dừng. Fresh UI dumps sau đó đạt. Log lỗi, APK01 và raw gốc giữ nguyên.

Build/QA cùng một agent, tách SPEC/BUILD/VERIFY và dùng Python replay riêng; không tự nhận nhóm kiểm độc lập. Source/asset parity và syntax nằm trong source-final.json. Không chạy SITL hoặc thay APK Native88 trong tác vụ này.

## Artifact và giới hạn

APK: `native/native89/dist/aeris-native89-development02.apk`  
SHA256: `2d7c8329145743c4fd8849b56c7cf92540fe19bb2677105bd94b502d3b237a1f`  
Cert development: `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`. Min26/target33; tương thích thực với HeraHub chưa được suy ra.

`evidence/native89/verification.json` ghi coverage/gap; `native/native89/README.md` mô tả sử dụng và policy. Input250ms/render callback500ms là fixture policy, không phải thông số Hera hay tiêu chí bay đã duyệt. Native88 intake vẫn thiếu thiết bị/SDK, clock camera, radio, mapping và approved budgets. Phase One/gimbal/đa payload/hai tay cầm thật, ảnh mapping, HIL/field, camera latency/thermal/display, auth/release và ENDURE24h vẫn NOT_CHECKED.

57.003đường dẫn bảo vệ khớp SHA trước/sau, gồm Native88. Đây là kiểm byte hiện tại, không sửa lịch sử thiếu đường dẫn hoặc khẳng định hiện diện liên tục. Emulator/controller/app sở hữu đã dừng; cổng5582/5583giải phóng. Mẫu dung lượng thấp nhất35,48GiB, trên sàn20GiB.

Dọn đúng2unsigned APK và2bytecode mới (~395kB); `.build` tự dọn. Giữ APK ký, raw/negative fixtures,AVD89 và SDK86 dùng lại. Không project copy/tmp install; Docker image prune theo quy tắc chung, không prune volume/container. Bước phần mềm tiếp theo là tích hợp nguồn local/mock này vào cockpit cô lập, rồi kiểm lại hành trình trước khi có adapter thiết bị thật.
