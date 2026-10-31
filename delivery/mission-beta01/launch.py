"""One workspace-bound entry point; no automatic flight, retry, or evidence cleanup."""
from pathlib import Path
import argparse, subprocess, sys, time, json, signal, os
R=Path(__file__).resolve().parents[2]
C=R/'pilot/missionbeta01/companion.py'
def main():
 p=argparse.ArgumentParser();p.add_argument('action',nargs='?',choices=['start','doctor','status','stop'],default='start');p.add_argument('--mode',choices=['mock','sitl'],default='sitl');p.add_argument('--describe',action='store_true');a=p.parse_args()
 argv=[sys.executable,'-B',str(C),a.action,'--mode',a.mode,'--emulator']
 if a.describe:print(json.dumps({'argv':argv,'root':str(R),'autoFlight':False,'autoRetry':False,'physicalDevices':False}));return 0
 if a.action!='start':return subprocess.call(argv,cwd=R)
 proc=subprocess.Popen(argv,cwd=R);interrupted=False
 def stop(*_):
  nonlocal interrupted
  interrupted=True
  if proc.poll()is None:proc.send_signal(signal.SIGTERM)
 signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
 try:
  deadline=time.monotonic()+105
  while proc.poll()is None and not interrupted:
   f=R/'.local/missionbeta01/active/owner.json'
   if f.exists():
    q=json.loads(f.read_text())
    if q['pid']==proc.pid and (Path(q['run'])/'launch.json').exists():
     adb=Path('/opt/homebrew/share/android-commandlinetools/platform-tools/adb');readyDeadline=time.monotonic()+65
     while True:
      if proc.poll()is not None or interrupted:return proc.wait()
      devices=subprocess.run([str(adb),'devices'],capture_output=True,text=True,timeout=10)
      if 'emulator-5582\tdevice' in devices.stdout:
       boot=subprocess.run([str(adb),'-s','emulator-5582','shell','getprop','sys.boot_completed'],capture_output=True,text=True,timeout=10)
       if boot.returncode==0 and boot.stdout.strip()=='1':break
      if time.monotonic()>readyDeadline:raise RuntimeError('OWNED_EMULATOR_BOOT_DEADLINE')
      time.sleep(.5)
     rc=subprocess.call([sys.executable,'-B',str(C),'android'],cwd=R)
     if rc:stop();return rc
     print('Android ready. Open http://127.0.0.1:8895/publisher and explicitly start the synthetic source. No flight command was sent.',flush=True)
     break
   if time.monotonic()>deadline:raise RuntimeError('BOUNDED_LAUNCH_DEADLINE')
   time.sleep(.5)
  return proc.wait()
 finally:
  if proc.poll()is None:stop();proc.wait(timeout=35)
if __name__=='__main__':sys.exit(main())
