from pathlib import Path
import os,subprocess,json,time,shutil,socket,hashlib
R=Path(__file__).resolve().parents[2];E=R/'evidence/cockpit82';W=R/'.local/cockpit82-android';SDK=W/'sdk';A='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';S='emulator-5582';AVD=W/'avd';NAME='aeris-cockpit82'
assert shutil.disk_usage(R).free>=30*2**30 and not(E/'launch03.json').exists(),'AVD_ADMISSION_OR_RELAUNCH'
for port in [5582,5583]:
 with socket.socket()as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
AVD.mkdir(exist_ok=True);d=AVD/(NAME+'.avd');d.mkdir(exist_ok=True);(W/'android-user').mkdir(exist_ok=True)
cfg='''avd.ini.encoding=UTF-8
avd.name=aeris-cockpit82
abi.type=arm64-v8a
hw.cpu.arch=arm64
hw.cpu.ncore=4
hw.ramSize=2048
hw.lcd.width=1280
hw.lcd.height=800
hw.lcd.density=160
hw.gpu.enabled=yes
hw.gpu.mode=swangle
hw.keyboard=yes
hw.camera.back=none
hw.camera.front=none
hw.audioInput=no
hw.sdCard=no
disk.dataPartition.size=6442450944
disk.cachePartition.size=32M
fastboot.forceColdBoot=yes
showDeviceFrame=no
image.sysdir.1='''+str(SDK/'system-images/android-33/default/arm64-v8a')+'\n'
(d/'config.ini').write_text(cfg);(AVD/(NAME+'.ini')).write_text('avd.ini.encoding=UTF-8\npath='+str(d)+'\ntarget=android-33\n');(E/'avd-config03.ini').write_text(cfg)
env={**os.environ,'ANDROID_AVD_HOME':str(AVD),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
cmd=[str(SDK/'emulator/emulator'),'-avd',NAME,'-port','5582','-no-snapshot','-no-boot-anim','-gpu','swangle','-no-audio','-camera-back','none','-camera-front','none','-memory','2048','-cores','4']
log=(E/'emulator-console03.txt').open('x');p=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT);samples=[];failure=None;started=time.monotonic()
(E/'launch03.json').write_text(json.dumps({'controllerPid':os.getpid(),'pid':p.pid,'serial':S,'command':cmd,'freeBytes':shutil.disk_usage(R).free,'emulatorSha256':hashlib.sha256((SDK/'emulator/emulator').read_bytes()).hexdigest()},indent=2)+'\n');print(json.dumps({'controllerPid':os.getpid(),'emulatorPid':p.pid}),flush=True)
try:
 while not(E/'stop-request03.json').exists():
  free=shutil.disk_usage(R).free;samples.append(free)
  if free<21*2**30:raise RuntimeError('DISK_21GIB_HEADROOM_STOP')
  if p.poll()is not None:raise RuntimeError('EMULATOR_EXIT_'+str(p.returncode))
  if time.monotonic()-started>2700:raise RuntimeError('RUNTIME_DEADLINE')
  time.sleep(1)
except Exception as ex:failure=str(ex)
finally:
 if p.poll()is None:
  try:subprocess.run([A,'-s',S,'emu','kill'],capture_output=True,timeout=15)
  except subprocess.TimeoutExpired:p.terminate()
  try:p.wait(timeout=20)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
 log.close();(E/'runtime-closure03.json').write_text(json.dumps({'exit':p.returncode,'failure':failure,'explicitStop':(E/'stop-request03.json').exists(),'minimumFreeBytes':min(samples)if samples else None,'finalFreeBytes':shutil.disk_usage(R).free,'noWipe':True},indent=2)+'\n');print(json.dumps({'closed':True,'failure':failure}),flush=True)
