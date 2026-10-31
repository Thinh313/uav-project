from pathlib import Path
from datetime import datetime,timezone
import json,re,sys,ast,subprocess,hashlib
R=Path(__file__).resolve().parents[2];D=R/'planning/simtrain52';E=R/'evidence/simtrain52-plan';checks=[]
def ck(n,v):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
j=json.loads((D/'plan.json').read_text());req={r['id']:r for r in j['requirements']};pk={p['id']:p for p in j['packages']};sc=j['scenarios'];ck('planning scope not runtime acceptance',j['status']=='PLAN_ONLY_NOT_IMPLEMENTED'and j['runtimeAcceptance']=='NOT_CHECKED_FOR_SIMTRAIN52');ck('25 unique requirements',len(req)==len(j['requirements'])==25);ck('22P0 and3P1',sum(r['priority']=='P0'for r in req.values())==22 and sum(r['priority']=='P1'for r in req.values())==3)
ck('all requirements have behavior/observable acceptance/no pass claim',all(r['behavior']and r['acceptance']and r['status']=='PLANNED_NOT_CHECKED'for r in req.values()));ck('17 unique planned scenarios',len(sc)==17==len({s['id']for s in sc}));covered=set(x for s in sc for x in s['requirements']);ck('all25 requirements mapped to scenarios',covered==set(req));ck('no executed scenarios claimed',all(s['status'].startswith('NOT_RUN')for s in sc));ck('8 unique main gates',len(pk)==8);seen=set()
for p in j['packages']:
 ck('dependency order '+p['id'],set(p['dependsOn'])<=seen);seen.add(p['id']);ck('exit and deliverable '+p['id'],bool(p['exit']and p['deliverable']and p['role']))
p0={r['id']for r in req.values()if r['priority']=='P0'};ck('P0 mapped to council work packages',p0<=set(x for p in pk.values()for x in p['requirements']));ck('P1 assigned to future extensions',set(req)-p0==set(x for f in j['extensions']for x in f['requirements']));ck('no hard schedule promise',not j['schedule']['commitment']and j['schedule']['confidence']=='LOW_UNTIL_G0');ck('laptop projector and ASAP captured','chiếu'in j['audience']and j['deadline'].startswith('ASAP'));ck('no frozen mutation or signature scope',not j['freeze']['modifySourceCandidateEndure']and not j['freeze']['newSoftwareSignature'])
last=0
for d in j['demo']:
 a,b=d['time'].split('–');t=lambda s:int(s.split(':')[0])*60+int(s.split(':')[1]);ck('demo contiguous '+d['id'],t(a)==last and t(b)>t(a));last=t(b)
ck('script ends at18minutes',last==1080);ck('8 proposed measurement contracts',len(j['metrics'])==8 and all(m['status']=='PROPOSED_NOT_MEASURED'for m in j['metrics']));x=j['resourceExample'];ck('frame count sizing math',x['physicsFrames']==x['physicsHz']*x['demoSeconds']);ck('raw sizing math',x['rawBytesCases']==[n*x['physicsFrames']for n in x['bytesPerFrameCases']]);ck('video/image sizing math',x['videoBytesExample']==x['videoMbpsExample']*1e6/8*x['demoSeconds']and x['imageBytesTotalExample']==x['imageCountExample']*x['imageBytesEachExample']);ck('resource example not measured',x['status']=='ILLUSTRATIVE_NOT_MEASURED')
h=(D/'index.html').read_text();embedded=re.search(r'<script id="plan-data" type="application/json">(.*?)</script>',h,re.S).group(1);ck('HTML embedded final contract exact',json.loads(embedded)==j);targets=re.findall(r'data-pane="([^"]+)"',h);panes=re.findall(r'<section id="([^"]+)" class="pane"',h);ck('6 navigation targets defined',len(targets)==6 and set(targets)==set(panes));ck('3 mode selectors defined',set(re.findall(r'data-mode="([^"]+)"',h))=={'manual','assisted','auto'})
for f in ['PLAN.md','COUNCIL-RUNBOOK.md','ACCEPTANCE-MATRIX.md','presentation.css','presentation.js']:
 ck('artifact '+f,(D/f).is_file())
ck('local font exists',(R/'native/preflight44/assets/IBMPlexSans.ttf').is_file());ck('no remote script/link runtime assets',not re.search(r'<(?:script|link)[^>]+(?:src|href)="https?://',h));ck('initial authoring seed refuses replacement','refusing overwrite'in(D/'author_plan.py').read_text())
for p in D.glob('*.mjs'):
 ck('JS syntax '+p.name,subprocess.run(['node','--check',str(p)],capture_output=True).returncode==0)
for p in D.glob('*.js'):
 ck('JS syntax '+p.name,subprocess.run(['node','--check',str(p)],capture_output=True).returncode==0)
for p in D.glob('*.py'):ast.parse(p.read_text());ck('Python syntax '+p.name,True)
br=json.loads((E/'browser2/receipt.json').read_text());ck('final planning UI37checks',br['status']=='PASS_PLANNING_PRESENTATION_ONLY'and br['checks']==37 and all(x['pass']for x in br['results']));ck('browser no JS errors or remote fetch',not br['errors']and not br['external'])
for row in json.loads((E/'sources/captures.json').read_text()):ck('source capture '+row['id'],row['status']==200 and hashlib.sha256((E/'sources'/(row['id']+'.html')).read_bytes()).hexdigest()==row['sha256'])
sys.path.insert(0,str(R/'pilot/apstream40'));import guard as g
b=json.loads((E/'preservation-before.json').read_text());ck('20207protected bytes unchanged',len(b['files'])==20207 and not g.bad(b['files']));ck('ENDURE5051inventory unchanged',len(g.endure())==5051 and g.endure()==b['endurePaths']);ck('host floor20GiB',g.free()>=20*2**30);allocated=sum(p.stat().st_blocks*512 for d in[D,E]for p in d.rglob('*')if p.is_file());ck('planning budget8MiB',allocated<8*2**20)
out={'at':datetime.now(timezone.utc).isoformat(),'status':'PASS_PLAN_AND_PRESENTATION_ONLY','planningAC':{'done':5,'total':5},'requirementsDefined':25,'requirementsRuntimeVerified':0,'scenariosDefined':17,'scenariosRuntimeExecuted':0,'mainGatesDefined':8,'documentConsistencyChecks':len(checks),'results':checks,'planningBrowserChecks':37,'sourcesCaptured':3,'protectedCount':len(b['files']),'endureCount':len(b['endurePaths']),'allocatedBytes':allocated,'freeBytes':g.free(),'independentReview':False,'runtime3DPhysicsInputAudioProjector':'NOT_CHECKED_FOR_SIMTRAIN52','actualLaptopGpuAndStaff':'NOT_SELECTED','deadline':'ASAP; dates conditional afterG0','sourceCandidateEndureChanges':False,'cleanupRemoved':[]}
with(E/'verification.json').open('x')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items()if k!='results'},ensure_ascii=False))
