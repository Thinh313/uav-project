"""Verify host preparation and preserve failure truth; writes only new N30 metadata."""
from pathlib import Path
import json,hashlib,re,subprocess,ast,zipfile,datetime
R=Path(__file__).resolve().parents[2];N=R/'native/shell30';E=R/'evidence/native30';checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def check(n,v,d=None):checks.append({'name':n,'pass':bool(v),'detail':d})
def mismatch(files):return[p for p,s in files.items()if not(R/p).is_file()or h(R/p)!=s]
b=load(E/'preservation-before.json');after={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sets':{}}
for name,v in b['sets'].items():
 files=load(R/v['inventory'])['files'];bad=mismatch(files);after['sets'][name]={'files':len(files),'mismatches':bad};check(name+' old inventory exact',not bad,after['sets'][name])
for name in ['stable','oldTrust']:
 bad=mismatch(b[name]);after[name]={'files':len(b[name]),'mismatches':bad};check(name+' preserved bytes',not bad,after[name])
candidate=load(R/'evidence/endure27/candidate.json');f=load(R/'evidence/endure20/freeze.json')['files']
for name,base in [('source140',R),('slot140',Path(candidate['slot']))]:
 bad=[x['path']for x in f if not(base/x['path']).is_file()or h(base/x['path'])!=x['sha256']];after[name]={'files':len(f),'mismatches':bad};check(name+' unchanged',len(f)==140 and not bad)
(E/'preservation-after.json').write_text(json.dumps(after,indent=2)+'\n')
build=load(E/'native-build.json');apk=R/build['apk'];check('final build source hashes exact',not mismatch(build['sourceHashes']));check('final APK/JAR exact unsigned',h(apk)==build['apkSha256']and apk.stat().st_size==build['apkBytes']and h(N/'dist/journal-host.jar')==build['hostJarSha256']and build['signing']=='NONE'and build['keyReads']==0 and build['nativeUI']=='NOT_CHECKED')
for core,s in build['coreHashes'].items():check(core+' same vendor SHA',h(R/core)==s and h(N/'vendor'/Path(core).name)==s)
with zipfile.ZipFile(apk)as z:
 check('all packaged editor assets exact',all(z.read('assets/editor/'+str(p.relative_to(N)))==p.read_bytes()for p in [N/'index.html',N/'shell.css',N/'shell.mjs',N/'editor.mjs',N/'pins.mjs',*list((N/'vendor').glob('*.mjs'))]))
 check('DEX and no JAR signature','classes.dex'in z.namelist()and not any(n.startswith('META-INF/')for n in z.namelist()))
check('zero permissions and signature verify refusal','uses-permission:'not in(E/'apk-permissions.txt').read_text()and 'DOES NOT VERIFY'in(E/'unsigned-verification.txt').read_text())
host=(E/f"host-tests{build['attempt']:02d}.txt").read_text();check('31 Java host journal',host.count('PASS ')==31 and 'TOTAL 31 PASS'in host)
test=(E/'editor-tests03.txt').read_text();check('46 editor checks no fails/skips',all(re.search(r'ℹ '+k+' '+str(v)+r'\b',test)for k,v in [('tests',46),('pass',46),('fail',0),('skipped',0)]))
q=load(E/'browser3.json');check('30 current shared editor/browser/Java checks',q['status']=='PASS'and len(q['checks'])==30 and all(x['pass']for x in q['checks']))
crash=load(E/'host-crash.json');check('12 actual owned host JVM SIGKILL/restart',crash['status']=='PASS'and len(crash['checks'])==12 and all(x['pass']for x in crash['checks'])and len(crash['runs'])==3 and all(x['exit']==-9 for x in crash['runs']))
for name,n in [('native29-regression.txt',84),('native24-regression.txt',38)]:check(name+' readonly regressions',sum(x.startswith('PASS ')for x in(E/name).read_text().splitlines())==n and 'TOTAL '+str(n)in(E/name).read_text())
runtime=load(E/'runtime-qa.json');commands=load(E/'runtime-commands.json');android_failure=next((x for x in commands if 'ANDROID_RUNTIME API=33 ABI=arm64-v8a'in x.get('stdout','')),None);log=(E/'android-logcat.txt').read_text();check('Android failure retained never promoted',runtime['status']=='FAIL'and android_failure is not None and android_failure['code']==137 and 'SecurityException: getFileStore'in log and 'Sending signal. PID: 2223 SIG: 9'in log)
check('reserve API fix present without Android PASS','root.toFile().getUsableSpace()'in(N/'src/vn/rtr/aeris/shell30/DraftStore.java').read_text()and 'Files.getFileStore(root)'not in(N/'src/vn/rtr/aeris/shell30/DraftStore.java').read_text()and load(E/'runtime-diagnosis.json')['status']=='ANDROID_REPRODUCED_FAILURE_FIXED_NOT_RETESTED_ON_ANDROID')
check('build/emulator/test scratch absent',all(not(N/p).exists()for p in ['.runtime','.build','.regress','.qa-crash','.qa-drafts','.qa-drafts-reviews'])and not Path('/private/tmp/codex-tmp-native30-sdk-list-20261013.txt').exists())
sources=load(E/'sources.json')['sources'];check('four official sources captured',len(sources)==4 and all(x['status']=='CAPTURED'and h(R/x['path'])==x['sha256']for x in sources))
syntax=[]
for p in N.rglob('*.mjs'):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);syntax.append({'path':str(p.relative_to(R)),'code':r.returncode,'output':r.stdout+r.stderr})
for p in N.glob('*.py'):ast.parse(p.read_text())
check('new JS/Python syntax',all(x['code']==0 for x in syntax));(E/'syntax.json').write_text(json.dumps(syntax,indent=2)+'\n')
ok=all(x['pass']for x in checks);result={'at':after['at'],'status':'PARTIAL_HOST_EDITOR_PERSISTENCE_VERIFIED_ANDROID_RUNTIME_OPEN'if ok else'NOT_READY','hostPreparationPass':ok,'requirements':{'implemented':7,'verifiedHostPreparation':6 if ok else 0,'total':7,'open':['N30-05 actual Android persistence/real SIGKILL after fix; new Activity install/runtime'],'nativePortionsNOT_CHECKED':['N30-04 Activity/bridge/SAF runtime','N30-06 native dp/window/keyboard/runtime']},'functionalChecks':{'javaJournal':31,'editor':46,'browser':30,'hostRealSIGKILL':12,'N29Regression':84,'N24Regression':38,'totalHost':241},'android':{'boot':'OBSERVED_API33_ARM64','DEX':'OBSERVED_ART_SHELL','journal':'FAILED_GETFILESTORE_FIXED_NOT_RETESTED','newUI':'NOT_CHECKED_UNSIGNED','legacyN24UI':'NOT_CHECKED_PROBE_NOT_REACHED','hardware':'NOT_CHECKED'},'metadataChecks':checks,'apkSha256':build['apkSha256'],'limits':['Host checks not Android/hardware acceptance','No new signatures/key reads/PackageManager bypass/SDK/Hera/transport/Fly/ENDURE','Same runtime requires actual sufficient free space plus20GiB reserve','No physical power-loss/durable every-keystroke/operational media/flight claims'],'review':'Single-agent sequential verification, not independent audit'}
(E/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
files=[p for p in N.rglob('*')if p.is_file()]+[R/'delivery/TIP-NATIVE30.md',R/'delivery/COMPLETION-NATIVE30.md',R/'docs/ADR-039-OFFLINE-NATIVE-EDITOR-DRAFT-JOURNAL.md'];(E/'module-fingerprints.json').write_text(json.dumps({'at':after['at'],'files':{str(p.relative_to(R)):h(p)for p in sorted(files)},'scope':'New isolated module metadata only, not a signature or frozen baseline replacement'},indent=2)+'\n');(E/'evidence-fingerprints.json').write_text(json.dumps({'at':after['at'],'files':{str(p.relative_to(R)):h(p)for p in sorted(E.rglob('*'))if p.is_file()and p.name!='evidence-fingerprints.json'}},indent=2)+'\n')
print(result['status'],len(checks),'metadata checks',sum(not x['pass']for x in checks),'failures')
if not ok:print(json.dumps([x for x in checks if not x['pass']],indent=2));raise SystemExit(1)
