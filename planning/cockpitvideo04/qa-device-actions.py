"""Root-only owned emulator setup/cold-start/store snapshots. Never installs or edits native data."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,re,sys,time
spec=importlib.util.spec_from_file_location('qa_android04',Path(__file__).with_name('qa-android.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
EXPECTED='df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d'
def run(attempt,action,variant=''):
    assert attempt in ['01','02']and action in ['setup','start','store-before','store-after'];assert not variant or re.fullmatch('[a-z0-9-]{1,24}',variant)
    launch=q.owned(attempt);suffix=('-'+variant+'-'if variant else'')+attempt
    def path(name):return q.E/(name+suffix+'.json')
    def put(name,data):
        with path(name).open('x')as f:json.dump(data,f,indent=2);f.flush();os.fsync(f.fileno())
    target='android-device'if action=='setup'else'android-activity-start'if action=='start'else'android-'+action;assert not path(target).exists(),'EXCLUSIVE_ACTION_RECEIPT_ALREADY_EXISTS_NO_RETRY'
    if action=='setup':
        assert not variant,'ONE_SETUP_PER_ADMITTED_LAUNCH';put(target+'-intent',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'EXPLICIT_OWNED_ADB_ROOT_SETUP_INTENT_NO_AUTO_RETRY','serial':q.S});q.adb('root',timeout=10);q.adb('wait-for-device',timeout=30)
        end=time.monotonic()+90
        while q.adb('shell','getprop','sys.boot_completed').strip()!=b'1':
            assert time.monotonic()<end,'BOOT_COMPLETION_BOUND';time.sleep(1)
        q.owned(attempt);assert q.adb('shell','id','-u').strip()==b'0','ADB_ROOT_EMULATOR_ONLY_REQUIRED';q.adb('reverse','tcp:8872','tcp:8872');q.adb('reverse','tcp:8873','tcp:8873')
        pm=q.adb('shell','pm','path',q.P).decode().strip().splitlines();assert len(pm)==1 and pm[0].startswith('package:/data/app/')and pm[0].endswith('/base.apk');installed=q.adb('shell','sha256sum',pm[0][8:]).decode().split()[0];assert installed==EXPECTED,'UNCHANGED_INSTALLED_APK_REQUIRED'
        facts={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'serial':q.S,'emulatorPid':launch['pid'],'package':q.P,'installedApkSha256':installed,'bootId':q.adb('shell','cat','/proc/sys/kernel/random/boot_id').decode().strip(),'cpuOnline':q.adb('shell','cat','/sys/devices/system/cpu/online').decode().strip(),'release':q.adb('shell','getprop','ro.build.version.release').decode().strip(),'sdk':q.adb('shell','getprop','ro.build.version.sdk').decode().strip(),'webview':q.adb('shell','dumpsys','webviewupdate').decode()[-8192:],'adbRootScope':'EXPLICIT_AUTHORIZED_OWNED_EMULATOR_5582_ONLY','reversePorts':[8872,8873],'noInstallOrSign':True};assert facts['sdk']=='33'and facts['cpuOnline']=='0-3';put(target,facts);print(json.dumps(facts,ensure_ascii=False))
    elif action=='start':
        host=q.state();assert not host['flight'].get('run')and not host['flight'].get('authority'),'CLOSE_SIMULATION_BEFORE_INTENTIONAL_PROCESS_RESTART';lease=host.get('payloadLeaseObservation');assert not lease or lease.get('leaseCount')==0,'REVOKE_PAYLOAD_BEFORE_PROCESS_RESTART';before=q.adb('shell','pidof',q.P,allow=True).decode().strip();put(target+'-intent',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'EXPLICIT_OWNED_ACTIVITY_START_INTENT_NO_AUTO_RETRY','previousPid':before,'variant':variant,'noAppDataClear':True});started=time.monotonic_ns();result=q.adb('shell','am','start','-S','-W','--user','0','-f','0x10008000','-n',q.P+'/.ShellActivity',timeout=30).decode();after=q.adb('shell','pidof',q.P).decode().strip();assert'Status: ok'in result and after
        facts={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'startHostMonoNs':str(started),'endHostMonoNs':str(time.monotonic_ns()),'previousPid':before,'currentPid':after,'amOutput':result,'variant':variant,'scope':'EXPLICIT_OWNED_PROCESS_COLD_START_CLEAR_TASK_ONLY_NOT_APP_DATA_NO_VIEWER_RETRY','authorityRestored':False};put(target,facts);print(json.dumps(facts))
    else:
        root='/data/user/0/'+q.P+'/files/field02';raw=q.adb('shell','find',root,'-type','f','-exec','sha256sum','{}','+').decode();assert len(raw.encode())<65536;files={}
        for line in raw.splitlines():
            h,name=line.split(None,1);assert re.fullmatch('[a-f0-9]{64}',h)and name.startswith(root+'/');assert re.fullmatch(r'(journal\.jsonl|mirror-[a-f0-9]{64}\.json|[a-f0-9-]{36}\.artifact)',name[len(root)+1:]),'UNEXPECTED_NATIVE_STORE_FILE';files[name]=h
        assert 15<=len(files)<=64,'EXPECTED_RETAINED_NATIVE15_BASELINE_AND_BOUNDED_APPENDS';journal=q.adb('exec-out','cat',root+'/journal.jsonl');assert journal.endswith(b'\n')and len(journal)<=1024*1024;assert hashlib.sha256(journal).hexdigest()==files[root+'/journal.jsonl'],'STORE_SNAPSHOT_CHANGED_DURING_COLLECTION';jp=q.E/('android-native-journal-'+action+suffix+'.jsonl');jp.open('xb').write(journal)
        facts={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'fileCount':len(files),'listingSha256':hashlib.sha256(raw.encode()).hexdigest(),'journalFile':str(jp.relative_to(q.R)),'journalBytes':len(journal),'journalSha256':hashlib.sha256(journal).hexdigest(),'scope':'READONLY_NATIVE_STORE_HASHES_AND_EXACT_JOURNAL_NO_MUTATION'}
        if action=='store-after':
            bp=path('android-store-before');assert bp.exists(),'MATCHED_BEFORE_SNAPSHOT_REQUIRED';old=json.loads(bp.read_text());missing=[n for n in old['files']if n not in files];changed=[n for n,h in old['files'].items()if n in files and files[n]!=h and not n.endswith('/journal.jsonl')];assert not missing and not changed,'OLD_NATIVE_ARTIFACT_CHANGED_OR_MISSING';oldJournal=(q.R/old['journalFile']).read_bytes();assert journal.startswith(oldJournal),'NATIVE_JOURNAL_PREFIX_CHANGED';facts.update({'oldArtifactShaUnchanged':True,'journalPrefixIdentical':True,'newFiles':sorted(set(files)-set(old['files'])),'journalAppendBytes':len(journal)-len(oldJournal)})
        put(target,facts);print(json.dumps({'files':len(files),'journalBytes':len(journal),'receipt':str(path(target))}))
if __name__=='__main__':
    assert len(sys.argv)in[3,5]and(len(sys.argv)==3 or sys.argv[3]=='--variant'),'ATTEMPT_ACTION_OPTIONAL_VARIANT_REQUIRED';run(sys.argv[1],sys.argv[2],sys.argv[4]if len(sys.argv)==5 else'')
