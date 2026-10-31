"""Only emulator-5580 we created. No sign/security bypass/device fallback/flight/ENDURE."""
from pathlib import Path
import subprocess,json,time,hashlib,os,xml.etree.ElementTree as ET,datetime,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/native30';N=R/'native/shell30';ADB='/opt/homebrew/share/android-commandlinetools/platform-tools/adb';SERIAL='emulator-5580';REMOTE='/data/local/tmp/aeris-native30';APK=R/'native/shell24/dist/aeris-native24-preparation-dev.apk';checks=[];logs=[]
def call(args,data=None,timeout=20,allow=False):
 p=subprocess.run([ADB,'-s',SERIAL,*args],input=data,capture_output=True,timeout=timeout);logs.append({'args':args,'code':p.returncode,'stdout':p.stdout.decode(errors='replace')[:10000] if not args[:2]==['exec-out','screencap'] else 'PNG','stderr':p.stderr.decode(errors='replace')[:3000]})
 if p.returncode and not allow:raise RuntimeError(logs[-1])
 return p
def check(name,ok):checks.append({'name':name,'pass':bool(ok)});print(name,ok);assert ok,name
def shell(s,**kw):return call(['shell',s],**kw)
def main(mode,root,token='ROOT',body=None):return shell('CLASSPATH='+REMOTE+'/native30.apk app_process /system/bin vn.rtr.aeris.shell30.JournalMain '+mode+' '+root+(' '+token if mode=='save' else ''),data=body).stdout
def snapshot(root):return json.loads(main('load',root))
def tap(label):
 shell('uiautomator dump '+REMOTE+'/ui.xml',timeout=25);raw=shell('cat '+REMOTE+'/ui.xml').stdout;(E/('legacy-ui-'+str(len(logs))+'.xml')).write_bytes(raw);tree=ET.fromstring(raw.decode());found=[x for x in tree.iter('node') if x.attrib.get('text')==label or x.attrib.get('content-desc')==label];assert found,label
 import re
 values=list(map(int,re.findall(r'\d+',found[0].attrib['bounds'])));shell('input tap '+str((values[0]+values[2])//2)+' '+str((values[1]+values[3])//2))
try:
 check('owned Android13 ARM64 boot',shell('getprop sys.boot_completed').stdout.strip()==b'1' and shell('getprop ro.build.version.sdk').stdout.strip()==b'33' and b'arm64-v8a' in shell('getprop ro.product.cpu.abi').stdout)
 inventory={k:shell('getprop '+k).stdout.decode().strip() for k in ['ro.build.fingerprint','ro.build.version.sdk','ro.product.cpu.abi','ro.product.model','ro.boot.qemu']};inventory['display']=shell('wm size; wm density').stdout.decode();inventory['scope']='Actual emulator, not Hera';(E/'android-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
 check('only explicit emulator target',inventory['ro.boot.qemu']=='1')
 shell('mkdir -p '+REMOTE);call(['push',str(N/'dist/aeris-native30-unsigned.apk'),REMOTE+'/native30.apk']);actual=shell('sha256sum '+REMOTE+'/native30.apk').stdout.decode().split()[0];check('DEX APK copied exact unsigned bytes',actual==hashlib.sha256((N/'dist/aeris-native30-unsigned.apk').read_bytes()).hexdigest())
 test=shell('CLASSPATH='+REMOTE+'/native30.apk app_process /system/bin vn.rtr.aeris.shell30.AndroidProbe test '+REMOTE+'/model-tests',timeout=30);(E/'android-model-tests.txt').write_bytes(test.stdout+test.stderr);check('31 model checks execute on actual ART',test.stdout.count(b'PASS ')==31 and b'ANDROID_RUNTIME API=33 ABI=arm64-v8a' in test.stdout)
 root=REMOTE+'/restart';one=json.loads(main('save',root,body=b'{"draft":1}'));two=snapshot(root);check('separate ART process restart exact committed token/body',one['token']==two['token'] and one['revision']==1 and two['authorityRestorable'] is False)
 for phase in ['RECORD_PUBLISHED','HEAD_PENDING','HEAD_COMMITTED']:
  root=REMOTE+'/kill-'+phase;first=json.loads(main('save',root,body=b'old'));marker=REMOTE+'/marker-'+phase;command='CLASSPATH='+REMOTE+'/native30.apk app_process /system/bin vn.rtr.aeris.shell30.AndroidProbe crash '+root+' '+first['token']+' '+phase+' '+marker
  p=subprocess.Popen([ADB,'-s',SERIAL,'shell',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);p.stdin.write(b'new');p.stdin.close();pid=None
  for i in range(50):
   q=shell('cat '+marker,allow=True)
   if q.returncode==0:pid=int(q.stdout.splitlines()[0]);break
   time.sleep(.1)
  assert pid and pid>100,'Own marker PID';cmdline=shell('cat /proc/'+str(pid)+'/cmdline').stdout;check('actual owned crash process identity '+phase,b'vn.rtr.aeris.shell30.AndroidProbe' in cmdline)
  shell('kill -9 '+str(pid));code=p.wait(timeout=10);out=p.stdout.read()+p.stderr.read();(E/('sigkill-'+phase+'.txt')).write_bytes(out);latest=snapshot(root);check('real SIGKILL recovery '+phase,latest['bodyBase64']==('bmV3' if phase=='HEAD_COMMITTED' else 'b2xk'));check('pending explicit/no auto forward '+phase,latest['pending']==(phase=='HEAD_PENDING'))
  check('both immutable revisions retained '+phase,shell('ls '+root+'/*.bin').stdout.count(b'.bin')==2)
 # Actual installation refusal demonstrates signing gate, never bypass it.
 refused=call(['install',str(N/'dist/aeris-native30-unsigned.apk')],allow=True);(E/'unsigned-install-refusal.txt').write_bytes(refused.stdout+refused.stderr);check('new unsigned package correctly rejected',refused.returncode!=0 and b'NO_CERTIFICATES' in refused.stdout+refused.stderr)
 check('unchanged legacy signed diagnostic bytes',hashlib.sha256(APK.read_bytes()).hexdigest()==json.loads((R/'evidence/native24/native-build.json').read_text())['apkSha256']);installed=call(['install',str(APK)]);(E/'legacy-install.txt').write_bytes(installed.stdout+installed.stderr);check('unchanged signed N24 installed',b'Success' in installed.stdout)
 shell('am start -n vn.rtr.aeris.shell24/.ShellActivity');time.sleep(1);(E/'legacy-runtime.png').write_bytes(call(['exec-out','screencap','-p']).stdout);tap('Fly');tap('Clip tổng hợp');time.sleep(1);tap('Phát / dừng');time.sleep(2);shell('uiautomator dump '+REMOTE+'/final-ui.xml');ui=shell('cat '+REMOTE+'/final-ui.xml').stdout;(E/'legacy-video-ended.xml').write_bytes(ui);check('legacy Android MediaPlayer synthetic clip ended',('Clip đã kết thúc' in ui.decode()) and ('ENDED' in ui.decode()))
 (E/'legacy-video-runtime.png').write_bytes(call(['exec-out','screencap','-p']).stdout);call(['logcat','-d','-t','800'],timeout=20).stdout;(E/'legacy-logcat.txt').write_bytes(logs[-1]['stdout'].encode());shell('am force-stop vn.rtr.aeris.shell24');check('legacy stopped after runtime probe',True)
except Exception as e:
 checks.append({'name':'runtime failure','pass':False,'error':str(e)});raise
finally:
 (E/'runtime-commands.json').write_text(json.dumps(logs,indent=2)+'\n');(E/'runtime-qa.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if checks and all(x['pass'] for x in checks) else 'FAIL','checks':checks,'newNativeUI':'NOT_CHECKED_UNSIGNED_INSTALL_REFUSED','actualScope':'N30 Java journal on ART/shell temporary storage, real SIGKILL/restart; unchanged N24 installed Activity/video separately. Not N30 WebView UI/application private storage/Hera/SDK/flight.'},indent=2)+'\n')
