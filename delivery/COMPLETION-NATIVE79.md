# NATIVE79 — Android installed mock journey

16/10/2026 · **PASS_INSTALLED_ANDROID_MOCK_GATE**. Native live-flight alpha remains incomplete and outside this gate. Single agent SPEC/BUILD/VERIFY; no independent-review claim.

Đã cài và chạy development APK trên Android 13 arm64 thật trong emulator-5582. Hành trình khảo sát → preflight → xác nhận Home/chuẩn cao độ → Fly mock → hai điểm tuyến → hạ cánh mock → review đã hoàn tất bằng thao tác UI, không inject trạng thái. Đây là ứng dụng Android được cài, không phải ảnh browser thay cho bằng chứng Android. Chưa có điều khiển live SITL từ Android hoặc nghiệm thu HeraHub thực.

## Kết quả và phạm vi

| Yêu cầu | Kết quả | Bằng chứng |
|---|---|---|
| REQ79-01: cô lập, bảo toàn, dung lượng | PASS: 44.183 đường dẫn khớp SHA ở kiểm cuối | preservation-before.json, preservation-mid-corrected.json, preservation-final-after.json, cleanup-final.json |
| REQ79-02: APK development riêng, không quyền radio/network | PASS | build07.json, signature07.txt, permissions07.txt; chứng thư NATIVE31 development hiện có |
| REQ79-03: Android/ART, dữ liệu app-private, restart | PASS theo phạm vi build/package bên dưới | android-inventory.json, art-verification.json, instrument04.txt, ui-cold-restart-completed.*, uiqa3-device-reboot.* |
| REQ79-04: installed UI journey và ca chặn | PASS trên đúng primary07; ca âm tính bổ sung trên QA2 | ui07-final-completed.*, ui07-final-ack.*, ui-stale-blocked.*, uiqa2-wrongtype-blocked.*, uiqa2-airspace-blocked.* |
| REQ79-05: journal fault/kill, background và thu hồi quyền | PASS theo phạm vi runtime | art-journal.txt, art-sigkill-*.txt, uiqa3-background05.*, uiqa3-kill-restart.*, uiqa3-device-reboot.* |
| REQ79-06: bàn giao, fingerprints, cleanup, phạm vi acceptance | PASS | ui-verification-final.json, verification-final.json, module-fingerprints.json; đúng primary07 đã chạy trọn hành trình ở AVD06 |

Các đường dẫn bằng chứng trong bảng nằm tại `evidence/native79/`. Kết quả định lượng: 31 kiểm journal JVM trên mỗi build, 31 kiểm journal ART, các điều kiện outer ART harness ghi trong art-verification.json; 33/33 kiểm workflow/mock host; 25/25 điều kiện đối chiếu cuối trên 36 capsule UI đã semantic-replay (receipt trước17/28 vẫn giữ). Không cộng các phép kiểm lặp thành số chức năng sản phẩm.

Primary package: `vn.rtr.aeris.native79`. APK bàn giao là `native/runtime79/dist/aeris-native79-development07.apk`, SHA256 `b94612c7f32a90703549e89dbb7d6cf42b415145ef7c2ddbfafe03f75dd1d34f`. Đây là development/debug APK ngoại tuyến, không phải candidate/release hay phần mềm bay thực.

Build05 chạy đầy đủ hành trình; ACK được ghi nhưng cursor vẫn0, điểm quan sát đưa cursor1→2, landing mới đóng COMPLETED_MOCK. Force-stop ngay sau hoàn tất giữ cùng HEAD. Cold restart giữ toàn bộ record đã capture và phiên hoàn tất trong history. Các lượt kiểm tiếp tạo phiên mới và chạm quota; không được mô tả current của lần cold restart là COMPLETED_MOCK: current lúc đó là PREFLIGHT_CONFIRM, phiên hoàn tất nằm trong history.

Build07 sửa background storage; primary07 được cài giữ journal cũ và ghi INTERRUPTED_RESTART. Các package QA2/QA3 dùng cùng Java sau chuẩn hóa package và cùng packaged asset hashes (source-equivalence.json), có app-private workspace riêng để giữ nguyên quota/bằng chứng primary. QA2 kiểm sai kiểu/vùng cấm; QA3 kiểm từ RUNNING_MOCK thực → INTERRUPTED_BACKGROUND, rồi một phiên RUNNING_MOCK khác bị force-stop → INTERRUPTED_RESTART; reboot giữ đúng HEAD của hồ sơ đã recovery. Đây là bằng chứng bổ sung của biến thể QA và được tách khỏi lượt exact-primary sau đó.

### Đóng gate đúng primary07

Sau khi mọi app files của AVD cũ đã được xuất/kiểm SHA và runtime scratch được dọn, tạo AVD06 mới từ cùng official archive pin. Không reset hay ghi đè journal cũ. Cài đúng APK07 SHA nêu trên; instrument07-final.txt PASS_APP_DOMAIN_SAVE_LOAD. UI sửa/lưu tên _Final07 → compile → Home/datum → RUNNING_MOCK → ACK cursor0 → hai điểm → COMPLETED_MOCK. Force-stop giữ đúng HEAD13. Phiên mock tiếp theo của chính package07 được bắt đầu rồi đưa ra nền, ghi INTERRUPTED_BACKGROUND HEAD22; reboot giữ đúng HEAD22 và mọi record trước đó, history vẫn giữ phiên hoàn tất. Bằng chứng ui07-final-*.json/.tar/.png và ui-verification-final.json. Không còn thiếu lượt hành trình trên đúng primary07.

## Lỗi đã tìm và sửa trong derivative

1. Android Context filesDir đi qua symlink hệ thống. Canonicalize đường dẫn do Context cấp trước khi dựng DraftStore; không nới guard symlink của journal. Instrument03 FAIL được giữ; instrument04 PASS trong sandbox ứng dụng thật. Run-as ART có UID/app-private nhưng khác sandbox Activity, vì vậy không dùng nó thay cho probe này.
2. WebView101 chưa hỗ trợ `dvh`: thêm fallback `vh` trước `dvh`, đưa thanh thao tác trở lại viewport. Không sửa native44 gốc.
3. Bridge foreground-only từ chối journal ghi INTERRUPTED_BACKGROUND. Chỉ save/load từ trang nội bộ có origin chính xác được hoàn tất ở background; export/file picker vẫn cần foreground. Schema operational=false, authorityRestorable=false, single-writer/quota/expected-head giữ nguyên. Bản sửa được kiểm bằng active mock QA3, không công nhận ca QA2 chưa bắt đầu là phép kiểm background active.

Instrument07 **FAIL Stale expected head**: probe development một lần dùng ROOT trong thư mục instrument04 đã có dữ liệu. Đây là lỗi fixture lặp, guard journal đã từ chối đúng; không ghi PASS cho lần này, không xóa thư mục để làm đẹp kết quả. Lượt AVD06 riêng đã kiểm đúng primary07 thành công với fixture mới, không xóa fixture cũ để làm đẹp kết quả. Nâng probe thành idempotent vẫn là cải thiện harness tiếp theo, không ghi đè receipt FAIL. Probe này không nằm trong hành trình sản phẩm.

## Bảo toàn và dọn dẹp

Không sửa source/candidate/trust/SOT đóng băng, không chạy soak, SITL, SDK/HeraHub, emulator của tác vụ khác hoặc flight command. Không tạo khóa hay chữ ký production. Các lần emulator lỗi layout, missing platform-tools, hết thời hạn30 phút và các assertion QA thất bại đều được giữ nguyên receipt; không cộng thời gian này thành ENDURE.

Đã xuất khoảng3,49MB từ thư mục files của bốn package mới, giữ orphan/pending và symlink fixture ART dưới dạng tar/metadata; không extract hay dereference link. Không phải bản sao toàn bộ Android userdata/cache. Export đầu tiên từ chối symlink fixture; archive đầu cũng được giữ. Chỉ sau verify SHA archive và controller05 dừng sạch mới xóa runtime riêng.

Đã xóa `native/runtime79/.runtime` gồm archive tải, image, emulator và AVD riêng; khoảng6,64GiB được trả lại. Symlink tái sử dụng platform-tools chỉ được unlink, bộ SDK có sẵn giữ nguyên. `.build` từng build được dọn trong finally. Không tạo project copy/tmp, không xóa bằng chứng cũ hay dữ liệu khác. Lượt AVD06 cũng được xuất app files khoảng1,31MB vào appdata-final-primary07.tar, kiểm SHA cùng tất cả archive cũ, rồi controller06 dừng sạch và runtime scratch được dọn lần cuối. Free cuối khoảng40,05GiB; minimum ghi tại controller03/04/05/06 đều cao hơn20GiB. Hai lần dọn trả khoảng6,6–6,7GiB mỗi lần; không cộng chúng thành net free vì đã tải runtime lại để đóng gate. Xem cleanup-final.json và runtime-closure*.json để lấy số byte gốc.

## Gate còn mở và bước kế tiếp

Gate installed mock trên đúng APK cuối đã đóng. Ưu tiên tiếp: workspace mới có kiểm soát thay vì tăng quota/xóa history, probe idempotent; SAF export/import trên Android còn NOT_CHECKED. Nối native với một bridge SITL riêng theo contract và ADR mới: nhận diện aircraft/boot/session, preflight freshness/typed params, mission upload/readback, lệnh có quyền và thu hồi khi disconnect/reboot/background. Chưa mở SDK/HeraHub, camera thật, radio hoặc flight real.

Chưa kiểm: physical power loss/Hera storage, controller input/video thực, payload thật/dual operator live, Android live SITL, bản production. NATIVE79 không chứng minh AERIS đã thay RAGAS trên Hera hoặc đạt/chứng nhận mức DJI.

UI polish còn mở: sau restart bundle bị thu hồi có chủ đích, header có thể hiện DRAFT trong khi review giữ phiên terminal; cần phân biệt rõ trạng thái biên tập với trạng thái hồ sơ, không phục hồi authority chỉ để đổi nhãn.
