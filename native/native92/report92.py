from pathlib import Path
import json,ast,html
R=Path(__file__).resolve().parents[2];E=R/'evidence/native92';D=R/'delivery';read=lambda n:json.loads((E/n).read_text());v=read('final-verification.json');b=read('build08.json');clean=read('cleanup.json');minimum=read('android-closure.json')['minFreeBytes']/2**30
assert v['status']=='PASS_ENGINEERING_ANDROID_SITL_MODEL92'
rows=[('92-01','PASS','Một model KML có revision/SHA, feature, options, camera/Home/datum; sửa dữ liệu hủy compiled. Polygon và corridor qua34ca mock.','mock92.json; assets/mission92.mjs'),('92-02','PASS','Một editor KML trên cockpit; bỏ editor riêng trong panel SITL. Preview lấy đúng mission items. Native và host đối chiếu cả committed document, HEAD, phiên bản và bốn binding.','android92-compiled07.png; flight-pins.json; build08.json'),('92-03','PASS','Android SAF export/import; tái biên dịch trước bật xác nhận. Gói đã thay camera thành placeholder và rehash bị từ chối kích hoạt, CURRENT/HEAD không đổi. Giữ stage bị từ chối để điều tra.','android-mutant-verification.json; receiver-negative.json; semantic-negative92.json'),('92-04','PASS','Hai lượt Android→read-only4.7.1→preflight→upload/readback→arm→Home mới→AUTO→takeoff/NAV/RTL→ground/disarm→review. Lượt cuối chạy APK08.','runs/sdd2b59b0672441a29b94; runs/sd9ad41fb943340d28f38'),('92-05','PASS','16mission items,6camera commands,2readback/lượt; giải mã JS và upstream Python riêng; receiver raw xác nhận thực thi.0PARAM_SET và0ảnh thực.','raw-verification-final.json của từng run; upstream-raw-oracle-closed08.json; independent-raw-receiver'),('92-06','PASS','Restart ứng dụng, update APK và Android reboot giữ toàn bộ workspace byte/CURRENT;2review vẫn còn. Cold host không phục hồi plan/binding/grant. SAF giữ2COMPLETED;33guard chạy trên ART.','final-verification.json; android92-cold-host08.json; diag-ops-after-reboot08.json'),('92-07','PASS','60.507đường dẫn bảo vệ và10link fixture91 đúng byte/target; sandbox90=28file,91=94file nguyên vẹn. PID/port riêng đã đóng; sàn20GiB giữ.','preservation-after.json; native90-private-preservation-final.json; native91-private-preservation-final.json; runtime-closure.json')]
md=f'''# COMPLETION — NATIVE92

18/10/2026 · PASS_ENGINEERING_ANDROID_SITL_MODEL92. Một agent chuyển SPEC→BUILD→VERIFY theo MethodBox; kiểm bằng decoder/receiver riêng không có nghĩa là QA team độc lập hay nghiệm thu hardware.

## Kết quả

Cockpit và SITL dùng chung một model nhiệm vụ KML có phiên bản. Editor chính giữ nguồn KML, đối tượng đã chọn, tên, độ cao/tốc độ/overlap/heading và camera/Home/datum; compiled gắn model revision/SHA. Panel SITL không có nguồn KML hoặc trường độ cao/tốc độ thứ hai. Đường legacy direct-plan bị từ chối. Native lấy actual committed document từ journal, kiểm HEAD/binding trước thao tác; host so sánh cả model và plan với bản đã biên dịch. Không chỉ tin hash do caller đưa lên.

Mock polygon+corridor đã chạy trước lần SITL thật. Hai lượt Android AUTO hoàn tất trong môi trường ArduPilot4.7.1 internal quad. Lượt cuối APK08 đi từ model nhập đã tái biên dịch qua preflight→upload/readback→arm→Home mới→AUTO→review. Receiver riêng tái biên dịch model và giải mã raw, không suy thực thi từ ACK.

## Ma trận yêu cầu

| Yêu cầu | Kết quả | Hành vi đã kiểm | Bằng chứng tương đối từ evidence/native92 |
|---|---|---|---|
'''+''.join('| '+ ' | '.join(x)+' |\n'for x in rows)+f'''
## Bản bàn giao

- APK development: `{b['apk']}`. KýV2/V3 engineering bằng certificate development đã có; cài và đọc lại đúngSHA sau reboot. Không ký production, không promote candidate.
- APK SHA256: `{b['sha256']}`.
- SourceID: `{b['sourceId']}`.
- App riêng `vn.rtr.aeris.native92`; bridge8870, AP5901/proxy5902, container92. Tái dùng AVD90/Android33 ARM64/WebView101, không tải SDK/image mới. APK engineering yêu cầu nguồn SITL explicit và token bridge cấp chủ ý; mở từ launcher không phải quy trình cài Hera đã nghiệm thu.
- Raw qualification:07=`sdd2b59b0672441a29b94`;08=`sd9ad41fb943340d28f38`. Cả hai có16items/6lệnh camera/2readback; hai receipt raw missionAccepted=true. Mỗi run có0partial RX/TX byte khi đóng. Không coi camera ACK là ảnh.
- Bộ kiểm cuối: {v['checkCount']}đối chiếu đạt;34ca model/protocol mock,13ca adverse ZIP/receipt +7ca adverse semantic,125file gate,33guard ART. Các suite này kiểm các lớp khác nhau, không cộng thành tỷ lệ hoàn thành toàn sản phẩm.

## Persistence, nhập gói và sai lệch

APK restart, update07→08 và Android reboot giữ toàn bộ byte của workspace/CURRENT, gồm các generation đã lưu. SAF export/import hợp lệ có bước xác nhận chủ ý; gói imported được biên dịch lại qua compiler host bất biến trước bật nút kích hoạt. Gói mutant camera được rehash toàn bộ nhưng bị IMPORTED_COMPILE_REPLAY_MISMATCH, không đổi workspace đang chọn; stage đã nhập vẫn giữ riêng và không tự dọn. Receiver cuối đối chiếu được1tham chiếu trace→HEAD review hiện tại. Gói trace chỉ là committed prefixes:9trace/94event trong snapshot cuối, không phải chứng cứ toàn phiên hoặc tự đủ chứng minh bay.

Hai review giữ trong lịch sử sau reboot. Cold host plan/model binding/session/grant rỗng; dữ liệu cũ không cấp quyền trở lại. Sau restart cần đối chiếu/biên dịch và preflight mới cho phiên mới. Hai giao dịch SAF đềuCOMPLETED với provider readback và journal nguyên byte.

Các lỗi phát triển được giữ tại `development-incidents.json`, gồm khởi tạo DOM, NetworkOnMainThreadException, scope Java sai, preflight hết hạn đã bị từ chối, test observer chờ sai event close và một capture descriptor sai đường dẫn. Lượt08 có lần chạm close khi Android còn hiển thị control disabled; raw chứng minh chưa có close, sau quan sát UI/control mới đã đóng đúng một request. Raw verifier gọi trước review đóng đã báo thiếu review; kết luận cuối chỉ dùng raw đã đóng và oracle `closed08`. Không xóa hoặc nâng các bằng chứng lỗi thành PASS.

## Giới hạn và phần chưa kiểm

- Chỉ polygon mẫu đã bay AUTO trên SITL thật trong tác vụ; corridor mới đạt protocol mock, chưa AUTO corridor. Chưa có corpus KML lớn/phức tạp của khách, polygon holes hoặc terrain thật.
- KML≤64KiB; envelope simulator10–30m,0,5–2m/s. Camera/Home/reference/mặt đất phẳng là fixture tổng hợp khóa, chưa hiệu chuẩn Hera/Phase One. Không tự diễn giải Home/MSL thành độ cao địa hình thật.
- Parser/compiler đang ở bridge host; chưa có parser KML hoàn toàn offline trên Android. Legacy Native44 capsule không được tự chuyển sang schema92; app/sandbox cũ được giữ nguyên.
- UI engineering giữ blur glass/Barlow và island đã có; các màn đã quan sát trên1280×800 Android. Chưa có nghiệm thu mọi kích thước, accessibility đầy đủ hoặc renderer/thermal/performance. Một số lỗi kỹ thuật vẫn hiển thị mã nội bộ trong panel engineering; cần product-copy riêng.
- Chưa HeraHub/HID/MCU/video thật, Phase One/gimbal/dual-operator hardware, điều khiển Hera ngoài thực địa, pacing1× hoặc ENDURE24h. Không dùng nhiệm vụ này để vượt gate production.

## Bảo toàn và vệ sinh

60507đường dẫn cũ qua91 được đối chiếu SHA, kèm link fixture91; không sửa source/candidate/ENDURE/canonicalSOT. Sandbox Android90 và91 đối chiếu28/94file bằng snapshot gốc. Kết quả chỉ xác nhận byte hiện tại, không khẳng định đường dẫn hiện diện liên tục.

Dừng sạch runtime92, PID và port8870/5901/5902/5582/5583; container thử đã removed theo controller. Token được bridge dọn theo lifecycle. Dung lượng tối thiểu quan sát{minimum:.2f}GiB, cao hơn sàn20GiB. Dọn đúng6APK unsigned do task tạo ({clean['removedBytes']:,}bytes); `.build` dọn tự động, không scratch ngoài repo, giữ signed APK/raw/fixture/AVD. Đã chạy docker image prune -f, không prune container/volume.

## Chạy lại

Không chạy helper vào thư mục bằng chứng đã đóng: các receipt/file dùng exclusive create. Lần kiểm tiếp phải có namespace/attempt mới và admission dung lượng; không xóa token/lock hay ghi đè bằng chứng để chạy lại. Xem TIP-NATIVE92, ADR-107 và ROADMAP-NATIVE92.
'''
(D/'COMPLETION-NATIVE92.md').open('x').write(md)
road='''# ROADMAP sau NATIVE92

18/10/2026. Model KML cockpit/native/SITL đã hợp nhất, qualified engineering; baseline source/candidate/ENDURE vẫn đóng băng.

1. P1 — mở rộng compiler/import corpus với KML thật của khách: nhiều feature, corridor hẹp/gấp khúc, kinh tuyến biên, self-intersection, thứ tự tọa độ, Home/relative/MSL/AGL và options. Cho người vận hành xem diff nguồn→tuyến→mission items, diện tích/thời gian/ảnh kèm giả định. Native KML parser offline là gap hiện hữu; không gọi host bridge thành giải pháp standalone.
2. P1 — AUTO corridor và failure matrix trên cùng model: mất foreground/link trong upload và AUTO, reboot trước/sau commit, sai session/boot/HEAD, nhập stage không hợp lệ. Thực hiện với namespace mới và đủ dung lượng; giữ bằng chứng thất bại, không tự cấp lại quyền.
3. P1 — chuẩn hóa UX nhiệm vụ: chọn/import KML dễ dùng, options corridor/heading/overlap đầy đủ trên UI, cảnh báo Home/terrain và mã lỗi thân thiện; focus/IME, accessiblity, screen sizes, thao tác vật lý cần kiểm trên runtime đích. Canvas preview hiện là WGS84 cục bộ, chưa thay bản đồ sản phẩm/terrain3D.
4. P1 — bench HeraHub khi có thiết bị/API: transport MCU/HID, mapping/calibration/deadman, serial/firmware/capability và input watchdog; video đúng payload/tuổi nguồn; Phase One identity/settings/trigger/media; quyền dual-operator riêng flight/payload. Hiện chưa có thiết bị/SDK, chưa chứng minh điều khiển Hera.
5. Gate riêng — product integration/candidate/trust/release, resource/thermal/pacing và ENDURE24h. Không tự tích hợp vào source/candidate đang đóng băng hoặc ký production từ các PASS engineering này.

Bước kế tiếp đề xuất: corpus KML khách + AUTO corridor và faults trên cùng model, sau đó thu hẹp bridge dependency để có native standalone. Không tăng mock coverage rồi gọi là hardware readiness.
'''
(D/'ROADMAP-NATIVE92.md').open('x').write(road)
old=ast.parse((R/'native/native91/report91.py').read_text());style=next(ast.literal_eval(n.value)for n in old.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='style'for t in n.targets)).replace('native91','native92')
trs=''.join('<tr>'+''.join('<td>'+html.escape(t)+'</td>'for t in r[:3])+'</tr>'for r in rows)
page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AERIS NATIVE92 — Một model nhiệm vụ</title><style>{style}</style><main><header><div class="brand"><i>RtR</i> AERIS</div><div class="tag">NATIVE92 · ENGINEERING PASS</div></header><h1>Một nhiệm vụ.<br>Xuyên suốt cockpit và SITL.</h1><p>KML → biên dịch và lưu model → preflight → upload/readback → AUTO → review. Đã kiểm trên Android và ArduPilot4.7.1, chưa phải nghiệm thu Hera thật.</p><div class="cards"><div class="card"><b>2 AUTO</b><span>Hai lượt hoàn tất · bản cuối development08</span></div><div class="card"><b>20 / 20</b><span>Ca adverse gói và semantic bị từ chối</span></div><div class="card"><b>60.507</b><span>Đường dẫn bảo vệ giữ đúng SHA</span></div></div><div class="links"><a href="../{b['apk']}">APK development08</a><a href="COMPLETION-NATIVE92.md">Báo cáo đầy đủ</a><a href="../evidence/native92/final-verification.json">29 đối chiếu cuối</a><a href="ROADMAP-NATIVE92.md">Roadmap tiếp theo</a></div><figure><img src="../evidence/native92/android92-fly-mid08.png" alt="Fly Android quan sát vị trí thật từ SITL"><figcaption>Model dùng chung đã upload/readback. Fly lấy vị trí quan sát từ autopilot mô phỏng; video và ảnh thực chưa có.</figcaption></figure><h2>Đã kiểm những gì</h2><table><thead><tr><th>Yêu cầu</th><th>Kết quả</th><th>Hành vi đã kiểm</th></tr></thead><tbody>{trs}</tbody></table><figure><img src="../evidence/native92/android92-mutant-refused08.png" alt="Android từ chối kích hoạt gói đã sửa camera và rehash"><figcaption>Gói bị thay camera bằng placeholder dù rehash đầy đủ vẫn bị từ chối trước kích hoạt. CURRENT và model cũ không đổi.</figcaption></figure><figure><img src="../evidence/native92/android92-history-after-reboot08.png" alt="Hai review Android sau reboot"><figcaption>Hai hồ sơ vẫn còn sau reboot; lịch sử không khôi phục quyền. Cold host cần đối chiếu model và cấp quyền phiên mới.</figcaption></figure><h2>Bản bàn giao cuối</h2><p>Development08 · Android33 ARM64/WebView101 · ký engineeringV2/V3. SHA sau cài/reboot khớp byte bàn giao.</p><code>SHA256 {b['sha256']}</code><div class="note"><p>Giới hạn:64KiB KML,10–30m và0,5–2m/s trong simulator. Polygon đã AUTO; corridor mới protocol mock. Parser còn phụ thuộc bridge host; camera/Home/terrain là fixture tổng hợp.</p><p>Chưa HeraHub, SDK, payload/video thật, điều khiển Hera, ENDURE hay production. Không nâng PASS engineering thành cam kết thay thế Ragas ngoài thực địa.</p></div><h2>Bảo toàn và dung lượng</h2><p>Giữ nguyên source/candidate/ENDURE và sandbox90/91. Runtime thử đã đóng sạch. Trống tối thiểu{minimum:.2f}GiB; dọn6APK unsigned riêng (~{clean['removedBytes']/2**20:.1f}MiB), giữ signed/raw/AVD. Không tải SDK/image mới.</p><footer>18/10/2026 · Single-agent SPEC / BUILD / VERIFY · Bằng chứng cục bộ, không công bố ngoài.</footer></main></html>'''
(D/'COMPLETION-NATIVE92.html').open('x').write(page);print('Completion MD/HTML + roadmap created')
