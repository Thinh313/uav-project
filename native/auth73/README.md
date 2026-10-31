# AUTH73 source/receipt contract

Module cô lập trên RECEIVER72, chưa bảo mật endpoint72 đang chạy. Xem contract.json và delivery/TIP-AUTH73.md. Không có SDK, install/build, khóa riêng, MAC hay chữ ký mới. Oracle fixture là giả lập verifier, không chứng minh cryptographic possession; production mode bị từ chối.

Caller cấp policy pin realm/epoch/source keys/root allowlists và đúng receiverId72. MockOracle được cấp bởi test harness, không nhận fixture đăng ký từ payload sender. Production verifier/TLS/trusted clock/anchor cần adapter khác và nghiệm thu riêng; không thay mock flag để phát hành.

Receiver flow: `offer` → harness cấp CHALLENGE fixture → sender tạo claim và harness cấp SOURCE fixture → sender `declare`/`recordClaim` → receiver `admit` → `chunk` → `finalizeData` → `draftReceipt` → harness cấp RECEIPT fixture → `commitReceipt` → sender `remember`. Request/receipt replay bị từ chối; mất response dùng `getReceipt`/`inspectReceipt` read-only. Sender inspect chỉ chứng minh local historical receipt +bundle hiện tại, không suy trạng thái receiver từ xa.

ADMIT log+anchor sync trước data writes; commit-time phải trong TTL nguồn. Receipt lịch sử có thể nhận lại sau TTL, nhưng phải thuộc local intent/claim, key hiện tại còn hợp lệ, và thời điểm commit nằm trước expiry. Restart không tự tạo challenge/admission hay finalize; dùng sequence cao hơn với challenge/boot mới để tiếp tục transfer chưa commit. Không reset sequence hoặc tự đổi policy/epoch/key trên ledger cũ.

Ledger/anchor là workspace độc lập và flock riêng. Giữ nguyên file khi quota/disk floor/corruption/frontier lệch. Crash log đã sync nhưng anchor chưa sync giữ HOLD; không có API repair hoặc dọn. Mock anchor cùng máy không chống joint rollback với ledger/oracle. Key revocation mô phỏng giữ hồ sơ nhưng chặn current-auth result/data mutation; không khôi phục quyền.

Từ thư mục aeris, kiểm `df -h /` rồi dùng fresh run name:

```
A73_RUN=<fresh-name> node native/auth73/tests.mjs
A73_RUN=<fresh-name> node native/auth73/corpus-qa.mjs
A73_RUN=<fresh-name> node native/auth73/process-qa.mjs
python3 native/auth73/verify.py evidence/auth73/corpus-<fresh-name> --output evidence/auth73/<fresh-output>.json
```

Mỗi run giữ toàn bộ evidence/fault artifacts, chỉ tạo native/auth73, evidence/auth73 và fixture mới evidence/receiver72/auth73. Không chạy trên source/candidate/ENDURE hoặc preview72. Không tự retry/dọn; case lỗi phải được phân tích trước run mới. Thay `<fresh-name>` bằng tên chưa tồn tại, không dùng nguyên dấu ngoặc nhọn trong shell.
