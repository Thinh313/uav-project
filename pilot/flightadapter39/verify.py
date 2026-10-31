"""Cold actual replay and readonly fingerprint verification; same agent, separate process."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,re,ast
from guard import R,H,E,sha,append,free,FLOOR,BUDGET,check_files,endure_paths

logic=json.loads((E/'logic4.json').read_text()); replay=json.loads((E/'replay4.json').read_text())
before=json.loads((E/'preservation-before1.json').read_text());checks=[]
def check(name,value):checks.append({'name':name,'pass':bool(value)})
check('236 current logic checks pass',logic['status']=='MOCK_PASS' and logic['checkCount']==logic['passed']==236 and all(x['pass'] for x in logic['results']))
check('185 pinned oracle vectors and5671 split positions',logic['oracleVectors']==185 and logic['splitPositions']==5671)
check('40 current replay cases and9 rejecting bites',replay['status']=='MOCK_PASS' and replay['replay']['caseCount']==40 and all(r['matched'] for r in replay['replay']['results']) and len(replay['bites'])==9 and all(r['rejected'] for r in replay['bites']))
check('current exact source-bound receipts',logic['sourceHashes']==replay['sourceHashes'] and not check_files(logic['sourceHashes']))
code="""import {readFile}from'node:fs/promises';import{replayCorpus,run}from'./pilot/flightadapter39/corpus.mjs';import{validateLedger}from'./pilot/apflight36/ledger.mjs';import{replayCorpus as a36}from'./pilot/apflight36/corpus.mjs';import{replayCorpus as m37}from'./pilot/mavflight37/scenarios.mjs';import{replayCorpus as f38}from'./pilot/firmware38/corpus.mjs';const read=async p=>JSON.parse(await readFile(p,'utf8'));const corpus=await read('evidence/flightadapter39/corpus4.json');let journals=0;for(const c of corpus.cases){const r=await run(c.input);await validateLedger(r.audit.session);await validateLedger(r.audit.parameters);if(r.outputs.some(p=>p.id!==20||p.networkSent!==false||p.operationalAllowed!==false))throw Error('outbound breach');journals+=2;}console.log(JSON.stringify({current:await replayCorpus(corpus),journalChecks:journals,a36:await a36(await read('evidence/apflight36/corpus6.json')),m37:await m37(await read('evidence/mavflight37/corpus4.json')),f38:await f38(await read('evidence/firmware38/corpus4.json'))}));"""
p=subprocess.run(['node','--input-type=module','-e',code],cwd=R,capture_output=True,text=True,timeout=30)
cold=json.loads(p.stdout) if p.returncode==0 else None
cold_error=p.stderr
check('cold replay exactly reproduces40 receipts',cold is not None and cold['current']==replay['replay'])
check('80 journal chains valid and readonly output whitelist',cold is not None and cold['journalChecks']==80)
for key,folder,file,total in [('a36','apflight36','replay6.json',33),('m37','mavflight37','replay4.json',41),('f38','firmware38','replay4.json',54)]:
 expected=json.loads((R/'evidence'/folder/file).read_text())['replay']
 check(f'old {folder} exact {total}-case replay',cold is not None and cold[key]==expected and cold[key]['caseCount']==total)
syntax=[]
for f in sorted(H.glob('*.mjs')):
 p=subprocess.run(['node','--check',str(f)],cwd=R,capture_output=True,text=True,timeout=15)
 syntax.append({'path':str(f.relative_to(R)),'exit':p.returncode,'stderr':p.stderr})
check('7 JavaScript syntax checks',len(syntax)==7 and all(x['exit']==0 for x in syntax))
for f in H.glob('*.py'):ast.parse(f.read_text())
check('Python syntax valid without cache/build',True)
cores=[H/'adapter.mjs',H/'framer.mjs']
check('core has no IO/transport/process imports or endpoints',all(not re.search(r'node:|\bfetch\s*\(|\bWebSocket\b|https?://|udp://',(f.read_text())) for f in cores))
bad=check_files(before['files']);paths=endure_paths();allocated=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file())
check('all protected historical bytes unchanged',not bad)
check('ENDURE exact file inventory unchanged',paths==before['endureGuardPaths'])
check('20GiB floor and16MiB namespace budget',free()>=FLOOR and allocated<BUDGET)
check('no new runtime/build/install/cache directory',not any(p.name in ['node_modules','__pycache__','dist','build','.build'] for d in [H,E] for p in d.rglob('*') if p.is_dir()))
report={'at':datetime.now(timezone.utc).isoformat(),'status':'MOCK_COMPOSITION_VERIFIED' if all(c['pass'] for c in checks) else 'FAIL',
 'requirementsImplemented':7,'requirementsTotal':7,'requirementsScope':'OFFLINE_READONLY_COMPOSITION_ONLY','checks':checks,'syntax':syntax,
 'protectedCount':len(before['files']),'protectedDeltas':bad,'endureGuardCount':len(paths),'allocatedBytes':allocated,'freeBytes':free(),
 'receiptHashes':{str((E/n).relative_to(R)):sha(E/n) for n in ['logic4.json','replay4.json','corpus4.json','preservation-before1.json']},
 'sourceHashes':logic['sourceHashes'],'coldReplay':cold,'coldError':cold_error if cold is None else None,
 'sameAgentSeparateInvocation':True,'independentReview':False,'actualFirmware_SITL_Android_Hera':'NOT_CHECKED',
 'newBuild_Runtime_Signature':False,'networkSent':False,'continuousOriginalPathPresence':'NOT_CLAIMED'}
path=append('verification',report)
print(json.dumps({'receipt':str(path),'status':report['status'],'checks':len(checks),'failures':[c for c in checks if not c['pass']],
 'protectedCount':len(before['files']),'deltas':len(bad),'endureGuardCount':len(paths),'allocatedMiB':allocated/2**20,'freeGiB':free()/2**30}))
assert report['status']=='MOCK_COMPOSITION_VERIFIED'
