"""Contractor completion from independent receipts; never changes product/evidence history."""
from pathlib import Path
import json,hashlib,datetime,html
R=Path(__file__).resolve().parents[3];E=R/'evidence/betaintegrated01-m1control01'
def read(p):return json.loads((R/p).read_text())
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
loss=read('evidence/betaintegrated01-m1control01/qa/actual-loss05/closed-cold01.json')
auth=read('evidence/betaintegrated01-m1control01/qa/actual-loss05/native-authority01.json')
ground=read('evidence/betaintegrated01-m1control01/qa/actual-ground206/closed-cold01.json')
bound=read('evidence/betaintegrated01-m1control01/preservation-after01.json')
restart=read('evidence/betaintegrated01-m1control01/android-exit01/restart-result02.json')
assert loss['physics']['status']=='EXACT_ADMITTED_FRAME_AND_ORIGINAL_MODEL_BYTES_PASS'
assert ground['originalOracleOutcome']['status']=='CONTROL_OBSERVATIONS_PASS'
assert loss['originalOracleOutcome']['status']=='CONTROL_NOT_READY' # Preserve known conservative startup0,0 failure.
assert bound['status']=='PASS_BOUNDARY_OBSERVATION'
metrics=loss['originalOracleOutcome']['metrics'];home=loss['independentPredeclaredHomeWindowMetrics']
rows=[]
for case,receipt in [('actual-loss05',loss),('actual-ground206',ground)]:
 backend=read('evidence/betaintegrated01-m1control01/'+case+'/raw/backend-result.json')
 rows.append({'case':case,'frames':receipt['physics']['frames'],'APEvents':receipt['physics']['APEventCount'],
              'RTF':backend['actualRTF'],'framesDropped':backend['framesDropped'],'requestedSpeedup':backend['requestedSpeedup'],'capMs':backend['capMs']})
assert sum(x['frames']for x in rows)==115208 and all(x['framesDropped']==0 and x['requestedSpeedup']==1 and x['capMs']==500 for x in rows)
free=[]
for p in E.glob('actual-*/control/guard.jsonl'):
 for line in p.read_text().splitlines():free.append(json.loads(line)['freeBytes'])
for line in(E/'emulator01/guard.jsonl').read_text().splitlines():free.append(json.loads(line)['freeBytes'])
progress={'format':'aeris-m1-control01-completion','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'PARTIAL_NOT_READY','scopedActualObservations':'LOITER_PILOT_FORWARD_ASSISTED_TAKEOFF_GCS_LOSS_LAND_DISARM_GROUND_AP_REBOOT',
 'wholeM1OrBetaAccepted':False,'originalLossOracleStatus':loss['originalOracleOutcome']['status'],
 'lossOracleKnownConservativeFailure':'First startup uninitialized position0,0 used as horizontal envelope origin; original outcome not overwritten',
 'fullFrameCases':rows,'inputProducerToLocalWriteMaxMs':auth['maxProducerToWrittenNs']/1e6,
 'lossLastHeartbeatToLANDSeconds':metrics['observedLandAfterLastForwardedHeartbeatSeconds'],
 'postLANDQualifiedGroundGroups':home['distinctFreshGroundGroupsAfterFirstLAND'],'manualForwardM':metrics['manualObservedForwardDisplacementM'],
 'maxArmedDistanceFromConfirmedHomeM':home['maxDistanceFromConfirmedHomeWhileArmedWindowM'],
 'journalBytePersistenceFiles':len(restart['files']),'minimumObservedFreeGiB':min(free)/2**30,
 'currentHostManifest':'host/runtime-manifest05.json','currentNativeBuild':'native/build-02.json',
 'launchBudget':{'emulatorStarts':1,'hostStarts':len((E/'actual-launch-ledger.jsonl').read_text().splitlines()),'capHostPlusEmulator':6,'runtimeStartsRemaining':0},
 'preservation':'preservation-after01.json','productionSigned':False,'ENDUREChanged':False,'frozenCandidateChanged':False,
 'notActualTested':['nominalUP_CANCEL_BRAKE_release','userLANDcommand','roll_yaw_throttleFlightAxes','inflightAPreboot','physicalHID_HeraHub_Xiaomi','fullCockpitMedia','30minutes'],
 'next':'Qualify geographic startup handling in a new oracle, then bounded nominalUP/BRAKE/reconsent/userLAND Android-SITL case. Keep all current receipts immutable.'}
(E/'PROGRESS.json').open('x').write(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
text=f'''# BETA-CAMPAIGN01 · M1-CONTROL01

27/10/2026 · **PARTIAL / NOT READY** · native diagnostic controller + owned Android emulator + external ArduCopter 4.7.1-dev ARM SITL.

Đã triển khai native sticks bốn trục, consent/lease 200 ms, assisted GUIDED/ARM/Home/takeoff/LOITER, release hữu hạn và đóng phiên khi lỗi. Trong kiểm thực, cần tiến đã làm drone di chuyển; mất đường MAVLink khi vẫn giữ cần dẫn tới GCS failsafe LAND và ground/disarm. AP khởi động lại trên mặt đất bằng EEPROM lưu lại, native discovery chỉ đọc và không tự khôi phục quyền. Đây là app chẩn đoán native cô lập, chưa phải bản cockpit sản phẩm đã tích hợp đủ manual/video/payload.

## Kết quả đã đo

| Phép kiểm | Kết quả và phạm vi |
|---|---|
| Điều khiển cần tiến trong LOITER | {metrics['manualObservedForwardDisplacementM']:.3f} m theo hướng đầu drone, input liên tục {metrics['longestForwardInputSpanNs']/1e9:.3f} s trước cắt link. Touch được inject bằng ADB vào Android thật của emulator, không phải HID/tay cầm vật lý. |
| Assisted | Non-forced ARM, xác nhận đúng Home mới sau ARM, cất cánh 3 m; hover quan sát {metrics['observedPreManualHoverSpanNs']/1e9:.3f} s trước manual. Cao nhất {home['maxRelativeAltitudeMm']/1000:.3f} m; xa Home đã xác nhận tối đa {home['maxDistanceFromConfirmedHomeWhileArmedWindowM']:.3f} m. |
| Mất link khi giữ cần tiến | Chỉ cắt native MAVLink; FDM/clock/passive vẫn chạy. Tại deadline GCS 5 s còn armed/LOITER, cao 2,979 m. LAND sau {metrics['observedLandAfterLastForwardedHeartbeatSeconds']:.3f} s từ heartbeat forwarded cuối; raw có GCS Failsafe, không có lệnh LAND native gây nhiễu. |
| Ground/disarm sau failsafe | Hai nhóm heartbeat + landed + position mới và riêng biệt sau LAND, thỏa độ cao tuyệt đối ≤0,4 m. Không dùng AP forced-stop hay ACK làm bằng chứng hạ cánh. |
| Reboot AP trên mặt đất | Container/boot/epoch mới, cùng byte AP, no-wipe và EEPROM 16.384 B khớp SHA snapshot; 39 tham số đúng kiểu, không ARM/RC/consent. PID số 8 được tái dùng trong namespace mới, không gọi đó là PID số thay đổi. |
| Native input/authority | 247 input, 1 consent, 246 lease renewals, 55 input-wire bindings. Producer → local write tối đa {auth['maxProducerToWrittenNs']/1e6:.3f} ms. Đây chưa phải độ trễ từ tay người tới phản ứng drone; tuổi dữ liệu ở kernel/network chưa đo. |
| Toàn vẹn frame | **115.208 FRAME/STAGE/AP-covered** của hai lượt khép kín, replay đúng byte bằng model Python gốc. Không mất frame, fsync trước gửi sensor; speedup 1, cap 500 ms. |
| Persistence hẹp | 28 file journal trong bốn run khớp đúng byte với tar đã xuất trước khi Activity restart. Mở lại không CONNECT, màn hình NO_SESSION. Chưa chứng minh full workspace/cockpit persistence ở lát cắt mới này. |

| Lượt khép kín | Frame | AP event | RTF đo được |
|---|---:|---:|---:|
'''
for r in rows:text+=f"| {r['case']} | {r['frames']:,} | {r['APEvents']:,} | {r['RTF']:.6f}× |\n"
text+='''
## Những bản sửa đã kiểm

- Native APK02 chặn GPS sentinel/STATIC/undefined và EKF không đủ điều kiện. Giữ nguyên arming checks; trạng thái EKF 0xa7 đã từ chối cấp quyền, chỉ khi quan sát 0x33f mới tiếp tục. Nguyên nhân nội bộ khiến EKF cần thời gian hội tụ chưa được chứng minh từ covariance nội bộ.
- Host control02 cho chờ TCP khởi tạo tối đa 20 s/200 attempts trước byte AP đầu tiên. Sau bất kỳ byte AP nào, EOF vẫn đóng epoch, không reconnect tự động.
- Host control03 dùng journal transport hữu hạn 32 MiB/40 segment, dự toán thêm original/copy/export 96 MiB. Mock với guard/fsync thật chứng minh vượt ngưỡng 8 MiB cũ vẫn đóng và kiểm anchor được; chạm quota mới vẫn dừng và giữ prefix.
- Bộ kiểm Android13 đọc focus từ dumpsys window đầy đủ. Action dựa geometry XML ban đầu đã xem ảnh, kiểm focus/state/screenshot mới trước từng tap; không nói mọi screenshot từng tap đều đã được xem trực quan.

## Vì sao chưa nghiệm thu toàn mốc

**Giữ nguyên kết quả gốc của oracles03: CONTROL_NOT_READY.** Oracle lấy vị trí khởi tạo 0,0 chưa hợp lệ làm gốc kiểm bán kính, nên cờ horizontal-envelope vẫn FAIL. Đối chiếu độc lập theo cửa sổ Home sau ARM đã công bố trước kiểm cho kết quả 6,227 m trong giới hạn 10 m; đây là bằng chứng bổ sung, không viết lại kết quả oracle gốc hay quảng cáo toàn bộ mốc PASS.

Luồng nominal thả cần → observed BRAKE → neutral/relinquish → consent mới → người dùng ra LAND hiện có code và mock, **chưa hoàn tất kiểm thực**. Roll/yaw/throttle mới kiểm mapping bằng mock, kiểm bay thực mới dùng cần tiến. AP reboot thực chỉ trên mặt đất, dùng bản sao EEPROM chính xác trong thư mục state mới; không có chứng cứ reboot khi đang bay hoặc đường dẫn gốc hiện diện liên tục. Chưa có HeraHub/Xiaomi/HID, calibration Hera, full cockpit/media hay lượt 30 phút.

Hai P2 native còn để riêng: lỗi callback cuối có thể cản release singleton, và lỗi tạo Thread trước khối start có thể giữ reservation. Đường callback đang dùng bắt lỗi ghi checkpoint; chưa coi các kiểm hiện tại là chứng nhận production.

Đã dùng hết ngân sách 5 host starts + 1 emulator start. Không mở vòng thử mới, không hạ gate hay đổi tiêu chí sau khi thấy dữ liệu. Bước tiếp theo: qualification oracle địa lý bằng corpus có startup 0,0/invalid và Home mới, sau đó kiểm nominal ngắn với thả cần/BRAKE/LAND và mở rộng trục điều khiển trong milestone kế tiếp.

## Bằng chứng lỗi giữ nguyên

| Lượt | Phân loại |
|---|---|
| nominal01 | Docker nhận TCP trước AP, EOF trước byte đầu; 0 frame, chưa CONNECT native/chưa lệnh bay. Giữ failed prefix. |
| nominal02 | 30 s chưa đủ điều kiện EKF, không consent/ARM. 36.848 frame/model/AP kiểm được; native bị force-stop nên journal chỉ là prefix, không có terminal commit. |
| loss03 | Đã bay và thấy GCS LAND nhưng transport chạm quota 8 MiB. 87.948 nhóm frame hoàn chỉnh chỉ là retained prefix; thiếu hồ sơ hoàn chỉnh và ground qualified, không PASS. |
| loss05 | Khép kín đủ frame, native commit, failsafe và ground/disarm. Giữ cờ FAIL bảo thủ của oracle gốc như trên. |
| ground206 | Khép kín, no-wipe retained EEPROM, discovery chỉ đọc và không khôi phục quyền. |

Không cộng interval hay frame của lần lỗi để thay bằng chứng hoàn chỉnh. Giữ cả lỗi fixture QA/root (sai offset/nhãn operator và lệnh shell chỉ liệt kê thay vì hash), dùng receipt hiệu chỉnh riêng, không sửa lịch sử.

## Bảo toàn và vận hành

Áp dụng Vibecode Kit 6.3: Builder native/host, QA độc lập và Contractor thực hiện các launch. Kỷ luật provenance: mock, app Android thực trên emulator, AP SITL thật, raw replay và kiểm trực quan giới hạn được tách rõ; không suy thành thiết bị hay drone thật.

'''
text+=f'''Boundary check: 17.117 mục legacy và bốn seal cũ (1.620 / 48 / 830 / 1.651 mục) không drift so với baseline. 165 mục thiếu từ trước và 97 tracked deletion có sẵn giữ nguyên, không tự khôi phục. Source/candidate/ENDURE/canonical SOT không sửa. Không tuyên bố ENDURE đạt 24 giờ.

Gate entry 20 GiB / live floor 10 GiB + reserve giữ nguyên, hai journal guard có prime 15 s thật. Free thấp nhất quan sát {min(free)/2**30:.2f} GiB. Emulator và toàn bộ host/AP của tác vụ đã đóng; native force-stop. Dọn đúng 5 file truyền/XML của tác vụ trên Android, không xóa journal/AVD/bằng chứng. Docker image prune thu hồi 0 B. Không tạo bản sao dự án trong tmp; thư mục build riêng hiện trống.

APK development cô lập: `native/betaintegrated01/control02/dist/aeris-control01-development-02.apk`, SHA256 `b0e99a320938970190912cb64d0843d10bc50e4475e8b3ce6d21936438779212`. Không ký production, không công bố, không commit/push trong tác vụ này.

## Hồ sơ tham chiếu

- TIP: `planning/betaintegrated01/TIP-M1-CONTROL01.md`
- QA đóng kín: `evidence/betaintegrated01-m1control01/qa/actual-loss05/closed-cold01.json` và `qa/actual-ground206/closed-cold01.json`
- Native authority: `evidence/betaintegrated01-m1control01/qa/actual-loss05/native-authority01.json`
- Source manifest hiện hành: `evidence/betaintegrated01-m1control01/host/runtime-manifest05.json`
- Native build: `evidence/betaintegrated01-m1control01/native/build-02.json`
- Preservation: `evidence/betaintegrated01-m1control01/preservation-after01.json`
- Progress: `evidence/betaintegrated01-m1control01/PROGRESS.json`

**Disposition: giữ các kết quả đạt trong phạm vi hẹp; M1-CONTROL01 còn PARTIAL / NOT READY, toàn M1/Beta chưa được nghiệm thu.**
'''
name='COMPLETION-BETA-CAMPAIGN01-M1-CONTROL01';(R/'delivery'/f'{name}.md').open('x').write(text)
# Local static HTML; simple paragraphs/tables generated from the same exact Markdown content.
import re
parts=[];table=False;listing=False
for line in text.splitlines():
 if line.startswith('|'):
  if re.match(r'^\|[\s:|-]+\|$',line):continue
  cells=[x.strip()for x in line.strip('|').split('|')]
  if not table:parts.append('<table>');table=True
  parts.append('<tr>'+''.join('<td>'+html.escape(x)+'</td>'for x in cells)+'</tr>');continue
 if table:parts.append('</table>');table=False
 if line.startswith('- '):
  if not listing:parts.append('<ul>');listing=True
  parts.append('<li>'+html.escape(line[2:])+'</li>');continue
 if listing:parts.append('</ul>');listing=False
 if not line:continue
 if line.startswith('#'):
  n=len(line)-len(line.lstrip('#'));parts.append(f'<h{n}>'+html.escape(line[n:].strip())+f'</h{n}>')
 else:parts.append('<p>'+html.escape(line)+'</p>')
body='\n'.join(parts);body=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',body);body=re.sub(r'`([^`]+)`',r'<code>\1</code>',body)
css='''body{max-width:1100px;margin:48px auto;padding:0 24px;background:#f7f7f5;color:#17191b;font:16px/1.7 system-ui,sans-serif}h1{font-size:34px;line-height:1.2}h2{margin-top:36px;font-size:23px;border-top:1px solid #ccc;padding-top:18px}table{width:100%;border-collapse:collapse;margin:22px 0}td{border-bottom:1px solid #d4d4d1;text-align:left;padding:12px;vertical-align:top}tr:first-child{font-weight:700;background:#ecece8}code{font-size:12px;overflow-wrap:anywhere;background:#e9e9e6;padding:2px 4px}strong{font-weight:750}li{margin:10px 0}a{color:inherit}'''
(R/'delivery'/f'{name}.html').open('x').write('<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>M1-CONTROL01 verification</title><style>'+css+'</style><body>'+body+'</body></html>')
print(json.dumps({'progress':str(E/'PROGRESS.json'),'report':str(R/'delivery'/f'{name}.html'),'status':progress['status'],'verifiedFrames':sum(x['frames']for x in rows)},ensure_ascii=False))
