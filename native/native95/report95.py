from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[2];E=R/'evidence/native95';v=json.loads((E/'final-verification.json').read_text());r=v['independentReceiver']
md=f'''# COMPLETION — NATIVE95

18/10/2026 · PASS engineering trong phạm vi TIP · APK development03 · {v['checkCount']} kiểm nghiệm thu cuối. Có một P2 còn mở ở chẩn đoán UI; chưa phải bản điều khiển Hera thương mại.

## Gap đã khép

Android tự biên dịch model KML/corridor và trực tiếp discovery, đọc preflight, upload/readback, arm tại mặt đất, xác nhận Home mới, vào AUTO, quan sát tuyến/RTL/hạ cánh/disarm và lưu review. Transport/control không còn qua HTTP GCS bridge trên laptop. Java sở hữu socket/journal/wire gate; các thuật toán nhiệm vụ và preflight chạy trong APK qua WebView. Laptop chỉ chạy autopilot/physics ArduPilot SITL và observer thụ động không gửi MAVLink payload.

Endpoint engineering cố định 10.0.2.2:5907, chỉ emulator thuộc tác vụ; đây chưa phải adapter radio/UDP/TCP thương mại trên HeraHub. Định danh container được đối chiếu như launch assertion, không phải xác thực mật mã của máy bay thật.

## Chứng cứ cuối

- APK03 trên Android13 ARM64/WebView101.0.4951.61,1280×800 được kéo lại từ Android và đối chiếu đúng SHA. Full E2E cuối: `{v['acceptedFinalRun']}`.
- Parser Python upstream tách khỏi runtime Java/JS kiểm SHA chain, CRC, target, quyền30s, typed parameters, mission payload và thực thi: {r['nativeRecords']} record native, {r['nativeRxFrames']} frame RX, {r['nativeTxFrames']} frame TX; {r['observerFrames']} frame ở observer riêng. Hai miền clock được kiểm riêng, không coi host và Android cùng clock.
- 12 mission item,2 readback,4 camera command,23 typed parameter checks,0 PARAM_SET,0 ảnh thực. Có bằng chứng vị trí/độ cao khi cất cánh, NAV, terminal RTL, mặt đất/disarm gần Home. Không suy execution từ ACK hay ảnh từ lệnh camera.
- Compiler đối chứng AUTO63 đã đóng băng khớp toàn bộ plan/model/hash; Home-review và geography digest khớp;862 điểm track giữ đủ trong giới hạn1200, không truncate.
- 34 kiểm mock trong4 suite, gồm đối chiếu3.627 frame nhận và215 frame gửi từ corpus đã nghiệm thu,9 negative wire/profile,6 journal,6 fault clock/CRC/foreign/reboot/stale,7 socket-generation/lifecycle/ack/queue/endpoint. Số34 là top-level checks của các suite, không phải tổng mọi assertion từng frame. Host JVM storage/file gates cũng chạy trong build03.
- Force-stop và reboot cuối giữ nguyên workspace/CURRENT/raw/review, không tự kết nối hay khôi phục quyền. Sandbox Native90–94 giữ nguyên270 file private. Review Android hiện có5 hồ sơ, phân biệt kết thúc và gián đoạn; đây là trạng thái native, không thay chứng nhận QA bên ngoài.
- 63.830 đường dẫn bảo vệ qua NATIVE94 khớp SHA, không có lỗi. Source/candidate/ENDURE không thay đổi. Chỉ xác nhận byte hiện tại, không tuyên bố các đường dẫn đã hiện diện liên tục trong quá khứ.

## An toàn và độ bền trong phạm vi này

Raw RX được fsync trước khi đưa vào JS; TX_INTENT fsync trước khi gửi frame lệnh và TX_WRITTEN ghi riêng. Socket không reconnect/retry/resume hoặc phục hồi quyền. Native gate ràng buộc target, phiên/boot, kiểu tham số, compiled item và quyền tạm thời; JS giữ preflight/mission gates riêng. Các giới hạn32MiB raw,queue,clock,stale và foreground fail closed. Đây chưa phải chứng minh mọi fault native IO/airborne.

## Các lần không được dùng làm PASS đầu-cuối

Docker chưa sẵn sàng ở prelaunch đầu; emulator đầu exit−9, nguyên nhân socket/OS chính xác chưa chứng minh. Giữ receipt, không suy thiếu dung lượng vì sàn vẫn đạt.

Run b có review native hoàn tất nhưng observer chỉ có heartbeat; không nghiệm thu đầu-cuối. Run c/d dừng ở read-only vì thiếu observer stream, không cấp quyền hay arm. Cấu hình per-channel message-intervals đã pin trước launch mới cho đủ dữ liệu; run e (APK02) và f (APK03 cuối) đã qua receiver riêng. Nguyên nhân chính xác vì sao MAV2 defaults chưa có stream chưa được chứng minh; không sửa hồi tố các receipt.

Mock tìm được lỗi pending-open của adapter JS: trả lời open muộn sau close có thể đặt lại writable. APK03 đã sửa, mock fail→pass được giữ và full E2E trên APK03 đã chạy lại. Không phát hiện sự cố này trong hai lần bay live.

## P2 còn mở: chẩn đoán UI

File UI diagnostic đã bão hòa mức cấu hình2MiB; guard cũ tính Java character nhưng ghi UTF-8 nên thực tế dư376B. Receipt cũ không được dùng làm runtime attestation. Phát biểu ban đầu quy do cap180 chưa đủ chứng cứ đã được hiệu chỉnh bằng receipt riêng. Harness nay chặn diagnostic stale; nghiệm thu cuối dùng ảnh UI mới và SHA private journal/raw. Không xóa/truncate bằng chứng. Flight raw journal là tệp khác, có bound theo byte và đã replay độc lập. Cần chuyển diagnostic sang generation/quota đúng byte trong NATIVE96.

## Artifact

- [APK development03](../{v['apk']}) · SHA256 `{v['apkSha256']}`.
- SourceID `{v['sourceId']}`.
- Cert development hiện có: `3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800`, v2/v3 đạt; không ký production/candidate.
- [VERIFY](../evidence/native95/final-verification.json), [receiver cuối](../evidence/native95/runs/{v['acceptedFinalRun']}/receiver95.json), [semantic oracle](../evidence/native95/runs/{v['acceptedFinalRun']}/semantic95.json), [reboot](../evidence/native95/restart03.json), [preservation](../evidence/native95/preservation-final03.json), [TIP](TIP-NATIVE95.md), [ADR110](../docs/ADR-110-NATIVE95-DIRECT-ANDROID-MAVLINK.md).

## Chưa kiểm và bước tiếp

HeraHub/radio/HID/video thật, PhaseOne/gimbal/nhiều payload/dual-operator thực; ma trận native direct airborne mất link/reboot/kill và unknown outcome; gói raw qua SAF và receipt bên nhận; lỗi native IO/quota/fsync dài hạn; DEM/RTK/PPK và chất lượng photogrammetry; pacing1×/thermal/24h/production. Chứng cứ host-bridge cũ không thay các gate native mới. Internal quad không phải mô hình Hera đã hiệu chuẩn.

NATIVE96 nên ưu tiên fault và bàn giao bằng chứng trên chính APK direct vừa hoàn thiện, cùng quota diagnostic; sau đó mới nối contract payload/quyền vào native và bench khi có thiết bị/API. Không mở khóa candidate đóng băng.

## Dọn dẹp

Đã dừng các runtime/emulator/controller thuộc95, cổng5907/5908/5582/5583 không còn listener. Xóa3 APK unsigned, .host95 và cache Python do tác vụ tạo (kể cả oracle-v2.pyc mới, đã kiểm không thuộc manifest bảo vệ). .build tự dọn; không tạo scratch/copy dự án ngoài repository. Giữ APK development01–03, AVD dùng lại và mọi evidence. Docker image prune đã chạy, thu hồi0B, không prune volume/container. Dung lượng thấp nhất {v['minimumFreeGiB']:.2f}GiB, trên sàn20GiB.
'''
(R/'delivery/COMPLETION-NATIVE95.md').open('x').write(md)
road='''# ROADMAP sau NATIVE95

18/10/2026. Android direct MAVLink → AP4.7.1 internal-quad SITL đã qua E2E với APK development03; không còn GCS/control HTTP bridge host. Chưa nghiệm thu Hera thật.

1. P1 — NATIVE96: fault ngay trên APK direct: disconnect/reboot/Android lifecycle/kill ở ranh giới upload, readback, arm/Home và AUTO; bảo toàn unknown outcome, không retry/reconnect/regrant/resume. Observer nguồn khác chỉ đọc. Xuất raw native qua SAF, độc lập verify/receipt, restart ở bên nhận. Sửa diagnostic generations và quota UTF-8 đúng byte; không tự xóa bằng chứng.
2. P1 — Contract payload và quyền vào native: PhaseOne discovery/settings/capture correlation, gimbal/camera routing nhiều target, hai operator và thu hồi quyền khi mất link. Giữ unknown cho thiếu SDK/hardware; mock không thành bench PASS.
3. Hardware gate — HeraHub MCU/HID/calibration/deadman/radio/video, model/firmware/SDK payload cụ thể, bench props-off rồi HIL và flight có quy trình. Đây là phụ thuộc còn thiếu để thay Ragas trên Hera.
4. Qualification — field survey/corridor/DEM/RTK/PPK, geometry/customer quality, resource/pacing/thermal/24h trên cấu hình triển khai; release trust/signing/rollout được nghiệm thu trước khi tích hợp candidate hoặc ký production.

Không dùng số milestone làm tỷ lệ hoàn thành thương mại. Ưu tiên luồng native bay và payload có chứng cứ, tránh tăng thêm nhánh mock rời rạc. Giữ source/candidate/ENDURE và sàn20GiB cho các bước tiếp theo.
'''
(R/'delivery/ROADMAP-NATIVE95.md').open('x').write(road)
rows=[('Android → ArduPilot','PASS · direct','Discovery → preflight → upload/readback → Home → AUTO → review'),('Toàn vẹn hồ sơ','PASS · restart','Raw fsync · SHA chain · reboot · không khôi phục quyền'),('Nguồn đối chiếu','PASS · riêng','Python upstream + observer thụ động + compiler đã đóng băng'),('Chẩn đoán UI','P2 còn mở','Quota2MiB; cache stale bị loại khỏi chứng cứ runtime'),('HeraHub / payload thật','CHƯA KIỂM','Cần thiết bị/API và bench; chưa ký production')]
tr=''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>'for x in row)+'</tr>'for row in rows)
page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AERIS · NATIVE95</title><style>@font-face{{font-family:Barlow;src:url('../native/native95/assets/fonts/Barlow-Medium.ttf')}}*{{box-sizing:border-box}}body{{margin:0;background:#101313;color:#edf0ec;font:18px/1.6 Barlow,system-ui}}main{{max-width:1120px;margin:auto;padding:48px 28px}}header{{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #3b4240;padding-bottom:20px}}b.logo{{font:bold italic 30px system-ui}}small,.muted{{color:#aab6af}}.eyebrow{{color:#e7c83b;letter-spacing:.13em;font-size:14px;margin-top:50px}}h1{{font-size:clamp(32px,5vw,62px);line-height:1.07;max-width:900px;margin:18px 0 24px}}p{{max-width:900px}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin:36px 0}}.stats div{{border-top:1px solid #758178;padding:18px 0}}.stats strong{{display:block;font-size:36px;line-height:1.2}}table{{border-collapse:collapse;width:100%;margin:36px 0}}td{{padding:20px 12px;border-top:1px solid #39443e;vertical-align:top}}td:first-child{{padding-left:0;width:25%}}td:nth-child(2){{width:22%;color:#e8cb4b}}a{{color:#f0d34b;text-underline-offset:5px}}.links{{display:flex;gap:24px;flex-wrap:wrap;margin:32px 0}}img{{display:block;width:100%;border:1px solid #455249;border-radius:12px;margin:28px 0}}.notice{{border-left:3px solid #e7c83b;padding-left:20px;margin:32px 0}}code{{overflow-wrap:anywhere;font-size:13px}}footer{{border-top:1px solid #39443e;padding-top:20px;margin-top:36px;font-size:15px}}@media(max-width:700px){{.stats{{gap:12px}}td{{font-size:15px;padding:12px 8px}}}}</style><main><header><div><b class="logo">RtR</b> &nbsp; AERIS</div><small>NATIVE95 · 18.10.2026</small></header><div class="eyebrow">ENGINEERING DELIVERY · APK DEVELOPMENT03</div><h1>Android trực tiếp điều hành nhiệm vụ SITL.</h1><p>Đã đưa transport và điều khiển MAVLink vào APK: một model KML/corridor đi xuyên suốt preflight, readback, Home, AUTO và review. Laptop chỉ chạy autopilot/physics giả lập cùng observer thụ động.</p><div class="stats"><div><strong>12 / 2</strong><small>mission item / vòng readback</small></div><div><strong>10.753</strong><small>frame RX native được đối chiếu</small></div><div><strong>0</strong><small>PARAM_SET · ảnh thực</small></div></div><table>{tr}</table><div class="notice">PASS trong phạm vi engineering NATIVE95. Internal quad chưa phải Hera đã hiệu chuẩn; chưa phải bản điều khiển HeraHub thương mại. Camera command không chứng minh có ảnh thực.</div><div class="links"><a href="../{v['apk']}">APK development03</a><a href="COMPLETION-NATIVE95.md">Báo cáo đầy đủ</a><a href="../evidence/native95/final-verification.json">VERIFY · {v['checkCount']} checks</a><a href="ROADMAP-NATIVE95.md">Bước tiếp theo</a></div><img src="../evidence/native95/03-fly-telemetry-midflight.png" alt="Fly trên APK03: telemetry quan sát trực tiếp từ ArduPilot SITL, camera chưa có ảnh thực"><p class="muted">Raw native và observer riêng xác nhận cất cánh, NAV, RTL, mặt đất/disarm. Compiler đối chứng khớp toàn bộ plan; quyền30s không tự phục hồi. Chưa kiểm fault airborne native, radio/video/payload thật hay production.</p><img src="../evidence/native95/95-final03-history-fresh.png" alt="Lịch sử native sau reboot, dữ liệu được kiểm SHA, không khôi phục quyền"><footer>63.830 đường dẫn bảo vệ khớp SHA. Tối thiểu {v['minimumFreeGiB']:.2f}GiB trống; runtime thuộc95 đã đóng. Đã dọn3 APK unsigned và cache/host compile thuộc tác vụ.<br><small>APK SHA256 <code>{v['apkSha256']}</code></small></footer></main></html>'''
(R/'delivery/COMPLETION-NATIVE95.html').open('x').write(page)
(R/'delivery/NATIVE95-LATEST.json').open('x').write(json.dumps({k:v[k]for k in ['status','apk','apkSha256','sourceId','acceptedFinalRun']},indent=2))
print('NATIVE95_COMPLETION_WRITTEN')
