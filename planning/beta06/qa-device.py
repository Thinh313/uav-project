# BETA06 isolated QA helper; previous helpers remain immutable.
"""Contractor readonly device/source inventory. Never installs, starts or grants control."""
from pathlib import Path
import importlib.util,sys,json,hashlib
spec=importlib.util.spec_from_file_location('qa_android04',Path(__file__).with_name('qa-android.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
def inventory(attempt,name):
    q.owned(attempt);assert name.replace('-','').isalnum();props={k:q.adb('shell','getprop',k).decode().strip()for k in['ro.build.version.sdk','ro.build.version.release','ro.product.cpu.abi','ro.boot.qemu']};assert props['ro.build.version.sdk']=='33'and props['ro.boot.qemu']=='1';pm=q.adb('shell','pm','path',q.P).decode().strip().splitlines();assert len(pm)==1 and pm[0].startswith('package:');apk=q.adb('exec-out','cat',pm[0][8:]);expected='df49885f45fd94fb05226712838769ccca48ecb4185b8d7a0c71a68bba03753d';assert hashlib.sha256(apk).hexdigest()==expected,'UNCHANGED_APK_REQUIRED';report={'props':props,'apkSha256':expected,'apkBytes':len(apk),'wmSize':q.adb('shell','wm','size').decode(),'wmDensity':q.adb('shell','wm','density').decode(),'webviewProvider':q.adb('shell','dumpsys','webviewupdate').decode()[-8192:],'topology':'ANDROID_RECEIVER_ONLY_HOST_PRODUCER','noInstallOrSignature':True};(q.E/(name+'.json')).open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':assert len(sys.argv)==3;inventory(*sys.argv[1:])
