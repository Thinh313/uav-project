# HOSTISOLATE14: tách đọc nguồn, đóng monitor sau lỗi

**Kết quả: hai đường sửa đã được kiểm mock và quan sát trên Android–ArduPilot SITL. Toàn luồng vẫn NOT READY vì product writer vượt giới hạn commit200ms. Chưa đạt preflight hoặc beta stable.**

## Phần đã triển khai

Tiến trình HostHealth không còn tạo subprocess pmset theo chu kỳ. Một helper riêng được tạo trước priming/service, có PID/parent/instance/sequence/challenge, timestamp thật và pipe hữu hạn. Mỗi truy vấn vẫn chịu deadline/freshness2s và nguyên tắc pin30% khi vào/20% khi dừng. PID của lệnh pmset và thời gian Popen được gắn vào raw POWER_ROW có markerPB14,92byte. Dữ liệu cũ không bị giải mã nhầm theo schema mới. Helper chết, dữ liệu sai/stale/thiếu hoặc mất EOF đều từ chối; không dùng lại giá trị cũ như quan sát mới.

Monitor có nhánh đóng sau lỗi riêng: dừng worker, ghi hết audit và xác minh prefix thực, giữ lỗi đầu tiên và lỗi phụ; không gọi guardian xin lại quyền. Hồ sơ FAILED_DRAINED_NOT_ACCEPTANCE chỉ chứng minh đã ghi đủ bằng chứng thất bại. Lần đóng lại của một drain chưa đủ vẫn báo cùng lỗi, không biến thành thành công. Đường đóng bình thường vẫn yêu cầu guardian fence.

## Kiểm mock và nguồn

35 phương thức kiểm khác nhau đạt:12 power,8 failure-drain/audit,9 invariant/integration và6 kiểm Contractor. Contractor chạy lại cả35; không cộng số lần chạy thành số test mới. Ca kiểm lần đóng thứ hai ban đầu thất bại đã được giữ, sửa và chạy lại đạt. Kiểm AST/byte đối chiếu xác nhận hàm GuardianClient guard100ms cùng physics, journal, global quota và các policy quan trọng giữ nguyên.

Fault injection tổng hợp giữ GIL250ms: cùng tiến trình bị timeout3/3, tách tiến trình trả lời0,519–0,671ms cả3/3. Đây là mock cơ chế, không chứng minh pmset là nguyên nhân duy nhất của lỗi NAVFIX13 hoặc hiệu suất sản phẩm thực tế.

Source closure118file/204writer sites/14owners, future budget60.686.336B;138file planning giữ SHA sau HOLD. Hai helper dùng2 slot còn lại trong diagnosticChildren4, chỉ hỗ trợ một case của probe này. Không tăng quota hoặc bỏ các pool cũ.

## Lượt Android–SITL thực tế

Một lượt hostisolate14-disarmed01, chạy157,3865giây host và exit1; không tự retry. Đã khởi động Android, companion, ArduPilot, khảo sát/compile/lưu và thao tác b-connect. Lỗi phát sinh trong lúc chờ navigation: PRODUCT_WRITER_COMMITTED_AFTER200MS_NO_RETRY. Chưa có chứng cứ preflight đạt, không ARM, RC manual hoặc AUTO.

HostHealth ghi tổng1.460exchange, không có firstFailedSequence hoặc frozen latch. Ring chỉ giữ8exchange cuối:8accepted,8join khớp nonce và byte request/response; lớn nhất trong phần giữ lại3,611666ms, dưới100ms. Không có toàn bộ lịch sử latency để báo max/p99 cả lượt.

Đối chiếu độc lập hai raw audit:281 powerrow guardian và206 monitor, khớp helper/parent/PIDpmset và timing; cả hai prefix có SHA/sequence hợp lệ. Helper đều exit0, process group đã biến mất. Monitor ghi đủ produced=committed, pending0; guardianRPCsDuringFailureDrain=0; owner không có lỗi phụ khi đóng. Lỗi đầu tiên vẫn là writer200ms.

Raw main journal có43.693RX/INTENT/SENT/STAGE tương ứng, unknown-send0. Atomic clock age lớn nhất205,106375ms, dưới250ms. AP-stage349.551event. Main vẫn INCOMPLETE_RECORDING; AP-stage COMPLETE_BYTES_UNATTESTED. Byte hợp lệ không được coi là execution hoặc nhiệm vụ hoàn thành.

Mọi PID/cổng/container thuộc lượt đã đóng. Emulator exit-6 trong giai đoạn xử lý thất bại được giữ nguyên; không chứng nhận shutdown bình thường. Guardian ghi exceptional physical disposal, không có flight command. Hai tiến trình helper exit0 và không còn process group.

Đã dựng lại độc lập toàn bộ byte request/response của487truy vấn nguồn từ auditPB14; hai SHA khớp footer của helper. Query lâu nhất ở hai helper là704,277ms và707,420ms, vẫn dưới deadline2s. Đây là thời gian truy vấn nguồn, không phải latency của socket HostHealth.

Chưa có receipt RPC riêng theo từng operation của product writer để xác định path/sequence hay thời gian commit chính xác; chưa quy nguyên nhân cho filesystem hoặc lock. PollUI cuối lưu giữ không phải bằng chứng tươi tại thời điểm lỗi.

## Guard, bảo toàn và dọn dẹp

Giữ guard HostHealth100ms, freshness250ms, lease200ms, các guard vòng đời/nguồn/đĩa, speedup1/cap500ms, fsync trước sensor và đủ frame. Artifact thực9.289.728/9.437.184B, tính đủ tám pool. Admission metadata/artifact/disk đều đạt trước lượt; disk khoảng28GiB và AC thực. Không tăng cap, xóa lock hoặc reset native lifetime.

Source/candidate cũ, ENDURE, NAVFIX13, repo bàn giao public/intake và hai gói private giữ nguyên. Kiểm6.177entry theo hai phạm vi có giao nhau,833entry NAVFIX13 và138file planning mới; không cộng thành số file duy nhất. Case đã đóng có189file baseline.98đường dẫn thiếu có từ trước không được phục hồi hoặc stage thành deletion. HEAD hai repo không đổi; không commit/push hoặc ký mới trong task.

Dùng lại APK development8bc0a7… và AP77344f…/image ARM64 đã pin, không build/tải/ký. Fixture tạm của mock đã tự dọn, không còn pycache hoặc copy cả dự án vào tmp. Docker image prune thu hồi0B; không prune container/volume.

## Bước tiếp theo

Đo đường commit product writer200ms: tách rõ chờ ledger/lock, write, fsync, publish và reply; kiểm fault injection và deadline trước/sau commit. Không gửi lại thao tác đã commit muộn, không nới200ms hoặc100ms. Sau sửa có bằng chứng, tạo candidate cô lập và admission mới rồi mới kiểm ngắn trước mốc10phút. Chưa triển khai phần sửa writer trong task này.

Bằng chứng: ROOT-TEST1..4.stderr.txt, mock-ab01.json, BUILDER-HOLD01.json, ROOT-QA-GATE01.json, FROZEN-CANDIDATE01.json, ROOT-ADMISSION01.json, ROOT-LAUNCH01.json và stdout/stderr đầy đủ, ROOT-COLD-REVIEW01.json, ROOT-IPC-TAIL01.json, ROOT-POWER-PREFIX01.json, ROOT-POWER-WIRE01.json, diagnostic-S01-hosthealth01.json, diagnostic-S01-disposition02.json, PRESERVATION-FINAL01.json, PRIVATE-HANDOFF-PRESERVATION01.json, S01-CLOSED-BASELINE01.json. Báo cáo này chỉ nghiệm thu trong phạm vi host/mock/SITL; chưa xác nhận HeraHub, payload thật, flight thực hoặc production.
