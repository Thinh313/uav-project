# MISSION55 · Corpus và đối chiếu semantic, toán–địa lý

15/10/2026 · **DONE_SCOPED_OFFLINE_B1_B2**. Triển khai module cô lập theo RAGAS54, không tích hợp vào source/candidate đóng băng. Một agent thực hiện specification → build → verify; oracle có implementation khác không đồng nghĩa có người kiểm độc lập.

## Kết quả sử dụng được

- CLI chỉ đọc `pilot/mission55/cli.py compare BEFORE AFTER`: exit0 equal trong scope,2 different,3 review,4 rejected. So riêng header/Home, editable Survey design và cached executable items. Không bỏ ngầm camera/null/frame/doJumpId/extension, không gán flatten thành editable compatibility.
- Parser typed cho206/2000/2001/2500/2501, phân biệt camera ID/stream ID và receiver GCS của mission readback. Profile readback chỉ nhận các command đã có scope giữ lại của Copter4.7.1; schema MAVLink mới không được suy thành firmware support.
-50 plan tổng hợp/dẫn xuất của attempt cuối,11 fixture QGC có provenance giữ nguyên;79 ca số học/địa lý. Vector GeographicLib chính thức, wheel2.1/SHA/license và MAVLink XML được pin trong increment; không cài vào môi trường app hoặc `.venv`.
- Oracle/implementation riêng cho planar area, WGS84 inverse distance, unit/metric, ETA từng leg, optics/spacing/count/cadence/GSD, Home/AMSL/ellipsoid/geoid/terrain-calc/terrain-native, stale/no-data/session/boot và ridge. Count dùng endpoint policy tổng hợp rõ ràng, chưa phải chứng minh thuật toán QGC tương đương. Geodesic area là reference service bằng GeographicLib, chưa đối chiếu area thực của AERIS/RAGAS.
- Home10→7 được giữ là DIFFERENT: tọa độ ngang không đổi, AMSL suy ra từ file cho NAV tương đối giảm3m. Đối chiếu `qgc-home-height-geometry.json` cho thấy tác động thay vì chỉ đổi marker hoặc normalize Home.
-38 raw outbound MISSION_ITEM_INT trong hai journal cũ được decoder mới kiểm CRC/metadata.8 cycle readback19item khớp trong scope JSON đã decode. Chiều nhận **không có raw bytes**, nên CRC độc lập inbound là NOT_CHECKED.95 frame của session trước trong journal chuyến sau được cách ly. Boot không có trong journal, age context là replay tổng hợp, không chứng minh live freshness.
- ACK không tạo capture, duplicate/foreign/stale capture không cộng số; file declaration giả lập không trở thành ảnh thật. VerifiedPhysicalFiles luôn0 vì chưa có verifier media vật lý.

## Nghiệm thu và REQ/AC

| AC theo TIP | Kết quả cuối và giới hạn |
|---|---|
| AC01 camera | PASS_SCOPED_MOCK_REPLAY: mutation placeholder/drop/order/flags/ID/interval/count/reserved-null/video; không chứng minh camera/firmware thực thi ảnh hoặc video. |
| AC02 QGC | PASS_SCOPED_STORED_SEMANTICS: source SHA, design/cache/header, unknown extension và DO_JUMP review,50 synthetic +11 retained. QGC runtime/regeneration mới NOT_CHECKED. |
| AC03 Home/cao độ | PASS_SCOPED_MODEL: mismatch Home, frame/mode/display conflict, datum/đơn vị/nguồn/no-data/stale/reboot; mốc launch/geoid thực NOT_CHECKED. |
| AC04 toán–địa lý | PASS_SCOPED_ORACLES:79 numeric cases và kiểm analytic/library,20 primary geodesic vectors,20 seed55 local pairs; Vincenty từ chối không hội tụ gần antipodal. Không fallback sang cầu. Area ellipsoid/planar/coverage khác metric; ridge chỉ bảo đảm mẫu cung cấp, không toàn tế bào DEM hay obstacle clearance. |
| AC05 readback | PASS_SCOPED_RETAINED_REPLAY:8 cycle19item, đúng hướng receiver, rule AP4.7.1 command/field có ghi normalization. Raw inbound CRC/whole-flight continuity/newSITL NOT_CHECKED. |
| AC06 CLI/resource | PASS:6 CLI cases, bound256KiB/depth32, negative inputs;1.000item diff,20samples p95=29,59525ms trên host, max31,62525ms. Không phải độ trễ Fly/UI/AP/HeraHub. |
| AC07 bảo toàn | PASS: `evidence/mission55/preservation-final.json` failures=0; đối chiếu20.600 pin kế thừa gồm RAGAS54. Không suy ENDURE PASS hoặc hiện diện liên tục từ pin. Host khoảng37GiB trống, trên sàn20GiB. |

Functional final: **234 PASS,0 FAIL**, ở `evidence/mission55/run5/verification.json`. Verify riêng pha sau: **183 PASS,0 FAIL**, ở `evidence/mission55/verify1/verification.json`, gồm source-at-start, corpus/provenance/vendor byte match, syntax/CLI và các bite chống đổi top count hoặc nâng RAGAS runtime thành PASS. Không cộng run1–4 vào tổng cuối.

run1 giữ209PASS/1FAIL do test chờ nhãn antipodal trong khi engine đã từ chối bằng nhãn không hội tụ; run2 sửa expected classification và mở rộng typed camera; run3 thêm geometry/unit, run4 harden input/policy/resource, run5 trên source cuối và CLI đọc giới hạn bytes. Receipt/corpus các lần trước được giữ, không sửa để thành PASS. Source-at-start bắt đầu được seal từ run2; không tuyên bố source run1 đã được seal trước sửa.

## Bàn giao và bước tiếp

[README/CLI](../pilot/mission55/README.md), [corpus cuối](../evidence/mission55/run5/corpus.json), [test cuối](../evidence/mission55/run5/verification.json), [replay giữ lại](../evidence/mission55/run5/retained-replay.json), [oracle số](../evidence/mission55/run5/numeric-corpus.json), [so Home/cao độ](../evidence/mission55/run5/qgc-home-height-geometry.json), [hiệu năng](../evidence/mission55/run5/performance.json), [ADR067](../docs/ADR-067-ISOLATED-MISSION-SEMANTIC-ORACLES.md).

Increment khoảng4,3MiB; không có project copy hoặc scratch ngoài repo, build APK, emulator, SITL/soak mới, lệnh bay hoặc chữ ký mới. Không sửa canonical SOT/trust/source/candidate/ENDURE. Giữ toàn bộ dữ liệu kiểm và dependency có provenance trong module/evidence.

Bước tiếp: chạy B3 trên cùng corpus với QGC regeneration và AP SITL riêng, thu **raw hai chiều** cùng firmware/session/boot/time envelope. Sau khi giải quyết identity RAGAS manifest112/tên111, thêm binary RAGAS pin cho A/B. Chưa có bằng chứng ở đợt này để kết luận tương thích mọi Survey, ảnh thật, nghiệm thu HeraHub hoặc thay RAGAS/DJI.
