# AERIS: milestone sản phẩm, 19/10/2026

Theo yêu cầu chủ việc: task lớn có outcome nghiệm thu, triển khai theo Vibecode Kit6.3 hiện hành. Một lần sửa/đếm test không phải milestone. Không đóng milestone với critical AC còn FAIL/NOT_CHECKED; không đổi mock thành chứng cứ phần cứng. Lịch sử/source/candidate/ENDURE/canonical SOT giữ nguyên. Đây là overlay điều phối mới, không viết lại baseline cũ.

## Mục tiêu và baseline

Thay Ragas trên Hera/HeraHub bằng phần mềm độc lập, tập trung khảo sát và utility inspection, Phase One và nhiều payload, dual operator, UI cảm ứng/joystick cao cấp; simulator phục vụ đào tạo/demo. Cạnh tranh/vượt DJI là mục tiêu phải đo trên cấu hình/workflow xác định, không phải trạng thái hiện tại.

Baseline đã có: APK N98verify development05 với một nhiệm vụ16 item, camera/gimbal tổng hợp một lần, native direct TCP/WAL, link-loss/UNKNOWN/review/process+coldboot. Camera/gimbal lặp còn bị fence; hai actor local không phải hai phiên operator; chưa thiết bị/SDK. N98verify và báo cáo cũ được pin, không chỉnh tiếp tại chỗ.

## Milestone và gate thực

| Milestone | Outcome người dùng | Gate ra bắt buộc | Phụ thuộc/trạng thái |
|---|---|---|---|
| P1 OPERATOR | Một APK dùng được để bay nhiệm vụ và thao tác payload lặp trong Fly chính | UNKNOWN/units đúng; chụp/zoom/focus/gimbal lặp có authority+target+raw; nominal/loss/handover/restart trên Android/SITL và independent decoder; không còn phải restart để thực hiện lệnh mới hợp lệ | IN_PROGRESS, native/operator01, TIP riêng12AC |
| P2 CREW | Phi công và operator payload vận hành trên hai phiên độc lập | Identity/session auth, consent handover, arbitration từng aircraft/camera/gimbal, revoke/loss/partition/reboot; nhiều payload đúng route; UI/video source không chuyển quyền; hai runtime thật trong mô phỏng | Sau P1; không gọi hai card trong1Activity là DONE |
| P3 SURVEY | Kỹ sư nhận KML/QGC, lập polygon/corridor và bàn giao dataset có chất lượng giải thích được | Held-out corpus KML/QGC, toán–địa lý/Home/datum/camera độc lập; preview→compile→readback không sai nghĩa; Android/SITL nominal+fault; review/media/package receiver integrity; ảnh tổng hợp không tính ảnh thật | Sau P1; tận dụng QGC/GEO/HANDOFF/RAGAS54, không làm lại từ0 |
| P4 TRAINING | Đào tạo và trình diễn bay manual/bán tự động/AUTO bằng 3D+audio trong cùng sản phẩm | Điều khiển vòng kín AP/physics; load/CG/wind/collision/sensor failures theo model+seed; renderer/audio không tạo trạng thái giả; tốc độ1×/jitter/frame/fidelity theo máy reference; kịch bản training có review | Sau P1, dùng SIM32/SIMTRAIN52; fidelity Hera cần calibration, không suy từ model reference |
| P5 HERA BENCH | Tay cầm HeraHub và payload mục tiêu điều khiển được trên bàn thử/HIL | Actual firmware/model/config; MCU/HID/calibration/deadman; radio/video source/age; Phase One/lens/gimbal/thermal/LiDAR đúng API; dual-controller và fault; hardware operator witness | Chờ HeraHub/payload/SDK/API phù hợp; chưa có, không tự thay bằng mock |
| P6 CUSTOMER RELEASE | Bản cài thương mại và quy trình giao khách được nghiệm thu | Release integration có review, signed production+SBOM/update/rollback; resource/thermal/endurance trên target; bay kiểm soát do RtR/khách thực hiện; mapping/inspection deliverables; Ragas/DJI A/B cùng điều kiện; formal customer acceptance | Sau các gate có liên quan + quyền release/flight thực tế. ENDURE cũ giữ nguyên, không tự coi PASS hoặc restart |

P2 và P3 là năng lực độc lập cùng dựa P1; utility/Phase One/dual-operator P0 theo Research Partner, survey vẫn là workflow nền. Không hứa ngày giao khi chưa có hardware/team/cấu hình và số đo năng lực.

## Definition of DONE chung

1. Requirement/AC được chốt trước BUILD, output chạy trong sản phẩm, không chỉ contract/module/demo rời.
2. Builder có source, build/runtime pins, raw failures/success, giới hạn và Completion. Contractor/QA kiểm output bằng đối chứng phù hợp; human semantic/flight/customer acceptance vẫn riêng.
3. Tất cả AC bắt buộc PASS, không P0/P1 mở trong scope. Deferred không được dùng để gọi milestone DONE. Scope bị chặn bởi hardware giữ NOT_CHECKED/BLOCKED_DEPENDENCY, không hạ gate.
4. Quality/authority/data-integrity/disk floor không đổi để chạy nhanh; thử có giới hạn, sửa đúng vùng, giữ intermediate có giá trị và failures. Không mở nhiều module thay cho outcome.
5. Báo cáo cho chủ việc theo milestone đạt hoặc blocker cần hành động; chi tiết build/test nằm trong evidence. Không báo DONE từng patch.

## Giá trị và đối chứng

P1 baseline là N98verify one-shot lab workflow: các thao tác hợp lệ tiếp theo bị fence và cần restart. Đo task completion, số thao tác/intent, retry không chủ ý, output/authority correctness trên cùng host/emulator/SITL; đây là technical/task benchmark, không nghiên cứu người dùng thật. P3 có toán/schema/reference và held-out inputs. P4 có nghiệm tham chiếu, profile/version/clock/fidelity. P5/P6 cần actual hardware/operator và customer evidence. Direct LLM/tool-agent baseline không áp dụng cho deterministic flight transport; khi thêm runtime AI assistant, phải so trực tiếp LLM/agent trong cùng task/budget/privacy và không trao quyền bay ngầm.

## Quyền và nguồn lực

Tái dùng quyền development signing, ADB/UIAutomator/root chỉ emulator-5582, localhost SITL. Không production sign/publish, không gửi tin khách, không bay thiết bị thật hoặc chạy campaign24h mới từ plan này. Giữ source/candidate/ENDURE; làm ở namespace cô lập. Admission26GiB cho build/emulator, runtime guard trên20GiB; bounded artifacts, không copy project ra/tmp. Không thêm dependency/compute khi chưa có ích đo được.

## Điều phối6.3

Root làm Contractor/spec/verification. Builder agent riêng implement, QA agent riêng adversarial review. Không gọi tự-review là independent QA, không giả review con người. Bounded delegation được chọn cho vùng authority/protocol có rủi ro, không nhân agent theo số file. Root không viết production code trong phân vai này.
