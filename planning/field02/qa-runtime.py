"""Owned emulator lifecycle observer, not product code. No flight or UI actions."""
from pathlib import Path
import os,sys,json,time,datetime,subprocess,shutil,socket,signal
R=Path(__file__).resolve().parents[2];E=R/'evidence/field02';W=R/'.local/field02';SDK=R/'.local/native86-android/sdk';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
attempt=sys.argv[1];assert attempt in ['01','02'];assert not(E/('android-launch'+attempt+'.json')).exists()
def put(name,d):
 with(E/name).open('x')as f:json.dump(d,f,indent=2);f.flush();os.fsync(f.fileno())
samples=[]
for n in range(31):
 free=shutil.disk_usage(R).free;samples.append({'hostMonoNs':str(time.monotonic_ns()),'freeBytes':free});assert free>=29*2**30,'29GIB_STABLE_ADMISSION'
 if n<30:time.sleep(1)
for port in [5582,5583]:
 with socket.socket()as s:s.bind(('127.0.0.1',port))
assert(SDK/'emulator/emulator').is_file();assert(W/'avd/aeris-field02.avd/config.ini').is_file()
env={**os.environ,'ANDROID_AVD_HOME':str(W/'avd'),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
a=subprocess.run([str(SDK/'emulator/emulator'),'-accel-check'],env=env,capture_output=True,text=True,timeout=20)
put('android-acceleration'+attempt+'.json',{'exit':a.returncode,'output':a.stdout+a.stderr});assert a.returncode==0 and 'Hypervisor.Framework'in a.stdout+a.stderr
cores='2' if attempt=='01' else '4'
cmd=[str(SDK/'emulator/emulator'),'-avd','aeris-field02','-port','5582','-no-window','-accel','on','-gpu','host','-no-snapshot','-no-boot-anim','-no-audio','-camera-back','none','-camera-front','none','-memory','2048','-cores',cores,'-no-metrics']
f=(E/('android-console'+attempt+'.txt')).open('x');p=subprocess.Popen(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT);caffeine=subprocess.Popen(['caffeinate','-i','-w',str(p.pid)]);stopped=False
def stop(*_):
 global stopped
 stopped=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
put('android-launch'+attempt+'.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':p.pid,'controllerPid':os.getpid(),'serial':'emulator-5582','avd':'aeris-field02','command':cmd,'samples':samples,'hardFloorBytes':20*2**30,'guardBytes':21*2**30,'hardDurationS':3600,'forecastAdditionalBytes':2**30,'source':'CACHED_API33_ARM64_OWN_AVD_NOT_XIAOMI'})
print('OWNED_ANDROID_LAUNCHED '+str(p.pid),flush=True);start=time.monotonic();minimum=shutil.disk_usage(R).free;error=None
try:
 while not stopped and not(E/('android-stop-request'+attempt+'.json')).exists():
  free=shutil.disk_usage(R).free;minimum=min(minimum,free);assert free>=21*2**30,'GUARD_PROTECT20GIB';assert p.poll()is None,'EMULATOR_EXIT';assert time.monotonic()-start<3600,'BOUNDED_RUNTIME';assert f.tell()<4*2**20,'CONSOLE_LOG_BOUND';time.sleep(1)
except BaseException as ex:error=str(ex)
finally:
 if p.poll()is None:
  subprocess.run([ADB,'-s','emulator-5582','emu','kill'],capture_output=True,timeout=15)
  try:p.wait(timeout=20)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
 f.close()
 try:caffeine.wait(timeout=5)
 except subprocess.TimeoutExpired:caffeine.terminate()
 put('android-closure'+attempt+'.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':p.pid,'exit':p.returncode,'error':error,'minFreeBytes':minimum,'finalFreeBytes':shutil.disk_usage(R).free,'explicitStop':stopped or(E/('android-stop-request'+attempt+'.json')).exists(),'notAndroidAcceptance':True})
 print('OWNED_ANDROID_CLOSED '+str(error),flush=True)
