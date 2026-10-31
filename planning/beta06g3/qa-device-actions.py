# BETA06g2 isolated QA helper; previous helpers remain immutable.
"""Root-only owned emulator setup/cold-start/store snapshots. Never installs or edits native data."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,re,sys,time
spec=importlib.util.spec_from_file_location('qa_android04',Path(__file__).with_name('qa-android.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
EXPECTED='df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d'
def journal_chain(raw,previous='ROOT',start_seq=0,ordered=False):
    assert len(raw)<=1024*1024 and (not raw or raw.endswith(b'\n')),'JOURNAL_COMPLETE_BOUNDED_LINES'
    seq=start_seq;head=previous;first=None;last=None;pending=0
    for line in raw.splitlines():
        wrapper=json.loads(line);body=wrapper['body'];h=hashlib.sha256(body.encode()).hexdigest();assert h==wrapper['sha256'],'JOURNAL_BODY_SHA';r=json.loads(body);assert r['seq']==seq+1 and r['previous']==head,'JOURNAL_CHAIN';elapsed=r['elapsedMs'];assert isinstance(elapsed,int)and elapsed>=0,'JOURNAL_ELAPSED_FINITE';assert not ordered or last is None or elapsed>=last,'KNOWN_BOOT_APPEND_ELAPSED_ORDER';first=elapsed if first is None else first;last=elapsed;seq+=1;head=h;pending+=r['kind']=='PICKER_PENDING'
    return {'records':seq,'head':head,'firstElapsedMs':first,'lastElapsedMs':last,'pickerPendingCount':pending,'remainingLifetimePickerOperations':16-pending if start_seq==0 else None,'historyElapsedOrderClaimed':False}

def quota_decision(snapshot,required):
    assert isinstance(required,int)and not isinstance(required,bool)and 0<=required<=16,'BOUNDED_SAF_PLAN_REQUIRED';used=snapshot['journalChain']['pickerPendingCount'];assert isinstance(used,int)and 0<=used<=16 and used+required<=16,'NATIVE_LIFETIME_PICKER_QUOTA_INSUFFICIENT_NO_CLEAR';return {'used':used,'required':required,'remaining':16-used,'noQuotaResetOrDelete':True}

def run(attempt,action,variant='',before_receipt=None):
    assert attempt in ['04','05']and action in ['setup','start','store-before','store-after'];assert not variant or re.fullmatch('[a-z0-9-]{1,24}',variant)
    launch=q.owned(attempt);boot_id=q.adb('shell','cat','/proc/sys/kernel/random/boot_id').decode().strip();assert re.fullmatch('[a-f0-9-]{36}',boot_id),'ACTUAL_GUEST_BOOT_ID_REQUIRED';suffix=('-'+variant+'-'if variant else'')+attempt
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
        facts={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'serial':q.S,'guestBootId':boot_id,'attempt':attempt,'emulatorPid':launch['pid'],'package':q.P,'installedApkSha256':installed,'bootId':q.adb('shell','cat','/proc/sys/kernel/random/boot_id').decode().strip(),'cpuOnline':q.adb('shell','cat','/sys/devices/system/cpu/online').decode().strip(),'release':q.adb('shell','getprop','ro.build.version.release').decode().strip(),'sdk':q.adb('shell','getprop','ro.build.version.sdk').decode().strip(),'webview':q.adb('shell','dumpsys','webviewupdate').decode()[-8192:],'adbRootScope':'EXPLICIT_AUTHORIZED_OWNED_EMULATOR_5582_ONLY','reversePorts':[8872,8873],'noInstallOrSign':True};assert facts['sdk']=='33'and facts['cpuOnline']=='0-3';put(target,facts);print(json.dumps(facts,ensure_ascii=False))
    elif action=='start':
        host=q.state();assert not host['flight'].get('run')and not host['flight'].get('authority'),'CLOSE_SIMULATION_BEFORE_INTENTIONAL_PROCESS_RESTART';lease=host.get('payloadLeaseObservation');assert not lease or lease.get('leaseCount')==0,'REVOKE_PAYLOAD_BEFORE_PROCESS_RESTART';before=q.adb('shell','pidof',q.P,allow=True).decode().strip();put(target+'-intent',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'EXPLICIT_OWNED_ACTIVITY_START_INTENT_NO_AUTO_RETRY','previousPid':before,'variant':variant,'noAppDataClear':True});started=time.monotonic_ns();result=q.adb('shell','am','start','-S','-W','--user','0','-f','0x10008000','-n',q.P+'/.ShellActivity',timeout=30).decode();after=q.adb('shell','pidof',q.P).decode().strip();assert'Status: ok'in result and after
        facts={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'startHostMonoNs':str(started),'endHostMonoNs':str(time.monotonic_ns()),'guestBootId':boot_id,'emulatorPid':launch['pid'],'attempt':attempt,'previousPid':before,'currentPid':after,'amOutput':result,'variant':variant,'scope':'EXPLICIT_OWNED_PROCESS_COLD_START_CLEAR_TASK_ONLY_NOT_APP_DATA_NO_VIEWER_RETRY','authorityRestored':False};put(target,facts);print(json.dumps(facts))
    else:
        root='/data/user/0/'+q.P+'/files/field02';raw=q.adb('shell','find',root,'-type','f','-exec','sha256sum','{}','+').decode();assert len(raw.encode())<65536;files={}
        for line in raw.splitlines():
            h,name=line.split(None,1);assert re.fullmatch('[a-f0-9]{64}',h)and name.startswith(root+'/');assert re.fullmatch(r'(journal\.jsonl|mirror-[a-f0-9]{64}\.json|[a-f0-9-]{36}\.artifact)',name[len(root)+1:]),'UNEXPECTED_NATIVE_STORE_FILE';files[name]=h
        assert 19<=len(files)<=64,'EXPECTED_RETAINED_NATIVE19_BASELINE_AND_BOUNDED_APPENDS';journal=q.adb('exec-out','cat',root+'/journal.jsonl');assert journal.endswith(b'\n')and len(journal)<=1024*1024;assert hashlib.sha256(journal).hexdigest()==files[root+'/journal.jsonl'],'STORE_SNAPSHOT_CHANGED_DURING_COLLECTION';jp=q.E/('android-native-journal-'+action+suffix+'.jsonl');jp.open('xb').write(journal)
        chain=journal_chain(journal);assert chain['records']>=34 and 13<=chain['pickerPendingCount']<=16,'RETAINED_NATIVE34_RECORDS13_PENDING_NO_QUOTA_RESET';facts={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'guestBootId':boot_id,'emulatorPid':launch['pid'],'attempt':attempt,'variant':variant,'journalChain':chain,'files':files,'fileCount':len(files),'listingSha256':hashlib.sha256(raw.encode()).hexdigest(),'journalFile':str(jp.relative_to(q.R)),'journalBytes':len(journal),'journalSha256':hashlib.sha256(journal).hexdigest(),'scope':'READONLY_NATIVE_STORE_HASHES_AND_EXACT_JOURNAL_NO_MUTATION'}
        if action=='store-after':
            bp=Path(before_receipt)if before_receipt else path('android-store-before');assert bp.resolve().is_relative_to((q.R/'evidence/beta06').resolve())and bp.exists(),'MATCHED_BEFORE_SNAPSHOT_REQUIRED';old=json.loads(bp.read_text());missing=[n for n in old['files']if n not in files];changed=[n for n,h in old['files'].items()if n in files and files[n]!=h and not n.endswith('/journal.jsonl')];assert not missing and not changed,'OLD_NATIVE_ARTIFACT_CHANGED_OR_MISSING';oldJournal=(q.R/old['journalFile']).read_bytes();assert journal.startswith(oldJournal),'NATIVE_JOURNAL_PREFIX_CHANGED';same_boot=old.get('guestBootId')==boot_id;append_rows=journal_chain(journal[len(oldJournal):],previous=old['journalChain']['head'],start_seq=old['journalChain']['records'],ordered=same_boot)
            facts.update({'beforeReceipt':str(bp.relative_to(q.R)),'sameKnownGuestBoot':same_boot,'appendChain':append_rows,'elapsedOrderScope':'APPENDED_SEGMENT_ONLY_SAME_GUEST_BOOT'if same_boot else'CROSS_BOOT_NO_GLOBAL_ELAPSED_ORDER_ASSERTION','oldArtifactShaUnchanged':True,'journalPrefixIdentical':True,'newFiles':sorted(set(files)-set(old['files'])),'journalAppendBytes':len(journal)-len(oldJournal)})
        assert q.adb('shell','cat','/proc/sys/kernel/random/boot_id').decode().strip()==boot_id,'GUEST_BOOT_CHANGED_DURING_SNAPSHOT';put(target,facts);print(json.dumps({'files':len(files),'journalBytes':len(journal),'receipt':str(path(target))}));return facts
if __name__=='__main__':
    assert len(sys.argv)in[3,5]and(len(sys.argv)==3 or sys.argv[3]=='--variant'),'ATTEMPT_ACTION_OPTIONAL_VARIANT_REQUIRED';run(sys.argv[1],sys.argv[2],sys.argv[4]if len(sys.argv)==5 else'')
