from pathlib import Path
import os,json,subprocess,socket,shutil,time,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/native93';W=R/'.local/native90-android';SDK=R/'.local/native86-android/sdk';AVD=W/'avd';NAME='aeris-native90';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb'
assert shutil.disk_usage(R).free>=26*2**30
for port in[5582,5583]:
 with socket.socket()as s:s.bind(('127.0.0.1',port))
d=AVD/(NAME+'.avd');assert d.is_dir()and(AVD/(NAME+'.ini')).is_file();env={**os.environ,'ANDROID_AVD_HOME':str(AVD),'ANDROID_USER_HOME':str(W/'android-user'),'ANDROID_SDK_ROOT':str(SDK),'ANDROID_HOME':str(SDK)}
a=subprocess.run([str(SDK/'emulator/emulator'),'-accel-check'],env=env,capture_output=True,text=True);(E/'acceleration.txt').open('x').write(a.stdout+a.stderr);assert a.returncode==0 and 'Hypervisor.Framework'in a.stdout+a.stderr
cmd=[str(SDK/'emulator/emulator'),'-avd',NAME,'-port','5582','-no-window','-accel','on','-gpu','host','-no-snapshot','-no-boot-anim','-no-audio','-camera-back','none','-camera-front','none','-memory','2048','-cores','2'];f=(E/'android-console.txt').open('x');p=subprocess.Popen(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT);caffeine=subprocess.Popen(['caffeinate','-i','-w',str(p.pid)]);receipt={'reusedAvd':True,'appPackage':'vn.rtr.aeris.native93','forecastAdditionalBytes':1073741824,'pid':p.pid,'controllerPid':os.getpid(),'avd':NAME,'serial':'emulator-5582','command':cmd,'at':datetime.datetime.now().astimezone().isoformat()};(E/'android-launch.json').open('x').write(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True);start=time.monotonic();samples=[];error=None
try:
 while not(E/'android-stop-request.json').exists():
  free=shutil.disk_usage(R).free;samples.append(free);assert free>=21*2**30,'HEADROOM_STOP';assert p.poll()is None,'EMULATOR_EXIT';assert time.monotonic()-start<3600,'RUNTIME_BOUND';time.sleep(1)
except BaseException as ex:error=str(ex)
finally:
 if p.poll()is None:
  subprocess.run([ADB,'-s','emulator-5582','emu','kill'],capture_output=True,timeout=15)
  try:p.wait(timeout=20)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
 f.close();caffeine.wait(timeout=5);(E/'android-closure.json').open('x').write(json.dumps({'exit':p.returncode,'error':error,'minFreeBytes':min(samples),'finalFreeBytes':shutil.disk_usage(R).free}));print('CLOSED '+str(error),flush=True)
