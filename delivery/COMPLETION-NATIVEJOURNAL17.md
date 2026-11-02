# NATIVEJOURNAL17: hoàn tất code và mock

**Phạm vi nghiệm thu: READY cho code/mock đã kiểm. Android lifecycle và Beta tích hợp: NOT READY.**

Theo chỉ đạo cuối của anh, phần việc kết thúc ở code và mock. Không mở thêm Android, emulator, SITL hay ADB; không tạo candidate hoặc ký APK mới sau chỉ đạo này. APK development đã được tạo và kiểm trước đó, không phải bản production.

## Kết quả cho sản phẩm

Đã bổ sung vòng đời journal trong native shell cô lập để xử lý giới hạn tám journal mà không tự xóa dữ liệu hoặc khôi phục quyền điều khiển. Giữ tối đa tám journal trực tiếp; các thế hệ đủ điều kiện được chuyển nguyên byte vào archive có giới hạn. Index, archive, pending và dữ liệu điều khiển đều chịu quota. PREVIEW/APPLY/RECOVER là các thao tác tường minh, có khóa liên tiến trình, số thứ tự tăng đơn điệu và kiểm toàn vẹn.

Tám journal cũ chỉ chứa header được phân loại **UNUSED**, không được xem là chuyến bay thành công hoặc bằng chứng input đã thực thi. Tiếp nhận các journal lịch sử đã dùng với trạng thái CLOSED_VERIFIED vẫn bị từ chối cho đến khi có đủ raw STATUS và kiểm chữ ký P256 gốc.

Đã sửa ba ranh giới pipeline:

1. Writer phải được khởi tạo trước khi readiness gọi guard. Thứ tự cũ gây lỗi đã được tái hiện bằng mock; kiểm tra không bị bỏ qua.
2. Allowlist trước gửi lệnh và receipt sau lệnh dùng cùng một authorization bền vững. Receipt cài đặt có schema riêng, ràng buộc đúng candidate, APK, nguồn, receiver và lần sử dụng. Không tự retry khi kết quả chưa chắc chắn.
3. Đường tiếp nhận sau gián đoạn chỉ đọc APK và dữ liệu hiện có trước khi quyết định tiếp tục. Không chứa lệnh cài lại. TAR phải đúng framing, dấu kết thúc, toàn bộ file và directory; từ chối dữ liệu thừa ẩn, TAR thiếu kết thúc và namespace mới chưa được phép.

Generic STATUS reader cũ không được nới lỏng. Việc kiểm đầy đủ archive được thực hiện ở bước cold audit tường minh, tránh quét archive trong đường STATUS/input nóng.

## Kiểm chứng đã thực hiện

Root chạy lại bảy lệnh cuối, tất cả exit 0:

| Phép kiểm | Phạm vi | Kết quả |
|---|---|---|
| test-runtime17.py | 15 phương thức mock runtime | PASS |
| test-writer-order02.py | 3 phương thức về thứ tự writer/readiness | PASS |
| test-adoption03.py | 4 phương thức qua command/export/cold reader | PASS |
| test-tar-shape03.py | 3 phương thức cấu trúc TAR | PASS |
| independent-install-boundary17.py | 20 ca đối chiếu ranh giới install | PASS |
| independent-adoption03.py | 10 ca đối chiếu tiếp nhận sau gián đoạn | PASS |
| prepare-source-gate03.py, không --write | Đồ thị nguồn và ràng buộc tĩnh | PASS |

Các kiểm này dùng mock, filesystem host và FakePopen không tạo tiến trình Android/AP. Những bộ kiểm có phần giao nhau; không cộng số ca thành chứng nhận chất lượng sản phẩm. Ca cấu trúc TAR sau APPLY dùng registry placeholder chỉ chứng minh cấu trúc, không chứng minh lifecycle hợp lệ.

Các kiểm native/host trước đó cũng được giữ: fault injection journal, giới hạn index/receipt, archive receiver và đối chiếu độc lập. Số đo host JVM không đại diện hiệu năng ART/Android hoặc tải journal 64 MiB.

Evidence cuối: `evidence/nativejournal17/qa/ROOT-FINAL-CODE-MOCK05.json` và `evidence/nativejournal17/ROOT-FINAL-VERIFICATION01.json`.

## Hai lượt thực đã dừng, bằng chứng giữ nguyên

| Lượt | Điểm dừng | Diễn giải |
|---|---|---|
| N01 | PRODUCT_WRITER_NOT_STARTED_OR_CLOSED | Readiness chạm writer chưa mở. Guardian đã chuẩn bị ADB server, nhưng chưa tới lệnh ADB của case. |
| N02 | Lỗi serialize receipt sau lệnh install | Cold backup và receiver đã hoàn tất; kết quả cài vẫn UNCONFIRMED_COMMAND_RECEIPT_NOT_PERSISTED. |

N02 đã gọi `install -r`. Raw SDK có dòng Success, nhưng receipt hoàn thành/exit và quan sát SHA APK đang cài chưa được lưu đầy đủ. Vì vậy không kết luận cài thành công, không tự gửi lại lệnh và không sửa lịch sử thành PASS.

Backup N02 gồm 70 file riêng của ứng dụng, trong đó tám journal UNUSED. TAR gốc 199.680 byte, SHA256 `1cfcf1b2cceab0f94563f900c71dd643590285783a1086ffde848587b71ddb08`. Không có nghiệm thu APPLY, startup/restart native, persistence Android, nhiệm vụ bay hoặc phiên tích hợp 10 phút từ hai lượt này.

## Artifact và nguồn đã kiểm

- APK development: `evidence/nativejournal17/candidates/eed4ba7851897af3fb57cd29005a84df41e39a5d97b5ae510baf02321ddc5c17.apk`.
- APK SHA256: `eed4ba7851897af3fb57cd29005a84df41e39a5d97b5ae510baf02321ddc5c17`.
- Package `vn.rtr.aeris.betasim09`, versionCode 13017; minSDK 26, targetSDK 33, development/debuggable.
- Chữ ký development đã kiểm, certificate SHA256 `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`.
- Native source digest: `c4e122d55248d59d2d606046557bfc47e3c58911da5f8bd314f8c1a7ae987af1`.
- Runtime HOLD03: `planning/nativejournal17/runtime/BUILDER-RUNTIME-HOLD03.json`, SHA256 `4d1e439c2e8c038f1a26b7b442b278e0420e3399c0937cccaeec13afa8bb3207`.
- Hướng dẫn tái chạy mock và điều kiện runtime tương lai: `planning/nativejournal17/runtime/README.md`.

APK có chữ ký hợp lệ không đồng nghĩa đã nghiệm thu trên Android. Không có kết luận UI trực quan, HeraHub, SDK payload hoặc drone thật ở milestone này.

## Guard và bảo toàn

Giữ freshness 250 ms, HostHealth 100 ms, writer 200 ms, input lease 200 ms, speedup 1, cap 500 ms; không bỏ frame hoặc bỏ fsync trước sensor. Giữ sàn disk 10 GiB cùng reserve 256 MiB, artifact 11 MiB tính đủ 11 pool, metadata 64 MiB, native journal 64 MiB và export 192 MiB.

Đối chiếu cuối đạt cho 8.893 đường dẫn tham chiếu riêng biệt, gồm các đường dẫn bảo vệ cũ và raw N01/N02; nguồn HOLD khớp SHA và hai candidate Native17 đóng băng đều qua full load chỉ đọc. Bản bàn giao public và TAR private giữ nguyên. 98 tracked deletion đã tồn tại ở entry baseline không được phục hồi, stage hoặc che giấu trong task này. Đây là đối chiếu tại thời điểm kiểm, không khẳng định đường dẫn gốc luôn hiện diện liên tục.

Trước chỉ đạo code/mock, các text artifact mới do task Native17 sở hữu đã được nén vật lý để giữ cap: byte logic, chữ ký, mode và mtime giữ nguyên; inode, flags và ctime của các alias liệt kê có thay đổi. Không nén hay sửa raw N01/N02 hoặc artifact của pool cũ. Receipt: `evidence/nativejournal17/ROOT-OWN-ARTIFACT-COMPACTION03.json`.

Đã dọn scratch build native, classes/fixtures mock và cache `native/nativejournal17/__pycache__/build.cpython-314.pyc` do task tạo. Không xóa bằng chứng, dữ liệu người dùng, image/volume Docker hay source cũ. Không tải dependency/SDK và không sao chép toàn dự án vào thư mục tạm.

## Bước tiếp theo khi anh cho tiếp tục runtime

1. Kiểm admission mới theo guard hiện tại; quan sát lạnh SHA APK đang cài và toàn bộ byte/file/directory của dữ liệu native. Không tự cài lại để che kết quả N02 chưa xác nhận.
2. Chỉ khi đúng APK đã review và dữ liệu khớp nguyên bản mới APPLY có kiểm soát; kiểm hai phiên native khác PID/epoch/key, đóng journal, restart và đọc lại hồ sơ. Không khôi phục quyền tự động.
3. Khi native lifecycle đạt mới quay lại Android–SITL ngắn, sau đó kiểm tích hợp 10 phút với nhiệm vụ, video/payload, mất link, reboot và persistence.

**Disposition: hoàn tất phạm vi code/mock hiện được giao; chưa nghiệm thu Android lifecycle và chưa đạt Beta stable.**
