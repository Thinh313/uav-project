# AUTH73 — authentication contract over isolated RECEIVER72

16/10/2026. SPEC → BUILD → VERIFY do một agent, không tuyên bố auditor độc lập. SCAN: RECEIVER72 có hash/custody consistency và replay package, chưa xác thực nguồn. Baseline mới34.025 đường dẫn khớp SHA; preview72 gồm26 file sẽ được kiểm riêng. Ngân sách32MiB, sàn20GiB+32MiB; không install/build/ký/SDK/SITL.

REQ-01: Contract version1, exact schema, realm/policy/trust epoch/purpose, principal/key-role/sourceRoot allowlist, receiverId, manifest/bundle/source tuple. Mock verifier fail closed, không tạo private key/MAC/digital signature; production mode không được dùng mock.
REQ-02: Receiver challenge nonce +boot +TTL, source sequence persistent và sender nonce. Replay, reuse nonce/JTI, wrong receiver/root/realm/key/purpose/epoch, expiry/clock rollback không tạo data/receipt side effect.
REQ-03: Durable receiver admission trước gọi R72, explicit resume khi restart bằng challenge mới. Commit receipt bind admission+sender nonce+receipt72+source/receiver/bundle; sender chỉ nhận receipt cho intent/claim đã lưu. Receipt replay không append lại; reconcile/read-only tách riêng.
REQ-04: Append-only ledger + mock external anchor frontier, single writer, quota/floor; restart đọc, không tự finalize/quyền. Torn/corrupt log, missing/rollback frontier, crash giữa log sync và anchor advance giữ HOLD, không repair/cleanup.
REQ-05: Kiểm adversarial mock,22 corpus H71 qua adapter+R72 namespace mới, replay từ cold restart và process fault. Byte/hash/nonce/sequence bằng Python implementation riêng; semantic vẫn R72 frozen.
REQ-06: Baseline, ENDURE5.051 và preview72 unchanged; TIP/ADR/Completion/coverage/fingerprints. Không sửa canonical SOT hay source/candidate/module cũ.

Blueprint: native/auth73/{contract,oracle,ledger,adapter,tests,corpus-qa,process-qa,verify} + evidence/auth73; R72 fixture dưới evidence/receiver72/auth73. Chỉ mock call/replay in-process và subprocess restart, chưa transport production hoặc retrofit API72 đang chạy. HTTP multi-host/cryptographic auth/real trusted clock/external anchor là NOT_CHECKED.

Decisions: yêu cầu đã ủy quyền triển khai contract mock, không hỏi lại. Nonce single-use và domain separation tham khảo RFC9421/RFC9449, không triển khai hay tuyên bố tuân thủ hai RFC này. Chỉ hỗ trợ manifest<=16KiB trong adapter mock để giữ log bounded; module72 gốc không đổi. Mock anchor trên cùng host chỉ mô phỏng trust boundary; joint rollback ledger+anchor và attacker có quyền sửa oracle/anchor chưa được bảo vệ.
