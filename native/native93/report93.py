from pathlib import Path
import json,ast,html
R=Path(__file__).resolve().parents[2];E=R/'evidence/native93';D=R/'delivery';read=lambda n:json.loads((E/n).read_text());v=read('final-verification.json');b=read('build02.json');clean=read('cleanup.json');minimum=read('android-closure.json')['minFreeBytes']/2**30
assert v['status']=='PASS_ENGINEERING_CORRIDOR_ANDROID_SITL_FAULT_RESTART'
rows=[('93-01','PASS','Giữ đúng shared model92/fixture/compiler; Android chọn KML LineString, inspect feature, Home rồi compile/save.34ca mock polygon/corridor và11ca revoke/restart trước SITL.'),('93-02','PASS','Corridor Android→preflight4.7.1 chỉ đọc→grant→upload/readback→arm→Home mới→AUTO→takeoff/NAV/RTL→ground/disarm→review.12items/4camera commands/2readback.'),('93-03','PASS','Ngắt duplex bằng UI khi đang AUTO airborne; revoke, observer thấy GCS failsafe/RTL/hạ cánh; xác nhận ground riêng rồi đóng. Review gián đoạn, accepted=false.'),('93-04','PASS','Force-stop/mở lại APK khi AUTO: foreground lease hết hạn, no-grant/no-resume, model/review cũ nguyên byte. Reboot Android và cold bridge sau đóng giữ data nhưng không khôi phục quyền.'),('93-05','PASS','Python MAVLink decoder và receiver raw riêng kiểm ba lượt; một missionAccepted=true/hai false, cả hai lỗi failureVerified=true. Hai gói giả hoàn tất dù rehash bị semantic receiver từ chối.'),('93-06','PASS','62.059đường dẫn cũ qua92 giữ SHA; private files90/91/92 giữ28/94/76file. Runtime/PID/port sạch; sàn20GiB giữ. Không ký production hay promote candidate/ENDURE.')]
scenario='\n'.join('| '+r['label']+' | '+r['run']+' | '+('Hoàn tất'if r['accepted']else'Gián đoạn · '+str(r['failure']))+' | '+str(r['rawRecords'])+' |'for r in v['scenarioResults'])
md=f'''# COMPLETION — NATIVE93

18/10/2026 · DONE trong phạm vi engineering · `{v['status']}`.

## Kết quả và phạm vi

Đã kiểm corridor trên APK Android thật trong emulator với ArduPilot4.7.1 SITL; không phải dữ liệu replay giả làm bay thật. Model nhiệm vụ, Home/camera fixture và compiler từ92 được giữ nguyên byte/contract. Người vận hành chọn hành lang KML, inspect và compile ngay trên cockpit. Không có editor KML thứ hai hoặc thay ngầm bằng polygon.

Ba lượt độc lập dùng cùng modelSHA/planSHA/missionSHA, ba boot/container ArduPilot khác nhau: một nominal hoàn tất, một ngắt duplex và một force-stop/mở lại APK khi airborne AUTO. Hai fault đều quan sát GCS failsafe→RTL→ground/disarm qua observer; phải xác nhận riêng mặt đất trước đóng, không tự phục hồi quyền. Hai review lỗi giữ accepted=false và không được cộng thành mission PASS.

## Ma trận nghiệm thu

| REQ/AC | Kết quả | Hành vi và bằng chứng |
|---|---|---|
'''+''.join('| '+' | '.join(r)+' |\n'for r in rows)+f'''
Bằng chứng chính: `evidence/native93/final-verification.json`, các `*-qualification.json`, từng `runs/<run>/raw.jsonl`/observer/review/closure, `independent-raw-receiver`, `receiver93-final.json`, `receiver-false-completion93.json`, `preservation-after.json`, `runtime-closure.json`.

## Các lượt thực tế mô phỏng

| Kịch bản | Run | Kết quả nhiệm vụ | Raw records |
|---|---|---|---|
{scenario}

Mỗi lượt upload12mission items,4lệnh camera và đọc lại2vòng trước/sau arm; oracle derive kỳ vọng từ plan bất biến thay cho hardcode polygon16/6. Camera command có đúng giá trị/frame trong upload/readback, không thay bằng placeholder; không chứng minh camera đã chụp. PARAM_SET=0, ảnh thực=0. Nominal chỉ đạt khi raw có AUTO armed, takeoff geometry, đủ NAV, terminal RTL, fresh ground/disarm và gần Home. Fault receiver kiểm no-forward sau cut, GCS timeout thực quan sát trong khoảng gate4,5–15s, RTL/disarm/nearHome và recovery acknowledgement.

Model SHA `{read('nominal-qualification.json')['modelSha256']}`; planSHA `{read('nominal-qualification.json')['planSha256']}`; missionSHA `{read('nominal-qualification.json')['missionSha256']}`. Root workspaceHEAD `{read('android93-final-journal.json')['journals']['workspaces/initial']['head']}` không đổi qua ba lượt; SITL review journal append ba record.

## Restart, bằng chứng và chống kết luận sai

Force-stop APK khi AUTO được watchdog nhận là `NATIVE_FOREGROUND_LEASE_EXPIRED`. Mở lại bằng explicit source/token: native instance mới, grant=false; mọi byte workspace/CURRENT/review cũ không đổi trước khi đóng lượt thứ ba. Observer độc lập tiếp tục ghi sau control cut. Không tự reconnect, tiếp tục mission hay cấp lại quyền.

Sau khi đóng cả ba lượt, reboot Android33 và cold restart bridge: workspace/CURRENT/ba review và SAF ledger nguyên byte; plan/binding/run/grant rỗng ở cold host. Đây là reboot Android khi đã đóng, không phải reboot autopilot khi đang bay. SAF export có provider readback, receiver tái biên dịch KML/model và đối chiếu1tham chiếu trace→HEAD review hiện tại, giữ latest accepted=false. Snapshot cuối có{v['diagnosticTraces']}trace/{v['diagnosticEvents']}event, là committed prefixes chứ không toàn phiên bay.

Hai corpus gói sửa review thành accepted=true/complete=true rồi cập nhật SHA/manifest/contentId vẫn qua byte-integrity nhưng bị semantic replay từ chối. Không tạo success receipt cho chúng. Các gói mutant và raw gốc được giữ, không ghi đè lịch sử.

## VERIFY định lượng

- REQUIREMENT COVERAGE:6/6REQ93-01..06 (100% scope của task này, không phải tỷ lệ trưởng thành toàn sản phẩm).
- SCENARIO RESULTS:3/3kịch bản đạt tiêu chí tương ứng; một mission hoàn tất và hai failure được phân loại đúng.35đối chiếu cuối đạt.
- TECHNICAL HEALTH: build02 và V2/V3 signature verification đạt;45ca protocol/model mock;125file gate;33guard chạy trên Android ART;2ca giả hoàn tất bị từ chối. Không cộng các suite thành một tỷ lệ an toàn bay.
- OVERALL: READY_FOR_SCOPED_ENGINEERING_DELIVERY. Phần ngoài scope bên dưới còn NOT_CHECKED.

## Artifact development

APK `{b['apk']}` · SHA256 `{b['sha256']}` · SourceID `{b['sourceId']}`. App riêng `vn.rtr.aeris.native93`, versionCode93. Bản02 là bản duy nhất cài và kiểm trong tất cả ba lượt. Bản01 build host đạt nhưng còn metadata label/version cũ; sửa trước lần cài đầu. Ký development bằng key engineering đã có, chưa production.

Origin native93; bridge8872/AP5903/proxy5904; container93. Tái dùng AVD90/Android33 ARM64/WebView101 và SDK86 đã có, không download/install image. APK vẫn cần host bridge/compiler, explicit `source87=sitl` và token cấp chủ ý; chưa là bản standalone cài lên HeraHub rồi điều khiển Hera.

## Giới hạn và NOT_CHECKED

- Mới một corridor KML tổng hợp, không phải corpus khách hàng rộng, corridor dài/phức tạp/nhiều nhánh, terrain3D hay mapping accuracy thực địa. Envelope KML≤64KiB,10–30m,0,5–2m/s và Home/mặt đất phẳng/camera synthetic khóa.
- Mô hình ArduPilot internal quad; không hiệu chuẩn physics Hera, payload nặng, cảm biến tránh vật cản hay pin/âm thanh/video/camera thật. Gimbal/Phase One/dual-operator hardware chưa kiểm.
- Chưa cắt USB/radio HeraHub, khôi phục transport vật lý, process crash của firmware hay autopilot reboot airborne. Chưa kiểm fault giữa upload hoặc pending commit mới trong task này.
- Chưa standalone parser Android, mọi kích thước/accessibility/thermal/performance/pacing1×, ENDURE24h, production release hay thay Ragas ngoài thực địa. UI giữ layout blur glass cũ; panel engineering còn mã lỗi/notice kỹ thuật, chưa phải product-copy hoàn chỉnh.

## Bảo toàn và vệ sinh

62.059đường dẫn được đối chiếu SHA theo manifests qua92; fixture symlink metadata kiểm riêng. Không sửa source/candidate/ENDURE/canonicalSOT. Private workspace/trace trong appfiles90/91/92 đối chiếu28/94/76file với snapshot gốc. Chỉ xác nhận byte hiện tại, không khẳng định hiện diện liên tục của đường dẫn.

Runtime93 đóng sạch; port8872/5903/5904/5582/5583 không còn listener và bind lại được; PID bridge/emulator đã hết, container thử removed theo controller. Dung lượng thấp nhất quan sát{minimum:.2f}GiB, cao hơn20GiB. Dọn2APK unsigned riêng ({clean['removedBytes']:,}bytes); `.build` tự dọn, giữ signed APK/raw/fixture/AVD. Không temp copy toàn dự án; đã docker image prune -f, không prune container/volume.

Lưu quyết định tại `decisions-and-observations.json`: driver khôi phục vị trí cuộn panel sau recovery trước nút connect; thao tác đầu trúng vùng không-control, state xác nhận chưa phát kết nối rồi mới bấm control đang thấy. Không retry HTTP control hoặc thêm flight ngầm. Không chạy lại helper ghi đè vào receipt đã đóng.
'''
(D/'COMPLETION-NATIVE93.md').open('x').write(md)
road='''# ROADMAP sau NATIVE93

18/10/2026. Corridor Android–SITL đã qualified trên một fixture: nominal hoàn tất, duplex loss và APK restart có failsafe/khôi phục bằng chứng. Giữ riêng phần engineering và nghiệm thu Hera thật.

1. P1 — Corpus KML khách hàng thực: corridor dài/gấp khúc/đa feature, biên tọa độ, self-intersection, holes, Home/MSL/relative/terrain; đối chiếu toán độc lập về chiều rộng/coverage/overlap/ảnh/thời gian. Không suy coverage rộng từ một corridor.
2. P1 — Fault ở ranh giới upload/commit: mất liên kết giữa upload/readback, process restart khi journal pending, sai session/boot/HEAD, thu hồi quyền lúc thao tác. Nghiệm thu unknown/failure rõ ràng, no auto retry/regrant/resume; namespace mới, đủ headroom.
3. P1 — Native standalone: thu hẹp phụ thuộc host compiler/parser/bridge, đưa model/mission compiler đủ kiểm lên Android; UI chọn file KML và diff source→plan→upload, lỗi dễ hiểu, options corridor đầy đủ và kiểm accessiblity/IME/screen sizes.
4. Bench khi có thiết bị/API: HeraHub MCU/HID/calibration/deadman/transport, nguồn video đúng payload và tuổi; Phase One camera/gimbal và quyền hai operator. Hiện chưa có thiết bị/SDK, không gọi engineering APK là bản điều khiển Hera đã nghiệm thu.
5. Gate riêng: source/candidate integration, ký production, resource/thermal/pacing và ENDURE24h. Không tự promote từ PASS93.

Bước kế tiếp đề xuất: corpus KML khách và fault giữa upload/readback/commit trên cùng model, trước khi thêm tính năng demo mới. Không cần HeraHub cho phần chuẩn bị/mock; actual SITL theo admission và ngân sách dữ liệu.
'''
(D/'ROADMAP-NATIVE93.md').open('x').write(road)
old=ast.parse((R/'native/native91/report91.py').read_text());style=next(ast.literal_eval(n.value)for n in old.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='style'for t in n.targets)).replace('native91','native93')
trs=''.join('<tr>'+''.join('<td>'+html.escape(t)+'</td>'for t in r)+'</tr>'for r in rows)
page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AERIS NATIVE93 — Corridor & recovery</title><style>{style}</style><main><header><div class="brand"><i>RtR</i> AERIS</div><div class="tag">NATIVE93 · ENGINEERING PASS</div></header><h1>Corridor đã bay.<br>Lỗi được ghi nhận đúng.</h1><p>Android → model KML dùng chung → ArduPilot4.7.1 SITL → review. Một nhiệm vụ hoàn tất; hai lượt lỗi có GCS failsafe/RTL và review gián đoạn, không khôi phục quyền tự động.</p><div class="cards"><div class="card"><b>1 + 2</b><span>Một corridor hoàn tất · hai failure đã kiểm</span></div><div class="card"><b>12 / 4</b><span>Mission items / lệnh camera · hai readback mỗi lượt</span></div><div class="card"><b>62.059</b><span>Đường dẫn cũ giữ đúng SHA</span></div></div><div class="links"><a href="../{b['apk']}">APK development02</a><a href="COMPLETION-NATIVE93.md">Báo cáo đầy đủ</a><a href="../evidence/native93/final-verification.json">35 đối chiếu cuối</a><a href="ROADMAP-NATIVE93.md">Roadmap tiếp theo</a></div><figure><img src="../evidence/native93/nominal-fly.png" alt="Corridor trên Fly Android với telemetry SITL"><figcaption>Corridor từ KML LineString đã compile, lưu và upload/readback bằng cùng model. Telemetry từ autopilot mô phỏng; ảnh thực0.</figcaption></figure><h2>Ma trận nghiệm thu</h2><table><thead><tr><th>REQ/AC</th><th>Kết quả</th><th>Hành vi đã kiểm</th></tr></thead><tbody>{trs}</tbody></table><figure><img src="../evidence/native93/link-recovery-enabled.png" alt="Mất liên kết đã failsafe, hạ cánh và chờ xác nhận rõ"><figcaption>Observer đã thấy GCS failsafe và ground/disarm; quyền không phục hồi. Người vận hành xác nhận riêng trước khi đóng phiên gián đoạn.</figcaption></figure><figure><img src="../evidence/native93/android93-history-after-reboot.png" alt="Lịch sử ba lượt sau reboot Android"><figcaption>Sau reboot: một review hoàn tất và hai review chưa nghiệm thu bay. Không có failure nào được nâng thành mission PASS.</figcaption></figure><h2>Giữ nguyên bằng chứng, không suy quá phạm vi</h2><p>Hai gói thử được sửa thành “hoàn tất” và rehash đầy đủ vẫn bị semantic receiver từ chối. Cold host không tự phục hồi plan/binding/grant; workspace và SAF ledger nguyên byte sau reboot.</p><div class="note"><p>Chỉ một corridor tổng hợp trên internal quad. Chưa corpus KML khách rộng, physics Hera, thiết bị/payload/video thật hay autopilot reboot airborne. Android reboot được kiểm sau khi đã đóng phiên.</p><p>Không ký production, không promote candidate/ENDURE. APK engineering còn cần host bridge và token explicit; chưa là bản standalone điều khiển Hera.</p></div><h2>Bản bàn giao</h2><p>Development02, Android33 ARM64/WebView101. Ký engineeringV2/V3 và đọc lại đúng byte sau reboot.</p><code>SHA256 {b['sha256']}</code><p>Runtime/PID/port thử đã đóng sạch; trống tối thiểu{minimum:.2f}GiB. Dọn2APK unsigned riêng, giữ signed/raw/AVD và sandbox90/91/92.</p><footer>18/10/2026 · Single-agent SPEC / BUILD / VERIFY · Nghiệm thu engineering trong phạm vi host.</footer></main></html>'''
(D/'COMPLETION-NATIVE93.html').open('x').write(page);print('Completion MD/HTML and roadmap created; minGiB',round(minimum,2))
