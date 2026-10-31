"""Cold source-bound mock verification, no simulator, install or old writes."""
import json,sys,subprocess,ast,re
from datetime import datetime,timezone
from guard import R,H,E,sha,bad,endure,free,FLOOR,BUDGET,append
logic=json.loads((E/'logic2.json').read_text());replay=json.loads((E/'replay2.json').read_text());oracle=json.loads((E/'oracle-check1.json').read_text());schema=json.loads((E/'schema1.json').read_text());before=json.loads((E/'preservation-before1.json').read_text());checks=[]
def check(name,value):checks.append({'name':name,'pass':bool(value)})
check('1015 current logic checks',logic['status']=='MOCK_PASS' and logic['checkCount']==logic['passed']==1015 and all(x['pass'] for x in logic['results']))
check('974 full-dialect vectors and37166 split positions',logic['oracleVectorCount']==974 and logic['splitPositions']==37166)
check('44 new cases and9 rejecting bites',replay['status']=='MOCK_PASS' and replay['replay']['caseCount']==44 and all(x['matched'] for x in replay['replay']['results']) and len(replay['bites'])==9 and all(x['rejected'] for x in replay['bites']))
check('current exact source hashes',logic['sourceHashes']==replay['sourceHashes'] and not bad(logic['sourceHashes']))
check('upstream reverse decoding974 JS vectors',oracle['status']=='PASS' and oracle['checks']==974 and sha(R/oracle['inputPath'])==oracle['inputSha256'] and not bad(oracle['oracleHashes']))
check('nine XML + parser pins unchanged',schema['xmlFiles']==9 and schema['messages']==schema['allLayoutCRCMatches']==299 and not bad(schema['pins']))
sys.path.insert(0,str(R/'runtime/sim32-instrument01-build/ardupilot/modules/mavlink'))
from pymavlink.generator import mavparse
definitions=json.loads((H/'definitions.mjs').read_text().split('export const DEFINITIONS=',1)[1].rstrip().rstrip(';'));ids=set();layouts=0
for path in schema['pins']:
 if not path.endswith('.xml'):continue
 for m in mavparse.MAVXML(str(R/path),wire_protocol_version='2.0').message:
  d=definitions[str(m.id)];assert (d['crc'],d['min'],d['max'],[f['name'] for f in d['fields']])==(m.crc_extra,m.wire_min_length,m.wire_length,m.ordered_fieldnames);ids.add(m.id);layouts+=1
check('fresh upstream299 layouts cover exact schema',layouts==299 and ids==set(map(int,definitions)))
code="""import{readFile}from'node:fs/promises';import{run,replayCorpus}from'./pilot/apstream40/corpus.mjs';import{validateJournal}from'./pilot/apstream40/journal.mjs';import{validateLedger}from'./pilot/apflight36/ledger.mjs';import{FullFramer,unhex}from'./pilot/apstream40/wire.mjs';import{replayCorpus as a36}from'./pilot/apflight36/corpus.mjs';import{replayCorpus as a37}from'./pilot/mavflight37/scenarios.mjs';import{replayCorpus as a38}from'./pilot/firmware38/corpus.mjs';import{replayCorpus as a39}from'./pilot/flightadapter39/corpus.mjs';const read=async p=>JSON.parse(await readFile(p,'utf8'));const corpus=await read('evidence/apstream40/corpus2.json');let chains=0;for(const c of corpus.cases){const r=await run(c.input);await validateJournal(r.audit.fullStream);await validateLedger(r.audit.parameters);chains+=2;for(const p of r.outputs){const f=new FullFramer().push(unhex(p.rawHex),100,100)[0];if(p.networkSent!==false||p.operationalAllowed!==false||!([20,76].includes(f.id))||f.id===76&&(f.fields.command!==512||f.fields.param1!==148||[2,3,4,5,6,7].some(k=>f.fields['param'+k]!==0)))throw Error('outbound scope');}}console.log(JSON.stringify({current:await replayCorpus(corpus),chains,a36:await a36(await read('evidence/apflight36/corpus6.json')),a37:await a37(await read('evidence/mavflight37/corpus4.json')),a38:await a38(await read('evidence/firmware38/corpus4.json')),a39:await a39(await read('evidence/flightadapter39/corpus4.json'))}));"""
p=subprocess.run(['node','--input-type=module','-e',code],cwd=R,capture_output=True,text=True,timeout=45);cold=json.loads(p.stdout) if p.returncode==0 else None;cold_error=p.stderr
check('cold44 case replay matches exactly',cold is not None and cold['current']==replay['replay'])
check('88 journal chains and output whitelist',cold is not None and cold['chains']==88)
for key,folder,rp,count in [('a36','apflight36','replay6.json',33),('a37','mavflight37','replay4.json',41),('a38','firmware38','replay4.json',54),('a39','flightadapter39','replay4.json',40)]:
 expected=json.loads((R/'evidence'/folder/rp).read_text())['replay'];check(f'old {folder} exact{count} cases',cold is not None and cold[key]==expected and cold[key]['caseCount']==count)
syntax=[]
for f in sorted(H.glob('*.mjs')):
 p=subprocess.run(['node','--check',str(f)],cwd=R,capture_output=True,text=True,timeout=15);syntax.append({'path':str(f.relative_to(R)),'exit':p.returncode,'stderr':p.stderr})
check('nine JS syntax checks',len(syntax)==9 and all(x['exit']==0 for x in syntax))
for f in H.glob('*.py'):ast.parse(f.read_text())
check('Python syntax no cache/build',True)
check('production core no IO/process/network imports',all(not re.search(r'node:|\bfetch\s*\(|\bWebSocket\b|https?://',(H/n).read_text()) for n in ['wire.mjs','adapter.mjs','journal.mjs']))
failures=bad(before['files']);paths=endure();allocated=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file())
check('all protected historical SHA unchanged',not failures)
check('ENDURE inventory unchanged',paths==before['endureGuardPaths'])
check('floor20GiB and namespace32MiB',free()>=FLOOR and allocated<BUDGET)
check('no new cache/build/install/runtime directory',not any(p.name in ['node_modules','__pycache__','dist','build','.build'] for d in [H,E] for p in d.rglob('*') if p.is_dir()))
obj={'at':datetime.now(timezone.utc).isoformat(),'status':'MOCK_FULL_STREAM_DISCOVERY_VERIFIED' if all(c['pass'] for c in checks) else 'FAIL','requirementsImplemented':7,'requirementsTotal':7,'scope':'PINNED_DIALECT_OFFLINE_MOCK_ONLY','checks':checks,'syntax':syntax,'protectedCount':len(before['files']),'protectedDeltas':failures,'endureGuardCount':len(paths),'sourceHashes':logic['sourceHashes'],'sourcePins':schema['pins'],'receiptHashes':{str((E/n).relative_to(R)):sha(E/n) for n in ['logic2.json','replay2.json','corpus2.json','schema1.json','overlap1.json','oracle-vectors1.json','oracle-check1.json','preservation-before1.json']},'coldReplay':cold,'coldError':cold_error if cold is None else None,'allocatedBytes':allocated,'freeBytes':free(),'sameAgentSeparateInvocation':True,'independentReview':False,'actualBinary_SITL_Android_Hera':'NOT_CHECKED','newRuntime_Signature':False,'networkSent':False,'continuousOriginalPathPresence':'NOT_CLAIMED'}
path=append('verification',obj);print(json.dumps({'receipt':str(path),'status':obj['status'],'checks':len(checks),'failures':[c for c in checks if not c['pass']],'protectedCount':len(before['files']),'deltas':len(failures),'allocatedMiB':allocated/2**20,'freeGiB':free()/2**30}));assert obj['status']=='MOCK_FULL_STREAM_DISCOVERY_VERIFIED'
