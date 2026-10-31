from pathlib import Path
import os,subprocess,json,time,shutil,socket,hashlib
R=Path(__file__).resolve().parents[2];N=R/'native/runtime79';W=N/'.runtime';E=R/'evidence/native79';ADB=Path('/opt/homebrew/share/android-commandlinetools/platform-tools/adb');SERIAL='emulator-5582';AVD=W/'avd';NAME='aeris-native79';STOP=20.75*2**30
ATTEMPT='05'; SDK=W/'sdk'
assert shutil.disk_usage(R).free>=30*2**30,'AVD_PEAK_ADMISSION'
assert not(E/('launch'+ATTEMPT+'.json')).exists(),'NO_RELAUNCH'
for port in [5582,5583]:
 with socket.socket()as s:s.bind(('127.0.0.1',port))
AVD.mkdir(exist_ok=True);d=AVD/(NAME+'.avd');d.mkdir(exist_ok=True);(W/'android-user').mkdir(exist_ok=True)
cfg='''avd.ini.encoding=UTF-8
avd.name=aeris-native79
abi.type=arm64-v8a
hw.cpu.arch=arm64
hw.cpu.ncore=2
hw.ramSize=1536
hw.lcd.width=1280
hw.lcd.height=800
hw.lcd.density=160
hw.gpu.enabled=yes
hw.gpu.mode=swiftshader_indirect
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
(d/'config.ini').write_text(cfg);(AVD/(NAME+'.ini')).write_text('avd.ini.encoding=UTF-8\npath='+str(d)+'\ntarget=android-33\n');(E/('avd-config'+ATTEMPT+'.ini')).write_text(cfg)
env={**os.environ,'ANDROID_AVD_HOME':str(AVD),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
cmd=[str(SDK/'emulator/emulator'),'-avd',NAME,'-port','5582','-no-snapshot','-no-boot-anim','-gpu','swiftshader_indirect','-no-audio','-camera-back','none','-camera-front','none','-memory','1536','-cores','2']
log=(E/('emulator-console'+ATTEMPT+'.txt')).open('x');p=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT);observations=[];failure=None;started=time.monotonic()
with(E/('launch'+ATTEMPT+'.json')).open('x')as f:json.dump({'pid':p.pid,'serial':SERIAL,'command':cmd,'freeBytes':shutil.disk_usage(R).free,'scope':'OWNED_AOSP_API33_ARM64_ONLY_NO_HERA','emulatorSha256':hashlib.sha256((SDK/'emulator/emulator').read_bytes()).hexdigest()},f,indent=2)
print(json.dumps({'controllerPid':os.getpid(),'emulatorPid':p.pid,'serial':SERIAL}),flush=True)
try:
 while not(E/('stop-request'+ATTEMPT+'.json')).exists():
  free=shutil.disk_usage(R).free;observations.append(free)
  if free<STOP:raise RuntimeError('RESOURCE_HEADROOM_STOP')
  if p.poll()is not None:raise RuntimeError('EMULATOR_EXIT_'+str(p.returncode))
  if time.monotonic()-started>1800:raise RuntimeError('BOUNDED_RUNTIME_DEADLINE')
  time.sleep(1)
except Exception as ex:failure=str(ex)
finally:
 if p.poll()is None:
  subprocess.run([str(ADB),'-s',SERIAL,'emu','kill'],capture_output=True,timeout=15)
  try:p.wait(timeout=20)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
 log.close()
 with(E/('runtime-closure'+ATTEMPT+'.json')).open('x')as f:json.dump({'exitCode':p.returncode,'failure':failure,'explicitStop':(E/('stop-request'+ATTEMPT+'.json')).exists(),'minimumObservedFreeBytes':min(observations)if observations else None,'freeBytes':shutil.disk_usage(R).free,'appDataNotWiped':True},f,indent=2)
 print(json.dumps({'closed':True,'failure':failure}),flush=True)
