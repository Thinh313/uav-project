from pathlib import Path
import os,subprocess,json,time,shutil,socket,hashlib,sys,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/cockpit82-emulator04';W=R/'.local/cockpit82-android';SDK=W/'sdk';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';SERIAL='emulator-5582';NAME='aeris-cockpit82';AVD=W/'avd'
attempt=sys.argv[1];assert attempt in ['04','05','06']
assert shutil.disk_usage(R).free>=30*2**30 and not(E/('launch'+attempt+'.json')).exists()
for port in [5582,5583]:
 with socket.socket()as s:s.bind(('127.0.0.1',port))
assert hashlib.sha256((SDK/'emulator/emulator').read_bytes()).hexdigest()=='5e2249e94368759aabd8fa942d2961cfef07b980a44639a2ec9b7ced3fbe2281'
env={**os.environ,'ANDROID_AVD_HOME':str(AVD),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
acc=subprocess.run([str(SDK/'emulator/emulator'),'-accel-check'],env=env,capture_output=True,text=True,timeout=15)
(E/('accel-check'+attempt+'.txt')).open('x').write(acc.stdout+acc.stderr);assert acc.returncode==0 and 'Hypervisor.Framework' in acc.stdout+acc.stderr,'HARDWARE_ACCELERATION_REQUIRED'
cfg=(AVD/(NAME+'.avd/config.ini')).read_text().splitlines();d=dict(line.split('=',1)for line in cfg if '='in line);d.update({'hw.cpu.ncore':'2','hw.ramSize':'2048','hw.gpu.enabled':'yes','hw.gpu.mode':'host','fastboot.forceColdBoot':'yes'});config='\n'.join(k+'='+v for k,v in d.items())+'\n';(AVD/(NAME+'.avd/config.ini')).write_text(config);(E/('avd-config'+attempt+'.ini')).open('x').write(config)
cmd=[str(SDK/'emulator/emulator'),'-avd',NAME,'-port','5582','-no-snapshot','-no-boot-anim','-no-window','-accel','on','-gpu','host','-no-audio','-camera-back','none','-camera-front','none','-memory','2048','-cores','2']
if attempt=='05':cmd+=['-feature','-Vulkan']
log=(E/('emulator-console'+attempt+'.txt')).open('x');p=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT);samples=[];failure=None;started=time.monotonic();killMethods=[]
r={'at':datetime.datetime.now().astimezone().isoformat(),'controllerPid':os.getpid(),'pid':p.pid,'serial':SERIAL,'avd':NAME,'attempt':attempt,'command':cmd,'freeBytes':shutil.disk_usage(R).free,'scope':'Existing AVD no wipe; engineering mock only'};(E/('launch'+attempt+'.json')).open('x').write(json.dumps(r,indent=2)+'\n');(E/'current-runtime.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
try:
 while not(E/('stop-request'+attempt+'.json')).exists():
  free=shutil.disk_usage(R).free;samples.append(free)
  if free<21*2**30:raise RuntimeError('DISK_HEADROOM_STOP')
  if p.poll()is not None:raise RuntimeError('EMULATOR_EXIT_'+str(p.returncode))
  if time.monotonic()-started>2700:raise RuntimeError('BOUNDED_RUNTIME_DEADLINE')
  time.sleep(1)
except Exception as ex:failure=str(ex)
finally:
 if p.poll()is None:
  try:subprocess.run([ADB,'-s',SERIAL,'emu','kill'],capture_output=True,timeout=10);killMethods.append('emu kill')
  except subprocess.TimeoutExpired:killMethods.append('emu kill timeout')
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:
   p.terminate();killMethods.append('SIGTERM')
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10);killMethods.append('SIGKILL')
 log.close();receipt={'exit':p.returncode,'failure':failure,'explicitStop':(E/('stop-request'+attempt+'.json')).exists(),'minimumFreeBytes':min(samples)if samples else None,'finalFreeBytes':shutil.disk_usage(R).free,'killMethods':killMethods,'noWipe':True};(E/('runtime-closure'+attempt+'.json')).open('x').write(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
