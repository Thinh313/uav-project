# ARCHIVE69 — quota/archive cho JOURNAL68

16/10/2026 · Contractor specification → Builder implementation → Verify, một agent chuyển phase; không tuyên bố independent review. Theo transfer Vibecode 6.3. User đã ủy quyền module/mock, không hỏi lại để tạo local preview. Không tự thực thi dọn dữ liệu thật.

Scope mới: native/archive69, evidence/archive69, .local/archive69, TIP/ADR/report mới. JOURNAL68/DUAL67/source/candidate/SOT/ENDURE read-only. Floor20GiB+32MiB headroom; tổng artifact mới <48MiB; không install/build/APK/SITL/emulator/signature.

- A69-01: đọc/kiểm snapshot JOURNAL68 có pin và semantic replay; copy nhỏ sang thế hệ do workspace mới sở hữu. Không copy project hay nối writer. Giữ trạng thái clean/unclean/pending/tail, không suy ra completion/ảnh thật/quyền.
- A69-02: bounded canonical archive chứa manifest/data SHA/source/catalog và đủ mọi run của thế hệ; xuất chỉ sau kiểm. Không xóa riêng run vì parent catalog ràng buộc toàn thế hệ. Gói không chứa session token hay quyền có thể phục hồi.
- A69-03: bên nhận kiểm byte/manifest/path/schema/source/catalog/semantic độc lập với trạng thái xuất; nhập sang namespace chỉ đọc mới; chỉ phát receipt sau file+directory sync. Không tự cấp quyền, không publish partial package.
- A69-04: quota tách hot/exports/receiver/audit và reserve đủ export+import; đầy thì chặn, không tự prune. UI hiển thị reclaim chỉ phần hot, không gọi đó là tăng free host vì archive vẫn chiếm disk.
- A69-05: lập plan binds generation/export/import/byteSHA/exact list/revision, challenge một lần có hạn và phiên server. Confirmation cụ thể mới dọn managed hot generation. Recheck cả package/receiver/source và disk ngay trước từng xóa. Mặc định không dọn, không xóa original JOURNAL68/snapshot/evidence/exports/receiver/audit.
- A69-06: append-only fsynced operation receipts, single writer, restart không tự thực hiện pending cleanup; đang dọn dở chuyển HOLD và cần plan/confirmation mới. Không tự retry IO, xóa lock, overwrite receipt, truncate hoặc reset quota metadata. Fail closed với drift/missing/unknown/symlink/hardlink/corrupt audit.
- A69-07: unit/corpus fault (export/import/cleanup boundary), stale confirmation, wrong ID, lost response, corruption/missing/mismatched hashes, pending/tail source, quota/low disk, lock/restart; raw receipts giữ lại. UI/browser kiểm download→receiver verify→preview confirmation; không click dọn managed demo trước xác nhận người dùng.
- A69-08: before/after cumulative SHA incl JOURNAL68+ENDURE; pins/quantitative verification/report. Scope hardware powercut/Android/prod auth not checked.

Decision: nguyên JOURNAL68 catalog không hỗ trợ tombstone. Giữ module frozen, archive/thu hồi trên managed snapshot-generation mới, không sửa catalog68, không giảm quota live68 hay thay dữ liệu .local/journal68. Cần migration/rotation có gate riêng để áp dụng thật. Cleanup trong fixture được kích hoạt bằng explicit test confirmation; demo không được tự xác nhận thay người dùng. Package SHA đảm bảo tính nhất quán, chưa là chữ ký/provenance xác thực hoặc anchor chống rollback đồng bộ.
