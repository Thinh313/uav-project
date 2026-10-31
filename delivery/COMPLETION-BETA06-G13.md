# AERIS: sửa heartbeat và kiểm Android–SITL G13

Ngày 23/10/2026. **OVERALL STATUS: NOT READY.** Bản sửa heartbeat đã đạt phạm vi source/mock/fault injection và được thử trên Android–SITL. Lượt thực tế dừng ở lỗi lưu sidecar video mới phát hiện; không chạy các kịch bản tiếp theo, không chạy lại campaign, không ghép kết quả cũ thành nghiệm thu mới.

## Kết quả phục vụ người dùng

Ứng dụng Android đã kết nối ArduPilot 4.7.1 SITL, kiểm preflight, upload/readback cùng model KML, duyệt Home sau arm, bay AUTO, quay về, hạ cánh/disarm và đóng hồ sơ bay. Camera/gimbal và video là tổng hợp/mock. Gói raw video đã được lưu nhưng sidecar liên kết nó với hồ sơ bay bị từ chối, nên **toàn bộ N1 chưa đạt** dù các phần raw bay và video riêng lẻ đã qua kiểm độc lập.

| Yêu cầu | Kết quả và bằng chứng |
|---|---|
| Giảm chặn heartbeat do kiểm lịch sử | PASS trong fault injection tương đương: cùng một lỗi đọc lịch sử 1250 ms, bản cũ 1005,10 ms timeout; worker7,00 ms. Không xác lập nguyên nhân khởi phát G12. |
| Giữ nguyên guard và ghi bền vững | PASS source/mock. Timeout1000 ms, nhịp750 ms, TTL3000 ms không đổi; chính fsync của heartbeat bị chậm1250 ms vẫn timeout1002,67 ms. Không cache metadata, không bỏ frame/journal, không ACK trước barrier. |
| Ngăn lệnh vượt kiểm lịch sử chưa xong | PASS 9 ca fence độc lập; giữ witness lỗi trước sửa. Worker chết chặn lệnh điều khiển và packet điều khiển có id khác 0 tiếp theo; heartbeat id0 vẫn được phép. |
| Bootstrap/foreground/epoch và snapshot | PASS mock độc lập. Snapshot thực sau lượt G13 đọc đủ 19 file/34 record,18 artifact cũ giữ SHA, journal15467 byte nguyên vẹn, append0. Đây là cùng một boot, chưa phải persistence sau cold restart. |
| AUTO SITL và hồ sơ raw | PASS độc lập:8175 RX/413 TX,12 mục upload/24 readback qua2 vòng,0 ghi tham số;4 lệnh camera206 được giữ; AUTO/ground/disarm/review được xác nhận từ raw. |
| Video riêng lẻ | PASS cửa sổ chọn30,0025 giây:880 frame,29,330889 FPS; P95 cận trên47,233459 ms; viewer ready316,1 ms; phục hồi relay pause500 ms trong542,4 ms. Không đại diện toàn chuyến bay. |
| Camera/gimbal mock | Capture tổng hợp đã commit WAL 109; review accepted tại index 114. actualImages0, không suy ra ảnh chụp vật lý từ ACK. |
| Lưu sidecar và nghiệm thu overlap | FAIL: RAW_SAVED_SIDECAR_FAILED:ACTIVE_FOREGROUND_CLIENT_EPOCH_REQUIRED. Raw report vẫn giữ đúng SHA; không tạo sidecar giả hoặc báo overlap PASS. |
| Mất link, reboot, host restart và cold persistence27 | NOT RUN sau lỗi bắt buộc của N1. Không cộng chứng cứ các generation trước. |

Coverage của4 kịch bản bắt buộc mới: **0/4 đạt trọn vẹn**; N1 đã chạy và lỗi tại sidecar, F1/N2/F2 chưa chạy. Không lấy số test mock để thay coverage sản phẩm.

## Chẩn đoán và phạm vi sửa

Bản sửa tối thiểu chuyển cùng thuật toán đọc/SHA lịch sử đã đóng sang 1 worker đọc, có giới hạn queue/input/result, giữ kiểm ngữ cảnh và fail closed. Cập nhật chẩn đoán theo request/document để phân biệt clock browser, Node và Python; không trừ clock khác miền khi thiếu mapping hợp lệ. Prototype async journal chưa được tích hợp.

Đối chứng healthy-load không cho thấy tăng tốc idle: max89,66 ms cũ và 92,03 ms worker đều đạt. Giá trị đã chứng minh là cô lập một lỗi stall đã mô hình hóa, không phải lời khẳng định mọi độ trễ hay nguyên nhân G12 đã được giải quyết. Giới hạn serialized1 MiB/16 pending không phải chứng nhận heap;224 MiB policy là dự phòng ghi đĩa, không phải capRAM.

Lỗi G13 là regression hợp đồng của route. Caller media-panel gửi đúng6 trường sidecar cũ, không có client identity; predispatch fence mới lại gọi client.assert trước nhánh sidecar cũ. Tại lỗi, bootstrap vẫn active và 582/582 request ACK,0 failed/0 deadline. Ring/UI được giữ sau đó đạt778/778;107 ACK event còn lưu có max111,6 ms. Đây là các snapshot/event bị giới hạn, không phải trace đầy đủ mọi heartbeat.

Mock trước G13 có GET media diagnostics và handler flight archival, nhưng chưa bao phủ POST sidecar6 trường của caller thật. Kết quả xanh của các phép kiểm đó vẫn có giá trị trong phạm vi của chúng và đã bỏ sót regression này.

Bản sửa sidecar đã được chuẩn bị riêng tại [route-contract.mjs](</Users/os/Downloads/AI technique/aeris/pilot/heartbeat13sidecarfix/route-contract.mjs>): chỉ thêm `media-sidecar` vào đúng ngoại lệ identity của route cũ; hàng rào worker/pending-state, Origin/CSRF, schema 6 trường, SHA, source và ngữ cảnh flight không đổi. Builder tái hiện lỗi baseline và kiểm 16 ca. QA độc lập kiểm 9 ca có kết quả PASS trong [qa-contract02.json](</Users/os/Downloads/AI technique/aeris/evidence/beta06-heartbeat13sidecarfix/qa-contract02.json>), SHA f7c38595ba9e4bccbbd0d803398ecd8643ca7182eae74c6af5fd66be2d820eba. Các bộ ca có phần giao nhau, không cộng thành một thước đo coverage sản phẩm.

QA giữ lại lần lỗi assertion thứ tự durability và source của lần đó: thực tế có thêm barrier ACTION_END fsync hợp lệ. Chỉ sửa kỳ vọng kiểm thử rồi kiểm lại; không sửa sản phẩm để né barrier. Candidate đã qua caller 6trường, Origin/CSRF/schema/ngữ cảnh sai, mất worker và pending-state lỗi; thứ tự journal flush → sidecar fsync → directory fsync → ACTION_END fsync → HTTP end được xác nhận.

Đây là replay qua handler/worker/saveSidecar thật với raw report, snapshot journal và media state đã ghi; HTTP request được dựng lại theo caller và measurement context, không phải request bytes được capture trên dây. **Patch chưa ghép vào runtime, chưa có Android–SITL xác nhận.** G13 không đổi và vẫn NOT READY. Tổng phạm vi patch 10 file, 278146 byte, không tạo generation/campaign mới.

## Bảo toàn và đóng runtime

QA kiểm lại11564đường dẫn bảo vệ,7 symlink literal, 1247 pin,28 helper và 7482 entry lịch sử bằng SHA; tất cả khớp.20file870221 byte của workspace gốc giữ nguyên, WAL bản sao chỉ append16971 byte theo quyền đã cấp. Source/candidate đóng băng, ENDURE và trust không đổi.95đường dẫn đã thiếu từ trước và hồ sơ khôi phục125đường dẫn vẫn được phân biệt; không khẳng định mọi đường dẫn tồn tại liên tục.

Dung lượng thấp nhất quan sát36070359040 byte (33,59 GiB), cao hơn sàn 20 GiB. Giữ nguyên timeout, speedup 1, relay pause 500 ms và quota; không xóa dữ liệu để ép gate.

Đã dừng publisher/viewer trước đóng host. Host56792, emulator56859 và helper56801 đều có quan sát exit0; controller56740/PTY34949 exit0. Đối chiếu ps:4PID đã vắng;5cổng8872/8873/5972/5582/5583 không còn listener; ADB không còn emulator. Container SITL d54a47…1820 giữ lại, exited0/OOMfalse; không xóa container/volume. Docker image prune chạy đạt, thu hồi0B. Không build/cài/ký APK mới.

Có 21 yêu cầu AP thực trước G13, thêm 1 lần G13, tổng 22; các MockSocket/video-source không được tính là AP thực. Frozen summary giữ tên field lịch sử `historicalActual19NotPooled`; tên field cũ không thay số 21/22 đã đối chiếu. Cụm nhắc không suy diễn numeric exit trong helper cũng không phủ định các exit0 thực đã ghi trong closure/journal G13.

## Bằng chứng chính

- [TIP và phạm vi](</Users/os/Downloads/AI technique/aeris/planning/heartbeat13fix/TIP.md>), [ADR](</Users/os/Downloads/AI technique/aeris/planning/heartbeat13fix/ADR.md>).
- [Đối chứng fault injection](</Users/os/Downloads/AI technique/aeris/evidence/beta06-heartbeat13fix/flight-handler-experiment-fd02.json>).
- [Gate source/mock độc lập](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation13/qa-final-gate01.json>), SHA 83b51564bd18cd63cf1e3dfe2264e4ecc9a0fc41f87a7767770cf5da2bc62a4e.
- [Raw bay](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation13/qa-n1-raw01.json>), [media riêng lẻ](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation13/qa-n1-media01.json>), [capture/index/closure](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation13/qa-n1-capture-index-closure01.json>), [lỗi sidecar](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation13/qa-n1-fault01.json>).
- [Snapshot/prefix Android](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation13/qa-native-prefix01.json>), [đóng runtime](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation13/qa-closure-summary01.json>).
- [Tổng kiểm cuối độc lập](</Users/os/Downloads/AI technique/aeris/evidence/beta06/generation13/qa-final-runtime-summary01.json>), SHA 1a4deaabd6a587fd54f9a6c4dbe5e162ddb9f0ce337d00a9310971de05e988ff.

## Bước kế tiếp và giới hạn

Bản sửa hợp đồng sidecar đã qua mock độc lập. Bước kiểm thực tế tiếp theo phải ghép patch vào một generation cô lập riêng, qua gate mới rồi chạy đầy đủ N1 → F1 → managed restart → N2 → F2 → cold persistence. Không chạy generation/campaign khác trong tác vụ hữu hạn này; không G14, chạy lại hay sửa G13. Chưa được gọi beta-ready, production-ready hay chứng nhận Hera/camera thật từ kết quả này. Đối chứng LLM không áp dụng cho sửa lỗi giao thức tất định này.

## Dọn dẹp scratch

Không copy cả project, không cài dependency ngoài repo, không xóa dữ liệu người dùng. Danh sách fixture tạm đã dọn nằm trong phụ lục dưới, đối chiếu từ receipt và kiểm đường dẫn không còn. File báo lỗi, raw trace, report và container bằng chứng đều giữ lại.

<details>
<summary>101 đường dẫn fixture tạm đã dọn, kiểm không còn tại thời điểm bàn giao</summary>

- `evidence/beta06-heartbeat13fix/codex-tmp-flight-healthy-20261023-TU9ybE`
- `evidence/beta06-heartbeat13fix/codex-tmp-flight-healthy-20261023-tlezuf`
- `evidence/beta06-heartbeat13fix/codex-tmp-flight-old-history-stall-20261023-I8Pciu`
- `evidence/beta06-heartbeat13fix/codex-tmp-flight-old-history-stall-20261023-SzuiVu`
- `evidence/beta06-heartbeat13fix/codex-tmp-flight-own-durable-stall-20261023-MJcK2Y`
- `evidence/beta06-heartbeat13fix/codex-tmp-flight-worker-history-stall-20261023-UWaBx2`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-0oQiWw`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-5jzKdG`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-7rNbB3`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-AKgdFI`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-ANxZAi`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-BTB6wz`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-Czoq1b`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-HJFsYj`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-JtXGbR`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-SDPX0C`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-UplmEo`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-ZrMapz`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-a6NN07`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-fence-20261023-zVsOaR`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-http-20261023-5tlgK0`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-http-20261023-IriVdg`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-http-20261023-M6Pm7P`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-http-20261023-UXLTyx`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-http-20261023-foGjY8`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-http-20261023-gIZ5GR`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-http-20261023-ndozRt`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-http-20261023-v3URYJ`
- `evidence/beta06-heartbeat13fix/codex-tmp-qa-send-20261023-ufDPaG`
- `evidence/beta06-heartbeat13sidecarfix/codex-tmp-heartbeat13sidecarfix-20261023-AgIPcZ`
- `evidence/beta06-heartbeat13sidecarfix/codex-tmp-heartbeat13sidecarfix-20261023-Qy8Axg`
- `evidence/beta06-heartbeat13sidecarfix/codex-tmp-heartbeat13sidecarfix-20261023-W6Iitv`
- `evidence/beta06-heartbeat13sidecarfix/codex-tmp-heartbeat13sidecarfix-20261023-czv4H2`
- `evidence/beta06-heartbeat13sidecarfix/codex-tmp-heartbeat13sidecarfix-20261023-qa-DxmV4Y`
- `evidence/beta06-heartbeat13sidecarfix/codex-tmp-heartbeat13sidecarfix-20261023-qa-TFJ2h4`
- `evidence/beta06-heartbeat13sidecarfix/codex-tmp-heartbeat13sidecarfix-20261023-qa-f3qljS`
- `evidence/beta06-heartbeat13sidecarfix/codex-tmp-heartbeat13sidecarfix-20261023-qa-pW6kOB`
- `evidence/beta06/generation13/codex-tmp-g12-binding-20261023-pmk1dmsp`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-history-20261023-G6djSj`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-history-20261023-aujNL3`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-history-20261023-c3hkuS`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-history-20261023-ijI5hn`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-history-20261023-jv4aC7`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-history-20261023-nhAmPK`
- `ValueError:'evidence/beta06/before.json' is not in the subpath of '/Users/os/Downloads/AI technique/aeris/planning/beta06g13/codex-tmp-beta06g13-20261023-9v2ncxq3' OR one path is relative and the other is absolute.`
- `ValueError:'evidence/beta06/before.json' is not in the subpath of '/Users/os/Downloads/AI technique/aeris/planning/beta06g13/codex-tmp-beta06g13-20261023-soij9s2i' OR one path is relative and the other is absolute.`
- `ValueError:'evidence/beta06/before.json' is not in the subpath of '/Users/os/Downloads/AI technique/aeris/planning/heartbeat13fix/codex-tmp-heartbeat13fix-20261023-4_8g1klo' OR one path is relative and the other is absolute.`
- `ValueError:'evidence/beta06/before.json' is not in the subpath of '/Users/os/Downloads/AI technique/aeris/planning/heartbeat13fix/codex-tmp-heartbeat13fix-20261023-c02fs02b' OR one path is relative and the other is absolute.`
- `ValueError:'evidence/beta06/before.json' is not in the subpath of '/Users/os/Downloads/AI technique/aeris/planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-_9p2d_m5' OR one path is relative and the other is absolute.`
- `ValueError:'evidence/beta06/before.json' is not in the subpath of '/Users/os/Downloads/AI technique/aeris/planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-v3le51do' OR one path is relative and the other is absolute.`
- `codex-tmp-beta06g13-20261023-31zvbyct`
- `codex-tmp-beta06g13-20261023-6e9gl5w2`
- `codex-tmp-beta06g13-20261023-7m7voxbt`
- `codex-tmp-beta06g13-20261023-9v2ncxq3`
- `codex-tmp-beta06g13-20261023-g278fik6`
- `codex-tmp-beta06g13-20261023-j43bbb13`
- `codex-tmp-beta06g13-20261023-mqjuu8cy`
- `codex-tmp-beta06g13-20261023-soij9s2i`
- `codex-tmp-beta06g13-20261023-uarvz2uc`
- `codex-tmp-beta06g13-20261023-uuqgt056`
- `codex-tmp-beta06g13-20261023-xm595tak`
- `codex-tmp-beta06g13-20261023-zjqvubq4`
- `codex-tmp-heartbeat13fix-20261023-4_8g1klo`
- `codex-tmp-heartbeat13fix-20261023-581zbff9`
- `codex-tmp-heartbeat13fix-20261023-7wnmywzf`
- `codex-tmp-heartbeat13fix-20261023-a6p0z1io`
- `codex-tmp-heartbeat13fix-20261023-c02fs02b`
- `codex-tmp-heartbeat13fix-20261023-crebr7s3`
- `codex-tmp-heartbeat13fix-20261023-etz03a4c`
- `codex-tmp-heartbeat13fix-20261023-gb9p7glf`
- `codex-tmp-heartbeat13fix-20261023-gi35oii9`
- `codex-tmp-heartbeat13fix-20261023-hewl4k_3`
- `codex-tmp-heartbeat13fix-20261023-ipt6ouc7`
- `codex-tmp-heartbeat13fix-20261023-jakr1kb8`
- `codex-tmp-heartbeat13fix-20261023-kpc4jyqr`
- `codex-tmp-heartbeat13fix-20261023-krerw2bn`
- `codex-tmp-heartbeat13fix-20261023-kt41zny0`
- `codex-tmp-heartbeat13fix-20261023-npn9o9qj`
- `codex-tmp-heartbeat13fix-20261023-nx2meet2`
- `codex-tmp-heartbeat13fix-20261023-oiuepg8u`
- `codex-tmp-heartbeat13fix-20261023-vbyrfh_9`
- `codex-tmp-heartbeat13fix-20261023-xg09moa1`
- `planning/beta06g13/codex-tmp-qa-g13-exit-20261023-0_2czb2v`
- `planning/beta06g13/codex-tmp-qa-g13-exit-20261023-0vzy32rk`
- `planning/beta06g13/codex-tmp-qa-g13-exit-20261023-tl48trvt`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-1w6vakfy`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-7qd1m2z0`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-9lhs_xrm`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-_9p2d_m5`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-exhrlt89`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-l5d46mri`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-lsatw1v5`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-nyvvamwb`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-oken6aeq`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-pwza5jd5`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-rda66j5q`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-sib5fk3_`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-v3le51do`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-wf29b2xo`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-y8idpzz3`
- `planning/heartbeat13fix/qa-scratch/codex-tmp-qa-heartbeat13fix-20261023-zb9py14l`

</details>
