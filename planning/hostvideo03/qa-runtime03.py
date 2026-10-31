"""Bounded owned-emulator observer; no UI, flight, install or build operations."""
from pathlib import Path
import datetime,json,os,shutil,signal,socket,subprocess,sys,time
R=Path(__file__).resolve().parents[2];E=R/'evidence/field02/hostvideo03';W=R/'.local/field02';SDK=R/'.local/native86-android/sdk'
ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
attempt=sys.argv[1];assert attempt in ['03']
def put(name,data):
    with(E/name).open('x') as f: json.dump(data,f,indent=2);f.flush();os.fsync(f.fileno())
assert not(E/f'android-launch{attempt}.json').exists()
samples=[]
for n in range(31):
    free=shutil.disk_usage(R).free;samples.append({'hostMonoNs':str(time.monotonic_ns()),'freeBytes':free})
    assert free>=29*2**30,'ADMISSION_29GIB'
    if n<30:time.sleep(1)
assert samples[-1]['freeBytes']>=samples[0]['freeBytes']-256*2**20,'UNSTABLE_DISK_TREND'
for port in [5582,5583]:
    with socket.socket()as s:s.bind(('127.0.0.1',port))
env={**os.environ,'ANDROID_AVD_HOME':str(W/'avd'),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
accel=subprocess.run([str(SDK/'emulator/emulator'),'-accel-check'],env=env,capture_output=True,text=True,timeout=20)
put(f'android-acceleration{attempt}.json',{'exit':accel.returncode,'output':accel.stdout+accel.stderr})
assert accel.returncode==0 and 'Hypervisor.Framework' in accel.stdout+accel.stderr
cmd=[str(SDK/'emulator/emulator'),'-avd','aeris-field02','-port','5582','-no-window','-accel','on','-gpu','host','-no-snapshot','-no-boot-anim','-no-audio','-camera-back','none','-camera-front','none','-memory','2048','-cores','4','-no-metrics']
console=(E/f'android-console{attempt}.txt').open('x');p=subprocess.Popen(cmd,cwd=R,env=env,stdout=console,stderr=subprocess.STDOUT)
caffeine=subprocess.Popen(['caffeinate','-i','-w',str(p.pid)])
put(f'android-launch{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':p.pid,'controllerPid':os.getpid(),'serial':'emulator-5582','avd':'aeris-field02','command':cmd,'admissionSamples':samples,'guardBytes':28*2**30,'floorBytes':20*2**30,'hardDurationS':1200,'noInstallOrSignature':True})
print('OWNED_ANDROID_LAUNCHED '+str(p.pid),flush=True)
stopped=False
def stop(*_):
    global stopped
    stopped=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
start=time.monotonic();minimum=shutil.disk_usage(R).free;error=None;previous=[];loggedAt=-1
guard=(E/f'android-guard{attempt}.jsonl').open('x')
try:
    while not stopped and not(E/f'android-stop-request{attempt}.json').exists():
        t=time.monotonic();free=shutil.disk_usage(R).free;minimum=min(minimum,free)
        previous.append((t,free));previous=[x for x in previous if x[0]>=t-2]
        rate=(previous[0][1]-free)/max(.001,t-previous[0][0]);forecast=free-max(0,rate)*15
        if t-loggedAt>=1 or free<28*2**30 or forecast<20*2**30:
            guard.write(json.dumps({'hostMonoNs':str(time.monotonic_ns()),'freeBytes':free,'observedMinimumBytes':minimum,'declineBytesPerS':rate,'forecast15sBytes':forecast})+'\n');guard.flush();loggedAt=t
        assert free>=28*2**30,'GUARD28_GIB_PROTECT20'
        assert forecast>=20*2**30,'GUARD_FORECAST15S'
        assert p.poll()is None,'EMULATOR_EXIT'
        assert t-start<1200,'BOUNDED_RUNTIME'
        assert guard.tell()<512*2**10,'GUARD_LOG_BOUND'
        assert console.tell()<4*2**20,'CONSOLE_LOG_BOUND'
        time.sleep(.25)
except BaseException as ex:error=str(ex)
finally:
    if p.poll()is None:
        subprocess.run([ADB,'-s','emulator-5582','emu','kill'],capture_output=True,timeout=15)
        try:p.wait(timeout=20)
        except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
    console.close();guard.close()
    try:caffeine.wait(timeout=5)
    except subprocess.TimeoutExpired:caffeine.terminate()
    put(f'android-closure{attempt}.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':p.pid,'exit':p.returncode,'error':error,'minimumFreeBytes':minimum,'finalFreeBytes':shutil.disk_usage(R).free,'explicitStop':stopped or(E/f'android-stop-request{attempt}.json').exists(),'notAcceptance':True})
    print('OWNED_ANDROID_CLOSED '+str(error),flush=True)
