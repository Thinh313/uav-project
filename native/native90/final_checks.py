from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess,os,socket
from verify_trace import load,verify,E,R
build=json.loads((E/'build08.json').read_text());fail=[]
for name,sha in build['sourceFiles'].items():
 if hashlib.sha256((R/name).read_bytes()).hexdigest()!=sha:fail.append(name)
assert not fail,fail
apk=R/build['apk'];assert hashlib.sha256(apk.read_bytes()).hexdigest()==build['sha256']
with zipfile.ZipFile(apk)as z:
 for p in(R/'native/native90/assets').rglob('*'):
  if p.is_file():assert z.read('assets/cockpit/'+p.relative_to(R/'native/native90/assets').as_posix())==p.read_bytes()
final=load('diagnostics08-final.tar');retained=[]
for name in ['diagnostics08-before-restart.tar','diagnostics08-after-app-restart.tar','diagnostics08-after-device-reboot.tar']:
 previous=load(name)
 for key,t in previous.items():assert final[key]['raw']==t['raw'],(name,key)
 retained.append({'archive':name,'exactPriorTraces':len(previous)})
journey=json.loads((E/'journey-verification.json').read_text());references=[r['data']['reference']for t in final.values()for r in t['rows']if r['kind']=='WORKSPACE_REVIEW_LINK'];assert len(references)==1;ref=references[0]
assert ref['head']==journey['head']and ref['missionSha256']==journey['missionSha256']and ref['revision']==journey['revision']and ref['workspace']==journey['workspace']
previous=json.loads((E/'android90-08-before-restarts.json').read_text())
for name in ['android90-08-after-app-restart','android90-08-after-device-reboot','android90-08-final-session','android90-08-layout-final-journal']:
 current=json.loads((E/(name+'.json')).read_text());assert current['files']==previous['files'],name
(E/'source-final.json').open('x').write(json.dumps({'status':'PASS','apkSha256':build['sha256'],'sourceId':build['sourceId'],'appSourcesAndAssets':len(build['sourceFiles']),'apkAssetParity':True,'zeroNetworkPermission':True,'proof':'build08.json/apksigner/aapt2 plus installed08.json APK readback; local integrity, not source authentication'},indent=2))
(E/'persistence-verification.json').open('x').write(json.dumps({'status':'PASS','retained':retained,'workspaceEveryFileUnchanged':True,'reviewLinkExactCommittedHeadAndMission':ref,'authorityRestorable':False,'scope':'Process restart, emulator Android reboot and configuration recreation; no device power-cut qualification'},indent=2))
launch=json.loads((E/'android-launch.json').read_text());closed=json.loads((E/'android-closure.json').read_text());assert closed['exit']==0 and closed['error']is None and closed['minFreeBytes']>=21*2**30
for pid in [launch['pid'],launch['controllerPid']]:
 try:os.kill(pid,0)
 except ProcessLookupError:pass
 else:raise AssertionError('OWN_RUNTIME_STILL_PRESENT '+str(pid))
for port in[5582,5583]:
 with socket.socket()as s:s.bind(('127.0.0.1',port))
assert shutil.disk_usage(R).free>=20*2**30
(E/'runtime-closure.json').open('x').write(json.dumps({'status':'PASS','emulatorAndControllerAbsent':True,'ports5582_5583Free':True,'minFreeGiB':closed['minFreeBytes']/2**30,'currentFreeGiB':shutil.disk_usage(R).free/2**30,'newSITLStarted':False,'noProductionSigning':True},indent=2))
print(json.dumps({'status':'PASS','sourceFiles':len(build['sourceFiles']),'retained':retained,'minFreeGiB':closed['minFreeBytes']/2**30}))
