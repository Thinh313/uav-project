# ADR-089 — Source/receiver proof contract và replay fence

Accepted16/10/2026, scope AUTH73 mock/replay. Không retrofit receiver72 preview, không ký phần mềm hoặc tạo khóa/chữ ký xác thực mới.

Policy pin realm/epoch, receiver identity/key/principal và source identities/keys/root allowlists. Injectable proof verifier có domain riêng CHALLENGE / SOURCE / RECEIPT. MockOracle chỉ tra fixture đã đăng ký theo digest nguyên body/purpose/principal/key/epoch; evidenceId không phải chữ ký, hash không xác thực nguồn. Production capability luôn false và production request fail closed. Live key status/validity được kiểm lại khi ghi/đọc trusted-current result.

Challenge volatile bind manifest SHA, receiver boot/id, source principal/key/root, senderNonce và TTL30s. Claim bind toàn tuple và source sequence tăng liên tục theo principal, không reset khi đổi key. ADMIT ghi sync + anchor trước data side effect; challenge đã dùng/replay sequence bị chặn. Restart không khôi phục challenge hay admission dùng để ghi; explicit claim mới với boot/nonce mới có thể tiếp tục đúng transfer, không đổi nguồn/manifest/client nonce. Mất response không dùng replay request để retry; read-only reconcile lấy receipt đã commit.

COMMIT bind claim digest, senderNonce, identity/policy/epoch, manifest/bundle và receipt72 SHA sau readback/replay hiện tại. Sender lưu INTENT và CLAIM trước khi nhận receipt, sau đó RECEIPT_ACCEPTED duy nhất; receipt đúng hash nhưng sai receiver/intent/claim cũng bị từ chối. Receipt73 assurance luôn MOCK_ONLY_NOT_AUTHENTICATED, authorityRestored=false, actualImages=0.

Ledger và mock anchor là hai workspace/lock riêng. Mỗi append: sync log → fault boundary → append sync anchor frontier. Không trả thành công trước cả hai. Frontier lệch, file ghi dở, thiếu log hoặc rollback giữ HOLD; không tự repair/advance anchor. External anchor thật và trusted clock chưa có; mock anchor có thể cùng rollback nếu kẻ sửa cả hai, không tuyên bố bảo vệ trường hợp ấy. Challenge TTL dùng clock injected trong test; backward clock so committed event frontier bị chặn, reboot/clock-domain thay đổi thật cần gate riêng.

Tham khảo: [RFC9421 §7.2.2](https://www.rfc-editor.org/rfc/rfc9421.html#section-7.2.2) mô tả nonce và thời hạn để hạn chế replay; [RFC9449 §4.2](https://www.rfc-editor.org/rfc/rfc9449.html#section-4.2) dùng identifier độc nhất và binding request. Đây là application contract riêng, chưa HTTP Message Signatures/DPoP implementation. TLS/PKI/hardware key và chứng minh possession thực đều NOT_CHECKED.
