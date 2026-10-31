"""Receipt-bound NATIVE87 completion; append-only outputs, no frozen-source mutation."""
from pathlib import Path
import json,hashlib,datetime,shutil,html
R=Path(__file__).resolve().parents[2];E=R/'evidence/native87';N=R/'native/native87';D=R/'delivery'
def read(n):return json.loads((E/n).read_text())
def put(p,v):p.open('x').write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
run='s8ed14645457e45388ac8';build=read('build07.json');raw=read('runs/'+run+'/raw-verification-final.json');review=read('runs/'+run+'/review.json');runtime=read('runtime-final-verification.json');pres=read('preservation-final.json');ui=read('ui-final-qa.json')
assert raw['executionVerified']and raw['missionItems']==16 and raw['readbackCycles']==2 and raw['transfer']['cameraCommands']==6
assert review['accepted']and review['execution']['complete']and not review['aborted']and review['actualImages']==0
assert read('upstream-raw-oracle.json')['status']=='PASS'and read('captured-replay.json')['status']=='PASS'
for n in ['apk07-source-verification.json','installed-apk07-verification.json','android87-restart-verification.json','android87-import-activation-verification.json','android87-mock-journey-verification.json','syntax-final.json']:assert read(n)['status']=='PASS'
assert pres['status']=='PASS'and pres['count']==53496 and not pres['failures']and runtime['status']=='PASS'
assert sha(R/build['apk'])==build['sha256']and runtime['minRuntimeFreeGiB']>=20
assert read('controls-regression.json')['pass']==31 and read('controls-regression.json')['fail']==0
assert len(read('model-regression.json')['checks'])==46 and len(read('mock-qa03.json')['checks'])==24
assert read('workflow-qa-final87.json')['pass']==16 and read('workflow-qa-final87.json')['fail']==0
ops=read('fileops-import-reconciled')['operations'] if (E/'fileops-import-reconciled').exists() else read('fileops-import-reconciled.json')['operations']
assert next(o for o in ops if o['id'].startswith('59c2ad58'))['phase']=='UNKNOWN'
assert next(o for o in ops if o['id'].startswith('d3916be2'))['reason']=='EXPLICIT_PROVIDER_RECONCILIATION_VERIFIED'
coverage={
 'REQ87-01':{'status':'PASS','evidence':['delayed-picker-result.json','fileops-restart-verification.json','android87-export-final-verification.json','fileops-after-wrong-sha.json','fileops-after-correct-reconcile.json','fileops-import-reconciled.json','android87-import-activation-verification.json','build-log07.json'],'limits':['Original export with no surviving exact artifact remains UNKNOWN; no invented completion','Quota fault tests are host JVM; actual Android exercised normal/restart/reconciliation paths']},
 'REQ87-02':{'status':'PASS','evidence':['android87-readonly07.json','readonly-prefix07.jsonl','android87-auto-main07b.png','loss-test-verification06.json','android87-loss-main06.png','model-regression.json'],'limits':['Flat local metre visualization; no satellite terrain/video/Hera identity attestation','Loss injection was disarmed on build06; identical DEX/flight modules on final07, with subsequent visual background correction']},
 'REQ87-03':{'status':'PASS','run':run,'evidence':['android87-plan07.json','android87-postarm-home07b.json','android87-auto-terminal07b.json','android87-accepted-review07b.json','runs/'+run+'/raw-verification-final.json','upstream-raw-oracle.json','captured-replay.json'],'limits':['One accepted internal-quad functional SITL run; not Hera flight/physics/pacing acceptance','16 items include Home; six camera commands, zero actual images']},
 'REQ87-04':{'status':'PASS_SCOPED_GROUND_RESTART_CASES','evidence':['android87-ap-reboot-before.json','android87-ap-reboot-after.json','android87-ap-reboot-review.json','android87-restart-verification.json','android87-import-activation-verification.json','android87-mock-journey-verification.json'],'limits':['AP test is owned guest/process restart; MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN NOT_CHECKED','In-flight disconnect/failsafe/background NOT_CHECKED in this milestone']},
 'REQ87-05':{'status':'PASS_WITH_RECORDED_UI_OBSERVATION','evidence':['controls-regression.json','model-regression.json','takeoff-qa.json','mock-qa03.json','workflow-qa-final87.json','host-qa01.json','build-log07.json','syntax-final.json','ui-final-qa.json','runtime-final-verification.json','preservation-before.json','preservation-final.json'],'limits':['91 selected renderer snapshots, one scrolled checkbox occlusion; explicit confirmation path passed','Heading near north can display 360 degrees; engineering reason codes remain','No exhaustive pixel, GPU/FPS, physical input or video qualification']}}
now=datetime.datetime.now().astimezone().isoformat();v={'milestone':'NATIVE87','at':now,'status':'PASS_SCOPED_ANDROID_SITL_WITH_DOCUMENTED_UI_OBSERVATION','productionReady':False,'apk':build['apk'],'apkSha256':build['sha256'],'certificateSha256':'3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800','developmentOnly':True,'acceptedSITLRun':run,'rawRecords':raw['rawRecords'],'missionItems':16,'readbackCycles':2,'cameraCommands':6,'actualImages':0,'parameterWritesMAVLink':0,'protectedFiles':pres['count'],'protectionStatus':pres['status'],'minRuntimeFreeGiB':runtime['minRuntimeFreeGiB'],'finalFreeGiB':runtime['finalFreeGiB'],'requirements':coverage,'regressions':{'controls':31,'modelFreshnessHistory':46,'takeoff':14,'mockProtocol':24,'workflowHostJava':16,'resourcePolicyJVM':22,'draftJournalJVM':31,'archiveEdgesJVM':4,'fileOpsJVM':12,'compositeExportJVM':3,'workspacesJVM':12,'historyJVM':11,'syntaxModules':48},'androidRecordReplay':read('captured-replay.json'),'ui':ui,'notChecked':['HeraHub/joystick/buttons/vendorSDK/radio','Physical payload camera/gimbal/video and actual photographs','MAV_CMD reboot on wire','In-flight failure acceptance in this milestone','Production release/signing','Pacing1x or24h ENDURE acceptance'],'workspaceArchiveLimit':'Contains mock/SITL journal records and hashes, not full host raw flight files. Raw retained separately under evidence/native87/runs.','cleanup':read('cleanup.json')}
put(E/'verification.json',v)
notes={'retainedIncidents':['Initial mock foreground-lease expiry; exact root cause not proven, guards unchanged','Review-format namespace mistake fixed before actual SITL','Initial Java test compile/race failures retained in build receipts','Initial Android task restart returned child picker task; confirmed cold start used NEW_TASK|CLEAR_TASK without data clearing','Development06 illustrative background leaked under SITL plan/preflight; development07 hides it in every SITL view','First actual Home-review window expired during QA inspection: no AUTO sent; separate aborted run retained','Mock UI driver missed scrolled control coordinates and old profile expired/trace bound; no start occurred; fully revealed controls and new bounded profile then completed','Upstream Python oracle initially omitted AP nonposition frame2→0 normalization; bounded rule documented, runtime unchanged','Closure probe initially matched Docker error with wrong letter case; actual absent container verified'],'frozenEvidenceRewritten':False,'speedup':1,'foregroundLeaseMs':3500,'grantMs':30000,'postArmHomeReviewMs':10000,'continuousOriginalPathPresenceClaim':False};put(E/'qualification-notes.json',notes)
md=f'''# NATIVE87 — Android workspace recovery and SITL cockpit

Status: **PASS in the scoped Android/SITL qualification, with a recorded UI observation**. {now}

Implemented in `native/native87`, package `vn.rtr.aeris.native87`; development07 is installed-byte verified on owned emulator-5582, Android33 ARM64/WebView101.0.4951.61,1280×800. No HeraHub or production qualification.

## Delivered and verified

- Durable file-operation journal before SAF picker. Late completion remains discoverable after the JS timeout; restart produces UNKNOWN for an unconfirmed transaction. No retry, invented success, auto activation or deletion.
- Final export held beyond65seconds, provider bytes/readback SHA matched. Wrong archive rejected; exact original reselected after restart. Import staging survived restart, required explicit reconciliation and activation, retained the original generation and all SITL reviews.
- Current composite mock+SITL HEAD binds export/fresh guard. An older export cannot authorize a changed SITL journal; quota failures retain evidence.
- Explicit mock/SITL sources. Real firmware4.7.1 position, Home/MSL, mode, armed, battery and data ages feed main Fly; stale observations clear. The illustrative terrain/camera background is hidden in all final SITL views.
- Actual Android KML→compile→readonly→preflight→grant→upload/readback→arm→separate fresh Home approval→AUTO→waypoints→terminal RTL item→observed land/disarm→committed Android review.
- Accepted run `{run}`:16items including Home,2readback cycles,6camera commands,5635raw records,0actual photos and0MAVLink PARAM_SET. A separate full-stream JS verifier and pinned upstream Python dialect checked bytes/CRC/target/mission/camera semantics; geometry establishes takeoff rather than ACK alone.
- Disarmed telemetry loss and owned ArduPilot guest/process restart invalidate the session, clear observations and do not reconnect or restore authority. App restart and Android reboot preserve exact journals. Imported generation and completed mock review also survive app restart.
- Final APK mock journey separately completed with2observed points; ACK leaves cursor unchanged; review remains `COMPLETED_MOCK`,0images, no physical execution claim.

## Coverage

| Requirement | Result | Evidence |
|---|---|---|
| REQ87-01 file outcomes/recovery/quota | PASS in tested scopes | `evidence/native87/verification.json` |
| REQ87-02 actual readonly Fly | PASS | readonly prefix, main Fly screenshots, freshness tests |
| REQ87-03 actual Android AUTO→review | PASS | accepted run/raw verification/upstream oracle |
| REQ87-04 restart/loss | PASS for ground/process/app/Android cases | restart receipts; in-flight and wire reboot NOT_CHECKED |
| REQ87-05 regression/UI/preservation/closure | PASS with UI observation | UI QA, runtime closure,53496-file SHA audit |

Regression sets:31controls,46freshness/history,14takeoff,24protocol mock,16workflow; JVM Policy22/DraftStore31/ArchiveEdges4/FileOps12/Composite3/Workspace12/History11.48modules pass syntax. Captured Android semantic replay verifies23unique records:17mock,2plans,4reviews, including exactly1accepted SITL review. These counts describe distinct suites, not independent review teams.

## UI QA and remaining limits

91selected renderer snapshots across mock plan/preflight/Fly/review and day/night. Telemetry/logo gutter delta0CSSpx; left/right island centre delta0CSSpx when both visible. One snapshot during scrolling records `confirm-route` under the sticky footer; fully revealed checkbox and the explicit confirmation path pass. Per-control coordinates were not captured in that snapshot. Do not claim zero overlap across every scroll state. A heading near north may round to360°; engineering reason codes and the SITL control panel remain prototype UX. No GPU/FPS/thermal or exhaustive pixel qualification.

The workspace ZIP verifies included journal bytes and hashes; **it does not contain the full host raw-flight files**. They remain at `evidence/native87/runs/{run}`. The exported ZIP predates the later mock run, by design; no claim it contains later revisions.

HeraHub input/radio/vendor SDK, physical cameras/gimbals/video, actual mapping images, flight performance, in-flight failure qualification and production signing remain NOT_CHECKED. ArduPilot restart here is a disarmed guest/process restart; the MAVLink firmware reboot command was not tested. No pacing or24h ENDURE PASS is inferred.

## Artifact, preservation and closure

APK: `{build['apk']}`  
SHA256: `{build['sha256']}`  
Development certificate: `{v['certificateSha256']}`. v2/v3signature; INTERNET permission only; no WebView debugging/backup.

53496protected paths match SHA before/after, including prior Native86. Frozen source/candidate/ENDURE and canonical SOT remain unchanged. This confirms present bytes; it does not rewrite historical missing-path incidents or claim continuous presence. Build then QA used the same agent, with separate deterministic replay paths; no independent-team claim.

All owned simulator/bridge/emulator PIDs and ports closed; token removed. Runtime controller minimum free{v['minRuntimeFreeGiB']:.2f}GiB; final observation{v['finalFreeGiB']:.2f}GiB. Removed only6temporary unsigned APKs plus native87 `__pycache__` (~19.5MB); reusable SDK86,AVD87,signed APKs and evidence retained. Docker image prune reclaimed0B; no volume/container prune.

## Next priority

Close the recorded UI details and replace engineering status codes with actionable operator outcomes. Add an explicit, separately authorized in-flight disconnect/background acceptance campaign and receiver handoff including full raw evidence. Then qualify payload/input/video on HeraHub when hardware/SDK is available. Do not expand mock results into commercial or hardware readiness.
'''
(D/'COMPLETION-NATIVE87.md').open('x').write(md)
page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AERIS · NATIVE87</title><style>@font-face{{font-family:Barlow;src:url('../native/native87/assets/fonts/Barlow-Medium.ttf');font-weight:500}}@font-face{{font-family:Barlow;src:url('../native/native87/assets/fonts/Barlow-Bold.ttf');font-weight:700}}*{{box-sizing:border-box}}body{{margin:0;background:#101714;color:#f0f4ee;font:500 18px/1.55 Barlow,system-ui}}main{{max-width:1200px;margin:auto;padding:40px 32px 80px}}header{{border-bottom:1px solid #b2c1b32e;padding-bottom:24px;margin-bottom:32px}}small,.muted{{color:#a7b6ab}}h1{{font-size:48px;line-height:1.1;margin:16px 0}}h2{{font-size:28px;margin-top:36px}}a{{color:#e7c64a}}.tag{{color:#e7c64a}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}img{{width:100%;border:1px solid #8fa79540;border-radius:16px}}.facts{{display:flex;gap:32px;flex-wrap:wrap;padding:20px 0;border-block:1px solid #b2c1b32e}}.facts strong{{display:block;font-size:34px}}.code{{overflow-wrap:anywhere;font-size:14px}}li{{margin:10px 0}}</style><main><header><small>RtR / AERIS · ENGINEERING QUALIFICATION</small><h1>Android cockpit<br>đã bay AUTO với SITL.</h1><p class="tag">NATIVE87 · Đạt trong phạm vi đã kiểm, có ghi nhận QA giao diện</p><p>Workspace khôi phục có kiểm toàn vẹn · Telemetry thật từ ArduPilot4.7.1 · Hồ sơ tách rõ mock, SITL và ảnh thực.</p></header><div class="facts"><div><strong>16</strong>mission item</div><div><strong>2×</strong>readback</div><div><strong>6</strong>lệnh camera</div><div><strong>5.635</strong>bản ghi raw</div><div><strong>0</strong>ảnh thực</div></div><h2>Hành trình đã kiểm trên Android</h2><p>KML → compile → preflight → cấp quyền SITL → upload/readback → arm → xác nhận Home mới → AUTO → waypoint → quay về, hạ cánh/disarm → lưu và đọc review. Chỉ dùng quad mô phỏng nội bộ; chưa hiệu chuẩn Hera.</p><div class="grid"><figure><img src="../evidence/native87/android87-auto-main07b.png" alt="Main Fly nhận vị trí AUTO SITL"><figcaption>Vị trí và chế độ từ SITL; nền minh họa đã được loại khỏi chế độ này.</figcaption></figure><figure><img src="../evidence/native87/android87-sitl-review-selected07.png" alt="Review AUTO SITL có SHA"><figcaption>Review có quỹ đạo, nguồn và raw head; xem lịch sử không phục hồi quyền.</figcaption></figure></div><h2>Workspace an toàn sau restart</h2><p>Chọn tệp quá65giây vẫn đối chiếu được kết quả native. Giao dịch chưa đủ bằng chứng giữ UNKNOWN. Tệp sai SHA bị từ chối; staging được phục hồi qua đối chiếu riêng và xác nhận trước chuyển. Thế hệ cũ giữ nguyên.</p><h2>QA ghi đúng giới hạn</h2><p>91snapshot chọn lọc: mép telemetry/logo và tâm hai đảo lệch0CSSpx. Có1snapshot checkbox bị footer cố định che khi cuộn; khi hiện đầy đủ, xác nhận và hành trình đạt. Heading gần bắc có thể hiển thị360°. Chưa kiểm mọi trạng thái, FPS hay phần cứng HeraHub.</p><p>ZIP workspace chứa journal, chưa chứa toàn bộ raw chuyến bay. Raw được giữ riêng trong thư mục bằng chứng. Không kết luận ảnh thực hoặc bay Hera từ kết quả này.</p><div class="grid"><img src="../evidence/native87/android87-mock-review-day07.png" alt="Review mock ghi rõ không có bằng chứng bay thực"><img src="../evidence/native87/android87-mock-payload-sheet-day07.png" alt="Popup chọn camera minh họa theme ngày"></div><h2>Bàn giao</h2><p><a href="../{build['apk']}">APK development07</a> · <a href="COMPLETION-NATIVE87.md">Báo cáo đầy đủ</a> · <a href="../evidence/native87/verification.json">Ma trận nghiệm thu</a></p><p class="code">SHA256 {build['sha256']}</p><p>53.496đường dẫn bảo vệ khớp SHA. Runtime đã đóng sạch; free thấp nhất{v['minRuntimeFreeGiB']:.2f}GiB. Giữ source/candidate đóng băng và ENDURE; chưa ký production, chưa nghiệm thu HeraHub.</p><p class="muted">{html.escape(now)} · Build và QA trong cùng agent; đối chiếu raw qua JS và upstream Python, không tự nhận hội đồng độc lập.</p></main></html>'''
(D/'COMPLETION-NATIVE87.html').open('x').write(page)
(D/'ROADMAP-NATIVE87.md').open('x').write('''# Roadmap overlay after NATIVE87

Frozen canonical SOT/source/candidate/ENDURE remain untouched. See COMPLETION-NATIVE87.md and evidence/native87/verification.json for proven scope.

DONE: durable SAF outcomes/reconciliation, composite mock+SITL export binding, Android readonly Fly, actual Android KML→preflight→upload/readback→Home→AUTO→review, ground link/process restart, Android reboot and explicit imported workspace activation.

NEXT P1: operator-ready UI outcomes for expired Home/unknown command state; resolve recorded scrolled-checkbox observation and north360° formatting. Full raw-evidence handoff to receiver must include the bytes referenced by review, not only journal hashes.

NEXT separate SITL gate: in-flight disconnect/app background/failsafe and explicit session recovery, with current safety deadlines and no automatic unknown-command retry. Ground pause/process restart is not evidence for this.

HARDWARE GATE: HeraHub firmware/SDK/input/radio/video, physical PhaseOne/Sony/gimbal routing, dual-operator transport and measured control latency. Existing mock payload and role contracts do not prove hardware support.

RELEASE GATE: actual Hera configuration/flight data, endurance and performance evidence, signed deployment/trust gates. No production or Ragas replacement acceptance inferred from Native87.
''')
put(D/'NATIVE87-LATEST.json',{'milestone':'NATIVE87','status':v['status'],'completion':'delivery/COMPLETION-NATIVE87.html','verification':'evidence/native87/verification.json','apk':v['apk'],'apkSha256':v['apkSha256'],'completionSha256':sha(D/'COMPLETION-NATIVE87.html'),'productionReady':False})
files={}
for root in [N,E]:
 for p in sorted(root.rglob('*')):
  if p.is_file()and p.name not in ['module-fingerprints.json','fingerprint-check.json']:files[str(p.relative_to(R))]=sha(p)
for p in [D/'TIP-NATIVE87.md',D/'COMPLETION-NATIVE87.md',D/'COMPLETION-NATIVE87.html',D/'ROADMAP-NATIVE87.md',D/'NATIVE87-LATEST.json',R/'docs/ADR-102-NATIVE87-FILE-OUTCOMES-AND-SITL.md']:files[str(p.relative_to(R))]=sha(p)
put(E/'module-fingerprints.json',{'at':now,'scope':'NATIVE87_ONLY_NOT_REPLACEMENT_FOR_FROZEN_PINS','files':files})
for n,h in files.items():assert sha(R/n)==h,n
put(E/'fingerprint-check.json',{'status':'PASS','files':len(files),'manifestSha256':sha(E/'module-fingerprints.json'),'scope':'Current bytes of new module/evidence/delivery only; frozen paths separately audited'})
print(json.dumps({'status':v['status'],'protected':pres['count'],'newFiles':len(files),'apk':v['apk'],'completion':'delivery/COMPLETION-NATIVE87.html'}))
