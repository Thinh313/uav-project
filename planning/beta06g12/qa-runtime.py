# BETA06g2 isolated QA helper; previous helpers remain immutable.
"""Contractor-only owned emulator controller. Import/--plan never launches anything."""
from pathlib import Path
import importlib.util,sys
if 'g12_native_writer'not in sys.modules:
 _w=importlib.util.spec_from_file_location('g12_native_writer',Path(__file__).with_name('qa-native-budget.py'));b=importlib.util.module_from_spec(_w);sys.modules[_w.name]=b;_w.loader.exec_module(b)
else:b=sys.modules['g12_native_writer']
import datetime,json,os,shutil,signal,socket,subprocess,sys,time
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation12';W=R/'.local/field02';SDK=R/'.local/native86-android/sdk';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
GIB=2**30

def budget_decision(samples):
    assert len(samples)==31 and samples[-1]['mono']-samples[0]['mono']>=30,'STABLE_31_SECONDS_REQUIRED'
    assert all(s['free']>=29*GIB for s in samples),'ADMISSION_29GIB'
    maximum=samples[0]['free']
    for s in samples:
        maximum=max(maximum,s['free']);assert maximum-s['free']<=256*2**20,'UNSTABLE_DISK_TREND'

def trend_decision(previous,t,free):
    previous=[*previous,(t,free)];previous=[x for x in previous if x[0]>=t-2]
    rate=max(0,(previous[0][1]-free)/max(.001,t-previous[0][0]));forecast=free-rate*15
    if free<28*GIB:raise RuntimeError('GUARD28_GIB_PROTECT20')
    if forecast<20*GIB:raise RuntimeError('GUARD_FORECAST15S_PROTECT20')
    return previous,rate,forecast

def plan():
    conf=(W/'avd/aeris-field02.avd/config.ini').read_text();assert 'android-33/default/arm64-v8a'in conf,'DECLARED_CACHED_API33_REQUIRED'
    cmd=[str(SDK/'emulator/emulator'),'-avd','aeris-field02','-port','5582','-no-window','-accel','on','-gpu','host','-no-snapshot','-no-boot-anim','-no-audio','-camera-back','none','-camera-front','none','-memory','2048','-cores','4','-no-metrics']
    return {'clockBasis':b.host_clock.BASIS,'serial':'emulator-5582','avd':'aeris-field02','cachedAPI':33,'command':cmd,'attempts':['24','25'],'admissionSamples':31,'minimumAdmissionSeconds':30,'admissionBytes':29*GIB,'maximumAdmissionDeclineBytes':256*2**20,'guardBytes':28*GIB,'floorBytes':20*GIB,'forecastSeconds':15,'pollMs':250,'hardDurationS':2700,'taskEvidenceMaximumBytes':b.load()['active']['hardBytes'],'noInstallBuildDownload':True}

def validate_bootstrap(env=None,*,parent_pid=None):
    source=os.environ if env is None else env;boot=b.host_clock.boot_id();b.host_clock.same_contract(source.get('BETA06_HOST_BOOT_UUID'),boot,source.get('BETA06_CLOCK_BASIS'))
    root=source.get('BETA06_ROOT_CONTROLLER_PID');assert isinstance(root,str)and root.isascii()and root.isdigit()and int(root)>0 and int(root)==(os.getppid()if parent_pid is None else parent_pid),'CLOCK_BOOTSTRAP_OWNED_PARENT_PID_REQUIRED';os.kill(int(root),0);b.host_clock.now_ns();return {'hostBootId':boot,'clockBasis':b.host_clock.BASIS,'rootControllerPid':int(root)}
def validate_parent_permit(permit,attempt,*,clock=b.host_clock.now_s,current_boot=None,parent_pid=None,pid_check=os.kill):
    boot=b.host_clock.boot_id()if current_boot is None else current_boot;b.host_clock.same_contract(permit.get('hostBootId'),boot,permit.get('clockBasis'))
    assert permit['anchorProof']['anchors']['clockBasis']==b.host_clock.BASIS and permit['anchorProof']['anchors']['hostBootId']==boot,'PARENT_ANCHOR_CLOCK_BOOT_CONTRACT_REQUIRED'
    assert permit['attempt']==attempt,'TRUSTED_ROOT_PRELAUNCH_PERMIT_REQUIRED';root_pid=permit['rootControllerPid'];assert isinstance(root_pid,int)and root_pid>0 and permit['anchorProof']['anchors']['emulatorBeforeLaunchPythonMonoS']is not None and permit['anchorProof']['attempt']==attempt and permit['anchorProof']['controllerPid']==root_pid and (os.getppid()if parent_pid is None else parent_pid)==root_pid,'PERSISTENT_ROOT_PID_ANCHOR_REQUIRED';pid_check(root_pid,0);parent_host_remaining=permit['parentHostRemainingS'];assert isinstance(parent_host_remaining,(int,float))and 0<parent_host_remaining<=2700,'PARENT_REMAINING_HOST_BUDGET_REQUIRED';permit_child_anchor=clock();parent_host_deadline=permit['parentHostDeadlinePythonMonoS'];emulator_deadline=permit['anchorProof']['anchors']['emulatorBeforeLaunchPythonMonoS']+2700;assert isinstance(parent_host_deadline,(int,float))and permit_child_anchor<parent_host_deadline<=permit_child_anchor+2700,'ORIGINAL_PARENT_DEADLINE_REQUIRED';assert permit_child_anchor<emulator_deadline<=permit_child_anchor+2700,'ROOT_PREPERMIT_EMULATOR_DEADLINE_REQUIRED'
    return {'rootPid':root_pid,'parentHostRemainingS':parent_host_remaining,'receivedPythonMonoS':permit_child_anchor,'parentHostDeadlinePythonMonoS':parent_host_deadline,'emulatorDeadlinePythonMonoS':emulator_deadline,'clockBasis':b.host_clock.BASIS,'hostBootId':boot}
def run(attempt,require_permit=True):
    assert require_permit is True,'PERSISTENT_ROOT_LAUNCH_PERMIT_REQUIRED';assert attempt in ['24','25'];bootstrap=validate_bootstrap();p=plan();E.mkdir(parents=True,exist_ok=True)
    for name in [f'android-attempt{attempt}.json',f'android-launch{attempt}.json',f'android-console{attempt}.txt',f'android-guard{attempt}.jsonl',f'android-closure{attempt}.json']:assert not(E/name).exists(),'ATTEMPT_ALREADY_RECORDED_NO_RETRY'
    def put(name,data):
        b.write_json(E/name,{**data,'clockBasis':b.host_clock.BASIS,'hostBootId':bootstrap['hostBootId']},kind='runtime-metadata',closure=name.startswith('android-closure'))
    samples=[]
    refusal=E/f'android-admission{attempt}-{time.time_ns()}.json'
    try:
        for n in range(31):
            samples.append({'mono':b.host_clock.now_s(),'free':shutil.disk_usage(R).free})
            if samples[-1]['free']<29*GIB:raise AssertionError('ADMISSION_29GIB')
            if n<30:time.sleep(1)
        budget_decision(samples)
    except BaseException as exc:
        b.write_json(refusal,{'clockBasis':b.host_clock.BASIS,'hostBootId':bootstrap['hostBootId'],'status':'REFUSED_BEFORE_LAUNCH_INTENT','attempt':attempt,'samples':samples,'error':str(exc),'noRuntimeStarted':True},closure=True)
        raise
    try:
        for port in [5582,5583]:
            with socket.socket()as s:s.bind(('127.0.0.1',port))
        env={**os.environ,'ANDROID_AVD_HOME':str(W/'avd'),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
        accel=subprocess.run([str(SDK/'emulator/emulator'),'-accel-check'],env=env,capture_output=True,text=True,timeout=20)
        put(f'android-acceleration{attempt}.json',{'exit':accel.returncode,'output':accel.stdout+accel.stderr});assert accel.returncode==0 and 'Hypervisor.Framework'in accel.stdout+accel.stderr
        budget_decision([*samples[:-1],{'mono':b.host_clock.now_s(),'free':shutil.disk_usage(R).free}])
    except BaseException as exc:
        b.write_json(refusal,{'clockBasis':b.host_clock.BASIS,'hostBootId':bootstrap['hostBootId'],'status':'REFUSED_PRE_INTENT_FINAL_CHECK','attempt':attempt,'samples':samples,'finalFreeBytes':shutil.disk_usage(R).free,'error':str(exc),'noRuntimeStarted':True},closure=True)
        raise
    scoped=b.admit('guard',remaining_ap=4,remaining_hosts=2,closed_runs=[],claim_id='emulator-'+attempt);put(f'android-quota-admission{attempt}.json',scoped)
    put(f'android-attempt{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'ADMITTED_LAUNCH_INTENT_NO_AUTOMATIC_RETRY','samples':samples,**p})
    console=b.BoundedFile(E/f'android-console{attempt}.txt',4*2**20,binary=True,kind='emulator-console');guard=b.BoundedFile(E/f'android-guard{attempt}.jsonl',512*2**10,kind='emulator-guard');capture=None;watch=None;proc=None;caffeine=None;root_pid=None;parent_host_remaining=None;permit_child_anchor=None;parent_host_deadline=None;emulator_deadline=None;stopped=False;error=None;minimum=shutil.disk_usage(R).free
    def stop(*_):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        if require_permit:
            put(f'android-ready-to-launch{attempt}.json',{'attempt':attempt,'controllerPid':os.getpid(),'permission':'AWAIT_PERSISTENT_ROOT_PYTHON_ANCHOR_BEFORE_LAUNCH','clockBasis':bootstrap['clockBasis'],'hostBootId':bootstrap['hostBootId']})
            ready_deadline=b.host_clock.now_s()+15
            while not(E/f'android-launch-permit{attempt}.json').exists():
                assert b.host_clock.now_s()<ready_deadline,'PERSISTENT_ROOT_LAUNCH_PERMIT_DEADLINE';time.sleep(.05)
            permit=json.loads((E/f'android-launch-permit{attempt}.json').read_text());binding=validate_parent_permit(permit,attempt);root_pid=binding['rootPid'];parent_host_remaining=binding['parentHostRemainingS'];permit_child_anchor=binding['receivedPythonMonoS'];parent_host_deadline=binding['parentHostDeadlinePythonMonoS'];emulator_deadline=binding['emulatorDeadlinePythonMonoS']
        assert not stopped and not(E/f'android-stop-request{attempt}.json').exists(),'ROOT_CLOSED_BEFORE_EMULATOR_LAUNCH'
        proc=subprocess.Popen(p['command'],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);capture=b.PipeCapture(proc,console);watch=b.QuotaWatch(clock=b.host_clock.now_s,claim='emulator-guard-'+attempt);caffeine=subprocess.Popen(['caffeinate','-i','-w',str(proc.pid)])
        put(f'android-launch{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':proc.pid,'controllerPid':os.getpid(),'attempt':attempt,'samples':samples,**p});print('OWNED_ANDROID_LAUNCHED '+str(proc.pid),flush=True)
        start=b.host_clock.now_s();previous=[];logged=-1
        while not stopped and not(E/f'android-stop-request{attempt}.json').exists():
            capture.check();quota_status=watch.check();t=b.host_clock.now_s();free=shutil.disk_usage(R).free;minimum=min(minimum,free)
            assert root_pid is not None and os.getppid()==root_pid,'PERSISTENT_ROOT_REQUIRED';os.kill(root_pid,0)
            try:previous,rate,forecast=trend_decision(previous,t,free)
            except RuntimeError as exc:guard.write(json.dumps({'clockBasis':b.host_clock.BASIS,'hostBootId':bootstrap['hostBootId'],'mono':t,'freeBytes':free,'error':str(exc)})+'\n');guard.flush();raise
            if t-logged>=1:guard.write(json.dumps({'clockBasis':b.host_clock.BASIS,'hostBootId':bootstrap['hostBootId'],'mono':t,'freeBytes':free,'observedMinimumBytes':minimum,'declineBytesPerS':rate,'forecast15sBytes':forecast,'quota':quota_status})+'\n');guard.flush();logged=t
            assert proc.poll()is None,'EMULATOR_EXIT';assert emulator_deadline is not None and t<emulator_deadline,'BOUNDED_RUNTIME_45MIN_FROM_ROOT_PREPERMIT';assert parent_host_deadline is not None and t<parent_host_deadline,'ORIGINAL_PARENT_HOST_BUDGET_EXHAUSTED';assert guard.tell()<512*2**10,'GUARD_LOG_BOUND';assert console.tell()<4*2**20,'CONSOLE_LOG_BOUND'
            time.sleep(.25)
    except BaseException as exc:error=str(exc)
    finally:
        if proc and proc.poll()is None:
            try:
                identity=subprocess.run([ADB,'-s','emulator-5582','emu','avd','name'],capture_output=True,timeout=5)
                if identity.returncode==0 and identity.stdout.splitlines()[0]==b'aeris-field02':subprocess.run([ADB,'-s','emulator-5582','emu','kill'],capture_output=True,timeout=10)
                else:proc.terminate()
                proc.wait(timeout=15)
            except BaseException:
                try:os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=5)
                except BaseException:
                    try:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
                    except ProcessLookupError:pass
        if watch:
            try:watch.close()
            except BaseException as exc:error=error or str(exc)
        if capture:
            try:capture.finish()
            except BaseException as exc:error=error or str(exc)
        console.close();guard.close()
        if caffeine:
            try:caffeine.wait(timeout=5)
            except subprocess.TimeoutExpired:caffeine.terminate()
        put(f'android-closure{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':proc.pid if proc else None,'exit':proc.returncode if proc else None,'error':error,'minimumFreeBytes':minimum,'finalFreeBytes':shutil.disk_usage(R).free,'explicitStop':stopped or(E/f'android-stop-request{attempt}.json').exists(),'notAcceptance':True,'otherHostAndAPClosure':'CONTRACTOR_MUST_VERIFY_SEPARATELY'})
        print('OWNED_ANDROID_CLOSED '+str(error),flush=True)

if __name__=='__main__':
    if sys.argv[1:]==['--plan']:print(json.dumps(plan(),indent=2))
    else:
        assert len(sys.argv)==4 and sys.argv[1]=='--start'and sys.argv[3]=='--require-permit','EXPLICIT_START_REQUIRED'
        run(sys.argv[2],require_permit=len(sys.argv)==4)
