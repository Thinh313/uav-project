# P2 CREW02: CHƯA NGHIỆM THU (NOT READY)

Ngày 2026-10-20T08:03:23.883726+07:00. Phương pháp: personal Vibecode Kit6.3, Contractor/Builder/QA tách vai. QA là agent AI riêng, không phải nghiệm thu con người hay chứng nhận khai thác.

Đã triển khai Android pilot A và companion payload B ở tiến trình độc lập, danh tính mTLS riêng, JOIN rõ ràng, scope aircraft/camera/gimbal riêng, consent/CAS và thu hồi quyền. Fixture có3camera100/102/101 và2gimbal qua component154. Tuy nhiên P2 **chưa đạt toàn bộ C01–C12**, chưa được chuyển thành production hoặc coi là đã thay Ragas trên Hera.

## Phần có chứng cứ thực tế

- APK development03 đã ký bằng certificate development và cài trên emulator Android13/API33. SHA `8d54b4d8004335ce7dd27b413d3deeb9b60893a3489035d91eca882aefb2dcba`. Native/APK source05 `24e1749957027eced065ca47a3260a457f811f657c4bfc737fc2b15bd61cd020`; host-only source06 `6e144354ee25762fa7e56915623b7222bcf5c2ca58f86bfc21f18a9f1fe0c3f2` chỉ thêm cấu hình resource admission. Không có APK build thứ4.
- mTLS thật, hostname/certificate/SPKI pin và các ca từ chối đã được QA kiểm. Chứng cứ hết hạn/chưa có hiệu lực là từ chối ở bộ nạp admin policy, không phải thử TLS với certificate hết hạn. TLS không biến peer MAVLink unsigned hoặc log hash thành xác thực phần cứng/chữ ký không thể phủ nhận.
- Pilot loss trên APK03: B đang có heartbeat riêng và quyền payload khi A rời foreground. Native đóng với `CREW_PILOT_LOST:BACKGROUND_REVOKE_NO_RESTORE`; pending thành UNKNOWN, mọi quyền đóng. Passive observer thấy GCS failsafe/RTL sau khoảng4,618s trong ca này, rồi ground/disarm gần Home. B không tự nối lại. B đã gửi manager device2, góc−57°/72°, zoom/capture qua đúng route trong run này.
- Process restart thật đổi PID và giữ nguyên hai journal head. QA đối chiếu49 file từ snapshot với manifest51 file sau restart:31 file core raw/workspace/crew/export khớp, không thiếu file cũ; thay đổi thuộc journal chẩn đoán UI. Kernel không tự mở lại flight/crew socket. Tất cả review hiện được bảo toàn là UNKNOWN, không đổi thành accepted.

## Các gate chưa đóng

| Gate | Hiện trạng và phần còn thiếu |
|---|---|
| C07, P1 runtime | Lượt nominal cuối đóng trước bay với `COHORT_SPAN_EXCEEDED`. Mới nhận10/20 reply đúng kiểu; native cohort3303ms vượt giới hạn3000ms. Không có PREFLIGHT đạt hoặc AUTO gửi trong lượt này. |
| Nguyên nhân độ trễ | Reply→request tiếp theo cộng2724ms, có khoảng1117/814/359ms; tổng request-written→reply527ms, TX WAL123ms. Những khoảng chờ trộn delivery/JS/IPC/scheduling, chưa cô lập được fsync hay nguyên nhân host. Không nới guard hoặc gọi giảm reader load là bản sửa performance đã chứng minh. |
| C05/C06 | Chưa có bằng chứng thực cuối cho A gimbal device1 ở góc frozen và B capture trong đúng session vừa nhận consent. Screenshot góc đặt không phải lệnh đã gửi. Consent/focus/zoom và nhiều route đã có chứng cứ ở lượt cũ nhưng không lấp các gap này. |
| C08 | B partition từng được kiểm3009/3010ms ở source03; chưa lặp đủ trên native05 sau sửa đường revoke. Một cut cũ đang bay có grant, một cut pending khác ở mặt đất; không gộp thành một ca. |
| Review accepted | Lượt source03 trước hoàn tất route nhưng review bị từ chối vì track vượt1200 điểm. Bản sửa raw-reference của source05 đạt kiểm offline, chưa được chứng minh bằng nominal accepted thật trên APK03. |
| SAF | Provider/staged gói01 đúng byte nhưng thuộc run cũ `sb58be0f62a1645bdb19f`, khác run mục tiêu `sbf8851e0c6ff4bc48e8d`. Receiver đã trả FAIL; expect01 và ca lỗi giữ nguyên. Lỗi chọn/không xác nhận UI của Contractor, chưa có chứng cứ đây là lỗi product. SAF02 đúng mục tiêu chưa chạy. |
| Cold boot cuối | Có manifest51 file sau force-stop, nhưng coldboot03 chưa khởi động. Cold boot21 file cũ là evidence của giai đoạn APK trước, không thay kiểm APK03 cuối. Final guest private525-file after-check chưa chạy. |
| UI | Home/AUTO từng hiện enabled khi extra-param freshness đã hết, dù guard từ chối trước wire. Đây là UX gap còn mở, phải gắn đầy đủ freshness predicate/reason trước release; không tự refresh/arm/AUTO. |

## Bốn lượt SITL, không cộng hoặc đổi kết luận

| Run | Kết quả |
|---|---|
| `sbf4d3c8a712241d18981` | Source03: AUTO/route/ground và các phép crew hữu ích; review bound fail, UNKNOWN. |
| `sb58be0f62a1645bdb19f` | Source05: extra-param đã quá10s ở Home; AUTO bị từ chối. Sau đó có stall delivery khác, nguyên nhân UNKNOWN; giữ riêng. |
| `sba631d2af67b4408b8a5` | Source05/host06: fresh preflight sau upload, AUTO và actual pilot foreground loss/failsafe đạt trong phạm vi ca; review UNKNOWN đúng nghĩa. |
| `sbf8851e0c6ff4bc48e8d` | Source05/host06: nominal cuối fail cohort trước bay; review UNKNOWN. Không có lượt thứ5. |

Đổi harness sang một raw-tail thụ động và preflight rõ ràng sau upload đã sửa trình tự hết freshness xác định được, nhưng không chứng minh đã sửa stall hoặc độ trễ cohort. Không có retry lệnh/campaign tự động, đổi speedup hay bỏ frame.

## Bảo toàn và tài nguyên

- Đối chiếu cuối đủ70.320 đường dẫn bảo vệ,0 lỗi SHA, gồm source/candidate/ENDURE/P1 và anchor manifests. Đây là byte hiện tại, không khẳng định đường dẫn từng hiện diện liên tục. Canonical SOT không sửa; tài liệu P2 là overlay riêng.
-159 source pins06 còn khớp.4 AP windows,6 companion process và2 emulator đã đóng sạch,0 container/listener còn lại trên các port task. Không có Fly integration hoặc production signature.
- Sàn20GiB được giữ; free tại managed closure khoảng23.15GiB. Gate bổ sung emulator-only đã từ chối: trong120s free giảm81.920.000B (~78,1MiB), AVD byte count không đổi. Gate này là kiểm ổn định bổ sung, không phải đã chạm sàn20GiB. Không hạ gate tiếp hoặc khởi động coldboot03.
- Đã dọn3 unsigned APK trung gian sau khi đối chiếu mọi ZIP payload entry đúng byte với3 development APK giữ lại; dọn5 file pyc task-owned. Các scratch build của Builder đã được dọn theo receipt; không tạo bản sao toàn project trong tmp. Docker image prune cuối thu hồi0B, không prune volume/container. Giữ raw, receipt, các ca FAIL và toàn bộ development APK.

## Bước tiếp theo có phạm vi rõ

Ưu tiên đóng C07 trước khi thêm tính năng: đo riêng native receipt→WAL→main-ready→JS delivery→ý định request tiếp theo và chi phí UI/diagnostic; sửa vùng gây chờ bằng mock/fault injection với giới hạn cohort3000ms, freshness, WAL-before-wire và frame integrity giữ nguyên. Chỉ sau sửa có nguyên nhân và đối chiếu lại budget mới lập campaign nghiệm thu kế tiếp; không tự chạy lần5 của campaign này.

Sau đó kiểm đúng các gate còn lại trong một nominal trên Android: A-device1, consent→B capture, B partition/rejoin không quyền, raw-reference review accepted, SAF đúng mục tiêu và cold boot. Hera/Phase One thật, dual-HeraHub,4payload vật lý,45+phút/Starlink, obstacle avoidance thực và production giữ gate P5/P6 riêng; ảnh thực trong các ca này bằng0.

## Hồ sơ kiểm chứng

- [QA cuối](</Users/os/Downloads/AI technique/aeris/evidence/crew02-qa/ac-final08.json>)
- [Nguồn APK05 / host06](</Users/os/Downloads/AI technique/aeris/evidence/crew02/source-freeze06.json>)
- [Pilot loss thực](</Users/os/Downloads/AI technique/aeris/evidence/crew02-qa/window03-pilot-loss05.json>)
- [Lỗi cohort cuối](</Users/os/Downloads/AI technique/aeris/evidence/crew02-qa/window04-causal06.json>)
- [SAF sai mục tiêu](</Users/os/Downloads/AI technique/aeris/evidence/crew02-qa/saf-targeted01.json>)
- [Process restart](</Users/os/Downloads/AI technique/aeris/evidence/crew02-qa/process-restart-records06.json>)
- [Managed closure](</Users/os/Downloads/AI technique/aeris/evidence/crew02-runtime/managed-closure-final01.json>)
- [70.320 đường dẫn bảo vệ](</Users/os/Downloads/AI technique/aeris/evidence/crew02/preservation-after02.json>)
- [Gate cold boot chưa đạt](</Users/os/Downloads/AI technique/aeris/evidence/crew02-runtime/emulator-only-observation03.json>)
- [APK development03](</Users/os/Downloads/AI technique/aeris/native/crew02/dist/aeris-crew02-development03.apk>)

- [Fingerprint bàn giao](</Users/os/Downloads/AI technique/aeris/evidence/crew02/module-fingerprints-final01.json>) (tạo sau báo cáo, không chứa chính nó).
