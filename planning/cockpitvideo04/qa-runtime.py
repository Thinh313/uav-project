"""Contractor-only owned emulator controller. Import/--plan never launches anything."""
from pathlib import Path
import datetime,json,os,shutil,signal,socket,subprocess,sys,time
R=Path(__file__).resolve().parents[2];E=R/'evidence/field02/cockpitvideo04';W=R/'.local/field02';SDK=R/'.local/native86-android/sdk';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
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
    return {'serial':'emulator-5582','avd':'aeris-field02','cachedAPI':33,'command':cmd,'attempts':['01','02'],'admissionSamples':31,'minimumAdmissionSeconds':30,'admissionBytes':29*GIB,'maximumAdmissionDeclineBytes':256*2**20,'guardBytes':28*GIB,'floorBytes':20*GIB,'forecastSeconds':15,'pollMs':250,'hardDurationS':1200,'taskEvidenceMaximumBytes':96*2**20,'noInstallBuildDownload':True}

def run(attempt):
    assert attempt in ['01','02'];p=plan();E.mkdir(parents=True,exist_ok=True)
    for name in [f'android-attempt{attempt}.json',f'android-launch{attempt}.json',f'android-console{attempt}.txt',f'android-guard{attempt}.jsonl',f'android-closure{attempt}.json']:assert not(E/name).exists(),'ATTEMPT_ALREADY_RECORDED_NO_RETRY'
    def put(name,data):
        with(E/name).open('x')as f:json.dump(data,f,indent=2);f.flush();os.fsync(f.fileno())
    samples=[]
    for n in range(31):
        samples.append({'mono':time.monotonic(),'free':shutil.disk_usage(R).free});assert samples[-1]['free']>=29*GIB,'ADMISSION_29GIB'
        if n<30:time.sleep(1)
    budget_decision(samples)
    for port in [5582,5583]:
        with socket.socket()as s:s.bind(('127.0.0.1',port))
    env={**os.environ,'ANDROID_AVD_HOME':str(W/'avd'),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
    accel=subprocess.run([str(SDK/'emulator/emulator'),'-accel-check'],env=env,capture_output=True,text=True,timeout=20)
    put(f'android-acceleration{attempt}.json',{'exit':accel.returncode,'output':accel.stdout+accel.stderr});assert accel.returncode==0 and 'Hypervisor.Framework'in accel.stdout+accel.stderr
    budget_decision([*samples[:-1],{'mono':time.monotonic(),'free':shutil.disk_usage(R).free}])
    put(f'android-attempt{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'ADMITTED_LAUNCH_INTENT_NO_AUTOMATIC_RETRY','samples':samples,**p})
    console=(E/f'android-console{attempt}.txt').open('x');guard=(E/f'android-guard{attempt}.jsonl').open('x');proc=None;caffeine=None;stopped=False;error=None;minimum=shutil.disk_usage(R).free
    def stop(*_):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        proc=subprocess.Popen(p['command'],cwd=R,env=env,stdout=console,stderr=subprocess.STDOUT,start_new_session=True);caffeine=subprocess.Popen(['caffeinate','-i','-w',str(proc.pid)])
        put(f'android-launch{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':proc.pid,'controllerPid':os.getpid(),'attempt':attempt,'samples':samples,**p});print('OWNED_ANDROID_LAUNCHED '+str(proc.pid),flush=True)
        start=time.monotonic();previous=[];logged=-1
        while not stopped and not(E/f'android-stop-request{attempt}.json').exists():
            t=time.monotonic();free=shutil.disk_usage(R).free;minimum=min(minimum,free)
            try:previous,rate,forecast=trend_decision(previous,t,free)
            except RuntimeError as exc:guard.write(json.dumps({'mono':t,'freeBytes':free,'error':str(exc)})+'\n');guard.flush();raise
            if t-logged>=1:guard.write(json.dumps({'mono':t,'freeBytes':free,'observedMinimumBytes':minimum,'declineBytesPerS':rate,'forecast15sBytes':forecast})+'\n');guard.flush();logged=t
            assert proc.poll()is None,'EMULATOR_EXIT';assert t-start<1200,'BOUNDED_RUNTIME_20MIN';assert guard.tell()<512*2**10,'GUARD_LOG_BOUND';assert console.tell()<4*2**20,'CONSOLE_LOG_BOUND'
            if int(t-start)%4==0:assert sum(q.stat().st_size for q in E.rglob('*')if q.is_file())<=96*2**20,'TASK_EVIDENCE_BOUND'
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
        console.close();guard.close()
        if caffeine:
            try:caffeine.wait(timeout=5)
            except subprocess.TimeoutExpired:caffeine.terminate()
        put(f'android-closure{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':proc.pid if proc else None,'exit':proc.returncode if proc else None,'error':error,'minimumFreeBytes':minimum,'finalFreeBytes':shutil.disk_usage(R).free,'explicitStop':stopped or(E/f'android-stop-request{attempt}.json').exists(),'notAcceptance':True,'otherHostAndAPClosure':'CONTRACTOR_MUST_VERIFY_SEPARATELY'})
        print('OWNED_ANDROID_CLOSED '+str(error),flush=True)

if __name__=='__main__':
    if sys.argv[1:]==['--plan']:print(json.dumps(plan(),indent=2))
    else:
        assert len(sys.argv)==3 and sys.argv[1]=='--start','EXPLICIT_START_REQUIRED'
        run(sys.argv[2])
