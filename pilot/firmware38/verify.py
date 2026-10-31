"""Separate cold replay/current-source/protected SHA gate; no runtime or build."""
from pathlib import Path
import json,hashlib,os,subprocess,re
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/firmware38'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
logic=json.loads((E/'logic3.json').read_text());replay=json.loads((E/'replay4.json').read_text());oracle=json.loads((E/'oracle-check2.json').read_text());before=json.loads((E/'preservation-before.json').read_text());checks=[]
def check(name,v):checks.append({'name':name,'pass':bool(v)})
check('96 current logic checks PASS',logic['status']=='MOCK_PASS' and logic['checkCount']==logic['passed']==96)
check('logic source hashes match',all(sha(R/p)==s for p,s in logic['sourceHashes'].items()))
check('54 scenarios and 7 bites PASS',replay['status']=='MOCK_PASS' and replay['replay']['caseCount']==54 and len(replay['bites'])==7 and all(b['rejected'] for b in replay['bites']))
check('replay source hashes match',all(sha(R/p)==s for p,s in replay['sourceHashes'].items()))
check('41 upstream oracle checks and inputs match',oracle['status']=='PASS' and oracle['checks']==41 and sha(E/'js-vectors3.json')==oracle['inputSha256'] and all(sha(R/p)==s for p,s in oracle['oracleHashes'].items()))
code="""import{readFile}from'node:fs/promises';import{replayCorpus}from'./pilot/firmware38/corpus.mjs';import{replayCorpus as p37}from'./pilot/mavflight37/scenarios.mjs';import{replayCorpus as p36}from'./pilot/apflight36/corpus.mjs';const read=async p=>JSON.parse(await readFile(p,'utf8'));console.log(JSON.stringify({new:await replayCorpus(await read('evidence/firmware38/corpus4.json')),p37:await p37(await read('evidence/mavflight37/corpus4.json')),p36:await p36(await read('evidence/apflight36/corpus6.json'))}));"""
p=subprocess.run(['node','--input-type=module','-e',code],cwd=R,capture_output=True,text=True,timeout=30);cold=json.loads(p.stdout) if p.returncode==0 else None
check('cold new replay exactly matches receipt',cold is not None and cold['new']==replay['replay'])
check('41 old MAVFLIGHT37 exact regression',cold is not None and cold['p37']==json.loads((R/'evidence/mavflight37/replay4.json').read_text())['replay'])
check('33 old APFLIGHT36 exact regression',cold is not None and cold['p36']==json.loads((R/'evidence/apflight36/replay6.json').read_text())['replay'])
syntax=[]
for f in H.glob('*.mjs'):
 p=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=15);syntax.append({'path':str(f.relative_to(R)),'exit':p.returncode,'stderr':p.stderr})
check('JS syntax checks pass',all(r['exit']==0 for r in syntax))
check('core no network/process imports',all(not re.search(r'node:(?:net|dgram|child_process)|\bfetch\s*\(|\bWebSocket\b', (H/n).read_text()) for n in ['wire.mjs','contract.mjs','readback.mjs','policy.mjs','altitude.mjs']))
fail=[]
for rel,s in before['files'].items():
 q=R/rel;current=sha(q) if q.is_file() else None
 if current!=s:fail.append({'path':rel,'expectedSha256':s,'observedSha256':current})
check('all protected SHA match before',not fail)
endure=set()
for parent in ['evidence','pilot','.local','delivery/releases']:
 for d in (R/parent).glob('*endure*'):
  if d.is_dir():endure.update(str(p.relative_to(R)) for p in d.rglob('*') if p.is_file())
for parent in ['docs','delivery']:endure.update(str(p.relative_to(R)) for p in (R/parent).glob('*ENDURE*') if p.is_file())
check('ENDURE inventory unchanged',endure==set(before['endureGuardPaths']))
allocated=sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file());v=os.statvfs(R);free=v.f_bavail*v.f_frsize
check('8MiB namespace and20GiB floor',allocated<8*2**20 and free>=20*2**30)
check('no dependency/cache/build directory created',not any(p.name in ['build','dist','node_modules','__pycache__'] for d in [H,E] for p in d.rglob('*') if p.is_dir()))
n=1
while (E/f'verification{n}.json').exists():n+=1
report={'at':datetime.now(timezone.utc).isoformat(),'status':'MOCK_CONTRACT_VERIFIED' if all(c['pass'] for c in checks) else 'FAIL','checks':checks,'requirementsImplemented':8,'requirementsTotal':8,'scope':'PINNED_SOURCE_INTERPRETATION_AND_MOCK_REPLAY_ONLY','syntax':syntax,'protectedCount':len(before['files']),'protectedDeltas':fail,'endureGuardCount':len(endure),'allocatedBytes':allocated,'freeBytes':free,'sourcePins':json.loads((E/'source-pins.json').read_text())['files'],'receiptHashes':{str((E/n).relative_to(R)):sha(E/n) for n in ['logic3.json','replay4.json','oracle-check2.json','preservation-before.json']},'sameAgentSeparateInvocation':True,'realFirmware_BinaryAssociation_Hardware_SITL':'NOT_CHECKED','newBuild_Runtime_Signature':False,'networkSent':False,'continuousOriginalPathPresence':'NOT_CLAIMED'}
with (E/f'verification{n}.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':[c for c in checks if not c['pass']],'protectedCount':len(before['files']),'deltas':len(fail),'allocatedMiB':allocated/2**20,'freeGiB':free/2**30}));assert report['status']=='MOCK_CONTRACT_VERIFIED'
