"""Contractor completion from scoped independent receipts; no historical overwrites."""
from pathlib import Path
import json,hashlib,datetime,html,re
R=Path(__file__).resolve().parents[3];E=R/'evidence/betaintegrated01-m1control02'
def load(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
q=load(E/'qa/actual-nominal03/results.json');assert q['status']=='SCOPED_NOMINAL_PASS_FULL_BETA_NOT_READY'
o=q['newOracle'];assert o['status']=='CONTROL_OBSERVATIONS_PASS'and not o['geography']['failures'];assert q['nativeClosure']['qualifiedIntentionalClose']and q['nativeClosure']['firstFailure']is None
assert o['nominalRelease']['status']=='HOST_NATIVE_RELEASE_WITNESS_PASS';assert q['authority']['status']=='PASS_INPUT_UP_REVOKE_OBSERVED_BRAKE_CLEANUP_NEW_LEASE_USER_LAND'
b=load(E/'actual-nominal03/raw/backend-result.json');bound=load(E/'preservation-after01.json');restart=load(E/'android-exit01/restart-result01.json');assert bound['status']=='PASS_BOUNDARY_OBSERVATION'
assert b['frames']==o['fullFrameModelAP']['frames']==80860 and b['stageRows']==80860 and b['framesDropped']==0 and b['requestedSpeedup']==1 and b['capMs']==500
geo=o['geography'];m=o['control']['metrics'];a=q['authority'];c=q['nativeClosure'];close=c['operatorCloseEvents'][0][1];close_latency=(close['writerBoundaryElapsedNs']-close['requestElapsedNs'])/1e6
free=[];percent=[]
for p in list(E.glob('actual-*/control/guard.jsonl'))+[E/'emulator01/guard.jsonl']:
 for line in p.read_text().splitlines():
  v=json.loads(line);free.append(v['freeBytes'])
  if v.get('batteryPercent')is not None:percent.append(v['batteryPercent'])
progress={'format':'aeris-m1-control02-completion','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'READY_SCOPED_GEOGRAPHY_NOMINAL_RELEASE_LAND',
 'wholeM1BetaAccepted':False,'selectedActualCase':'actual-nominal03','verifiedFrames':80860,'APEvents':653797,'nativeRecords':7349,
 'actualRTF':b['actualRTF'],'requestedSpeedup':1,'capMs':500,'framesDropped':0,'geographyArmedPositions':geo['checkedArmedPositions'],'preAuthorityPositionsRetained':geo['preAuthorityPositionsRetained'],
 'maximumDistanceFromConfirmedHomeM':geo['maximumDistanceFromConfirmedHomeM'],'maximumRelativeAltitudeMm':geo['maximumRelativeAltitudeMm'],
 'manualForwardM':m['manualObservedForwardDisplacementM'],'manualHoldSeconds':m['longestForwardInputSpanNs']/1e9,'hoverSeconds':m['observedPreManualHoverSpanNs']/1e9,
 'explicitConsents':2,'postUPNativeObservedBrakeCleanup':True,'userLandWithDistinctNewLease':True,'cleanCloseLatencyMs':close_latency,'journalRestartExactFiles':len(restart['files']),
 'sourceOldFrozenPreservation':'preservation-after01.json','selectedOracleManifest':'host/module-manifest02.json','selectedNativeBuild':'native/build-03.json',
 'oldCaseReceiptsRewritten':False,'currentUserAuthorizedBattery':True,'minimumObservedBatteryPercent':min(percent),'minimumObservedFreeGiB':min(free)/2**30,
 'launches':{'emulator':1,'hostAP':3,'remaining':0},'productionSigned':False,'ENDUREAcceptanceClaim':False,'notChecked':['physicalHeraHub/HID/Xiaomi','realHera/payloadcalibration','ACRO','nativeHome0,0support','fullpremiumcockpit/video/payload','30min','productionrelease']}
(E/'PROGRESS.json').open('x').write(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
report=f'''# BETA-CAMPAIGN01 · M1-CONTROL02

27/10/2026 · **READY trong phạm vi oracle địa lý và nominal Android–SITL**. **Toàn M1/Beta chưa nghiệm thu.**

Đã kiểm trọn chuỗi native: consent → GUIDED/ARM không force → xác nhận Home sau ARM → takeoff 3 m → hover → LOITER → giữ/thả cần → BRAKE17 được quan sát → neutral/relinquish → consent mới/lease mới → LAND chủ động → hạ cánh/disarm → đóng phiên sạch. Dùng app chẩn đoán Android cô lập và ArduCopter 4.7.1-dev ARM SITL đã pin, model quad-X tham chiếu; chưa phải điều khiển Hera thật hay cockpit sản phẩm tích hợp đầy đủ.

## Kết quả kiểm thực

| Yêu cầu | Chứng cứ đạt |
|---|---|
| Giữ/thả cần | Input touch được inject vào Android emulator. Giữ cần tiến {m['longestForwardInputSpanNs']/1e9:.3f} s; di chuyển theo hướng đầu drone {m['manualObservedForwardDisplacementM']:.3f} m. Hover trước manual {m['observedPreManualHoverSpanNs']/1e9:.3f} s. Không suy thành physical HID. |
| Thu hồi quyền và BRAKE | Raw UP record {a['UP']['record']} → revoke lease đầu ở record {a['firstActiveRevoke']['record']} → một BRAKE request → CRC heartbeat native mode17 trước cả hai cleanup INTENT → đúng neutral/release tới AP. Không có normal RC chen giữa BRAKE và LAND. |
| Cấp quyền mới | Hai consent rõ ràng, lease khác nhau. Consent sau UP dùng mẫu UI trung tính mới; trung tính đơn thuần không tự cấp quyền. LAND gắn lease thứ hai, không phục hồi lease cũ. |
| LAND chủ động | Lệnh từ native được đối chiếu đúng bytes/SHA qua host; AP chuyển mode9. Có hai nhóm heartbeat/landed/position mới, riêng biệt sau LAND, disarmed và trị tuyệt đối của relative altitude ≤0,4 m. Không có failsafe gây nhiễu. ACK hoặc forced AP stop không được dùng làm bằng chứng thực thi. |
| Địa lý toàn cửa sổ armed | {geo['checkedArmedPositions']} vị trí đã kiểm từ armed đầu đến disarm; giữ {geo['preAuthorityPositionsRetained']} mẫu trước quyền bay trong raw. Xa Home đã xác nhận tối đa {geo['maximumDistanceFromConfirmedHomeM']:.3f} m (giới hạn 10 m), cao nhất {geo['maximumRelativeAltitudeMm']/1000:.3f} m (giới hạn 5 m). |
| Đủ frame và clock | **80.860 FRAME/STAGE/AP-covered**, 653.797 AP event, replay đúng byte bằng model Python gốc, 7.349 native record khớp anchor ngoài raw. Speedup 1/cap 500 ms, fsync trước sensor, framesDropped=0. RTF {b['actualRTF']:.6f}×; {b['modelSeconds']:.3f} s model / {b['receiveWallSeconds']:.3f} s receive wall. |
| Đóng và restart | Explicit close được xử lý ở writer boundary sau {close_latency:.3f} ms, SEALED/firstFailure=null, không TX sau boundary. {len(restart['files'])} file journal trong các run cũ/mới khớp SHA với tar xuất trước restart Activity; mở lại NO_SESSION, không tự CONNECT/quyền. |

## Oracle mới đã chuẩn hóa

- Gốc đối chiếu là Home có CRC và xác nhận native sau ARM, liên kết terminal journal ngoài raw, record SHA, click CONFIRM_HOME, hash Home, run/epoch/boot/generation/operator/profile và binary/config SHA. Bracket host là quan sát điều phối cục bộ, không giả đồng bộ clock guest-host hay xác thực từ xa.
- Mẫu khởi tạo 0,0 giữ nguyên nhưng thuộc trước quyền bay; không dùng làm gốc hành trình. Oracle hỗ trợ Home hợp lệ ở 0,0, dateline và vùng cực; Native hiện vẫn từ chối Home 0,0, gap này chưa sửa và không được quảng cáo là năng lực global hoàn chỉnh.
- WGS84 GeographicLib2.1 vendor hiện có, không cài dependency mới. Toàn bộ mẫu trong cửa sổ armed được kiểm, không loại outlier hoặc lấy một đoạn đẹp; GPS/EKF/Home thiếu, stale, dữ liệu sai kiểu/miền, đổi Home, boot/context lạ và re-arm đều từ chối.
- Đối chiếu MSL − HomeMSL − relative với tolerance 20 mm theo lượng tử hóa cm/mm của profile AP giả lập. Đây là tiêu chí nhất quán dữ liệu của profile, **không phải cam kết độ chính xác GNSS hoặc Hera 20 mm**. Giới hạn 10 m/5 m giữ nguyên.
- Replay old loss05/ground206 bằng phiên bản mới có receipt mới. Kết quả CONTROL_NOT_READY của oracle cũ và toàn bộ bằng chứng cũ không viết lại.

## Hai lỗi tích hợp đã xử lý

**Khởi tạo UART:** raw đầu từng nhận 30 20 trước MAVLink. Nguồn AP GCS_Common.cpp200–220 có chuỗi reset bootloader SiK này ba lần trước cấu hình MAVLink. control05 chỉ phân loại 0–3 cặp chính xác, tối đa 6 byte trước byte MAV đầu, timeout 200 ms cho cặp chưa đủ và bound khởi tạo 20 s; mọi raw được giữ. Byte lạ, cặp thứ tư, prefix sau khi đã vào MAVLink hoặc EOF sau dữ liệu đều fail-closed, không resync tùy tiện. Native CONNECT đợi heartbeat AP hợp lệ từ kênh quan sát zero application TX. Hai lượt hoàn chỉnh hiện quan sát 0 cặp prefix; nhánh prefix khác 0 đã kiểm bằng source/mock và ca startup lỗi, chưa có complete actual run chứng minh nhánh đó. Chưa công nhận độ tin cậy qua nhiều lần khởi động từ một lượt cuối đạt.

**Explicit CLOSE:** Owner cũ gộp stop flag vào foreground nên close giữa receive/tick đôi khi bị ghi sai là chạy nền. Owner03 chỉ serialize close chủ động tại sole-writer boundary sau operation đã admit; chặn queue mới. Background/focus/fault vẫn đóng FD ngay, lỗi read/write/fsync thật không bị đổi thành close thành công. Mock độc lập đã kiểm race trong read, RX fsync, send và lỗi I/O đồng thời.

Chứng cứ BRAKE cũng được sửa để dùng thứ tự record/CRC native trước cleanup INTENT và đúng packet SHA đã relay. Kênh passive có tốc độ khác nên không lấy timestamp tuyệt đối của hai clock để sắp thứ tự; vẫn yêu cầu quan sát passive BRAKE trước LAND và không cho RC khác chen vào.

## Lượt lỗi giữ nguyên

| Lượt | Phân loại |
|---|---|
| nominal01 | 29 nhóm frame là prefix chưa commit; parser từ chối chuỗi khởi tạo, native chưa CONNECT/chưa lệnh bay. |
| nominal02 | Bay/thu hồi quyền/quyền mới/LAND/ground đã được quan sát, host đóng đủ 80.922 frame, nhưng native close ghi CONTROL_OWNER_BACKGROUND. Giữ failure, không lấy làm lượt hoàn tất. |
| nominal03 | Owner03 + runtime/oracle mới: luồng khép kín và native đóng sạch; dùng lượt này làm nghiệm thu hiện tại. |

Giữ cả các ca phản ví dụ mock đã phát hiện datum sai, thiếu causality, sai pha clock, missing import và close race. Số nhóm mock của Builder/QA có chồng lấp, không cộng thành chứng nhận chất lượng sản phẩm. Native raw/clock chỉ chứng minh input-to-local-wire, không suy ra tuổi packet ở kernel/network hoặc độ trễ từ tay người tới phản ứng drone.

## Bảo toàn và bàn giao

Áp dụng Vibecode Kit 6.3: Builder host/native, QA độc lập, Contractor sở hữu admission/launch/closure và báo cáo. Boundary check không drift so với baseline 17.117 mục legacy cùng các seal cũ 1.620 / 48 / 830 / 1.651 / 4.251 mục. 165 mục thiếu và 97 tracked deletion có sẵn giữ nguyên; không tự khôi phục. Không đổi source/candidate đóng băng, ENDURE hoặc canonical SOT; không kết luận ENDURE đạt 24 giờ.

Gate entry20/livefloor10 GiB + reserve256 MiB và prime15 s thật giữ nguyên. Theo chỉ định mới của người dùng, riêng lượt emulator/Android–SITL này được phép dùng pin; trạng thái nguồn thực được ghi, không giả AC. Free thấp nhất quan sát {min(free)/2**30:.2f} GiB, pin thấp nhất {min(percent)}%. Không sửa policy chiến dịch ENDURE cũ.

Đã dùng 3 host/AP starts và 1 emulator, tất cả đã đóng; không chạy lại. Dọn đúng 3 file truyền/XML của tác vụ trên Android; giữ journal/AVD/raw. Docker image prune thu hồi 0 B. Không tạo project copy trong tmp. Build dùng cached tools, dọn scratch riêng.

APK development **owned-emulator-only**: `native/betaintegrated01/control03/dist/aeris-control01-development-03.apk`, SHA256 `6bc826bcebf89691ca9b13d59c9b55b21d093104995935be76845a4a4820f3a6`. Chỉ thay Owner; UI/Flight02/profile39/assets giữ nguyên. Chứng thư development cũ được dùng lại; chưa ký production.

## Phần còn ngoài nghiệm thu

HeraHub/Xiaomi/HID, cấu hình vật lý và calibration Hera/payload, Home 0,0 ở native, ACRO, full cockpit/media/video/SAF và lượt 30 phút chưa được nghiệm thu trong lát cắt này. Hai P2 cũ về cleanup khi callback cuối ném lỗi và Thread construction OOM còn ghi riêng. App này là diagnostic shell; chưa chứng nhận cockpit sản phẩm hay Beta hoàn chỉnh.

**Disposition: READY trong phạm vi oracle + nominal UP/BRAKE/new-consent/user-LAND/clean-close đã kiểm. Toàn M1/Beta vẫn NOT READY.**

## Nguồn kiểm chứng

- `planning/betaintegrated01/TIP-M1-CONTROL02.md`
- `evidence/betaintegrated01-m1control02/qa/actual-nominal03/results.json`
- `evidence/betaintegrated01-m1control02/host/module-manifest02.json`
- `evidence/betaintegrated01-m1control02/native/build-03.json`
- `evidence/betaintegrated01-m1control02/native/OWNER-CLOSE-REVISION03.json`
- `evidence/betaintegrated01-m1control02/preservation-after01.json`
- `evidence/betaintegrated01-m1control02/PROGRESS.json`
'''
name='COMPLETION-BETA-CAMPAIGN01-M1-CONTROL02';(R/'delivery'/f'{name}.md').open('x').write(report)
parts=[];table=False;listing=False
for line in report.splitlines():
 if line.startswith('|'):
  if re.match(r'^\|[\s:|-]+\|$',line):continue
  if not table:parts.append('<table>');table=True
  parts.append('<tr>'+''.join('<td>'+html.escape(x.strip())+'</td>'for x in line.strip('|').split('|'))+'</tr>');continue
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
css='body{max-width:1100px;margin:48px auto;padding:0 24px;background:#f7f7f5;color:#17191b;font:16px/1.7 system-ui,sans-serif}h1{font-size:34px;line-height:1.2}h2{margin-top:36px;font-size:23px;border-top:1px solid #ccc;padding-top:18px}table{width:100%;border-collapse:collapse;margin:22px 0}td{border-bottom:1px solid #d4d4d1;text-align:left;padding:12px;vertical-align:top}tr:first-child{font-weight:700;background:#ecece8}code{font-size:12px;overflow-wrap:anywhere;background:#e9e9e6;padding:2px 4px}strong{font-weight:750}li{margin:10px 0}'
(R/'delivery'/f'{name}.html').open('x').write('<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>M1-CONTROL02 verification</title><style>'+css+'</style><body>'+body+'</body></html>')
print(json.dumps({'status':progress['status'],'frames':80860,'report':str(R/'delivery'/f'{name}.html')},ensure_ascii=False))
