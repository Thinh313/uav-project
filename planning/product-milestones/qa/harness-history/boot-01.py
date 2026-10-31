from android_qa import *
l=json.loads((E/'android-launch01.json').read_text());os.kill(l['pid'],0);end=time.monotonic()+90
while time.monotonic()<end:
 try:b=adb('shell','getprop','sys.boot_completed',allow_failure=True,timeout=3)
 except subprocess.TimeoutExpired:b=b''
 if b.strip()==b'1':break
 time.sleep(1)
else:raise AssertionError('OWNED_BOOT_DEADLINE')
owned();adb('root');time.sleep(.6);owned();samples=[]
for i in range(5):
 t=time.monotonic();assert adb('shell','getprop','ro.boot.qemu',timeout=10).strip()==b'1';samples.append((time.monotonic()-t)*1000);time.sleep(.15)
r={'status':'PASS'if max(samples)<=1500 else'BLOCKED','smallADBReadMs':samples,'maxAdmittedMs':1500,'scope':'Engineering host/emulator admission, not product latency benchmark'};(E/'android-readiness01.json').open('x').write(json.dumps(r,indent=2));print(json.dumps(r));assert r['status']=='PASS','HOST_EMULATOR_NOT_RESPONSIVE_NO_AP_LAUNCH'
