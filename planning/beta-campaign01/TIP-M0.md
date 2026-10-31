# TIP-M0 · Khóa đường tích hợp beta

Đây là work package sẵn để giao khi bắt đầu triển khai campaign. Không có runtime
được khởi động bởi tài liệu hoặc lượt lập kế hoạch này.

Outcome: chọn được một source/configuration closure để tạo bản beta tích hợp,
có chỗ sửa recorder và mission/media/crew mà không phá bản đóng băng.

Inputs: `MASTERPLAN.md`, `campaign.json`, commit `e5af80e`, overlay
`snapshots/simstability03/overlay.json`, các report/pins trong `localInputs`.
Không chọn một app mới chỉ vì versionCode lớn hơn hoặc README nói READY.

## Deliverables bắt buộc

1. Module decision map retain/adapt/retire: Native98 direct transport, Workbench,
   MissionBeta, video pipeline và8 source module +1 dependency overlay đã pin.
   Một owner cho mỗi vùng UI/domain; chứng minh route gọi thật và duplicate owners.
2. Release/configuration manifest: target API/ABI/OS/WebView/GPU/codec, host/toolchain,
   AP firmware/parameters, model, dialect, assets, geo sources và dependency closure.
   Chốt loopback/paired LAN boundary, identity và clientB độc lập.
3. Phân loại97 missing tracked paths. Chỉ materialize exact bytes cần cho beta vào
   isolated intake có nguồn/hash; không restore/reset đường dẫn frozen/canonical.
4. Recorder sizing: đo event/frame capacity và WAL/APtrace/media bytes; đề xuất
   lossless segmentation/instrumentation artifact riêng; preflight duration/storage
   model; expected envelope cho30min/2h/8h/24h. Không chạy soak để đo sơ bộ.
5. Freeze28 MUST,13 metric methods, held-out corpus seed strategy và kích thước
   polygon/corridor. Mọi giá trị chưa đủ evidence ghi assumption/owner/gate.
6. Budget trước M1: mock deadline/calls, actual host/AP launch counts, bytes/files,
   stage durations, stop/reconcile và source/preservation snapshots. Giữ20/10GiB,
   reserve256MiB/forecast15s, speedup1/cap500ms/fsync/no frame drop.
7. Verification report: selected closure không thiếu/unlisted executable, model/
   firmware/config không lẫn, source inputs không drift; lịch/effort dự báo lại từ
   actual analysis throughput. Không có BUILD/Android/SITL acceptance claim.

Vai: Contractor chốt lựa chọn và verify; Builder có scope implement về sau;
QA riêng khi có quyền và work package. Một người kiêm vai phải ghi self-review.
Ngân sách đề xuất cho M0: tối đa2 phiên phân tích×4giờ,0 runtime launch,0 install,
0 artifact signing; checkpoint sau4giờ. Hết ngân sách giữ output và nêu blocker,
không tự biến NOT_CHECKED thành PASS. Dự toán1–2 ngày không là deadline tự chạy.

M0 DONE khi cả7 deliverables được kiểm và đủ đầu vào để giao M1 có thể kiểm mock.
Không cần HeraHub/SDK để hoàn thành M0. Kế hoạch không cấp quyền bay thật hoặc
production release, và không yêu cầu hỏi lại những quyền người dùng đã cấp.
