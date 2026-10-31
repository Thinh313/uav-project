# ARCHIVE69 — lưu trữ và quota cho bản sao JOURNAL68

16/10/2026 · Host/mock only. [Mở giao diện](http://127.0.0.1:8824/).

Chạy từ aeris: `node native/archive69/server.mjs --initialize` duy nhất khi tạo workspace mới. Workspace bàn giao `.local/archive69/preview01` đã tồn tại: các lần sau dùng `node native/archive69/server.mjs`. SIGTERM/SIGINT đóng sạch; không xóa writer.lock, không reset hoặc khởi tạo lại. Cần Node và Python stdlib có sẵn, không install/build.

Luồng: thêm bản sao snapshot68 đã pin → chọn thế hệ → xuất gói → tải gói → nhập và đối chiếu bên nhận → xem phương án dọn → đọc danh sách/bytes và câu xác nhận → người dùng đánh dấu, nhập đúng câu và xác nhận nếu muốn dọn. Không bắt buộc dọn để hoàn thành xuất/nhập. Demo được bàn giao với toàn bộ hot data còn nguyên, chưa xác nhận dọn. Xác nhận đúng ID/digest, chỉ dùng một lần, hết hạn sau60 giây; restart xóa ticket khỏi bộ nhớ. UI làm mới cũng xóa phương án đang xem.

JOURNAL68 gốc không đổi. Catalog68 liên kết SHA/status của mọi run trước, nên không được xóa riêng WAL. Module này chỉ sở hữu các thế hệ snapshot nhỏ dưới ARCHIVE69, gồm store.json/catalog.wal/đủ WAL. Nó không thu hồi quota live68, không nối writer68, không rotate hay migration source đóng băng. Cần gate riêng cho live rotation. Snapshot có run chưa seal không chứng minh crash hay hoàn tất bay. Pending/tail giữ nguyên và không chạy lại; lịch sử owner không là quyền hiện tại, actualImages luôn0.

Gói canonical JSON có giới hạn24MiB, manifest SHA từng file và toàn body, source/corpus/catalog binding, Base64 strict, tên file allowlist. Gói không phải chữ ký hoặc chứng cứ danh tính. Bên nhận decode riêng, kiểm byte/catalog và replay semantic bằng Arbiter68 đã pin; ghi file+directory fsync rồi mới có receipt DONE. Namespace bên nhận chỉ đọc; không bootstrap engine có quyền điều khiển.

Quota workspace mặc định32MiB; store16MiB, tối đa32 run, audit512KiB/record32KiB. Kiểm cả hot, exports, receiver và audit; xuất cần reserve đủ receiver và audit, mọi mutation giữ sàn20GiB+32MiB. Đầy thì HOLD/no eviction. Thu hồi chỉ tính bytes hot thực sự bỏ; package/receiver/audit/identity markers vẫn ở disk. Dời dữ liệu trong cùng ổ không tự giải phóng dung lượng vật lý. Chính sách quota này dành cho fixture nhỏ, chưa là cấu hình vận hành dài hạn.

Operation BEGIN/DONE là file exclusive, SHA-chain, file/directory fsync, một OS flock writer. Crash giữa export/import giữ PENDING, không công bố receipt hoàn chỉnh. Crash giữa cleanup giữ phần chưa dọn; restart không tự xóa tiếp. Chỉ với package và receiver còn kiểm đạt mới được lập phương án mới cho phần còn lại và yêu cầu xác nhận mới. Package/receiver/audit không có endpoint xóa. Unknown file, symlink/hardlink, drift, thiếu file, source đổi hoặc audit lỗi đều chặn mutation. Không tự truncate/repair/retry cleanup/overwrite receipts. SHA nội bộ chưa chống được đối thủ sửa đồng bộ cả store và audit; chưa kiểm powercut/F_FULLFSYNC hay Android storage.

Kiểm lại với tên run chưa dùng (giữ receipts cũ):

```sh
A69_TEST_RUN=next01 node --test native/archive69/tests.mjs
A69_CORPUS_RUN=next01 node native/archive69/corpus-qa.mjs
A69_CRASH_RUN=next01 node native/archive69/crash-qa.mjs
A69_HTTP_RUN=next01 node native/archive69/http-qa.mjs
```

HTTP QA cần cổng8824 trống: dừng sạch riêng preview ARCHIVE69 trước khi chạy; không dừng JOURNAL68/ENDURE hoặc preview khác. Cleanup chỉ được thực thi qua xác nhận explicit trong fixture mới của các phép kiểm. Không xóa bằng chứng để chạy lại. Kiểm disk trước mọi vòng; artifact budget48MiB cho task, không clone/copy project hay tạo scratch install.

Phạm vi chưa kiểm: mất điện vật lý, Android/HeraHub/SDK, operator authentication sản xuất, replica ngoài máy/chữ ký/anchor rollback, schema migration và retention dài hạn. Không cần SDK, APK, SITL/emulator hay ký mới cho module này.
