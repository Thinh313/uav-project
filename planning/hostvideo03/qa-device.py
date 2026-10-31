"""Read/operate only the explicitly authorized, owned emulator-5582."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,sys,time
R=Path(__file__).resolve().parents[2];E=R/'evidence/field02/hostvideo03'
spec=importlib.util.spec_from_file_location('qa_android',R/'planning/hostvideo03/qa-android.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
attempt=sys.argv[1];action=sys.argv[2];assert attempt in ['01','02'];assert action in ['setup','start','store-before','store-after']
launch=json.loads((E/f'android-launch{attempt}.json').read_text());os.kill(launch['pid'],0)
assert q.adb('shell','getprop','ro.boot.qemu').strip()==b'1'
assert q.adb('emu','avd','name').splitlines()[0]==b'aeris-field02'
def put(name,data):
    with(E/name).open('x')as f:json.dump(data,f,indent=2)
if action=='setup':
    q.adb('root');time.sleep(1);q.adb('wait-for-device',timeout=30)
    q.adb('reverse','tcp:8872','tcp:8872');q.adb('reverse','tcp:8873','tcp:8873')
    boot=q.adb('shell','getprop','sys.boot_completed').strip();assert boot==b'1',boot
    pm=q.adb('shell','pm','path',q.P).decode().strip();assert pm.startswith('package:/data/app/')and pm.endswith('/base.apk'),pm
    installed=q.adb('shell','sha256sum',pm[len('package:'):]).decode().split()[0]
    assert installed=='df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d',installed
    facts={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'serial':q.S,'emulatorPid':launch['pid'],'package':q.P,'installedApkSha256':installed,
           'bootId':q.adb('shell','cat','/proc/sys/kernel/random/boot_id').decode().strip(),'cpuOnline':q.adb('shell','cat','/sys/devices/system/cpu/online').decode().strip(),
           'release':q.adb('shell','getprop','ro.build.version.release').decode().strip(),'sdk':q.adb('shell','getprop','ro.build.version.sdk').decode().strip(),
           'webview':q.adb('shell','dumpsys','webviewupdate').decode(),'adbRootScope':'OWNED_EMULATOR_5582_ONLY_PRIOR_EXPLICIT_AUTHORIZATION'}
    assert facts['cpuOnline']=='0-3';put(f'android-device{attempt}.json',facts);print(json.dumps(facts,ensure_ascii=False))
elif action=='start':
    before=q.adb('shell','pidof',q.P,allow=True).decode().strip();started=time.monotonic_ns()
    result=q.adb('shell','am','start','-S','-W','--user','0','-f','0x10008000','-n',q.P+'/.ShellActivity',timeout=30).decode()
    after=q.adb('shell','pidof',q.P).decode().strip();assert 'Status: ok' in result and after
    put(f'android-activity-start{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'startHostMonoNs':str(started),'endHostMonoNs':str(time.monotonic_ns()),'previousPid':before,'currentPid':after,'amOutput':result,'scope':'EXPLICIT_PROCESS_COLD_START_FIRST_RECEIVER_NO_PROBE_OR_VIEWER_RETRY'});print(result)
else:
    root='/data/user/0/'+q.P+'/files/field02'
    raw=q.adb('shell','find',root,'-type','f','-exec','sha256sum','{}','+').decode();files={}
    for line in raw.splitlines():
        h,name=line.split(None,1);assert len(h)==64 and name.startswith(root+'/');files[name]=h
    put(f'android-{action}{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'listingSha256':hashlib.sha256(raw.encode()).hexdigest(),'scope':'READONLY_NATIVE_STORE_HASHES_NO_FILE_CONTENTS'});print(json.dumps({'files':len(files)}))
