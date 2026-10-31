# ADR-088 — Byte transport và receiver commit riêng

Accepted, 16/10/2026, phạm vi host/mock của TIP-RECEIVER72.

Sender đóng package69 + proof71 + custody71 thành envelope canonical. Receiver chỉ nhận manifest và chunk16KiB qua HTTP, có receiverId được người vận hành chọn, hash từng chunk và toàn bundle. Manifest tối đa64KiB, bundle tối đa34MiB và quota workspace32MiB (reserve có thể chặn sớm hơn). Chọn16KiB để kiểm nhiều checkpoint trên corpus nhỏ, không phải benchmark dữ liệu lớn. Không đọc sourceRoot được khai trong proof; helper verifyCapture chỉ kiểm snapshot đã nhận. Control proof/hash unsigned chỉ chứng minh nhất quán, không chứng minh danh tính nguồn hay thời điểm lịch sử.

Workspace receiver có identity, writer flock, transfer manifest, immutable chunk files, snapshot xác minh và receipt. Receipt ghi cuối bằng exclusive create + fsync file/directory, bind receiver/transfer/source/job/package/manifest/proof/custody/bundle/inspection. Mọi GET receipt kiểm lại byte và semantic; corruption làm HOLD, không trả PASS cũ. Mất response không kích hoạt retry; explicit reconcile lấy receipt hiện có. Restart chỉ đọc; không finalize hay khôi phục quyền.

Mỗi chunk là checkpoint. EOF giữa HTTP body không ghi chunk; crash giữa file write có thể để file dở và HOLD, không truncate/overwrite. Crash giữa snapshot build được explicit finalize hoàn tất những file chưa có, nhưng chỉ từ bundle đã kiểm và không sửa file đang tồn tại. Crash khi ghi receipt dở giữ HOLD. Không cleanup API, retention hay tombstone. Quota tính cả staging, snapshot và receipt reserve; host floor 20GiB +32MiB. Không hứa dung lượng toàn bộ lớn hơn quota.

Receiver và sender chạy hai process trên cùng Mac. Loopback bearer/token process-local chống thao tác UI ngoài origin; chưa là auth mạng/remote production. Network partition được fault injection trên loopback, chưa hai host/ổ độc lập, chứng chỉ, Android/HeraHub hay powercut vật lý. Không tích hợp Fly/candidate hay tạo chữ ký phần mềm.
