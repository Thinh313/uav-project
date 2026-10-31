# RUNTIME-ACCEPTANCE02: chưa đạt lượt ngắn

**Trạng thái: NOT READY. Chỉ kiểm lượt ngắn theo lựa chọn của người dùng; không chạy30 phút.**

Đã sửa cách truyền đối số adb shell và hai đường đọc XML UIAutomator trong source cô lập. Giữ APK development hiện có, không build hay ký mới. Kiểm nguồn độc lập đạt31 ca transport và14 ca thay đổi UI;10 ca metadata của candidate cuối chạy trong Linux, không thay cho kiểm nhiệm vụ. Kiểm thực chuẩn bị giao diện đạt2,19 giây.

## Kết quả vận hành

| Chặng | Bằng chứng | Kết quả |
|---|---|---|
| Admission, nguồn và cached artifact | Candidate/module origins/Linux probe | Đạt trong phạm vi đã kiểm |
| Native bootstrap + READY | ACK thực gắn nonce/source/context; khảo sát r1 được lưu | Đạt; chưa có quyền điều khiển |
| AP/backend | Đã mở từ candidate cuối | Có khởi động, không phải nhiệm vụ bay hoàn tất |
| Mở preflight / CONNECT | UI có hình ảnh nhưng cây accessibility mất các nút | FAIL trước CONNECT |
| Manual/assisted, thả cần/BRAKE, quyền mới, LAND | Chưa đến được | NOT CHECKED |
| Review, restart và đối chiếu persistence | Chưa đến được | NOT CHECKED |
|30 phút | Ngoài phạm vi lần này | NOT RUN |

## Hai lỗi chặn phải đóng

1. **P1: contract giao diện có hình nhưng không quan sát được qua accessibility sau bootstrap.** Cây trước đó có nút Trước bay; cây lỗi không có nút, lần đọc sau chỉ còn 6 node/title WebView. Ảnh màn hình vẫn thấy đủ 4 nút điều hướng. Chưa xác định nguyên nhân gốc trong WebView/accessibility; không gọi đây là lỗi trùng nhãn. Bộ kiểm từ chối bấm và không dùng tọa độ để lách điều kiện.
2. **P1: đường thoát lỗi sau READY chưa đảm bảo đóng DAG tiến trình.** __exit__ dừng observer/guard; nhánh abort_preparation chỉ bao phủ lỗi trong prepare. Khi lỗi điều hướng sau READY, child còn chạy và backend chỉ kết thúc sau lỗi clock thứ cấp. Hiện không còn PID/cổng/container của lượt kiểm; sự vắng mặt này không chứng minh managed drain hoặc hạ cánh.

Run đầu giữ lỗi timeout XML trước AP. Run thứ hai đã qua READY nhưng dừng trước CONNECT, cấp quyền và ARM. Backend lưu prefix 32.909 frame, stageRows và journalCompletedFrames cùng 32.909; clock commit anchor rỗng. Lỗi freshness 250 ms được ghi sau lỗi UI khoảng48,93 giây: giữ như bằng chứng dừng lỗi, không xem là lỗi pacing chính hay nhiệm vụ hoàn tất.

## Bảo toàn và phục hồi

Đã phục hồi 722 đường dẫn bằng đúng SHA sau ủy quyền riêng, khoảng445 MiB tính theo đường dẫn; không ghi đè file có sẵn, không sửa lịch sử hay ký lại. Nguyên nhân mất đường dẫn chưa rõ. Không khẳng định các đường dẫn hiện diện liên tục.

Kiểm cuối: 17.117 mục lịch sử,27 manifest niêm phong gồm 628 mục của milestone trước,838 pin nguồn/metadata và 292 file mirror không có drift mới; 165 đường dẫn thiếu từ trước vẫn được tách riêng. 541 file Android cũ giữ nguyên SHA. Source/candidate cũ và lịch sử ENDURE không đổi sau phục hồi; không suy ra ENDURE đã nghiệm thu.

Toàn bộ guard giữ nguyên: freshness 250 ms, input 200 ms, speedup 1, cap 500 ms, fsync trước sensor, không bỏ frame, sàn 10 GiB và dự phòng 256 MiB. Campaign giữ nguyên đồng hồ 5.400 giây, dùng hết 3 candidate và 2 fixture; không mở lượt thứ tư hay chạy30 phút.

## Bàn giao tiếp

Ưu tiên sửa **contract quan sát/điều hướng UI native** và **đường đóng phiên khi lỗi sau READY**. Kiểm mock/fault injection cả trước và sau cấp quyền; chỉ mở campaign ngắn mới khi hai lỗi được kiểm độc lập. Không cần thêm tính năng hoặc giảm guard để giải quyết điểm chặn này.

Bản thử cuối: `5ba39e0f7b1892f5b548ca01f32dfb93440a6648838b00bd87c783742f991a45`. APK giữ nguyên: `43318d48…5961`.

[Root verification](../evidence/runtime-acceptance02/ROOT-VERIFY01.json) · [QA lỗi lượt ngắn](../evidence/runtime-acceptance02/qa/SHORT2-FAILURE-REVIEW01.json) · [Kiểm bảo toàn cuối](../evidence/runtime-acceptance02/preservation-final01.json)
