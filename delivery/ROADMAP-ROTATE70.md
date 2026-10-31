# ROTATE70 — roadmap overlay

16/10/2026. Giữ canonical SOT và source/candidate/ENDURE đóng băng.

Đã đóng gate host/mock: writer JOURNAL68 thực trong namespace mới, CLOSE/SEAL/semantic gate trước FREEZE, cold seed và SELECT, restart trước/sau commit, explicit rollback bằng writer mới, quyền rỗng, archive closed generations. Chưa migrate writer JOURNAL68 gốc.

Ưu tiên tiếp:

1. Kiểm handoff closed-generation từ ROTATE70 sang receiver ở máy/ổ độc lập, xác thực nguồn và custody. Hiện archive receiver verification trên cùng host, hash chưa là chữ ký hay anchor ngoài host.
2. Thiết kế retention/tombstone cho root70 có exported+receiver receipts và xác nhận trước dọn; root manifests hiện vẫn tham chiếu mọi frozen generation, nên không được xóa chúng bằng cách dùng cleanup69 trực tiếp. Hiện không có endpoint dọn.
3. Schema migration có kiểm và khả năng quay lui thực sự giữa hai phiên bản; ROTATE70 chỉ cùng schema/source68, rollback mới chỉ kiểm lineage/selection/writer isolation.
4. Qualification trên Android/storage/HeraHub và powercut khi đủ headroom/thiết bị. Sau đó mới đề xuất migration writer gốc và tích hợp vào native cockpit qua các gate được duyệt.

ENDURE, flight/SITL, firmware/capability, xác thực hai operator, SDK và ký/phát hành vẫn giữ gate hiện có. Không dùng kết quả rotation mock để mở gate bay thật hoặc kết luận ENDURE đạt.
