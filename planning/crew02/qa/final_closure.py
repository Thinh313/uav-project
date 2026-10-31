from pathlib import Path
import json,subprocess,hashlib,shutil,datetime
R=Path('.');E=R/'evidence/crew02-runtime';closures=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in sorted((E/'runs').glob('*/launch.json')):
 c=p.parent/'closure.json';assert c.exists();q=json.loads(c.read_text());assert q['stopped']and q['error']is None and q['observerError']is None;closures.append({'run':p.parent.name,'closureSHA256':sha(c),'error':q['error'],'minFreeBytes':q['minFreeBytes']})
assert len(closures)==4;b=[]
for p in sorted(E.glob('companion*/launch.json')):
 c=p.parent/'closure.json';assert c.exists();q=json.loads(c.read_text());assert q['error']is None;cmd=subprocess.run(['ps','-p',str(q['pid']),'-o','args='],capture_output=True,text=True).stdout;assert 'native/crew02/host/companion.mjs'not in cmd;b.append({'tag':p.parent.name,'pid':q['pid'],'closed':True,'closureSHA256':sha(c)})
a=[]
for p in sorted(E.glob('android-launch*.json')):
 c=E/p.name.replace('launch','closure');assert c.exists();q=json.loads(c.read_text());l=json.loads(p.read_text());assert q['error']is None;cmd=subprocess.run(['ps','-p',str(l['pid']),'-o','args='],capture_output=True,text=True).stdout;assert not('emulator'in cmd and '-port 5582'in cmd);a.append({'receipt':p.name,'closed':True,'closureSHA256':sha(c)})
f=json.loads((R/'evidence/crew02/source-freeze06.json').read_text());assert all(sha(R/k)==v for k,v in f['files'].items());containers=subprocess.check_output(['docker','ps','--filter','label=aeris.task=crew02','--format','{{.ID}}'],text=True).strip();assert not containers
listeners=[]
for ports in ['5937-5942','8850']:
 r=subprocess.run(['lsof','-nP','-iTCP:'+ports,'-sTCP:LISTEN'],capture_output=True,text=True);assert r.returncode in[0,1];assert not r.stdout;listeners.append({'ports':ports,'listeners':0})
q={'at':datetime.datetime.now().astimezone().isoformat(),'P2':'NOT_READY','sourceFiles':len(f['files']),'sourceId':f['sourceId'],'sourcePinsExact':True,'APruns':closures,'companions':b,'emulators':a,'listeners':listeners,'containers':0,'SITLWindows':4,'APKBuilds':3,'fifthSITLRun':False,'coldboot03Launched':False,'SAF01IntendedTarget':'FAILED_NO_EXPECTATION_REWRITE','finalFreeBytes':shutil.disk_usage(R).free,'floorGiB':20,'hardwareProductionClaims':False};(E/'managed-closure-final01.json').open('x').write(json.dumps(q,indent=2));print({'sourceFiles':q['sourceFiles'],'APruns':len(closures),'companions':len(b),'emulators':len(a),'P2':q['P2'],'freeGiB':q['finalFreeBytes']/2**30})
