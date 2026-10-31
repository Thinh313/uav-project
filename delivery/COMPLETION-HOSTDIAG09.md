# HOSTDIAG09 và BETA06 G9: kết quả chẩn đoán và campaign hữu hạn

22/10/2026. **Chẩn đoán và sửa binding đã hoàn tất trong phạm vi kiểm; nghiệm thu Android–SITL toàn campaign: NOT READY.** N1 bay AUTO đồng thời video/payload và F1 mất link đã đạt kiểm độc lập. Host restart bị chặn trước Popen; không retry, không mở G10.

## Dung lượng host

HOSTDIAG08 ghi 181 mẫu trong 180,004939 giây: available giảm 92.598.272 byte; APFS Data tăng 92.614.656 byte, VM không đổi. Bộ đếm ghi theo PID không xác lập chủ sở hữu dung lượng tăng. Tác nhân gây biến động lớn trong G7 vẫn UNKNOWN; không quy kết một ứng dụng hoặc hành vi dọn file.

G8 và G9 chỉ chạy sau fresh admission giữ nguyên. G9 host1: 31 mẫu/30,203717 giây, minimum39.984.197.632 byte, peak decline180.224 byte. Host2: 31 mẫu/30,095171 giây, minimum40.003.387.392 byte, peak decline237.568 byte. Cả hai admission đạt; host2 vẫn bị từ chối ở bước bind cổng sau đó. Emulator boot18 đã qua admission riêng, minimum free trong runtime39.892.353.024 byte, khoảng37,153 GiB, trên sàn20 GiB.

Không đổi admission29 GiB,31 mẫu/ít nhất30 giây, peak decline tối đa256 MiB; runtime28 GiB, forecast15 giây và sàn20 GiB. Giữ ngân sách gốc2700 giây/2host/4AP, AP540 giây, speedup1 và tất cả quota/closure reserve. Không có bảo đảm OS quota từ những kiểm này.

## Lỗi binding đã xử lý ở bản cô lập

G8 bị ORIGINAL_COUNTER_CAPACITY_MISMATCH trước Connect input/AP: regex còn host-app07 nhưng output thực host-app08, dẫn tới đếm host0 và phân loại sai file. G8 đã đóng, không sửa source hoặc kết quả của G8. G9 dùng một binding bất biến cho cả hai tên host canonical, chung cho routing và capacity.

Hai phép kiểm filesystem nhỏ, gồm kiểm độc lập, tái hiện old-fail/new-pass. Đường dẫn giả, symlink/file thay thư mục và counter sai bị từ chối. Toàn bộ hằng số guard/quota và thuật toán quyết định giữ nguyên. Gate trước runtime kiểm935 pin/23 helper/18production/132stage, một mock963row với reload và bốn fixture handler có stub công bố rõ. Số test không thay nghiệm thu runtime.

## Kết quả thực tế G9

| Phần kiểm | Kết quả và phạm vi |
|---|---|
| Android hiện có | Boot một lần, APK khớp SHA; không build/cài/ký mới |
| Ground trước N1/F1 | 75,397/75,206 giây, mỗi lượt ba renewal viewer và publisher; không lỗi lifecycle |
| N1 nhiệm vụ AUTO | PASS raw generic ArduPilot SITL: upload12lệnh, hai chu kỳ readback24lệnh, bốn camera206, không PARAM write; canonical hoàn tất/hạ cánh/disarm/gầnHome trước đóng |
| Video N1 | PASS884mẫu/30,0007giây,29,465979FPS, P95upper37,151333ms; first-ready262,7ms; đây là nguồn VP8 RGB tổng hợp trên host hiện tại |
| Payload/capture N1 | PASS hai điểm AUTO/payload,73điểm tương quan/không đổi context; capture tổng hợp ba artifact SHA khớp, actualImages0; không chứng minh camera/gimbal thật hoặc overlap liên tục |
| N1 index/closure | Strict WAL indexseq114, acceptedtrue; AP thuộc tác vụ exit0/OOMfalse, retained |
| F1 mất link | PASS deliberate TCP cut với lease còn45,85555giây; durable revocation trước cut, pre1/post0lease/không phục hồi quyền; không có wire hoặc lệnh cũ sau cut |
| F1 hồ sơ | PASS indexseq121, acceptedfalse/abortedtrue/incomplete; AP exit0, không kết luận quỹ đạo/hạ cánh sau mất link |
| Managed host restart | REFUSED: Errno48 Address already in use sau physical admission, trước host2 Popen/outputdir/counter increment |
| N2/reboot F2/cold persistence19 | NOT_RUN, campaign dừng sau lỗi bắt buộc |

Chuỗi đo N1 chưa gọi Lưu báo cáo khi bay. Sau đóng N1, UI vẫn giữ đúng report và measurementContext bất biến; Root dùng một thao tác video-save để lưu cửa sổ đã đo, không đo/bay lại. Raw đã lưu và sidecar được QA đối chiếu trước F1. ACK save có runnull ở thời điểm lưu; không làm giả bối cảnh hiện hành thành N1.

## Lỗi managed restart và mức độ biết

Source probe lần lượt8872/8873 bằng socket.bind nhưng không ghi port cụ thể khi exception. Log chỉ chứng minh Errno48 sau admission, trước Popen. Kiểm lsof/netstat về sau không thấy listener ở hai cổng, không chứng minh trạng thái tại thời điểm lỗi. TIME_WAIT là giả thuyết chưa kiểm chứng. Không nới check, không bật reuse, không bind lại để biến lỗi thành PASS.

Controller ghi COMMAND_REFUSED cho lỗi start-host; không tự latch campaign_failed ở nhánh này. Việc kết thúc/no-retry do Root thực thi và giữ rõ trong receipt, không bịa event nội bộ. Bước tiếp nên ghi port/socket-state ngay trước probe và kiểm lifecycle/reuse bằng mock/fault injection trong namespace mới; chỉ cho phép campaign khác sau gate và fresh admission riêng.

## Bảo toàn và đóng sạch

Root và QA đối chiếu8.665 đường dẫn bảo vệ;935pin/23helper hiện tại nguyên SHA. History4.788entry, workspace gốc20file/870.221byte và prefix được giữ. Native trước/sau cùng boot18:19file/34record/15.467bytejournal,0append,13PENDING/3pickerremaining. Đây là kiểm cùng boot, chưa phải persistence sau cold restart. Các sự cố phục hồi đúng SHA và95đường dẫn thiếu từ lịch sử vẫn ghi riêng; không khẳng định hiện diện liên tục.

Host3925, controller3864, helper3944 và emulator3975 đều đã thoát; TTY và host/emulator exit0. Các cổng8872/8873/5972/5582/5583 không còn listener. Viewer và publisher đã dừng, tab tạm đóng. Hai AP container giữ nguyên với bằng chứng đóng. Docker image prune thu hồi0B, không xóa container/volume.

Đã xóa riêng các tiny fixture scratch do Builder/QA tạo: codex-tmp-g9-binding-20261022-i13jo3r8 và qa-g9-real-binding-dzgckmjr trong evidence/beta06/generation09 (cùng fixture tạm của handler, danh sách trong receipt). Không sao chép toàn project ra tmp, không cài dependency hay sửa source/candidate đóng băng/ENDURE. Không sửa SOT canonical, trust/selection hoặc ký phần mềm.

## Chứng cứ chính

- delivery/COMPLETION-HOSTDIAG08.md và delivery/COMPLETION-BETA06-G8.md.
- evidence/beta06/generation09/qa-final-gate01.json: fd91b4513d0f22b607fa337dcb07abb9199babd9f66791b159929d4b0b9647a4.
- qa-n1-raw01.json, qa-n1-media01.json, qa-n1-overlap01.json, qa-n1-index01.json.
- qa-f1-cut01.json, qa-f1-raw01.json, qa-f1-index01.json.
- root-controller18-live.jsonl, host-admission-g9-host1.json, host-admission-g9-host2.json.
- qa-closure-summary01.json và qa-final-runtime-summary01.json.

G8 final completion fingerprint từng bị proofwriter G8 từ chối do có namespace G9 thêm mới; không ghi receipt đó và không sửa guard/history. Báo cáo G8 đã tồn tại trước lần từ chối; nguồn cho lần từ chối là Root tooloutput/message, được G9 gate đính chính rõ.

Value evidence: không áp dụng benchmark LLM cho sửa deterministic này. Chứng minh hữu ích hiện tại là đường AUTO/video/payload và mất link chạy thật trong SITL, có raw và ghi hồ sơ đúng nghĩa. Chưa phải beta hoàn chỉnh, flightworthiness Hera, media camera thật hoặc lợi thế DJI.
