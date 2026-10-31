from pathlib import Path
import json,importlib.util,subprocess
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/heraui46'
s=importlib.util.spec_from_file_location('g40',R/'pilot/apstream40/guard.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
results=[]
def check(name,v):
 assert v,name
 results.append({'name':name,'pass':True})
def read(n):return json.loads((E/n).read_text())
check('initial floor20GiB',g.free()>20*2**30+2**20)
b=read('preservation-before1.json');bad=g.bad(b['files']);same=g.endure()==b['endureGuardPaths']
check('protected14130 hashes exact including frozen45',len(b['files'])==14130 and not bad)
check('ENDURE5051 unchanged inventory/bytes',same and len(g.endure())==5051)
check('13workspace guard/fault checks',read('model2.json')['checks']==13 and read('model2.json')['passed']==13)
check('17loopbackHTTP origin/revision/bounds checks',read('http2.json')['checks']==17 and read('http2.json')['status']=='PASS')
br=read('browser7.json');check('40actualbrowser endtoendchecks',br['checks']==40 and br['status']=='PASS')
check('browser no externalfetch/JSexception',not br['errors'] and not br['external'])
for n in ['diagnostic-1280.png','calibration-1280.png','mapping-1280.png','review-1280.png','layout-1280.png','layout-1024.png','layout-360.png']:check('screenshot '+n,(E/'browser7'/n).is_file())
for i in range(1,8):check('QAclosed browser/server attempt'+str(i),read(f'browser-cleanup{i}.json')['browserClosed'] and read(f'browser-cleanup{i}.json')['qaServerClosed'])
check('3earlyfailures retained',all(read(f'browser-failure{i}.json')['status']=='FAIL' for i in [1,2,3]))
cold=read('cold1.json');check('45cold76cases/795events/chunkstream exact',cold['corpusCases']==76 and cold['eventsReplayed']==795 and cold['stream']['exactRecord'])
contract=json.loads((R/'pilot/heramcu45/contract.json').read_text());check('16unknown protocolitems still unresolved',len(contract['unknowns'])==16 and all(u['status']=='UNRESOLVED' for u in contract['unknowns']) and not contract['wire']['codecPermitted'])
syntax=[]
for p in H.glob('*.mjs'):
 c=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);check('syntax '+p.name,c.returncode==0);syntax.append(p.name)
allocated=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file())
check('namespace16MiB and finalfloor20GiB',allocated<16*2**20-65536 and g.free()>20*2**30+2**20)
check('noowned scratch directory',not (R/'.local/heraui46').exists())
pins={str(p.relative_to(R)):g.sha(p) for p in H.rglob('*') if p.is_file()}
out={'at':datetime.now(timezone.utc).isoformat(),'status':'PASS_SCOPED_HOST_MOCK_UI','checks':len(results),'results':results,'requirementCoverage':{'passed':8,'total':8,'ids':['R46-0'+str(i) for i in range(1,9)],'scope':'host/mock UI only, no productreadiness percentage'},'syntaxFiles':len(syntax),'sourceFingerprints':pins,'preservation':{'protectedCount':len(b['files']),'failures':bad,'endureCount':len(g.endure()),'endureUnchanged':same},'resources':{'freeBytes':g.free(),'allocatedBytes':allocated,'floorBytes':20*2**30,'budgetBytes':16*2**20},'limitations':{'USBSDKDevice':'NOT_CHECKED','AndroidEmulator':'NOT_CHECKED','MCUWireCodec':'BLOCKED_UNKNOWN','physicalFlight':'NOT_CHECKED','newAPK':False,'newSignature':False,'ENDURE24hAcceptance':'NOT_ACHIEVED_BY_THIS_TASK','memoryOnlyWorkspace':True,'independentReview':False}}
n=1
while (E/f'verification{n}.json').exists():n+=1
with (E/f'verification{n}.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(results),'syntaxFiles':len(syntax),'protectedFailures':len(bad),'freeGiB':g.free()/2**30,'allocatedBytes':allocated}))
