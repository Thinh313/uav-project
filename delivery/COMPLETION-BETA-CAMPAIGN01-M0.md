# Beta Campaign01 · M0

27/10/2026 · **M0 hoàn tất bàn giao source/configuration cho M1 mock. Beta chưa READY.**

Đã thực hiện7 deliverable M0: chọn đường tích hợp, pin prerequisite, bind dependency
thiếu, phân tích recorder, khóa tiêu chí/corpus, viết TIP/budget M1 và kiểm bảo toàn.
Không mở Android/AP/container, build hay ký trong M0. M1 entry bị từ chối trước
khi viết source hoặc compile vì free disk khoảng18,2GiB, dưới admission20GiB.

## Quyết định kiến trúc có căn cứ

Chọn Native98-derived Android transport/UnifiedCore làm **writer flight/payload
duy nhất**. MissionBeta và SIM-STABILITY03 đang có host writer riêng, chỉ giữ làm
regression/thuật toán tham chiếu, không ghép chạy đồng thời.

Native98 hiện hardcode emulator/endpoint/AP0116… và một Activity; SIM dùng APf2be…
với physics ngoài. Các binding này phải được thay bằng provider/session versioned
có kiểm, không bỏ guard. Mission92 chỉ tái dùng pattern lineage/parser: validator
cũ khóa Home/camera/datum/altitude10–30m/speed0,5–2m/s, chưa là schema beta đa nhiệm.

## Source và prerequisite

- Native source map: **47 Java +104 asset**,114 cạnh static import/resource,
  **0 thiếu trong virtual input map**.151 source/asset khớp SHA của baseline.
- **Sáu asset thiếu** đã bind từ Git vào intake mới, khoảng3,50MB; không phục hồi
  hay ghi đè đường dẫn cũ. Có2 projection definitions,3 font và1 ảnh.
- **16 prerequisite/artifact** được hash lạnh; host ARM/32GiB/10CPU, API33 ARM64
  image, JDK26/Node24/Python3.14 và build-tools hiện có được ghi nhận.
- WebView/GPU/codec thực chưa quan sát. Candidate AP mới chưa build/pin. Những
  trường này chặn actual launch/grant, không được suy từ cold hash.
- Source input closure đã kiểm cho adaptation; **chưa có final runnable beta
  closure**.37 tham chiếu union đã phân loại;6 recipe projection cần materialize
  trước build/runtime mới. Không dùng số source đủ để gọi APK chạy được.

## Nguyên nhân recorder và giới hạn dài hạn

- AP03/AP05 tràn128MiB/2.097.088event và thoát94; AP04 giữ riêng kết quả đạt.
- Clock map1024request hết khoảng341s; stage/timing arrays tăng theo toàn phiên.
- Native session hiện có deadline15phút và raw quota32MiB. Chỉ tăng mmap không
  giải quyết30phút hay24giờ.
- Đã viết contract segmentation/chain/fsync, bounded clock/stage memory, closure
  timing, capacity admission và cleanup khi UI harness lỗi.
- Sizing tách số đo và giả định: primary30phút khoảng9,33GiB;24giờ khoảng448GiB
  với giả định video tổng16Mbps, chưa gồm mọi overhead. Đây là ngoại suy, không
  phải upper bound hoặc soak đã đo. Có thêm backup/handoff thì ngân sách tăng;
  không tự dọn evidence hoặc hạ guard.

## Tiêu chí đã khóa và kiểm chứng

28 MUST,13 nhóm metric,48 nhóm case và18 seed nominal polygon/corridor đã được
commit bằng digest trước implementation. Đây là target/corpus design, **chưa là
28 requirement hoặc48 case đã đạt**. M1-MOCK TIP đã có phạm vi, fault injection,
receiver và ngân sách; actual build/runtime có gate riêng.

Contractor kiểm lại source/asset/toolchain hashes, dependency bindings, nguyên vẹn
17.117 định danh baseline và1.620 mục seal SIM-STABILITY03: không drift.97 tracked
missing và165 missing trong baseline vẫn được giữ nguyên. QA agent riêng chỉ
review profile do root viết; không gọi toàn bộ audit là independent human review.

Không có file dữ liệu cũ bị xóa. Đã dọn các thư mục rỗng do lỗi đường dẫn tạm của
analyzer tạo và thư mục M1 entry rỗng; chi tiết cleanup trong receipt. Không tạo
bản project trong/tmp, tải SDK/dependency hay thay source/candidate/ENDURE.

## Bước đã sẵn để tiếp tục

[TIP-M1-MOCK](../planning/betaintegrated01/TIP-M1-MOCK.md): triển khai journal phân
đoạn, bounded clock và terminal lifecycle/provider validation; mock/fault trước,
chưa cần thiết bị. Entry mới giữ20GiB, runtime floor10GiB+256MiB/forecast15s;
không launch khi admission chưa đạt. Toàn M1 còn phải ghép native provider và kiểm
Android–AP/link/reboot/30phút trên candidate mới.

- [Progress](../planning/betaintegrated01/PROGRESS.json)
- [Quyết định kiến trúc](../planning/betaintegrated01/m0/DECISIONS.md)
- [Virtual source closure](../planning/betaintegrated01/m0/dependencies/native98-virtual-input-closure.json)
- [M0 verification](../evidence/betaintegrated01-m0/verification-final01.json)
- [Admission M1](../evidence/betaintegrated01-m0/m1-admission-refused01.json)
