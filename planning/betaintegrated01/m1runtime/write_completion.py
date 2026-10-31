"""Contractor report from closed receipts; never launches or signs software."""
import hashlib
import html
import json
import os
from pathlib import Path
import re
import time
from datetime import datetime, timezone

R = Path(__file__).resolve().parents[3]
os.chdir(R)
E = Path('evidence/betaintegrated01-m1runtime')


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def write(p, data):
    with Path(p).open('x') as f:
        f.write(data)


def put(p, data):
    write(p, json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def main():
    now = datetime.now(timezone.utc).isoformat()
    actual = read(E/'qa/actual02-cold-audit.json')
    restart = read(E/'actual02/control/native-restart-persistence01.json')
    boundary = read(E/'preservation-after01.json')
    cleanup = read(E/'source-cleanup-final01.json')
    result = read(E/'actual02/raw/backend-result.json')
    external = read(E/'actual02/control/anchors-live01.json')
    closure = read(E/'actual02/control/controller-closure.json')
    profile = read('runtime/betaintegrated01/dist/run-profile03.json')
    apk = read(E/'native/build-05.json')
    caps = read(E/'actual02/control/duration-admission.json')
    assert actual['status'] == 'PASS_SCOPED_ACTUAL_READONLY_SHORT'
    assert restart['status'] == 'PASS_ANDROID_RESTART_PERSISTED_RAW_NO_AUTO_SESSION'
    assert boundary['status'] == 'PASS_BOUNDARY_OBSERVATION'
    assert cleanup['status'] == 'PASS_SOURCE_FREEZE_AND_OWNED_CLOSURE'
    assert closure['failure'] is None and closure['allPinnedInputsUnchanged']
    assert result['frames'] == result['stageRows'] == actual['host']['APCoveredFrames'] == 71350
    assert sha(apk['apk']) == apk['sha256']
    assert all(not s['admittedByArithmetic'] for s in caps['profiles'][1:])
    selected = caps['profiles'][0]
    longrun = caps['profiles'][-1]
    evidence_map = [
        ('R01','Ghép host journal/clock/AP drainer', 'PASS_ACTUAL_READONLY_SHORT', ['host02/runtime-manifest02.json','qa/actual02-cold-audit.json']),
        ('R02','Ghép native socket/provider/lifecycle/journal', 'PASS_ACTUAL_READONLY_SHORT', ['native/build-05.json','qa/actual02-cold-audit.json']),
        ('R03','Full admitted frames và đối chứng model', 'PASS_71350_EXACT_FRAMES_AND_STAGES', ['actual02/control/cross-layer-root01.json','qa/actual02-cold-audit.json']),
        ('R04','Guard và xử lý lỗi không làm sai bằng chứng', 'PASS_VERSIONED_RUNTIME02_POLICY', ['qa/runtime02-guards01/results.json','qa/runtime02-stage-fault01/results.json','actual02/control/observed-real-guard-prime.json']),
        ('R05','Đóng native, persistence/restart và đối chiếu raw', 'PASS_ANDROID_APP_RESTART', ['actual02/control/native-cold-root01.json','actual02/control/native-restart-persistence01.json','qa/actual02-restart-review.json']),
        ('R06','Bảo toàn source/candidate/ENDURE và dọn runtime', 'PASS_AT_FINAL_OBSERVATION', ['preservation-after01.json','source-cleanup-final01.json']),
        ('R07','Admission cùng gate20/10GiB trước actual', 'PASS_SHORT_ONLY', ['admission-environment03.json','actual02/control/duration-admission.json']),
        ('R08','Lượt30phút sau short', 'NOT_RUN_ADMISSION_REFUSED', ['actual02/control/duration-admission.json']),
    ]
    criteria = [{'id': i, 'outcome': o, 'status': s, 'evidence': [{'path': str(E/p), 'sha256':sha(E/p)} for p in paths]} for i,o,s,paths in evidence_map]
    summary = {
        'format':'aeris-m1-runtime-contractor-verification','version':1,'atUTC':now,
        'status':'READY_SCOPED_ADAPTER_AND_READONLY_SHORT_WITH_30MIN_DEFERRED',
        'actualM1Complete':False,'BETA_SIMReady':False,'productionOrHardwareReady':False,
        'criteria':criteria,'currentAPK':{'path':apk['apk'],'sha256':apk['sha256'],'developmentSigned':True,'productionSigned':False},
        'currentAP':{'path':'runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03','sha256':profile['APSHA256']},
        'currentConfigSHA256':sha('runtime/betaintegrated01/dist/run-profile03.json'),
        'actual02':{'run':external['run'],'epoch':external['epoch'],'boot':external['boot'],
            'frames':result['frames'],'stageRows':result['stageRows'],'APEvents':actual['host']['APEventCount'],
            'modelSeconds':result['modelSeconds'],'receiveWallSeconds':result['receiveWallSeconds'],'RTF':result['actualRTF'],
            'requestedSpeedup':1,'capMs':500,'admittedFramesDropped':0,
            'clockRequests':actual['host']['clockRegistered'],'clockMatched':actual['host']['clockMatched'],
            'nativeRecords':actual['nativeCold']['records'],'nativeActiveElapsedNs':31862891140,
            'onlyReadOnlyCommands':actual['nativeIndependentWire']['txCommands'],
            'anyObservedArmed':actual['nativeIndependentWire']['anyObservedArmed'],
            'APExit':-9,'APExitMeaning':'DECLARED_FORCED_SIM_STOP_NOT_GRACEFUL_OR_LANDING_PROOF'},
        'retainedFailures': ['bootstrap-incident01.json','actual01/control/controller-closure.json','qa/actual01-prefix-audit.json'],
        'budgets':{'elapsedSeconds':(datetime.now(timezone.utc)-datetime.fromisoformat(read(E/'entry01.json')['atUTC'])).total_seconds(),
                   'maxWallSeconds':14400,'hostAndEmulatorStarts':4,'APStarts':2,'limitHostAndEmulatorStarts':4,'limitAPStarts':6,
                   'shortDeclaredPeakGiB':selected['originalCopyExportPeakBytesBound']/2**30,
                   'thirtyMinuteDeclaredPeakGiB':longrun['originalCopyExportPeakBytesBound']/2**30,
                   'evidenceCapBytes':3*2**30,'evidenceCapFiles':10000},
        'limits':[
            'Actual test is unarmed read-only monitoring, not manual/AUTO/camera/gimbal mission execution.',
            'Actual Android native monitoring overlaps about35s of a bounded60s host capture; active lifecycle about31.86s. Model span59.458s, not a claimed full60s simulation qualification.',
            'Native actual journal is one segment; native rotation/faults tested by mock/JVM only. Host/AP segment rotation observed.',
            'Full M1 manual/assisted/neutral takeover/link/AP reboot/30min and full Beta cockpit/media/3D remain NOT_READY.',
            'All actual runs use provisional empty/calm/seed32 external model, not calibrated Hera flight or acoustic fidelity.',
            'Clock cold audit validates brackets/ages used perframe, not an independent replay of everycorrelatorfault or fullcrossdomain timing proof.',
            'Local anchors and hashes are local orchestration integrity, not remote authentication, physical powerloss proof, product certification or publication permission.',
            'Original165missing/97trackeddeletions remain preexisting; no continuous historical path presence claimed.',
            'No new product AI functionality/model baseline comparison is relevant or claimed in this deterministic transport task.',
        ],
        'next':'M1 actual manual/assisted/link/reboot plus lossless recording/storage admission for30min; no hidden threshold/frame/fsync change.',
    }
    assert summary['budgets']['elapsedSeconds']<14400
    put(E/'verification-final01.json',summary)
    put('planning/betaintegrated01/PROGRESS-M1-RUNTIME.json',{'atUTC':now,'M0':'COMPLETE_SOURCE_HANDOFF','M1Mock':'FOUNDATION_READY',
        'M1Runtime':'ADAPTERS_WIRED_READONLY_SHORT_PASSED','M1Actual':'NOT_READY','BETA_SIM':'NOT_READY',
        'verification':str(E/'verification-final01.json'),'failedIntervalsAddedToCurrent':False,
        'current':{'APK':apk['apk'],'AP':'runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03','profile':'runtime/betaintegrated01/dist/run-profile03.json'},
        'thirtyMinuteGate':'REFUSED_CAPACITY_NO_RUN','canonicalSOTOrPriorProgressEdited':False})
    report=f'''# AERIS · M1 runtime cô lập và Android–SITL ngắn

27/10/2026. **Đạt phạm vi ghép adapter và lượt chỉ đọc ngắn. M1 đầy đủ và Beta vẫn NOT READY.** Lượt30phút chưa chạy vì admission dung lượng không đạt. Không dùng kết quả này làm nghiệm thu bay manual/AUTO hay drone thật.

## Kết quả thực tế

Host journal phân đoạn, clock và AP drainer đã ghép với external SITL; native Android là writer MAVLink duy nhất. APK development05 và AP03 được đối chiếu SHA với artifact đang cài/chạy trước CONNECT. Chỉ nối loopback/owned emulator, manual=false, profile NO_MEDIA_M1_RUNTIME. Đây là shell chẩn đoán, chưa phải cockpit cuối.

- **71.350 frame**: đủ RX/INTENT/SENT, **71.350 dòng timing**, **71.350 frame được trace AP bao phủ**. Đối chiếu độc lập toàn bộ byte sensor với model Python nguyên bản đạt; không lấy mẫu/bỏ frame để đạt kết quả.
- **578.561 AP events**, giữ cả đuôi chưa được backend nhận vào model và các lần AP phát lại PWM trong lúc chờ. Đuôi này không được tính thành frame đã thực thi.
- Model59,4583s trên59,4427s khoảng nhận frame; RTF **{result['actualRTF']:.6f}×**. Giữ speedup1/cap500ms. Đây là phép đo ngắn bên host với UI chẩn đoán, chưa phải benchmark cockpit3D/video hoặc nghiệm thu vận hành dài hạn.
- Clock590 request,585 match hợp lệ; bracket/tuổi clock được kiểm tại RX và sau INTENT fsync trước sensor send. Lịch sử được ghi theo luồng, pending/recent có giới hạn. Chưa tái chứng minh mọi chính sách clock/cross-domain từ lượt ngắn này.
- Native nhận firmware4.7.1/custom dbe79216, Home/vị trí và23 tên tham số. Decoder độc lập kiểm CRC/target; các command thực gửi chỉ có512 và511. Mọi heartbeat quan sát đều unarmed; không ARM/takeoff/AUTO.
- Native đóng và đối chiếu được985 bản ghi bằng anchor giữ ở kênh điều phối ngoài raw.26 checkpoint đóng có cùng elapsed31,86289114s. Sau force-stop/relaunch Android,4 file raw giữ nguyên SHA; UI mới NO_SESSION, không tự nối hoặc khôi phục quyền.
- Raw gốc, bản sao và gói tar128 file đã kiểm byte/hash. Archive khoảng193,6MiB; anchor tin cậy không được suy ra từ chính gói nhận.

Native monitoring chồng lấp khoảng35s của capture host có ngân sách60s; phase active khoảng31,86s. Model thực có59,4583s, không gắn nhãn đã kiểm đủ60s mô phỏng. Native raw thực chỉ có1 segment; luân chuyển native được kiểm mock/JVM, còn host/AP có luân chuyển trong capture thực.

## Những lỗi đã sửa và bằng chứng giữ lại

Lượt actual01 thất bại và được giữ nguyên. Audit tìm được34.033 nhóm RX/INTENT/SENT khớp model, nhưng chỉ34.032 STAGE; bộ đếm cũ tăng sau ghi STAGE nên báo thiếu một frame đã gửi và gọi nhầm đó là input chưa được nhận. Runtime02 tách admission, SENT và timing commit, giữ attempted-stage/phase đúng và chặn gửi lại. Fault injection sau SENT với guard prime thực15s đã kiểm độc lập.

Guard cũ giữ64 mẫu theo từng check. Dưới tải ghi cao, cửa sổ đo co xuống vài mili giây rồi chiếu rate đó ra15s. Runtime02 giữ lịch sử theo cadence có giới hạn, lấy đủ15s từ host thật trước ghi, kiểm floor/forecast ở từng write/send và giữ diagnostic khi từ chối. **Entry20GiB, floor10GiB+256MiB và forecast15s không giảm**. Không sửa/monkeypatch module M1-MOCK hay runtime01.

Emulator01 đã dừng sạch do forecast sau biến động khoảng1,9GiB/2s, trước khi mở AP. Tác nhân cấp phát chưa xác định. Exact64 mẫu gây lỗi guard actual01 không được ghi, nên không kết luận một hoạt động host cụ thể là nguyên nhân; bug cửa sổ đo được xác nhận bằng source và ca tái hiện xác định.

Intent CONNECT cũ bị từ chối tại lifecycle. Cờ controller khi đó chỉ là đã gửi intent, không phải socket kết nối; thông báo tiến độ gọi “đã kết nối” trước đó đã được đính chính. APK05 chỉ tiêu thụ explicit intent một lần sau resume/foreground, có ID/TTL/cancel/replay fence; callback log thực ghi QUEUED foreground=false rồi CONSUMED foreground=true. Resume/history thông thường không tạo phiên mới. onPause vẫn thu hồi/đóng owner.

Các artifact link dynamic đầu tiên, AP trước sửa nhánh báo lỗi cạnh tranh dữ liệu, lỗi compile Android và ca QA schema/reader đều còn receipt; không promote hoặc cộng thời gian các lần thất bại. AP03 mới giữ object thuật toán/model/pacer cũ, thêm observer được kiểm unit Linux; chưa chứng nhận tương đương toàn bộ hành vi điều khiển firmware khi bay.

## Đóng tài nguyên và phạm vi an toàn của kết luận

Hai AP kết thúc bằng **forced simulator stop, exit-9** sau grace; parent quan sát EOF và drain trace. Đây không phải kết thúc AP graceful, hạ cánh hay an toàn máy bay. Native đóng có journal/anchor; emulator02 dừng theo owner, exit0. Không còn container của task hoặc class build tạm. Không gửi lệnh bay từ host controller.

Hash/anchor chỉ chứng minh tính toàn vẹn và local sync theo wrapper được tin cậy; không chứng minh mất điện vật lý, xác thực nguồn từ xa, execution từ ACK hay cấp quyền công bố. Một số nhãn scope trong snapshot foundation vẫn là nhãn policy mock; actual transport được chứng minh riêng bằng raw/CRC/process/artifact, không dùng nhãn đó làm PASS.

## Dung lượng, bảo toàn và cleanup

Lượt short được admission với cận peak gốc+bản sao+export **{selected['originalCopyExportPeakBytesBound']/2**30:.3f}GiB**. Cận30phút là **{longrun['originalCopyExportPeakBytesBound']/2**30:.3f}GiB**, chưa tính floor10GiB+256MiB. Host cuối khoảng21,4GiB nên từ chối30phút; không ký lách gate, không đổi fsync, speedup hoặc bỏ frame. Đây là cận định dạng được khai báo/kiểm, không lấy bitrate trung bình ngắn để suy ra chắc chắn cho30phút.

17.117 định danh baseline,1.620 mục bàn giao trước,48 file M0 và830 mục M1-MOCK không có sai lệch mới.165 đường dẫn thiếu từ baseline và97 tracked deletions từ trước vẫn giữ hiện trạng; không tuyên bố toàn codebase đủ file hoặc đường dẫn gốc hiện diện liên tục. Source/candidate đóng băng, canonical SOT và lịch sử ENDURE không sửa.

Đã dọn class/scratch build của task và4 file scratch Android dùng chuyển binding/XML, sau khi lưu bằng chứng. Docker image prune thu hồi0B; không prune container/volume. Giữ AVD riêng đã khởi tạo ở .local/betaintegrated01/android để tái dùng, giữ toàn bộ raw/receipt/artifact thất bại. Không tạo bản sao project trong /tmp, không cài SDK/dependency mới, không ký production hoặc push/publish.

## Còn lại để đạt M1 và Beta

Tiếp theo là manual/assisted với input thực, neutral takeover, mất link/AP reboot và30min cùng candidate đã định danh. Cần giải quyết admission bằng định dạng lossless có đối chứng hoặc lưu trữ phù hợp; giữ nguyên các gate. Rồi mới ghép cockpit cuối, workbench, video/payload và corpus nhiệm vụ toàn Beta. Lượt này không kiểm AUTO, ảnh/video,4payload/dual-operator, 3D/audio, HeraHub/Xiaomi thật, hiệu chuẩn Hera hay bay thực.

## Hồ sơ kiểm chứng

- [Nghiệm thu Contractor](../evidence/betaintegrated01-m1runtime/verification-final01.json)
- [QA độc lập actual02](../evidence/betaintegrated01-m1runtime/qa/actual02-cold-audit.json)
- [QA restart Android](../evidence/betaintegrated01-m1runtime/qa/actual02-restart-review.json)
- [Source/candidate/ENDURE bảo toàn](../evidence/betaintegrated01-m1runtime/preservation-after01.json)
- [Admission60s/5m/15m/30m](../evidence/betaintegrated01-m1runtime/actual02/control/duration-admission.json)
- [Quyết định sửa runtime02](../planning/betaintegrated01/m1runtime/ADR-RUNTIME02.md)
- [APK development05, chỉ emulator](../{apk['apk']})
- [Raw/native export tar](../evidence/betaintegrated01-m1runtime/actual02/m1short02-raw-native.tar)
- [Tiến độ kế tiếp, không ghi đè SOT cũ](../planning/betaintegrated01/PROGRESS-M1-RUNTIME.json)
'''
    md=Path('delivery/COMPLETION-BETA-CAMPAIGN01-M1-RUNTIME.md')
    write(md,report)
    def inline(t):
        t=html.escape(t)
        t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',t)
        return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t)
    blocks=[]
    for b in report.strip().split('\n\n'):
        if b.startswith('# '): blocks.append('<h1>'+inline(b[2:])+'</h1>')
        elif b.startswith('## '):blocks.append('<h2>'+inline(b[3:])+'</h2>')
        elif b.startswith('- '):blocks.append('<ul>'+''.join('<li>'+inline(s[2:])+'</li>'for s in b.splitlines())+'</ul>')
        else:blocks.append('<p>'+inline(b)+'</p>')
    page='<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AERIS M1 runtime</title><style>body{margin:0;background:#f5f5f3;color:#1b1d20;font:16px/1.7 system-ui,sans-serif}main{max-width:1040px;margin:auto;padding:48px 28px 80px}h1{font-size:clamp(27px,4vw,43px);line-height:1.2;letter-spacing:-.035em}h2{font-size:22px;margin-top:36px;border-top:1px solid #ccc;padding-top:24px}p,li{max-width:90ch}li{margin:.65em 0}a{color:inherit;text-underline-offset:3px}strong{font-weight:750}@media print{body{background:white}main{padding:0}}</style><main>'+''.join(blocks)+'</main></html>'
    hp=md.with_suffix('.html');write(hp,page)
    links=[]
    for ref in re.findall(r'href="([^"]+)"',page):
        p=hp.parent/ref
        assert p.is_file(),str(p)
        links.append({'link':ref,'sha256':sha(p)})
    put(E/'report-links01.json',{'links':links,'status':'PASS_LOCAL_LINKS','visualHTMLQA':'NOT_PERFORMED_STRUCTURAL_ONLY',
                               'AndroidActualUI':'Observed XML/screenshots/intentlogs for diagnostic shell only, not finalcockpitvisualcertification'})
    print(json.dumps({'status':summary['status'],'report':str(hp),'requirements':len(criteria),'reportLinks':len(links),
                      'shortFrames':result['frames'],'thirtyMinutePeakGiB':summary['budgets']['thirtyMinuteDeclaredPeakGiB']}))


if __name__=='__main__':
    main()
