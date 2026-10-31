import json,subprocess,ast,socket
from pathlib import Path
from guard import R,H,E,sha,free,FLOOR,BUDGET,check,put,g
checks=[]
def gate(n,v):checks.append({'name':n,'pass':bool(v)})
A=E/'run03';qa=json.loads((A/'qa.json').read_text());raw=json.loads((E/'raw-replay2.json').read_text());unit=json.loads((E/'unit3.json').read_text());fault=json.loads((E/'guard-faults1.json').read_text());bites=json.loads((E/'bites1.json').read_text());launch=json.loads((A/'launch.json').read_text());i=json.loads((A/'inspect-start.json').read_text());end=json.loads((A/'inspect-after-qa.json').read_text());cleanup=json.loads((A/'cleanup.json').read_text());pins=json.loads((A/'runner-source-pins.json').read_text());source=json.loads((E/'sources-qa.json').read_text())
gate('17 final actual checks',qa['status']=='PASS_SCOPED_REAL_SITL' and len(qa['results'])==17 and all(c['pass'] for c in qa['results']))
gate('56 final unit +9 focused guard faults',unit['passed']==unit['checks']==56 and fault['passed']==fault['checks']==9)
gate('13 semantic actual raw replay gates',raw['run']=='run03' and raw['checkCount']==13 and all(c['pass'] for c in raw['checks']))
gate('14 adversarial semantic/journal mutations rejected',bites['run']=='run03' and bites['total']==bites['passed']==14 and all(x['rejected'] for x in bites['results']))
for k,s in enumerate(['session01','session02']):gate(s+' raw SHA matches replay',sha(A/(s+'-raw.jsonl'))==raw['rawSha256'][k]==bites['baselineRawSha256'][k])
gate('runner module pins unchanged since actualrun03 admission',not g.bad(pins['files']))
gate('binary/defaults actual input pins unchanged',not g.bad(launch['inputHashes']))
gate('local AP source SHA unchanged',not g.bad(source['localSourceFiles']))
gate('actual source-bound binary exact41 SHA',launch['inputHashes']['runtime/sitl/arducopter']=='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482')
gate('container exact owned CID/image/mounts/security',i['Id']==end['Id']==cleanup['containerStoppedRemoved']==launch['containerId'] and i['Image']==launch['imageId']=='sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55' and i['Config']['Labels'].get('aeris.task')=='flightsafety42' and 'no-new-privileges' in i['HostConfig']['SecurityOpt'] and {m['Destination']:m['RW'] for m in i['Mounts']}=={'/aeris':False,'/task':False,'/state':True})
gate('CPU1 RAM256MiB log4MiB bounded',i['HostConfig']['NanoCpus']==10**9 and i['HostConfig']['Memory']==256*2**20 and i['HostConfig']['LogConfig']['Config'].get('max-size')=='2m' and i['HostConfig']['LogConfig']['Config'].get('max-file')=='2')
gate('loopback5797 only',i['HostConfig']['PortBindings']=={'5760/tcp':[{'HostIp':'127.0.0.1','HostPort':'5797'}]})
gate('same ownedAP PID/start no process rebind betweenflights',i['State']['Pid']==end['State']['Pid'] and i['State']['StartedAt']==end['State']['StartedAt'])
with socket.socket() as s:gate('port5797 closed',s.connect_ex(('127.0.0.1',5797))!=0)
gate('failure run01 and initial false-positive gap retained', (E/'run01/qa-failure.json').is_file() and (E/'run01/source-before-mapping/contract.mjs').is_file() and (E/'run01/cleanup.json').is_file() and (E/'run02/verification-gap.json').is_file() and (E/'run02/cleanup.json').is_file())
code="""import{readFile}from'node:fs/promises';import{replay}from'./pilot/flightsafety42/replay.mjs';import{replayAll}from'./pilot/sitldiscovery41/replay.mjs';import{replayCorpus as a36}from'./pilot/apflight36/corpus.mjs';import{replayCorpus as a37}from'./pilot/mavflight37/scenarios.mjs';import{replayCorpus as a38}from'./pilot/firmware38/corpus.mjs';import{replayCorpus as a39}from'./pilot/flightadapter39/corpus.mjs';import{replayCorpus as a40}from'./pilot/apstream40/corpus.mjs';const j=async p=>JSON.parse(await readFile(p,'utf8'));console.log(JSON.stringify({actual:await replay('run03'),a41:await replayAll(),a36:await a36(await j('evidence/apflight36/corpus6.json')),a37:await a37(await j('evidence/mavflight37/corpus4.json')),a38:await a38(await j('evidence/firmware38/corpus4.json')),a39:await a39(await j('evidence/flightadapter39/corpus4.json')),a40:await a40(await j('evidence/apstream40/corpus2.json'))}));"""
p=subprocess.run(['node','--input-type=module','-e',code],cwd=R,capture_output=True,text=True,timeout=60);cold=json.loads(p.stdout) if p.returncode==0 else None
expected={k:v for k,v in raw.items() if k!='run'};gate('fresh-process actual42 cold replay exact',cold is not None and cold['actual']==expected)
gate('41 original3 actual sessions exact',cold is not None and cold['a41']==json.loads((R/'evidence/sitldiscovery41/raw-replay1.json').read_text())['results'])
for key,folder,rp,count in [('a36','apflight36','replay6.json',33),('a37','mavflight37','replay4.json',41),('a38','firmware38','replay4.json',54),('a39','flightadapter39','replay4.json',40),('a40','apstream40','replay2.json',44)]:gate(f'old{folder} exact{count} cases unchanged',cold is not None and cold[key]==json.loads((R/'evidence'/folder/rp).read_text())['replay'])
syntax=[]
for f in H.glob('*.mjs'):
 p=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=15);syntax.append({'path':str(f.relative_to(R)),'exit':p.returncode,'stderr':p.stderr})
for f in H.glob('*.py'):
 try:ast.parse(f.read_text());syntax.append({'path':str(f.relative_to(R)),'exit':0})
 except SyntaxError as e:syntax.append({'path':str(f.relative_to(R)),'exit':1,'stderr':str(e)})
gate('allJS/Python syntax valid',all(x['exit']==0 for x in syntax))
preserve=check();gate('protected SHA/inventory exact and20GiB floor',not preserve['failures'] and preserve['endureUnchanged'] and preserve['freeBytes']>=FLOOR and preserve['allocatedBytes']<BUDGET)
gate('each owned runtime state below128MiB',all(sum(p.stat().st_size for p in d.rglob('*') if p.is_file())<128*2**20 for d in (R/'.local/flightsafety42').glob('run*')))
ok=all(x['pass'] for x in checks);o={'status':'READY_SCOPED_REAL_SITL_FLIGHTSAFETY42' if ok else 'NOT_READY','requirements':{'implemented':7,'verified':7 if ok else None,'total':7,'ids':['R42-01','R42-02','R42-03','R42-04','R42-05','R42-06','R42-07']},'gates':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks),'syntax':syntax,'actualRawReplay':raw,'preservation':preserve,'coldError':p.stderr if cold is None else None,'review':'Sequential one-agent specification/build/verify; no independent audit','limits':qa['scopeLimits']+raw['limits']+['No general firmware/Hera configuration or physical drone flight acceptance','No steady1x/latency/endurance/AI-flight/DJI superiority acceptance']};put('verification',o);print(json.dumps({'status':o['status'],'gates':len(checks),'passed':o['passed'],'preserved':preserve['protectedCount'],'freeGiB':free()/2**30}));assert ok,[x for x in checks if not x['pass']]
