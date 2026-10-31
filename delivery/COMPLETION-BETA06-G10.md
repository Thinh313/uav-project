# BETA06 G10: port restart guard và tương thích runtime

22/10/2026. **NOT READY cho Android–SITL.** Đã sửa và kiểm guard bind cổng; host thực mở được sau admission. Root phát hiện clock của interpreter mới chưa có mốc chung giữa process và dừng trước Android/AP. Không sửa hoặc tiếp tục G10.

Bản sửa cô lập gồm SO_REUSEADDR, bind/listen giữ hai socket và observer kernel trước/sau khi giữ socket. macOS cho phép listener wildcard và loopback cùng cổng trong một số trường hợp; hai ứng viên thiếu observer đã bị QA bác bỏ và giữ chứng cứ. Observer phải thấy đúng hai listener probe, từ chối listener khác hoặc dữ liệu rỗng/sai/thiếu/timeout/overflow. Có port/operation/errno, cleanup và latch trước Popen; không SO_REUSEPORT, không retry hay bảo đảm TOCTOU. Fixture tái hiện plain bind Errno48 sau Node đóng thật; nguyên nhân chính xác của G9 vẫn UNKNOWN.

12 nhóm helper,8 nhóm socket và26 ca QA độc lập đạt trên ApplePython3.9.6; một mock963raw/sharedcanonical/WAL/index/history và bốn handler có stub được kiểm riêng. Các guard số, quota, deadline và thuật toán quyết định không đổi. Một future annotations import hỗ trợ dataclass trên runtime này, không đổi thân hàm guard. Gate source/mock là bằng chứng cho đúng phạm vi đã kiểm, không chứng nhận toàn bộ runtime.

Live G10:31 mẫu/30,231796 giây, minimum39.898.054.656byte, peak decline68.612.096byte; admission đạt. Probe kernel pre0/held2 đạt trong13,20ms, host10987 được tạo. Host resource guard226mẫu; minimum39.888.433.152byte, trên20GiB. Chưa có emulator, publisher, Connect, ARM hay AP mới; fork có writer nhưng chưa dùng cho nhiệm vụ. Toàn bộ AUTO/mất link/reboot/cold persistence G10 đều NOT_RUN, không gộp N1/F1 đã đạt ở G9.

Lỗi tương thích mới: Apple3.9 time.monotonic() lấy gốc theo process. Parent0,066→0,275s và child0,0527s không cùng origin; guard parent/child yêu cầu anchor tuyệt đối cùng host boot. get_clock_info monotonictrue không chứng minh được thuộc tính đó. Clock_gettime(CLOCK_MONOTONIC) có gốc chung nhưng khác sleepbasis; CLOCK_UPTIME_RAW mới khớp BrewPythonmonotonic cũ trong phép đo. Đây là khoảng trống của gate khi đổi interpreter; Root kiểm bổ sung đã ngăn dùng anchor không tương thích trước emulator. Không có internal automatic rejection được bịa thêm. Module clock11 riêng chỉ là chuẩn bị/mô phỏng, không sửa G10.

ControllerTTY10939 nhận EOF và exit0; host có app-closure EXPLICIT_STOP, không lỗi payload/index, quyền0 và PID đã vắng. Numeric exit của child host không được lưu ở nhánh EOF: NOT_RECORDED. Root receipt ban đầu ghi0 quá mức được đính chính append-only trong qa-final-gate02.json; không sửa receipt cũ. Hai PID và năm cổng8872/8873/5972/5582/5583 đã được kiểm không còn listener. Không có container mới để dọn.

Kiểm độc lập cuối:1001pin/26helper/9822đường dẫn bảo vệ (gồm7symlink literal)/5936historyentry đều khớp SHA. Workspace19blob và journalprefix nguyên vẹn; không flightappend. Source/candidate đóng băng, ENDURE và SOT canonical giữ nguyên; không build/cài/ký APK. Chỉ tiny fixture của nhiệm vụ được đóng/dọn, các failure receipt vẫn giữ.

Chứng cứ: evidence/beta06/generation10/qa-final-gate01.json, qa-port-active-listener-failure01.json, builder-wildcard-candidate01.json, qa-port-observer-independent01.json, host-admission-g10-host1.json, host-admission-g10-host1-ports.json, root-controller20-live.jsonl, qa-closure-summary01.json, qa-final-gate02.json và qa-final-runtime-summary01.json (SHAd929339b608fa984eb54a9151e93c02813dc8dff9a23458f37191685f7973210).

Bước cần thiết tiếp: chứng minh CLOCK_UPTIME_RAW chung giữa process và cùng basis cũ, gắn nhất quán mọi provider/default deadline trong bản cô lập khác rồi gate/admission riêng. Không dùng alias muộn hoặc monkeypatch stdlib. Không suy ra sản phẩm beta, flightworthiness hoặc media thật từ các test này.
