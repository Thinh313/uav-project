# AERIS Beta Workbench03

Ngày kiểm: 24/10/2026. **PARTIAL, chưa phải Beta Android–SITL dùng được.**

Đã hoàn tất phần source và nghiệm thu mock được phép trong ngân sách hiện tại. Chưa có APK của source này, chưa kiểm ART/SAF và chưa chạy ArduPilot. Không được dùng các kết quả dưới đây để kết luận sẵn sàng điều khiển Hera hoặc thiết bị bay thật.

## Kết quả sản phẩm

Một cockpit mới cô lập ghép Workbench, preflight, Fly giao thức mock, payload, video nguồn host và review. Model KML, profile, plan, mission và hồ sơ liên kết bằng hash; camera/video có run, boot, config riêng. Cấp quyền và xác nhận Home trước/sau arm vẫn là thao tác riêng. Mất link, reboot, ra nền và restart không tự khôi phục quyền.

Shell Java được chiếu từ Workbench02 vào package `vn.rtr.aeris.betaworkbench03`, main origin 8894, media subresource loopback 8893. Sửa nhánh lỗi I/O SAF để hoàn tất và giải phóng đúng operation đang sở hữu; request bị từ chối, sai phiên hoặc trả muộn không giải phóng operation khác. Đây là bản sửa source, chưa phải chứng nhận lỗi SAF đã hết trên Android.

Phiên CUA cuối quan sát được: polygon → duyệt phương án → kích hoạt → xác nhận Home → preflight → cấp quyền → upload/readback → arm → duyệt Home sau arm → AUTO mock → ground/disarmed → đóng review. Gimbal có MOCK_READBACK; một frame video tổng hợp được lưu cùng receipt và tham chiếu telemetry host. Reload giữ nhiệm vụ và lịch sử, đồng thời yêu cầu kích hoạt mới.

## Ma trận nghiệm thu

| Gate | Chứng cứ | Trạng thái và giới hạn |
|---|---|---|
| B1 SAF busy và native store | `java-check01.json`, `native-projection01.json` | 19 ca host store đạt, owner gate đạt, Java typecheck đạt với Android37 stubs. Lỗi I/O/cancel/busy/session được kiểm bằng mô hình owner và assertion nhánh source. **Chưa chạy SAF/ART.** |
| B2 Model và định danh chung | `integration06/results.json` | Kiểm profile hẹp, không clamp, Home/model/plan sai bị từ chối; polygon và corridor dùng cùng compiler. Mock đạt. |
| B3 Flight/payload/restart | `integration06/results.json` | **8/8 nhóm đạt**: nominal, corridor, mất link/reboot với payload lease, background, sai model/đóng sớm, host close khi command pending. Peer MAVLink mock, không phải ArduPilot. |
| B4 Video host → cockpit | `browser06/media/report-01.json`, `receiver-verification01.json` | 885 mẫu / 30.000,5 ms: **29,50 FPS**, P95 upper bound **40,45 ms**, first fresh-ready **285 ms** từ thao tác mở viewer. IAB nhận và giải mã VP8 từ nguồn tổng hợp riêng. Chưa đo physical latency, app/codec cold-start hay Android. |
| B5 Hành trình và lưu hồ sơ | `browser-qa01.json`, `browser07`, ảnh review | UI mock đi hết hành trình, lưu workspace mock, reload giữ dữ liệu; raw và ảnh được kiểm hash. **Chưa nghiệm thu Android, SAF hoặc nhiệm vụ AUTO SITL đồng thời video/payload.** |
| B6 Guard và bảo toàn | `preservation-after.json`, `admission-final01.json` | **14.025 mục gốc + 80 mục Workbench02 không đổi**. Giữ guard và sàn 20 GiB; admission thực không đạt. Không ký mới/cài SDK/tải dependency. |

HTTP handler đạt **5/5 nhóm** trên source coordinator hiện tại: Host/Origin/CSRF, compile và UI tích hợp, import/validate workspace qua mock provider, từ chối caller tự bật SITL, sai đường dẫn capture và report spoof. Có **13 nhóm** kiểm fence/deadline/interlock đạt; không cộng các nhóm này thành số lần nghiệm thu sản phẩm.

Review cuối chứa run `m20406829a3ff4a398a18`, **4.757 raw records**, raw head `7c02b5db52cdcea093a1d219e853b6f08a8b3bffa5de0ea63cf5bcf23301467c`, workspace WAL 17 records và một JPEG 54.075 byte. Receiver chỉ đọc đã đối chiếu chain, SHA, model/run/boot và receipt. `actualImages=0`, thời điểm phơi sáng vật lý UNKNOWN, vị trí không đạt chuẩn survey. Không tự tính frame tổng hợp này vào độ phủ khảo sát.

## Các lỗi và giới hạn được giữ công khai

- Lượt đầu thiếu virtual loader, một fixture timestamp không nguyên microsecond và một thử FIFO bị backlog: giữ nguyên `integration-loader-failure01.json`, `integration01`, `integration04`. Sau sửa, lượt cuối `integration06` đạt; không gộp thành chiến dịch liên tục.
- Các lượt UI trước có lỗi heartbeat/pending và Home sau arm quá tuổi. Sửa fence trả muộn, giữ deadline 1.000 ms và cadence 750 ms; không gia hạn guard. Peer mock có FIFO hữu hạn 256 packet và bỏ burst telemetry thừa khi hỏi read-only; periodic 200 ms và phản hồi lệnh vẫn còn. Đây là **thay đổi fixture mock có công bố**, không chứng minh tối ưu ArduPilot hay giữ đủ frame physics.
- `browser06` đo video đạt nhưng **đóng review lỗi** do đọc `link.socket.peakDelivery` sau `close63()` đã xóa socket. Raw 25.531 records vẫn kiểm được; không có review committed và không công nhận lượt này hoàn tất. Khi dừng có `CAPTURE_BLOCKED`, exit 1, giữ nguyên dữ liệu. Sửa bằng giữ tham chiếu socket trước close; `browser07` đóng review và host sạch, exit 0.
- Thống kê video 30 giây thuộc browser06 trước bản sửa đóng review; không phải bằng chứng cả nhiệm vụ thành công trên source cuối. Browser07 quan sát video chạy trong cùng phiên và capture thành công, nhưng chưa đo đủ thời gian airborne overlap. Sidecar ghi rõ `BINDING_RECORDED_AUTO_OVERLAP_NOT_CHECKED`.
- Sau browser07 còn siết predicate hiển thị nút Arm khi preflight stale; 13 nhóm fence cuối đạt, chưa chạy lại toàn bộ UI journey cho thay đổi hiển thị cuối này. Backend đã từ chối preflight stale trong lượt UI.
- Chỉ soi bố cục review 1280×720 ở lượt này: không tràn ngang trang, panel cuộn nội bộ, hai đảo điều hướng tách header/footer. Không tuyên bố đã kiểm mọi breakpoint/popup. Publisher còn chuỗi hiển thị cổng cũ 8873, dù endpoint thực là 8893.
- Export workspace vẫn theo schema Workbench gốc; **chưa đóng gói toàn bộ raw/video/capture mới vào gói Beta portable qua SAF**. Import mock kiểm semantic/hash không thay cho Android SAF hay receiver của gói đầy đủ.

## Gate còn lại để đạt Beta tích hợp

Admission cuối đo **27,9236 GiB**, dưới mức entry **29 GiB**. Không khởi động APK/emulator/SITL. Gate gốc giữ nguyên: 31 mẫu/30 giây, mức giảm tối đa 256 MiB, runtime 28 GiB và forecast 15 giây, hard floor 20 GiB. Mức trống trên 20 GiB chỉ đủ cho công việc nhỏ, không đủ ngân sách vào campaign này.

Ngoài tài nguyên, coordinator mới hiện **chỉ cho mode mock**, cố ý từ chối SITL không được qualification. Cần ghép transport thật, admission/controller và pin source vào chính coordinator này, rồi tạo APK development của source cuối. Không được chạy campaign G17 cũ rồi dùng kết quả đó chứng nhận ứng dụng mới.

Thứ tự tiếp theo: (1) hoàn thiện đường actual native–SITL và bundle raw/media/review có receiver xác minh; (2) kiểm mock/fault cho hai phần đó; (3) đạt admission thực rồi build development; (4) kiểm SAF busy thành công/hủy/I/O lỗi/request cạnh tranh trên Android; (5) chạy AUTO cùng video/payload, thu hồi quyền khi mất link/reboot, lưu/restart và xuất SAF/kiểm nhập độc lập trên cùng source/APK. Chỉ tất cả gate bắt buộc đạt mới đổi trạng thái Beta. Hera/Phase One thật và production vẫn là gate riêng.

## Bàn giao và vệ sinh

Source mới nằm riêng trong `pilot/betaworkbench03`, `native/betaworkbench03`, `planning/betaworkbench03`; chứng cứ ở `evidence/betaworkbench03`. Không sửa canonical SOT, source/candidate đóng băng hoặc lịch sử ENDURE. Các đường dẫn thiếu từ trước được bảo toàn theo baseline, không tự phục hồi hay suy ra hiện diện liên tục.

Preview QA PID 71008 đã dừng sạch, cổng 8893/8894 hết listener; hai tab IAB của tác vụ đã đóng. Compiler scratch `native/betaworkbench03/.check` đã xóa, fixture và tất cả lượt lỗi giữ nguyên. Không tạo project copy trong `/tmp`, distDir, Docker image hay APK. Các preview khác của người dùng không bị dừng. Manifest bàn giao có SHA để phát hiện drift, **không phải chữ ký phát hành phần mềm**.

![Review mock đã đóng và ảnh tổng hợp liên kết](../evidence/betaworkbench03/review-final-browser07.png)
