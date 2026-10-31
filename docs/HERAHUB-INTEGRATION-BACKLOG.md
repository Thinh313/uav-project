# HeraHub · Backlog tích hợp sau HERA02

12/10/2026. Các mục dưới đây là đề xuất triển khai, chưa hoàn thành. Ưu tiên khảo sát/lập mission. Độ sáng đủ theo chủ việc; chênh nits không nằm trên critical path. Căn cứ và URL tại `HERAHUB-SOFTWARE-RESEARCH.md`.

| ID / ưu tiên | Work package | Kết quả review được | Điều kiện nghiệm thu / phụ thuộc |
|---|---|---|---|
| HI-01 · P0 | Capability contract + probe read-only | Schema riêng cho installed build, window, input, codecs, storage, links và power; giá trị kèm observed/source/unknown và thời điểm | Fixture không có thiết bị vẫn trả unknown đúng nghĩa; chạy trên Android chỉ sau có toolchain/SDK. Không đổi setting/firmware |
| HI-02 · P0 | Input adapter và ownership | Raw trace → axis/button semantic mapping; calibration version, neutral/deadzone/invert, hold/repeat/hot-plug; UI mapping overlay | Mock/replay có lost device và focus change. Channel map thật chờ trace/SDK; không gán mode bay từ hình L/R |
| HI-03 · P0 | Geospatial survey và QGC fixtures | Polygon, camera footprint/GSD/overlap, grid, altitude frame và round-trip manifest | Fixture theo phiên bản QGC xác định; invalid footprint/missing terrain không sinh con số hoặc cao độ giả. Chờ khảo sát format chính thức trước coder implementation |
| HI-04 · P0 | Mission transaction/session | Draft/saved/validated/uploading/uploaded/running/paused/failed; vehicle identity và plan digest; persistence qua restart | Replay ACK không bằng mission readback/observed execution; SITL kiểm upload, camera command và resume sau có transport |
| HI-05 · P1 | Video probe/player spike | Stream descriptor lấy từ endpoint/SDP; candidate matrix; một stream chủ đạo, reconnect/error state | Test H264/H265 nếu thực có; không suy codec live từ file recording. Thêm streams sau đo decoder/thermal và license check |
| HI-06 · P1 | Multi-link telemetry | Per-link age/statistics; active command owner và routing policy; signer capability | Fault replay disconnect/reconnect/duplicate. Chưa chọn dedup theo seq đa link; không hardcode IP ví dụ lịch sử |
| HI-07 · P1 | Offline mission package | Map/terrain footprint, nguồn/version/cache freshness, progress/quota và export/import local | Ra khỏi mạng vẫn review mission đủ dữ liệu; region thiếu hiện thiếu; giải phóng cache có preview, không xóa media/log âm thầm |
| HI-08 · P1 | NTRIP/RTCM bridge | Caster state/correction age/aircraft fix tách riêng; credentials không nằm trong log/export | Replay stale corrections không hiện RTK Fixed giả; route thật chờ SDK/autopilot configuration |
| HI-09 · P1 | Android lifecycle/power | Lưu session; screen-off/boot/process death/reconnect; power A/B tách vehicle | HIL hot-swap trên đúng controller; quyền/lifecycle theo installed/target SDK; mất API hiển thị unavailable |
| HI-10 · P1 | Package/update recovery | Xác nhận package/signing/min-target SDK/ABI; verify publisher metadata và downloaded bytes; phân biệt app/BSP/payload update | Không cài bản không tương thích hoặc downgrade sai chữ ký. Payload OTA guard là tham khảo đúng scope, chưa chứng minh app/BSP rollback |

HI-01–04 có phần contract/replay/fixture chạy được trên checkout hiện tại, không cần chờ số nits, bộ nhớ danh nghĩa hoặc BOM đầy đủ. Các phần chạm thiết bị đi qua SDK/trace đúng revision. Đợt HERA02 chỉ nghiên cứu và cập nhật contract; chưa phát hành APK hoặc đổi firmware.

Design review kế tiếp: bản đồ chiếm vùng chính, thứ bậc địa hình/camera/số liệu rõ, panel cấu hình gọn; một thao tác tương ứng một trạng thái thực. Đề xuất input/telemetry/video không tự tăng diện tích bảng dashboard. Bộ màu trắng/đen/vàng và tỷ lệ vàng đã xác lập tiếp tục áp dụng.

SURVEY02 implements bounded geographic/offline SITL portions of HI-03/04/07 and a native intake matrix. QGC complex-item/native offline lifecycle remain open. Next native scope starts with observed hardware/SDK evidence in HERAHUB-NATIVE-INTAKE.md; browser viewport and BOM claims do not close HI-01/02/05/09/10.
