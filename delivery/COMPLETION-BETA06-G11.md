# BETA06 G11: NOT READY, bản vá ground đã kiểm mock

Ngày 23/10/2026, giờ Việt Nam. Phạm vi: môi trường native cô lập, ArduPilot SITL dự kiến, video tổng hợp và payload mock. Không có HeraHub, camera thật, build/cài mới hoặc chữ ký mới.

## Kết quả cho người dùng

Đã tiếp tục sau gián đoạn, hoàn tất ghép clock dùng chung và sửa kiểm bind cổng, nghiệm thu source/mock rồi mở một lượt G11 có admission mới. Host đầu tiên và Android đã khởi động, video tổng hợp đã được nhận trong cockpit. Lượt thực dừng trước Connect/ARM vì bộ ghi metadata ground tham chiếu `os.environ` nhưng thiếu import `os`.

Đã sửa lỗi này ở bản vá riêng và kiểm độc lập bằng mock. Bản vá **chưa ghép vào runtime đang khóa**. Chưa hoàn tất mục tiêu reboot/persistence Android–SITL; không báo DONE hay beta READY.

## Phạm vi đã kiểm

| Yêu cầu | Kết quả | Giới hạn |
|---|---|---|
| Sửa kiểm cổng host, chặn listener đang hoạt động | PASS ở fixture và nghiệm thu source | Nguyên nhân socket lịch sử G9 vẫn UNKNOWN |
| Mở host thực qua admission mới và probe mới | PASS | Chỉ host1; chưa kiểm restart host2 của ứng dụng |
| Clock cùng mốc uptime giữa controller và Android helper | PASS mock và thực tới boot Android | Không khôi phục anchor từ JSON; không chứng nhận sleep/resume |
| Admission host | 31 mẫu / 30,122 giây; tối thiểu 38,988 GiB | Không thay ngưỡng 29 GiB hoặc các guard |
| Android 13/API33, APK đã có, 4 CPU | PASS boot/setup/cold activity start | APK SHA giữ nguyên, không cài hoặc ký lại |
| Store trước thử | 19 file / 34 record / 15.467 byte, đúng SHA gốc | Không có snapshot sau đóng runtime; không suy ra mutable AVD không đổi |
| Video host → Android | Đã quan sát ingress và calibration hợp lệ | Chưa đo cửa sổ FPS 30 giây hoặc nghiệm thu cold-start |
| Ground 75 giây thực | FAIL trước khởi tạo báo cáo | `NameError: name 'os' is not defined`; chưa có ground receipt |
| AUTO + video/payload, mất link, restart host, reboot AP | NOT RUN | AP0, Connect0, ARM0; không cộng kết quả G9 |
| Persistence/restart Android ở boot23 | NOT RUN | Không mở boot thứ hai |
| Bản vá import `os` riêng | PASS mock, QA độc lập | Chưa tích hợp hoặc chạy lại Android–SITL |

Các nguồn kiểm không được cộng thành tỷ lệ hoàn thiện sản phẩm: source/mock, trao đổi clock thực, video ingress và bay SITL là các phạm vi khác nhau.

## Chẩn đoán và sửa

G10 được giữ nguyên. Bản sửa clock G11 dùng `CLOCK_UPTIME_RAW_NS` cùng host boot, giải quyết mốc `time.monotonic()` khác nhau giữa các tiến trình Apple Python. Giữ nguyên các thời hạn 2700/540 giây, dự phòng 225/240/90 giây, quyền payload và mọi quota. Guard cổng vẫn kiểm bảng LISTEN trước/sau khi giữ hai socket; không bỏ probe, không dùng SO_REUSEPORT và không tuyên bố bảo đảm TOCTOU.

Trong G11 thực, lỗi tại `planning/beta06g11/qa-ground-soak.py:49` xảy ra trước `try/finally`. Controller giữ lỗi trong journal; ground receipt vắng mặt là đúng trạng thái. Nhánh ground trước Connect không tự latch `campaignFailed`; Root chủ động dừng theo điều kiện kết thúc đã chốt, không giả là tự động fail-close toàn campaign.

Khoảng trống kiểm thử đã được ghi nhận: kiểm clock trước đó xác nhận import/default/provider và đường permit, nhưng chưa gọi constructor báo cáo của `collect()`. Không viết lại các receipt PASS cũ.

Bản vá tại `planning/ground11fix/qa-ground-soak.py` chỉ thêm import `os`, giữ nguyên AST của mọi hàm và các guard. Builder và QA độc lập kiểm bốn nhóm: delta duy nhất; bản gốc tái hiện NameError trước reader/writer; bản vá lưu báo cáo từ chối qua finally; bản vá hoàn tất 75 giây giả lập với 151 lần kiểm mẫu, chuỗi hash journal và hai lần renewal cho publisher lẫn viewer. Clock/UI/pause/writer là mock được ghi rõ; không có chờ 75 giây thực hay kết luận chất lượng SITL từ kết quả này.

## Bảo toàn và đóng phiên

QA cuối xác nhận đúng mode/byte/SHA và link literal của 10.001 đường dẫn bảo vệ, 7 symlink, 1.071 pin, 25 helper và 6.052 entry lịch sử. Fork dữ liệu gốc 20 file / 870.221 byte và prefix journal không đổi, append0. Phạm vi này không phải chứng nhận toàn repo đầy đủ: 95 đường dẫn thiếu đã biết và sự cố khôi phục 125 đường dẫn vẫn được ghi riêng; không có tuyên bố hiện diện liên tục.

Đã dừng publisher, viewer, host, emulator và controller. Host PID 16766 exit 0 có receipt managed stop; emulator PID 16846 exit 0/error null có closure. Controller PTY exit 0 được quan sát. Exit số của helper PID 16814 không được ghi riêng, nên để NOT_RECORDED. Kiểm độc lập xác nhận bốn PID 16709/16766/16814/16846 không còn và các cổng 8872/8873/5972/5582/5583 không LISTEN. Không có AP/container G11 được tạo.

Dung lượng tối thiểu quan sát được: 40.735.748.096 byte, khoảng 37,94 GiB, trên sàn 20 GiB. Không đổi guard; không xóa dữ liệu người dùng, source/candidate, ENDURE, container hay volume. Docker image prune theo quy định trả 0 B. Không có bản sao toàn project hoặc dependency mới ngoài repo.

Các scratch Flight đã dọn theo receipt source-test: `codex-tmp-g11-clock-20261022-pjcvf3mb`, `codex-tmp-g11-clock-20261022-ao5yzyj2`, `codex-tmp-g11-binding-20261022-doh3hics` trong generation11. Fixture đồng hồ nội bộ dùng TemporaryDirectory đã tự dọn; không có scratch ngoài repo. Bằng chứng và synthetic fixture của bản vá được giữ.

Tệp permit 949 byte do fixture lỗi ghi nhầm trước lượt thực đã được chuyển tên bảo toàn đúng SHA sang `builder-clock-fixture-leaked-permit01.json`, cùng incident receipt. Không xóa byte, ghi đè, reset ledger hay bỏ qua stale permit. QA đã xác nhận namespace thật sạch trước G11. Bản sửa fixture và thiếu console tạm của lần thất bại được ghi trung thực.

## Bằng chứng chính

- `evidence/beta06/generation11/qa-final-gate01.json`: source/mock trước chạy, SHA `ebca29f3f89714559bdd9d66cb2a6a0f50c15e231388e87aa218f7e500c3d649`.
- `evidence/beta06/generation11/qa-final-runtime-summary01.json`: kết luận NOT READY, SHA `4c50b1be40f9ad2f1ae05eb3912a00f4f6cfe293bffb2845fa1dd837c0c496e9`.
- `evidence/beta06/generation11/qa-closure-summary01.json`: Root đóng phiên, trạng thái PID/cổng, các giới hạn và sửa tham số caller proof-writer trước khi ghi.
- `planning/ground11fix/builder-effective01.json`: kiểm bản vá mock, SHA `9134ddf356c26104ba0b8c56107c0818440abfd605531b2e93a5f96e81472b5f`.
- `planning/ground11fix/qa-independent01.json`: QA bản vá, SHA `7184193f4614062409ae9de6217412faeb20c62330242a52128313c6db94825c`.
- `planning/ground11fix/HANDOVER.md`: cách áp dụng bản vá trong bước ghép tiếp, không phải runtime đã cập nhật.

![Video tổng hợp đã hiển thị trong cockpit Android](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation11/g11-before-n1.png>)

## Việc còn lại và disposition

Bước tiếp là ghép đúng bản vá đã kiểm vào một bản thử cô lập mới, kiểm effective ground entry trước admission, rồi chạy các kịch bản còn thiếu trong ngân sách mới được chốt. Không tiếp tục hoặc sửa G11 đã đóng, không mở G12 trong lượt này. Chưa có bằng chứng thay thế nghiệm thu AUTO/video/payload, mất link/reboot hoặc cold persistence.

OVERALL STATUS: **NOT READY** cho mục tiêu Android–SITL trọn luồng. Bản vá thiếu import: **PASS trong phạm vi mock**, chưa tích hợp. So sánh LLM/agent baseline không áp dụng cho sửa lỗi xác định này; chưa đưa ra tuyên bố ưu việt sản phẩm hoặc chứng nhận thiết bị.
