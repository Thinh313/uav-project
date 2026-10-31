# G17: ghép STABILITY16 vào bản thử cô lập

Ngày 24/10/2026. **READY-with-deferred trong phạm vi source/mock. Android–SITL: NOT RUN. Sản phẩm/beta tích hợp: NOT READY.**

STABILITY16 đã được ghép vào entry và ứng dụng hiệu lực G17, không còn chỉ là module kiểm độc lập. QA chốt gate `6578f70df62f92849b3a9fb63050a929534ec93988aa5cf4813cf12f492bf8ef`. Không sửa bản source/candidate cũ, STABILITY16, ENDURE hay ký production.

## Đã triển khai

- Admission dùng worker kiểm kê đầy đủ, chờ đóng worker trước khi tạo observer. Inventory G17 bao gồm bằng chứng G15 đã đóng; tuple policy/history/tổng được kiểm riêng, không tái sử dụng ngầm tuple G15 của STABILITY16.
- Ứng dụng chờ resource guard sẵn sàng và kiểm tick đầu trước khi mở listener. Lỗi hoặc đóng trong lúc khởi tạo không để listener tiếp tục mở. Thời gian khởi tạo được tính trong thời gian host còn lại, không cấp lại cửa sổ 2.700 giây.
- Khi đóng, thu hồi quyền và chặn dispatch ngay, chờ đúng thao tác mutation đang xử lý trước khi đóng journal. Không thêm hàng đợi, retry hoặc kéo dài deadline. Đường lỗi resource/UI persist vẫn hoàn tất cleanup, lưu lỗi và từ chối kết luận đóng sạch.
- Native chỉ cho managed restart khi receipt có `resourceEvidenceFailure:null`, cùng các kiểm payload/index gốc. Mã thoát 0 không đủ. QuotaWatch Python lấy mốc trước khi gửi admission, không làm mới tuổi dữ liệu khi kết quả đến muộn; đóng watch thì không nhận/trả mẫu mới.
- Luồng UI nhận bản sao sau validator gốc, giữ riêng clock và identity, ghi snapshot tối đa 32 KiB với tham chiếu nhỏ trong closure 64 KiB. Correlation thiếu/sai được ghi UNKNOWN; không đổi schema Android, cadence, quyền hay fsync của heartbeat.
- Kiểm trước hiệu ứng rằng số entry hiện có cộng recipe tương lai vẫn nằm dưới trần 16.384. Không tăng trần hoặc quota từng nhóm. Trần 8.192 entry hoạt động không có nghĩa toàn bộ luôn khả dụng khi lịch sử tăng.

## Nghiệm thu source/mock

| Nhóm | Kết quả và phạm vi |
|---|---|
| Khởi tạo/đóng ứng dụng | QA 8 ca PASS: trì hoãn, scan lỗi, tick đầu từ chối, đóng khi startup, lỗi đóng resource và persist UI. |
| Mutation đang xử lý | QA 4 ca PASS: thu hồi quyền tức thì, chờ thao tác trước seal, từ chối thao tác sau close, giữ ACTION_END đúng một lần. |
| UI và closure | QA 5 ca PASS trên ứng dụng hiệu lực; validator chạy trước consumer, tuổi theo host, giữ lỗi, sidefile/hash và từ chối cập nhật sau close. |
| Native freshness/restart | QA 8 ca tuổi quota và 4 ca managed closure PASS; giữ ngưỡng và clock gốc. |
| Quota/binding/CLI | QA 5 ca PASS: tuple mới, số policy không đổi, biên 16.384/16.385, đóng worker và CLI từ chối vật lý đúng. |
| Camera/media sidecar | Builder 15 ca PASS trên handler hiện tại: caller sáu key, Origin/CSRF/schema/hash/run/boot và fence history. Dữ liệu đối chứng G13 tái dùng có ghi nguồn, không phải media mới từ G17. |
| Nghẽn quota trong app G17 | Tiêm block 1.250 ms: heartbeat khoảng 10,36 ms. Khi chính fsync heartbeat bị chặn, vẫn thất bại khoảng 1.003,87 ms. Đây là fault injection có kiểm soát, không chứng minh nguyên nhân lỗi Android cũ đã được sửa. |
| Hành trình giao thức bản pin cuối | MockSocket `mdc38f4887ca74d249b8d`, 995 bản ghi raw; connect → preflight → cấp quyền → upload → ARM/Home/AUTO mô phỏng → ground → đóng review, index và đọc lại lịch sử PASS. |
| Kết quả thực thi giả lập | 4 fixture nominal/cut/lost receipt/outcome failure PASS. Đây là stub kiểm xử lý kết quả, không phải bay/cắt link/reboot ArduPilot thật. |

QA replay độc lập raw, WAL 3 bản ghi, index sequence 3, outcome `CLOSED_REVIEW_INDEXED` và lịch sử của lượt dương tính `02`. Marker `HOST_END_RETURNED_NOT_CLIENT_ACK` được giữ đúng nghĩa. Không cộng lại 35 ca STABILITY16 như ca mới; chỉ tái dùng sau đối chiếu chính xác thân worker và thay đổi tuple/import được phép.

## Giữ nguyên các lỗi và cách chạy

Lượt app01 dừng do sandbox từ chối phép kiểm tra tiến trình cha `kill(pid,0)`. Giữ nguyên app/raw/WAL lỗi, không dùng làm bằng chứng nhiệm vụ thành công. Runner tiếp theo dừng trước khi cấp phát app02 vì `--input-type=module` bị truyền sang file worker. Sửa cách gọi sang CommonJS stdin, không sửa ứng dụng/worker.

Root cho phép hữu hạn lượt gọi cuối sau khi QA kiểm loader: chỉ ba đường dẫn output đổi sang `02`, có literal count, inverse equality và SHA trước/sau; `execArgv` rỗng. Gate cũng được chạy bằng qualification đường dẫn trong bộ nhớ, không sửa file gate đã pin hay assertion. Giữ cả qualification lỗi và qualification thành công; không gộp kết quả các lượt. G17 có 0 request AP/SITL thật.

Trong quá trình ghép còn phát hiện và sửa vòng import CLI quota dẫn tới mã thoát 13; log/source trước sửa được giữ. CLI hiện trả lỗi vật lý đúng định dạng. Các lỗi runner và các bản thử trước không bị ghi lại thành PASS.

## Admission thật và phần chưa chạy

Root gọi quota admission bằng source cuối đã pin, filesystem thật, phase `before-host`, đủ bốn AP/hai host còn dự phòng. Kết quả exit 1, `PHYSICAL_FLOOR_RESERVATION`, không retry. Dung lượng cuối phép kiểm **27.934.720.000 byte, khoảng 26 GiB**, dưới mức khởi chạy 29 GiB.

Do đó chưa bắt đầu 31 mẫu/30 giây admission, chưa tạo host runtime, emulator 32/33 hay phiên AP mới. Gate 29 GiB, ngưỡng chạy 28 GiB, dự báo 15 giây và sàn 20 GiB giữ nguyên. Heartbeat 1.000/750/3.000 ms, UI age 1.200 ms, audit 10 giây/freshness 15 giây, speedup, frame và fsync guard không nới.

**Chưa nghiệm thu Android–SITL AUTO cùng video/payload, mất link, reboot, managed restart và persistence trên G17.** Không build/cài/ký APK mới, không dùng HeraHub/SDK. Nguyên nhân khởi phát heartbeat G15 vẫn UNKNOWN; log ngủ máy giải thích sự kiện stale sau đó ở mức tương quan, không thay bằng chứng sửa lỗi sớm hơn.

## Bảo toàn, footprint và bàn giao

Gate kiểm 1.523 pin, 31 helper, 21 module mới, 5 compiled artifact và stage 132 file tái dùng. **12.925 mục bảo vệ, 7 literal symlink và 8.527 entry lịch sử đều khớp**, fork gốc 20 file/870.221 byte còn chưa dùng. 95 đường dẫn Git đã thiếu từ trước nằm ngoài baseline bảo vệ, được giữ hồ sơ riêng; không tự phục hồi hay khẳng định toàn repo nguyên vẹn. Không tạo các receipt cuối G15 vốn chưa từng được ghi.

Phạm vi G17 lúc QA chốt khoảng 5,52 MB/198 file, dưới ngân sách 32 MiB. Projection 16.018 entry gồm dự phòng kế tiếp, dưới 16.384. Các fixture scratch do tác vụ tạo đã dọn, worker/app mock đã đóng; app01 lỗi và app02 thành công là bằng chứng, được giữ. Không xóa bằng chứng cũ, không tạo scratch ngoài repo, không có dependency/build/Docker mới cần dọn.

Danh sách dọn của Builder trong `builder-completion01.json/cleanup`: ba thư mục tạm sidecar, `builder-integration-scratch01`, bốn `builder-sitl-wiring01-{nominal,cut,pending-lost-receipt,post-outcome-failure}` và `builder-smoke-app`, tổng chín đường dẫn đều thuộc G17. Fixture Native/QA được liệt kê trong các receipt tương ứng và đã kiểm không còn. `builder-completion01.json` có SHA `e1d1df6ecf881cd869ffd2c00627c25711f7a653750392ae1e5d0303f604cc12`.

Entry mới: `pilot/beta06g17/entry.mjs`. Khi đủ điều kiện, controller dự kiến là `planning/beta06g17/qa-root-live32.py`, boot32/33, host-app17/-restart. Không chạy chỉ dựa vào báo cáo này: phải qua admission mới và các guard/pin hiện hành, không nối tiếp campaign đã thất bại.

Các receipt chính trong `evidence/beta06/generation17/`: `qa-final-gate01.json`, `flight-pins01.json`, `native-helper-freeze01.json`, `builder-source-freeze01.json`, `builder-real-mock-journey02.json`, `builder-sitl-handler01.json`, `builder-protocol-qualification03.json`, `qa-gate-command-qualification01.json`, `root-readonly-admission01.json`. Manifest bàn giao gắn SHA của báo cáo, source và bằng chứng; đây là kiểm toàn vẹn cục bộ, không phải ký phát hành.
