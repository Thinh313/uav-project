# COMPLETION — NATIVE93

18/10/2026 · DONE trong phạm vi engineering · `PASS_ENGINEERING_CORRIDOR_ANDROID_SITL_FAULT_RESTART`.

## Kết quả và phạm vi

Đã kiểm corridor trên APK Android thật trong emulator với ArduPilot4.7.1 SITL; không phải dữ liệu replay giả làm bay thật. Model nhiệm vụ, Home/camera fixture và compiler từ92 được giữ nguyên byte/contract. Người vận hành chọn hành lang KML, inspect và compile ngay trên cockpit. Không có editor KML thứ hai hoặc thay ngầm bằng polygon.

Ba lượt độc lập dùng cùng modelSHA/planSHA/missionSHA, ba boot/container ArduPilot khác nhau: một nominal hoàn tất, một ngắt duplex và một force-stop/mở lại APK khi airborne AUTO. Hai fault đều quan sát GCS failsafe→RTL→ground/disarm qua observer; phải xác nhận riêng mặt đất trước đóng, không tự phục hồi quyền. Hai review lỗi giữ accepted=false và không được cộng thành mission PASS.

## Ma trận nghiệm thu

| REQ/AC | Kết quả | Hành vi và bằng chứng |
|---|---|---|
| 93-01 | PASS | Giữ đúng shared model92/fixture/compiler; Android chọn KML LineString, inspect feature, Home rồi compile/save.34ca mock polygon/corridor và11ca revoke/restart trước SITL. |
| 93-02 | PASS | Corridor Android→preflight4.7.1 chỉ đọc→grant→upload/readback→arm→Home mới→AUTO→takeoff/NAV/RTL→ground/disarm→review.12items/4camera commands/2readback. |
| 93-03 | PASS | Ngắt duplex bằng UI khi đang AUTO airborne; revoke, observer thấy GCS failsafe/RTL/hạ cánh; xác nhận ground riêng rồi đóng. Review gián đoạn, accepted=false. |
| 93-04 | PASS | Force-stop/mở lại APK khi AUTO: foreground lease hết hạn, no-grant/no-resume, model/review cũ nguyên byte. Reboot Android và cold bridge sau đóng giữ data nhưng không khôi phục quyền. |
| 93-05 | PASS | Python MAVLink decoder và receiver raw riêng kiểm ba lượt; một missionAccepted=true/hai false, cả hai lỗi failureVerified=true. Hai gói giả hoàn tất dù rehash bị semantic receiver từ chối. |
| 93-06 | PASS | 62.059đường dẫn cũ qua92 giữ SHA; private files90/91/92 giữ28/94/76file. Runtime/PID/port sạch; sàn20GiB giữ. Không ký production hay promote candidate/ENDURE. |

Bằng chứng chính: `evidence/native93/final-verification.json`, các `*-qualification.json`, từng `runs/<run>/raw.jsonl`/observer/review/closure, `independent-raw-receiver`, `receiver93-final.json`, `receiver-false-completion93.json`, `preservation-after.json`, `runtime-closure.json`.

## Các lượt thực tế mô phỏng

| Kịch bản | Run | Kết quả nhiệm vụ | Raw records |
|---|---|---|---|
| nominal | s7b9e908e5e274ad092e6 | Hoàn tất | 5535 |
| link | s559125cd5f3c458bbbb2 | Gián đoạn · EXPLICIT_DUPLEX_CUT | 4179 |
| restart | sc2b8648dc79d486b9035 | Gián đoạn · NATIVE_FOREGROUND_LEASE_EXPIRED | 2876 |

Mỗi lượt upload12mission items,4lệnh camera và đọc lại2vòng trước/sau arm; oracle derive kỳ vọng từ plan bất biến thay cho hardcode polygon16/6. Camera command có đúng giá trị/frame trong upload/readback, không thay bằng placeholder; không chứng minh camera đã chụp. PARAM_SET=0, ảnh thực=0. Nominal chỉ đạt khi raw có AUTO armed, takeoff geometry, đủ NAV, terminal RTL, fresh ground/disarm và gần Home. Fault receiver kiểm no-forward sau cut, GCS timeout thực quan sát trong khoảng gate4,5–15s, RTL/disarm/nearHome và recovery acknowledgement.

Model SHA `f03cce57852ec9532bdb93a4c169dd851aae1d388759b7f58ec4d5100166f1b6`; planSHA `1112590b7cc09cddf5458b15569585d1ff46bfacefd46b1157f96a6c873e3e7d`; missionSHA `e5b49d10e3e0b624f4b37e56a921e64796e7572e7433bf02d9cb54eb829aa027`. Root workspaceHEAD `95e696bc7f39679ad84d646ae53b8f2b73853b0a5f80e34280bc050da36b69b2` không đổi qua ba lượt; SITL review journal append ba record.

## Restart, bằng chứng và chống kết luận sai

Force-stop APK khi AUTO được watchdog nhận là `NATIVE_FOREGROUND_LEASE_EXPIRED`. Mở lại bằng explicit source/token: native instance mới, grant=false; mọi byte workspace/CURRENT/review cũ không đổi trước khi đóng lượt thứ ba. Observer độc lập tiếp tục ghi sau control cut. Không tự reconnect, tiếp tục mission hay cấp lại quyền.

Sau khi đóng cả ba lượt, reboot Android33 và cold restart bridge: workspace/CURRENT/ba review và SAF ledger nguyên byte; plan/binding/run/grant rỗng ở cold host. Đây là reboot Android khi đã đóng, không phải reboot autopilot khi đang bay. SAF export có provider readback, receiver tái biên dịch KML/model và đối chiếu1tham chiếu trace→HEAD review hiện tại, giữ latest accepted=false. Snapshot cuối có3trace/28event, là committed prefixes chứ không toàn phiên bay.

Hai corpus gói sửa review thành accepted=true/complete=true rồi cập nhật SHA/manifest/contentId vẫn qua byte-integrity nhưng bị semantic replay từ chối. Không tạo success receipt cho chúng. Các gói mutant và raw gốc được giữ, không ghi đè lịch sử.

## VERIFY định lượng

- REQUIREMENT COVERAGE:6/6REQ93-01..06 (100% scope của task này, không phải tỷ lệ trưởng thành toàn sản phẩm).
- SCENARIO RESULTS:3/3kịch bản đạt tiêu chí tương ứng; một mission hoàn tất và hai failure được phân loại đúng.35đối chiếu cuối đạt.
- TECHNICAL HEALTH: build02 và V2/V3 signature verification đạt;45ca protocol/model mock;125file gate;33guard chạy trên Android ART;2ca giả hoàn tất bị từ chối. Không cộng các suite thành một tỷ lệ an toàn bay.
- OVERALL: READY_FOR_SCOPED_ENGINEERING_DELIVERY. Phần ngoài scope bên dưới còn NOT_CHECKED.

## Artifact development

APK `native/native93/dist/aeris-native93-development02.apk` · SHA256 `657c6e8c4e0fbd90d6d1d9105622484817ad1314e64f32e10304791ba065c1ca` · SourceID `0fd778bdd73b45d956369d9be82e5dd0734858c274cef77cf7d926663146de2a`. App riêng `vn.rtr.aeris.native93`, versionCode93. Bản02 là bản duy nhất cài và kiểm trong tất cả ba lượt. Bản01 build host đạt nhưng còn metadata label/version cũ; sửa trước lần cài đầu. Ký development bằng key engineering đã có, chưa production.

Origin native93; bridge8872/AP5903/proxy5904; container93. Tái dùng AVD90/Android33 ARM64/WebView101 và SDK86 đã có, không download/install image. APK vẫn cần host bridge/compiler, explicit `source87=sitl` và token cấp chủ ý; chưa là bản standalone cài lên HeraHub rồi điều khiển Hera.

## Giới hạn và NOT_CHECKED

- Mới một corridor KML tổng hợp, không phải corpus khách hàng rộng, corridor dài/phức tạp/nhiều nhánh, terrain3D hay mapping accuracy thực địa. Envelope KML≤64KiB,10–30m,0,5–2m/s và Home/mặt đất phẳng/camera synthetic khóa.
- Mô hình ArduPilot internal quad; không hiệu chuẩn physics Hera, payload nặng, cảm biến tránh vật cản hay pin/âm thanh/video/camera thật. Gimbal/Phase One/dual-operator hardware chưa kiểm.
- Chưa cắt USB/radio HeraHub, khôi phục transport vật lý, process crash của firmware hay autopilot reboot airborne. Chưa kiểm fault giữa upload hoặc pending commit mới trong task này.
- Chưa standalone parser Android, mọi kích thước/accessibility/thermal/performance/pacing1×, ENDURE24h, production release hay thay Ragas ngoài thực địa. UI giữ layout blur glass cũ; panel engineering còn mã lỗi/notice kỹ thuật, chưa phải product-copy hoàn chỉnh.

## Bảo toàn và vệ sinh

62.059đường dẫn được đối chiếu SHA theo manifests qua92; fixture symlink metadata kiểm riêng. Không sửa source/candidate/ENDURE/canonicalSOT. Private workspace/trace trong appfiles90/91/92 đối chiếu28/94/76file với snapshot gốc. Chỉ xác nhận byte hiện tại, không khẳng định hiện diện liên tục của đường dẫn.

Runtime93 đóng sạch; port8872/5903/5904/5582/5583 không còn listener và bind lại được; PID bridge/emulator đã hết, container thử removed theo controller. Dung lượng thấp nhất quan sát33.57GiB, cao hơn20GiB. Dọn2APK unsigned riêng (6,682,246bytes); `.build` tự dọn, giữ signed APK/raw/fixture/AVD. Không temp copy toàn dự án; đã docker image prune -f, không prune container/volume.

Lưu quyết định tại `decisions-and-observations.json`: driver khôi phục vị trí cuộn panel sau recovery trước nút connect; thao tác đầu trúng vùng không-control, state xác nhận chưa phát kết nối rồi mới bấm control đang thấy. Không retry HTTP control hoặc thêm flight ngầm. Không chạy lại helper ghi đè vào receipt đã đóng.
