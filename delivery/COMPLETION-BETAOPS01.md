# Beta Operations01: tìm hồ sơ, kiểm raw và bàn giao

26/10/2026. **READY-with-deferred trong phạm vi bàn điều hành beta host, receiver và mock/replay. Không phải nghiệm thu toàn sản phẩm beta hoặc Hera thật.** Không yêu cầu người dùng dọn thêm dung lượng; không build APK, mở Android–SITL/emulator, tải dependency hoặc ký mới trong lượt này.

## Kết quả sử dụng

Đã có [Beta desk](http://127.0.0.1:8900/) để nhập gói SAF Beta05 hoặc manual02, tìm/lọc lịch sử, phân biệt nguồn SITL/mock/scripted, xem kết quả nhiệm vụ riêng với tính toàn vẹn, kiểm lại raw và xuất đúng byte gốc. Lịch sử còn sau restart và không phục hồi quyền. Các lượt launch Beta05 được tập trung ở cùng trang, có lỗi/thiếu closure riêng; metadata đóng runtime không được coi là nhiệm vụ PASS.

Mở lại bằng `delivery/beta-operations01/Open Beta Desk.command`. Giữ Terminal; tự đóng sau 30 phút hoặc Ctrl+C. Chỉ bind127.0.0.1:8900. Cockpit, Debrief và Manual là link tới các dịch vụ hiện có, cần mở bằng launcher riêng; desk không tự khởi động runtime hoặc phát lệnh ARM/AUTO/payload. Hướng dẫn ở `delivery/beta-operations01/README.md`.

## Phạm vi nghiệm thu

| AC | Kết quả | Bằng chứng |
|---|---|---|
| Lịch sử nhiều lượt | PASS metadata scope, 6 lượt hiện có; closure và lỗi tách khỏi flight outcome | http03/results.json; browser screenshots/AX; catalog fixtures |
| Receiver chung hai format | PASS: tính lại raw/model, giữ SITL/manual riêng, reject format/state/grade/scope sai; ảnh thực0 | tests03/results.json; http03/auto-summary.json |
| Persistence/quota/pending | PASS scoped: source fsync trước commit receipt, một writer, fault giữ pending/orphan, không resume/dọn; restart giữ byte và quyền không phục hồi | tests03/results.json; HTTP restart; preview-restart-before01.json; static-final01.json |
| Bàn điều hành UI | PASS desktop đã quan sát + mock hành vi; file picker, lưu file browser vào ổ nhận, mobile/touch DEFERRED | ui02.json; browser01.json; browser-final02.ax.txt; screenshots |
| Kiểm chứng/bảo toàn/tài nguyên | PASS theo phạm vi code/HTTP/replay; không là chứng nhận bay hoặc chất lượng tổng thể | verification-final01.json; preservation-betaops01-before/after.json; handoff-final01.json |

**31 nhóm kiểm tự động cuối:** 14 storage/receiver/fault, 10 UI Node VM/DOM double, 7 HTTP localhost thật. Các lượt lặp không cộng thành nhóm mới. HTTP dùng worker thật, filesystem thật và hai format; không bay mới. CLI receiver ở tiến trình lạnh tính lại gói từ original. Cùng assistant chuyển vai theo Vibecode6.3, không có QA con người độc lập.

Browser hiện đã hoạt động. Kiểm thật: mở hồ sơ SITL mẫu, tìm kiếm không kết quả và xóa lọc, đổi theme sáng/tối cùng icon sun/moon, mở panel giới hạn, đọc metadata lỗi/closure, reload trang và restart host rồi refresh/reverify raw. Ảnh desktop1265×720 được lưu. Không quan sát chồng đè ở các vùng đã xem; chưa suy ra pixel-perfect cho mọi viewport.

Bấm xuất qua browser đã hiện trạng thái giao gói tải xuống. Chưa xác định file được browser lưu ở đâu; đường dẫn Downloads dự kiến không có file tại lúc kiểm. Không gọi việc này là đã nghiệm thu receiver trên ổ đích. Qua HTTP, body xuất khớp đúng byte gói gốc và đã được receiver process riêng tính lại. File picker native chưa kiểm được: CUA không cho điều khiển app Codex; không dùng công nghệ khác để vượt hạn chế này, không yêu cầu người dùng bật quyền lặp.

## Dữ liệu đối chiếu và thuật toán

Dùng lại gói SAF Beta05 đã có, SHA256 `f38e71a7afd5c34dbfafa05f08579fa0a18bbd6f7f90bb0d58171c9c78295713`,7.244.638byte,6.341raw record. Worker tái dùng analyzer COACH01 và receiver Beta05 để dựng lại model/plan/telemetry/video từ source. Kết quả nguồn là SITL đã ghi, video PASS theo bộ đo trước,1ảnh tổng hợp,0ảnh thực. Cảnh báo vị trí ngoài miền mặt phẳng tham chiếu2.500m vẫn được giữ, hiển thị bằng tiếng Việt trong giới hạn, không suy ra độ chính xác khảo sát thực.

Gói manual tham chiếu giữ riêng kind/source, không dùng để chứng nhận AUTO hoặc người lái. Nhãn source trong gói vẫn là khai báo chưa được xác thực; SHA/recompute không là chữ ký. Bảy entrypoint verifier có fingerprint để nhận biết thay đổi phép tính; đây không phải inventory supply-chain đầy đủ. Nếu khác kết quả/fingerprint, export bị từ chối, không tự viết lại receipt cũ.

Tính lại chạy ở worker riêng, một việc, không hàng đợi/retry tự động, timeout30s, old-generation256MiB và young-generation32MiB. Đây là hạn mức V8, không phải số đo toàn bộ RSS hay cam kết FPS. Lịch sử catalog kiểm SHA source/receipt, không recompute mọi raw mỗi lần refresh; UI ghi rõ và export luôn recompute. Nguồn fsync rồi receipt được publish exclusive; lỗi/pending giữ nguyên, không tự xóa hoặc tiếp tục transaction.

## Các lỗi và sửa được giữ rõ

- tests01 đạt11/12: phép sửa string không khớp khoảng trắng của JSON nên không thực sự thay đổi bytes. Sửa fixture bằng parse/mutate; tests02 đạt14/14, tests03 kiểm thêm receipt đã reseal sai actualImages vẫn bị chặn. Không sửa gói gốc để hợp thức phép thử.
- Trong rà soát UI, token cũ sau host restart khiến thao tác từ chối. Đã thêm lấy token mới ở nút refresh, không tự gửi lại POST; kiểm bằng mock và browser thật. Khi bootstrap chưa có token, nút import/example bị khóa.
- http01 đạt7/7. http02, chạy sau tăng kiểm scope receipt, đạt6/7; negative Origin với body manual lớn nhận `write ECONNRESET`. Không có log status/cause đủ để khẳng định chính xác socket lịch sử. Giữ receipt lỗi. Harness http03 dùng body nhỏ để cô lập Origin, ghi từng route/status/body-size;25request,7/7 đạt, Origin/Host403, format400, flight/traversal404. Không thêm retry hoặc đổi server để bỏ guard; không tuyên bố đã chứng minh mọi kiểu stream bị từ chối đều trả response êm.
- Sau kiểm trực quan, thay footer “chưa kiểm trực quan” bằng “chưa nghiệm thu thiết bị thật”, dịch cảnh báo địa lý và sửa sun/moon action label. ui02 kiểm hành vi trên source cuối; các ảnh đầu là giai đoạn trước. Guard receipt cuối được kiểm lại bằng HTTP03 và UI raw reverify sau restart phiên cuối.

## Giá trị và khoảng trống beta còn lại

Bàn điều hành giảm việc ghép thủ công đường dẫn run và gọi receiver theo thiết kế; chưa đo thời gian/công sức người dùng đối chứng. Không đưa LLM vào runtime; không có tuyên bố lợi thế AI hoặc hơn DJI. Đây là phần hoàn thiện vận hành và evidence của beta, không thêm mô hình vật lý hoặc điều khiển bay mới.

Còn gate riêng: hành trình Android–SITL trên phiên bản tích hợp này chưa chạy lại; nhiều thiết bị/video dài hạn, file picker/download thực, điện thoại/HeraHub, camera/gimbal/radio/Phase One/thermal thật, input HID, phơi sáng/GNSS vật lý, UI ngoài desktop hiện tại, installer laptop sạch, production signing và thực địa. COACH01/COACH02 pages chưa được nghiệm thu lại trực quan trong task này chỉ vì browser đã mở được trang desk.

## Bảo toàn và dung lượng

Mã mới tách ở pilot/planning/evidence betaops01 và delivery/beta-operations01. Không sửa Beta05, COACH01/COACH02 hoặc các source/candidate/canonical SOT/ENDURE đóng băng. Giữ nguyên133member handoff COACH02. Preservation trước/sau khớp17.117định danh quan sát;165đường dẫn thiếu từ trước vẫn thiếu, không phục hồi hoặc khẳng định hiện diện liên tục. Không chạy hoặc kết luận nghiệm thu ENDURE mới.

Gate20GiB entry /10GiB floor +256MiB giữ nguyên, inbox64MiB/16gói, gói32MiB; không làm đầy ổ để thử boundary. Mọi lần kiểm HTTP8901 đã đóng. Preview cuối PID19546 giới hạn30phút, được giữ để bàn giao, chỉ là runtime đọc/replay. Workspace `evidence/betaops01/workspace01` có gói mẫu đã nhập qua browser và có thể thay đổi khi người dùng nhập tiếp; handoff không khóa store sống này, có snapshot hash trước restart.

Không project copy/tmp, buildcache, venv, SDK install, download dependency hoặc Docker. Không có scratch được tạo cần dọn; giữ fixture fault/pending làm bằng chứng. Không commit/push/phát hành ra ngoài. Bản kê source/evidence đã đóng: `evidence/betaops01/handoff-final01.json` + `.sha256`; trạng thái và ngân sách thực ở `verification-final01.json`.
