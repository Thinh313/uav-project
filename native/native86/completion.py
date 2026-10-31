from pathlib import Path
import json,html,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/native86';D=R/'delivery';v=json.loads((E/'verification.json').read_text());apk=R/v['acceptedApk'];now=v['at']
md=f'''# NATIVE86 — COCKPIT85 trên Android

Trạng thái: **PASS trong phạm vi Android/mock đã kiểm, có giới hạn ghi nhận**. {now}

Đã đưa mock COCKPIT85 vào shell Android riêng `vn.rtr.aeris.native86`, ký APK development và kiểm trực tiếp trên emulator-5582: Android33 ARM64, WebView101.0.4951.61,1280×800,density160. Đây là shell WebView đóng gói Android, chưa phải nghiệm thu trên HeraHub.

[APK development03]({apk}) · SHA256 `{v['apkSha256']}`. Chữ ký v2/v3 đạt; chứng thư development RtR, không phải production. SHA APK đã cài khớp gói host.

## Kết quả chính

- Khảo sát: nhập `Khao_sat_NATIVE86`,31m/Home,1,1m/s; lưu và compile polygon mẫu thành2điểm. Journal draft khớp byte qua restart.
- Preflight: profile mock mới, Home/chuẩn độ cao/tuyến được xác nhận có chủ ý. Profile stale khóa Fly; không kéo dài freshness để vượt kiểm.
- Fly: ACK không tăng cursor;2điểm quan sát và hạ cánh mock tạo `COMPLETED_MOCK`. Review ghi0ảnh thực, operational=false, authorityRestorable=false.
- Hồ sơ hoàn tất khớp toàn bộ byte qua force-stop và Android reboot với boot ID mới. SIGKILL đúng PID app khi cursor1 giữ nguyên prefix và thêm `INTERRUPTED_RESTART`; không tự hoàn tất, tiếp tục bay hay phục hồi quyền.
- SAF: xuất/provider-readback/nhập staging/xác nhận chuyển workspace/restart đạt. Bản nhập có cùng HEAD, thế hệ gốc được giữ. Guard4snapshot từ chối lần bắt đầu mới, không tự xóa. Tạo workspace mới đòi gói xuất đã kiểm của đúng HEAD hiện tại.
- UI:28trạng thái chọn lọc,2theme,4màn chính,9điểm mở popup và workspace.160kiểm UI/package đạt; footer thẳng logo0CSSpx, hai đảo công cụ cùng tâmY0CSSpx. Không thấy nút đang bật trong popup bị che hay tràn chữ ở các trạng thái đo.
- Android WebView thiếu`:has()` được xử lý bằng state mirror; hỗ trợ backdrop-filter được quan sát. Lỗi bàn phím fullscreen che ô nhập ở build01 đã sửa trong build02/03; ô tên và số xuất hiện trên bàn phím, phần biên tập cuộn được.

## Kiểm độc lập và bảo toàn

Replay trên host của dữ liệu thu từ Android xác minh SHA, chain và semantic của30revision duy nhất và2gói xuất;4ca âm kiểm cờ operational/authority và manifest hỏng bị từ chối. Đây là đối chiếu thuật toán riêng với dữ liệu app đã lưu, cùng một agent thực hiện build rồi QA, không tự nhận hội đồng QA độc lập.

Regression:31controls/icon,46freshness/history,16workflow; Java Policy22,DraftStore31,ArchiveEdges4,Workspace12,History11;104kiểm ghép asset tĩnh. Build03 và44asset trong APK khớp byte nguồn hiện tại.41/42asset COCKPIT85 được dùng đúng byte; index là thay đổi có ghi nhận, layout86 là lớp mới. Không chạy module fly84 override mock mặc định.

52432đường dẫn bảo vệ khớp SHA trước/sau,0thiếu hoặc lệch. Source/candidate đóng băng và ENDURE được giữ nguyên. Kiểm này chứng minh byte hiện tại; không xóa lịch sử sự cố đường dẫn thiếu hoặc khẳng định đường dẫn luôn hiện diện liên tục.

Emulator/controller thoát sạch, cổng5582/5583 đóng. Dung lượng nhỏ nhất khi runtime chạy:{v['minRuntimeFreeGiB']:.2f}GiB; sau dọn:{v['afterCleanupFreeGiB']:.2f}GiB, giữ sàn20GiB. Đã dọn89file tải/chunk/archive và bytecode tạm riêng của NATIVE86 (~2,03GiB), giữ APK/AVD/appdata/evidence và một SDK cache tái sử dụng có372file khớp pin. Không xóa dữ liệu khác, runtime cũ hay bằng chứng.

## Giới hạn và phần chưa kiểm

- Một picker SAF thứ hai được giữ mở quá60giây do quá trình thao tác kiểm, UI báo `NATIVE_COMMIT_UNKNOWN_NO_RETRY`; callback provider đến muộn vẫn có thể ghi file. Đã đối chiếu chỉ đọc toàn bộ manifest/byte trước khi chủ ý tạo workspace mới, không retry tự động. UX timeout này còn cần cải thiện; không suy ra mọi giao dịch chọn tệp kéo dài đã đạt.
- WebView101/UIAutomator đôi khi thiếu subtree; thao tác dùng screenshot hiện tại khi AX thiếu, không dùng XML cũ.28ảnh và báo cáo renderer được đối chiếu; renderer là tự quan sát, không phải attestation. Không tuyên bố mọi pixel/mọi trạng thái đều đạt.
- Chưa kiểm HeraHub, joystick/nút cứng thật, video thật, camera/gimbal hay UAV thật. Chưa chạy SITL trong lượt này; chưa benchmark FPS/GPU/độ trễ trên tay cầm hoặc WebView khác. Không có host token, bridge bay hay ký production.
- Các thông số footer và ảnh nền là dữ liệu đặt/minh họa, không phải telemetry hoặc ảnh thực. Bản này đủ cho hành trình diễn tập Android đã nêu, chưa đủ thay Ragas để bay thương mại.

## Bước tiếp theo

Ưu tiên xử lý vòng đời picker SAF dài và thông báo quota/recovery rõ nghĩa cho người dùng; sau đó nối main Fly mới với nguồn SITL chỉ đọc, kiểm freshness/reboot rồi mới mở chuỗi nhiệm vụ có quyền có thời hạn. Không gộp bằng chứng mock với SITL/Hera thật.

## Bằng chứng

[Verification]({E/'verification.json'}) · [UI QA]({E/'verification-ui.json'}) · [Raw replay]({E/'captured-replay02.json'}) · [Preservation]({E/'preservation-final.json'}) · [Crash/restart]({E/'crash-restart-verification.json'}) · [Android reboot]({E/'android-reboot-verification.json'}) · [Cleanup]({E/'cleanup.json'})

![Review Android]({E/'android86-review-completed.png'})
'''
(D/'COMPLETION-NATIVE86.md').open('x').write(md)
req=''.join('<tr><td>'+html.escape(q['id'])+'</td><td>'+html.escape(q['status'])+'</td><td>'+html.escape(q['result'])+'</td></tr>'for q in v['requirements'])
page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AERIS · NATIVE86 completion</title><style>@font-face{{font-family:Barlow;src:url('../native/native86/assets/fonts/Barlow-Medium.ttf')}}@font-face{{font-family:Barlow;src:url('../native/native86/assets/fonts/Barlow-Bold.ttf');font-weight:700}}*{{box-sizing:border-box}}body{{margin:0;background:#f2f3ef;color:#17201d;font:17px/1.6 Barlow,system-ui}}main{{max-width:1160px;margin:auto;padding:36px 32px 80px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:center;border-bottom:1px solid #bec6c0;padding-bottom:20px}}.brand{{font-size:30px;font-weight:700}}.brand i{{font-size:20px;font-style:normal;margin-left:20px}}small{{color:#526057}}h1{{font-size:clamp(32px,5vw,56px);line-height:1.1;letter-spacing:-.03em;margin:28px 0 16px}}h2{{line-height:1.2;font-size:25px;margin:36px 0 16px}}.pill{{border-left:4px solid #c7a52a;padding:12px 18px;background:#e7e9df}}.actions{{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}}a{{color:#284c3d;text-underline-offset:4px}}.actions a{{padding:12px 18px;border:1px solid #aeb8ae;border-radius:10px;text-decoration:none;font-weight:700}}.actions a:first-child{{background:#1c2923;color:white}}img{{width:100%;height:auto;display:block;border-radius:14px;border:1px solid #b4c0b7;margin:20px 0}}.scroll{{overflow:auto}}table{{width:100%;border-collapse:collapse;font-size:15px}}td,th{{padding:14px 12px;border-bottom:1px solid #cad0c8;text-align:left;vertical-align:top}}td:first-child{{white-space:nowrap}}td:nth-child(2){{overflow-wrap:anywhere;min-width:180px}}code{{font-size:13px;overflow-wrap:anywhere}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}.block{{padding:20px;border:1px solid #c2ccc4;border-radius:12px;background:#f8f9f5}}@media(max-width:700px){{main{{padding:24px 18px}}.grid{{grid-template-columns:1fr}}header{{align-items:flex-start}}}}</style><main><header><div class="brand">RtR <i>AERIS</i></div><small>NATIVE86 · Android mock<br>{html.escape(now)}</small></header><h1>COCKPIT85 đã chạy trên Android.</h1><p class="pill"><b>Đạt phạm vi mock đã kiểm.</b> APK development03 · Android33 ARM64 ·1280×800 · chưa nghiệm thu HeraHub.</p><div class="actions"><a href="../{v['acceptedApk']}">APK development03</a><a href="COMPLETION-NATIVE86.md">Báo cáo đầy đủ</a><a href="../evidence/native86/verification.json">Verification & REQ</a></div><code>SHA256 {v['apkSha256']}</code><img src="../evidence/native86/android86-review-completed.png" alt="Review mock đã hoàn tất trên Android,2điểm quan sát,0ảnh thực"><div class="grid"><div class="block"><b>Hành trình có hồ sơ</b><p>Khảo sát → preflight → Fly mock → review. ACK không tăng tiến độ; profile hết freshness khóa Fly.</p></div><div class="block"><b>Restart có kiểm toàn vẹn</b><p>Draft và review khớp byte qua restart/reboot. SIGKILL giữ prefix và ghi gián đoạn, không phục hồi quyền.</p></div></div><h2>Nghiệm thu từng yêu cầu</h2><div class="scroll"><table><thead><tr><th>REQ</th><th>Kết quả</th><th>Chứng cứ và phạm vi</th></tr></thead><tbody>{req}</tbody></table></div><h2>Giao diện Android ngày / đêm</h2><p>28trạng thái chọn lọc. Footer thẳng logo và tâm hai đảo lệch0CSSpx; IME không còn che ô đang sửa. Các popup có nội dung cuộn. Chưa có benchmark FPS hay kiểm phần cứng HeraHub.</p><div class="grid"><img src="../evidence/native86/android86-night-sheet-payload.png" alt="Popup payload theme đêm"><img src="../evidence/native86/android86-day-sheet-payload.png" alt="Popup payload theme ngày"></div><h2>Giới hạn còn lại</h2><p>Picker SAF quá60giây báo kết quả chưa biết; gói xuất muộn đã được đối chiếu độc lập, không tự retry. Workspace mẫu giữ tối đa4snapshot và khóa khi đầy, không tự xóa. Ưu tiên tiếp là UX pending/timeout/quota rồi nối Fly mới với SITL chỉ đọc.</p><p>Ảnh nền, camera và bản đồ là minh họa. Chưa kiểm joystick/video/camera/UAV thật; chưa ký production. Bản này chưa thay Ragas để bay thương mại.</p><h2>Bảo toàn và tài nguyên</h2><p>52432đường dẫn bảo vệ khớp SHA, không sửa source/candidate đóng băng hay ENDURE. Runtime đã đóng sạch. Free thấp nhất:{v['minRuntimeFreeGiB']:.2f}GiB; sau dọn:{v['afterCleanupFreeGiB']:.2f}GiB. Dọn89file tải trùng/tạm (~2,03GiB), giữ SDK cache tái sử dụng, AVD, APK và toàn bộ hồ sơ.</p><p>Build rồi QA trong cùng agent, không tự nhận nhóm kiểm độc lập. Kiểm byte hiện tại không thay lịch sử thiếu đường dẫn.</p></main></html>'''
(D/'COMPLETION-NATIVE86.html').open('x').write(page)
(D/'NATIVE86-LATEST.json').open('x').write(json.dumps({'milestone':'NATIVE86','status':v['status'],'apk':v['acceptedApk'],'sha256':v['apkSha256'],'report':'delivery/COMPLETION-NATIVE86.html','evidence':'evidence/native86/verification.json','scope':'ANDROID_MOCK_ONLY_NOT_HERAHUB_PRODUCTION'},indent=2)+'\n')
(D/'ROADMAP-NATIVE86.md').open('x').write('''# Roadmap sau NATIVE86

Done in scoped Android/mock qualification: COCKPIT85 integration, development03, full journey, persistence/app restart/Android reboot/running SIGKILL, selected28UI states, SAF timely export/import/activation/restart and exact preservation.

Next P1: improve explicit SAF pending/late callback handling without automatic retry, make outcomes reconcileable after activity/process restart, keep provider digest and workspace generation identity. Make snapshot quota/current-HEAD export guard messages actionable without automatic deletion. Mock/fault first; then Android. No change to frozen source/candidate or ENDURE.

Next P1: feed fresh read-only SITL telemetry into this new main cockpit through the isolated existing NATIVE84 seam; correct boot/session/altitude datum and review history. After readonly gate, explicitly authorized upload/readback/AUTO and loss/reboot tests. No reuse of mock evidence as actual flight proof.

Later hardware gate: exact HeraHub Android/WebView/GPU/MCU input/calibration/video SDK and PhaseOne/other payload capabilities, physical dual-operator/HIL/safety/flight validation. Production signing and commercial-release claims require their separate release gates.
''')
print('COMPLETION_N86_WRITTEN')
