from pathlib import Path
import json,html,hashlib
R=Path(__file__).resolve().parents[2];E=R/'evidence/native94';v=json.loads((E/'final-verification.json').read_text());b=json.loads((E/'build05.json').read_text());minimum=v['minimumFreeGiB']
md=f'''# COMPLETION — NATIVE94

18/10/2026 · PASS engineering · APK development05. {v['checkCount']} kiểm cuối đạt; R94-1..6 đạt trong phạm vi TIP, không phải phần trăm hoàn thành toàn dự án.

## Kết quả sản phẩm

Android tự chọn file KML qua SAF, đọc đối tượng, lập tuyến polygon/corridor, chỉnh chiều rộng corridor, biên dịch và lưu bằng một model92. Khâu này không cần parser/compiler của laptop hoặc token bridge. Bản nhập phải được local-recompile trước khi xác nhận kích hoạt. Lịch sử review vẫn đọc được khi bridge đã tắt.

SITL vẫn dùng bridge trên host cho transport/control. Kết nối chỉ đọc đòi host biên dịch độc lập và khớp toàn bộ plan đã commit; không thay thế âm thầm bản nhiệm vụ và không tự cấp quyền/upload/arm/AUTO.

## Kiểm chứng

- 126 mock assertions: 60 ca XML/KML đối chiếu Python; 24 cặp toàn bộ plan/hash đối chiếu AUTO63, kèm camera spacing, lineage, sai datum/Home và host attestation. Thuật toán hình học được tái dùng, không gọi đây là chứng minh toán độc lập.
- Android13 ARM64 / WebView101.0.4951.61 / 1280×800: SAF KML → compile offline → save; export/readback → nhập/recompile → xác nhận activation; force-stop và reboot giữ nguyên byte journal/CURRENT.
- Mutant đổi camera206 rồi rehash record/plan/archive đầy đủ: cấu trúc archive được nhận để staging, semantic replay chặn activation. Thế hệ bị từ chối được giữ để audit, không tự dọn. KML có thuộc tính __proto__ bị chặn bằng KML_ATTRIBUTE, workspace không đổi.
- Hai vòng Android–ArduPilot4.7.1 SITL (build04 và cuối05): preflight → upload/readback → Home sau arm → AUTO → mặt đất/disarm → review. Mỗi vòng 12 item,4 camera command,2 readback;0 PARAM_SET,0 ảnh thực. Raw JS và dialect Python upstream đối chiếu CRC/target/item/camera; receiver độc lập nhận gói đóng với receipt. Không xác thực nguồn thương mại từ receipt này.
- Source/candidate/ENDURE và lịch sử trước:62.732 đường dẫn khớp SHA; sandbox Native90–93 không đổi. Dung lượng tối thiểu {minimum:.2f}GiB, trên sàn20GiB. Tất cả runtime thuộc tác vụ đã đóng, token đã gỡ.

## Artifact cuối

- APK: [{Path(v['apk']).name}](../{v['apk']})
- APK SHA256: `{v['apkSha256']}`
- SourceID: `{v['sourceId']}`
- Development certificate SHA256: `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800` (khóa engineering hiện có, không ký production).
- [VERIFY](../evidence/native94/final-verification.json), [corpus/mock cuối](../evidence/native94/mock05/mock94.json), [lineage](../evidence/native94/compiler-lineage.json), [ADR109](../docs/ADR-109-NATIVE94-OFFLINE-PLANNING.md), [TIP](TIP-NATIVE94.md).

## Sửa lỗi trong quá trình kiểm

Timeout chọn KML trước đây dùng thông báo commit-unknown của writer dù chưa ghi workspace. Bản cuối phân biệt KML_SELECTION_TIMEOUT_NO_COMMIT và chờ tối đa300s, không áp dụng kết quả đến muộn. Positive SAF/negative KML đã kiểm; chưa chờ hết300s theo đồng hồ thực. Rà soát cuối chặn thêm thuộc tính __proto__; build05 chỉ thay đúng KML reader so với04, toàn bộ mã điều khiển và storage giữ nguyên byte. Toàn bộ run/receipt04 được giữ, không ghi đè.

## Giới hạn và gap còn lại

Chưa phải bản điều khiển Hera được nghiệm thu. Native transport bay vẫn qua host trong bài SITL này; chưa có bench HeraHub/HID/radio/video/PhaseOne hoặc payload vật lý và dual-operator thực. Chỉ camera tổng hợp, Home cố định và flat-world minh thị;10–30m,0.5–2m/s,100m,64KiB KML. Không suy từ ca này rằng DEM/địa hình, RTK/PPK thực hay chất lượng bản đồ khách hàng đã đạt. Chưa mở lại ma trận fault giữa upload/readback/commit trên94; giữ nguyên bằng chứng93. Không có ENDURE24h/pacing/thermal/production qualification mới và chưa tích hợp source/candidate đóng băng.

## Dọn dẹp

Đã xóa5 APK unsigned và cache Python thuộc94; .build tự dọn. Không tạo scratch ngoài repository, không copy toàn dự án. Giữ APK ký development01..05, evidence và AVD dùng lại. Docker image prune đã chạy, không prune volume/container.
'''
(R/'delivery/COMPLETION-NATIVE94.md').open('x').write(md)
road='''# ROADMAP sau NATIVE94

18/10/2026. Đã gỡ phụ thuộc laptop cho inspect/compile/import semantic của khâu lập nhiệm vụ Android. Hai E2E nominal trên SITL được nghiệm thu engineering; chưa thay Ragas trên Hera thực.

1. P1 — Native MAVLink transport trực tiếp Android → owned ArduPilot SITL: bỏ bridge điều khiển host, discovery firmware/typed parameters/freshness chỉ đọc trước; tiếp đó preflight, explicit grant, upload/readback, Home sau arm và AUTO/review. Giữ một model và authority volatile, không tự nối lại hoặc resume.
2. P1 — Fault tại ranh giới upload/readback/commit: mất link/reboot/sai boot–session–HEAD, unknown outcome, journal pending; kiểm no auto retry/regrant/resume. Corpus khách hàng và toán–địa lý độc lập về corridor/coverage/ảnh/thời gian trước mở rộng envelope bay.
3. Bench khi có thiết bị/API — HeraHub MCU/HID/calibration/deadman/radio/video; PhaseOne/gimbal và nhiều payload; hai operator thật. Chuẩn bị contract đã có nhưng không suy mock thành tích hợp thực.
4. Gate triển khai — thermal/resource/performance/pacing/24h, đóng gói và ký production, tích hợp candidate có kiểm soát; không mở khóa source/candidate/ENDURE trong94.

Trọng tâm: nối hoàn chỉnh lõi native tới autopilot, sau đó bench phần cứng; không mở thêm nhánh mock để thay cho hai gap này. Không đưa tỷ lệ hoàn thành toàn dự án khi chưa có ma trận nghiệm thu phần cứng và triển khai.
'''
(R/'delivery/ROADMAP-NATIVE94.md').open('x').write(road)
rows=[('Lập tuyến offline','PASS Android','KML SAF · polygon/corridor · compiler tại chỗ'),('Toàn vẹn workspace','PASS Android','Nhập/recompile · explicit activation · restart/reboot'),('Kế hoạch → AUTO','PASS SITL','Hai vòng04/05 · 12 item · 4 camera · 2 readback'),('Tay cầm/Hera/payload thực','CHƯA KIỂM','Cần thiết bị/API và bench; chưa phải bản triển khai')]
tr=''.join('<tr><td>'+html.escape(a)+'</td><td>'+html.escape(c)+'</td><td>'+html.escape(d)+'</td></tr>'for a,c,d in rows)
page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AERIS · NATIVE94</title><style>@font-face{{font-family:Barlow;src:url('../native/native94/assets/fonts/Barlow-Medium.ttf')}}*{{box-sizing:border-box}}body{{margin:0;background:#101313;color:#edf0ec;font:18px/1.6 Barlow,system-ui}}main{{max-width:1120px;margin:auto;padding:48px 28px}}header{{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #3b4240;padding-bottom:20px}}b.logo{{font:bold italic 30px system-ui}}small,.muted{{color:#aab6af}}.eyebrow{{color:#e7c83b;letter-spacing:.13em;font-size:14px;margin-top:50px}}h1{{font-size:clamp(32px,5vw,62px);line-height:1.07;max-width:900px;margin:18px 0 24px}}p{{max-width:880px}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin:36px 0}}.stats div{{border-top:1px solid #758178;padding:18px 0}}.stats strong{{display:block;font-size:36px;line-height:1.2}}table{{border-collapse:collapse;width:100%;margin:36px 0}}td{{padding:20px 12px;border-top:1px solid #39443e;vertical-align:top}}td:first-child{{padding-left:0;width:24%}}td:nth-child(2){{width:21%;color:#e8cb4b}}a{{color:#f0d34b;text-underline-offset:5px}}.links{{display:flex;gap:24px;flex-wrap:wrap;margin:32px 0}}img{{display:block;width:100%;border:1px solid #455249;border-radius:12px;margin:28px 0}}.notice{{border-left:3px solid #e7c83b;padding-left:20px;margin:32px 0}}code{{overflow-wrap:anywhere;font-size:13px}}footer{{border-top:1px solid #39443e;padding-top:20px;margin-top:36px;font-size:15px}}@media(max-width:700px){{.stats{{gap:12px}}td{{font-size:15px;padding:12px 8px}}}}</style><main><header><div><b class="logo">RtR</b> &nbsp; AERIS</div><small>NATIVE94 · 18.10.2026</small></header><div class="eyebrow">ENGINEERING DELIVERY</div><h1>Lập nhiệm vụ ngay trên Android.</h1><p>Đã gỡ phụ thuộc parser/compiler trên laptop cho khâu KML → lập tuyến → lưu/nhập workspace. Thực thi bay SITL vẫn qua bridge có xác nhận riêng.</p><div class="stats"><div><strong>126</strong><small>kiểm mock · 60 ca KML</small></div><div><strong>24</strong><small>cặp plan/hash đối chiếu</small></div><div><strong>2</strong><small>E2E Android–SITL04/05</small></div></div><table>{tr}</table><div class="notice">PASS trong phạm vi NATIVE94. Chưa phải bản điều khiển Hera được nghiệm thu; camera command không chứng minh có ảnh thực.</div><div class="links"><a href="../{v['apk']}">APK development05</a><a href="COMPLETION-NATIVE94.md">Báo cáo đầy đủ</a><a href="../evidence/native94/final-verification.json">VERIFY · {v['checkCount']} checks</a><a href="ROADMAP-NATIVE94.md">Bước tiếp theo</a></div><img src="../evidence/native94/05-review-offline-final.png" alt="Lịch sử review được kiểm SHA trên Android khi bridge đã tắt"><p class="muted">12 mission item · 4 camera command · 2 readback mỗi vòng. Có chứng cứ AUTO/NAV/RTL/hạ cánh/disarm;0 PARAM_SET,0 ảnh thực. Native94 độc lập với source/candidate đóng băng.</p><footer>62.732 đường dẫn bảo vệ khớp SHA. Sàn20GiB được giữ; tối thiểu {minimum:.2f}GiB. Runtime thuộc tác vụ đã dừng.<br><small>APK SHA256 <code>{v['apkSha256']}</code></small></footer></main></html>'''
(R/'delivery/COMPLETION-NATIVE94.html').open('x').write(page)
print('COMPLETION_NATIVE94_WRITTEN')
