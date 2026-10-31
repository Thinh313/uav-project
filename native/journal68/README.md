# JOURNAL68 — hồ sơ DUAL67 bền vững, quyền khởi động rỗng

16/10/2026. Adapter host/mock cô lập, sử dụng Arbiter DUAL67 chỉ đọc. Mở [Pilot](http://127.0.0.1:8823/pilot) và [Payload](http://127.0.0.1:8823/payload) trong hai phiên riêng. Không có kết nối UAV hay camera thật.

Từ thư mục aeris, lần đầu tạo một store mới bằng `node native/journal68/server.mjs --initialize`; các lần sau dùng `node native/journal68/server.mjs`. Store hiện tại `.local/journal68/preview01` đã được tạo: không khởi tạo lại. Không chạy instance thứ hai trên cùng store hoặc cổng; không xóa writer.lock. SIGTERM/SIGINT đóng có quản lý; SIGKILL chỉ dùng trong fixture kiểm thử.

Kết nối hai operator, cấp quyền theo thao tác rõ ràng rồi gửi capture mock. Journal sync INTENT trước mock dispatch, sync OUTCOME trước trả kết quả. Khi restart, mỗi run có boot và engine mới: token, station, grant và đề nghị bàn giao đều rỗng. Hồ sơ trước restart xuất hiện trong mục lịch sử chỉ đọc; owner cũ không có quyền hiện tại. Pending intent không được chạy lại. ACK và metadata mô phỏng không chứng minh phơi sáng hay ảnh thật (`actualImages=0`).

WAL UTF8 có length/sequence/previous/SHA; catalog ràng buộc run, boot, OPEN, source và digest phục hồi. File/directory được fsync khi tạo và append. Run cũ không được append sau restart. Tail thiếu giữ nguyên, kết quả chưa đủ ghi UNKNOWN; lỗi hash/schema/semantic/catalog/source chuyển HOLD chỉ đọc. Không tự retry, sửa tail, truncate, xóa hồ sơ hay giải phóng quota. Missing seal trên run đang sống chỉ có nghĩa live/unsealed, NOT_FINAL.

OS advisory lock dùng Python stdlib fcntl, không cài thư viện. Parent chết đóng pipe và giải phóng flock; inode writer.lock được giữ. Mất lock hoặc lỗi IO fence phiên hiện tại. Giới hạn mặc định: 16 KiB/record, 8 MiB/run, 16 MiB/store, 32 run; admission cần dự phòng 64 KiB và hai frame, disk cần sàn 20 GiB cộng 32 MiB. Đây là dịch vụ kiểm thử có giới hạn, chưa nghiệm thu soak hay retention lâu dài. Source thay đổi sẽ chặn phục hồi tự động; chưa hỗ trợ schema migration.

Kiểm lại bằng tên run mới (không ghi đè bằng chứng):

```sh
J68_TEST_RUN=next01 node --test native/journal68/journal.test.mjs
J68_CORPUS_RUN=next01 node native/journal68/corpus-qa.mjs
J68_HTTP_RUN=next01 node native/journal68/http-qa.mjs
```

HTTP QA cần cổng 8823 trống; dừng sạch preview do mình quản lý trước khi chạy, không dừng các preview/ENDURE khác. Kiểm dung lượng trước mọi vòng mới. Fixture fault và snapshot được giữ làm bằng chứng, không phải bản sao toàn dự án.

Nghiệm thu hiện tại: 23 unit, 22 corpus, 18 HTTP, 7 quan sát browser desktop đạt; snapshot replay đạt. Chỉ kiểm fsync và process crash trên host. Chưa kiểm mất điện vật lý/F_FULLFSYNC, Android/HeraHub, storage phần cứng hoặc xác thực operator sản xuất. SHA chain không tự chứng minh danh tính nguồn hay chống rollback đồng bộ cả store nếu không có anchor độc lập. Không build APK, ký mới, chạy SITL/emulator hoặc sửa source/candidate/ENDURE.
