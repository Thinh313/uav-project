# M1 Integrated Operational Alpha: tiến độ bootstrap04

20/10/2026. **M1 NOT READY.** Đã triển khai và kiểm độc lập phần sửa rig khởi động; chưa chạy lại Android–SITL vì chưa đạt admission dung lượng. Không báo milestone DONE từ kết quả mock.

## Kết quả đã đạt trong lượt này

- Rig mới kiểm đúng container sở hữu, trạng thái chạy bình thường và guest TCP5760 LISTEN trước khi thực hiện đúng một bootstrap connection. Cổng host đã publish, loopback-only hoặc IPv6-only chưa đủ để chấp nhận đường IPv4. Kiểm sẵn sàng thụ động có giới hạn30s; initial connect3s, không reconnect khi lỗi. Giữ recv idle polling0,5s thụ động như trước;0TX.
- Lưu trạng thái Running/Restart/OOM/ExitCode, guest socket và log trước khi dừng. Tách yêu cầu dừng bên ngoài khỏi việc controller bắt đầu dừng do lỗi. Lỗi đóng socket, probe, ghi diagnostic hoặc stop được giữ riêng và không che nguyên nhân đầu tiên đã quan sát.
- Tệp mới `bootstrap04.py`, `runtime04.py`, `bootstrap04_mock.py`; tổng34.845byte. Runtime cũ giữ nguyên SHA. Không sửa native source07/APK04/observer, tham số AP hoặc các guard1500/3000ms, fsync, frame, speedup1/cap500ms.
- Builder kiểm5 nhóm mock. QA agent riêng kiểm6 nhóm đối kháng, thêm12 assertion AST lineage và injected sequence4 lệnh DockerProbe. Đây là các lớp kiểm có phần giao nhau, không cộng thành số test sản phẩm. QA kết luận không có P0/P1 trong phạm vi rig và CLEAR cho bước đánh giá thực tế có điều kiện tài nguyên.
- QA result01 sai schema fixture vì thiếu RestartCount được giữ lại; result02 ánh xạ schema có giá trị thật rồi kiểm các nhánh đích. Không sửa production để làm fixture qua và không tính việc bị chặn sớm bởi schema là kiểm được predicate phía sau.

## Bằng chứng và trạng thái

| Hạng mục | Kết quả |
|---|---|
| Source rig | `dff20568baf38c0599aaef66fddc1facb621c55ce3c227e506c92c4658e4ee19`,3 pin |
| QA độc lập | `evidence/integration03-bootstrap04/qa/source-gate01.json`, OFFLINE_RIG_CLEAR_RUNTIME_NOT_ADMITTED |
| Native nguồn hiện giữ | source07,192 pin khớp; chưa có build mới |
| APK development giữ nguyên | SHA `9218acc3b71ad271b3ee9b7ba291d76fe1f97cd714e962ec34630fb6eb6f4ddf` |
| Frozen baseline | Trước/sau71.158/71.158 khớp SHA,0 sai lệch; chỉ là quan sát checkpoint |
| Prior handoff |70 đường dẫn tham chiếu khớp trước sửa rig |
| Runtime/flight | Chưa chạy Docker AP/Android/SITL; không arm/lệnh bay, không chữ ký mới |
| Dung lượng | Khoảng23,7GiB;30s observation chưa đạt≥29GiB ổn định |
| Dọn dẹp | Scratch `.mock-bootstrap04` đã dọn; không dependency/projectcopy/tmp; Docker image prune0byte, không dọn container/volume |

Nguyên nhân EOF thực tế cũ vẫn **UNKNOWN**. Mô phỏng chứng minh gate xử lý tình huống đã đặt; chưa chứng minh race đó gây lỗi cũ hoặc bản sửa đã chữa lỗi thực tế. Guest LISTEN cũng chưa chứng minh application handshake hoặc độ trễ đầu-cuối.

## Phần còn phải đạt

Giữ nguyên10AC INTEGRATION03: phiên>20kframe với3 cohort đúng kiểu/freshness; nominal AUTO và acceptedreview; B độc lập/consent/camera/gimbal đúng route; partition/pilot-loss; observer3D airborne đủ30s; SAF đúng selectedrun/receiver; process/coldboot/privatepreservation, UI và managedclosure. P1 OPERATOR01 cũ vẫn đạt scope riêng, không tự chuyển acceptance sang bản tích hợp mới.

Đã lưu trình tự kiểm tại `planning/product-standard01/M1-ACCEPTANCE-SEQUENCE04.md`. Trước nativeconnect phải có bootstrap record thực và gueststreams cần thiết sẵn sàng; launch.json hoặc dòng AP_CREATED không thay proof này. Freshresource admission cần≥29GiB ổn định30s trước boot và≥26,25GiB sau boot, guard21GiB để bảo vệ sàn20GiB. Chỉ sau gate mới cấp fresh runID, tối đa3 cửa sổ mới; lỗi đầu tiên dừng các bước phụ thuộc để phân tích, không tự retry.

**Disposition:** phần sửa rig đã kiểm offline; M1 chờ điều kiện dung lượng để kiểm thực tế. Không có thay đổi trạng thái nghiệm thu HeraHub/PhaseOne/video thật, production, simulator hiệu chuẩn hoặc ENDURE. Không dùng RAGAS parity làm gate.

## Value evidence

Đã loại bỏ việc coi host published-port là đủ readiness và bổ sung trace cho lần lỗi tiếp theo. Giá trị runtime/performance chưa đo. Đây là deterministic rig repair; baseline LLM không phù hợp. Không tuyên bố cải thiện tốc độ Android, độ tin cậy bay, khả năng thương mại hoặc ưu thế so với sản phẩm khác từ mock/source checks.
