import json,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from validate import validate
R=Path(__file__).resolve().parents[3];base=json.loads((Path(__file__).parent/'intake.json').read_text());checks=[]
def ck(n,v):assert v,n;checks.append({'name':n,'pass':True})
r=validate(base);ck('unknown hardware never PASS',r['hardwareAcceptance']=='NOT_CHECKED'and r['status']=='BLOCKED_MISSING_INPUTS');ck('reference emulator cannot satisfy real config',len(r['missing'])>30)
d=copy.deepcopy(base)
from validate import FIELDS,PAYLOAD
for group,fields in FIELDS.items():
 for f in fields:d[group][f]='SYNTHETIC_FIXTURE'
for f in PAYLOAD:d['payloads'][0][f]='SYNTHETIC_FIXTURE'
for g,fs in [('input',['latencyP95BudgetMs']),('video',['width','height','frameRate','staleThresholdMs','latencyP95BudgetMs'])]:
 for f in fs:d[g][f]=100
d['dualOperator']['pilotIdentity']='fixture-A';d['dualOperator']['payloadIdentity']='fixture-B';d['hardwareAvailable']=True;d['controller'].update(androidApi=33,screenPixels=[1280,800]);d['aircraft'].update(systemId=42,componentId=1);d['input']['neutralDeadzone']=0.03;d['payloads'][0]['controlTarget']={'system':42,'component':100,'deviceId':1};r=validate(d);ck('complete synthetic intake only review-ready',r['status']=='READY_FOR_BENCH_REVIEW_ONLY'and r['hardwareAcceptance']=='NOT_CHECKED'and not r['productionAccepted']);d['payloads'].append(copy.deepcopy(d['payloads'][0]));ck('duplicate routing blocked','payloads.AMBIGUOUS_TARGET_ROUTING'in validate(d)['missing']);d['input']['latencyP95BudgetMs']=-1;ck('invalid input budget rejected',any('POSITIVE_BUDGET'in s for s in validate(d)['missing']));d['dualOperator']['payloadIdentity']='fixture-A';ck('same operator identity blocked','dualOperator.DISTINCT_IDENTITIES_REQUIRED'in validate(d)['missing'])
(R/'evidence/native88/bench-qa02.json').open('x').write(json.dumps({'status':'PASS','checks':checks,'hardwareAcceptance':'NOT_CHECKED'},indent=2));print('BENCH_QA_PASS',len(checks))
