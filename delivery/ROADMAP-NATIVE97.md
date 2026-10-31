# Roadmap sau NATIVE97

18/10/2026. Dựa trên delivery/COMPLETION-NATIVE97.md; không cập nhật canonical SOT/candidate đóng băng.

1. Native session chung flight + payload: một transport/discovery/session identity, arbiter tách quyền pilot và payload; UI quan sát trước, mock fault/replay trước khi AP SITL. Không cho payload phát lệnh bay. Nghiệm thu nhiệm vụ bay cùng capture/gimbal mock, mất link/boot/thu hồi không gửi lại.
2. Correlation cho repeated/shared-manager command: định nghĩa unknown/timeout/quarantine, nhiều phản hồi muộn/sai device; chỉ mở thao tác khi phân biệt được phản hồi. Không suy execution hay ảnh từ ACK.
3. Hai phiên cockpit/operator độc lập: enrollment/identity/lease/consent/revocation và journal bền vững; lỗi network/partition/restart không khôi phục quyền. Trước mắt mock/SITL, chưa giả làm hai radio thật.
4. Khi có target/API: bench HeraHub input/video/MCU và PhaseOne/gimbal/model cụ thể; tiếp đó HIL và bay kiểm soát. Chưa được coi là vượt DJI hoặc thay Ragas thương mại chỉ từ nghiệm thu engineering.

Mọi increment tiếp tục tách source/candidate/ENDURE, sàn20GiB, có admission/resource budget riêng và không tự ký production.
