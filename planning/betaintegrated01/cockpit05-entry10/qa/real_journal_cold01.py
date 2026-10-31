"""Independent cold replay only; does notprime/writeactualruntime orlaunch."""
from pathlib import Path
from importlib import import_module
import hashlib,json,base64,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));E=R/'evidence/betaintegrated01-cockpit05-entry10';D=E/'host/real-journal01';new=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal');old=import_module('pilot.betaintegrated01.runtime02.journal')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((D/'before.json').read_text());proof=json.loads((D/'proof.json').read_text());external=json.loads((D/'external-commit.json').read_text());manifest=json.loads((D/'journal/manifest.json').read_text());assert before['sourceSHA256']==sha(R/'planning/betaintegrated01/cockpit05-entry10/host/actual_journal_check.py');assert before['inputProvenance']=='SYNTHETIC_HOST_JOURNAL_ONLY_NO_AP_SENSOR'and before['APStarted']is False
assert manifest['diskGuardPolicy']['entryBytes']==10*2**30 and manifest['diskGuardPolicy']['floorBytes']==10*2**30 and manifest['diskGuardPolicy']['reserveBytes']==256*2**20
prime=manifest['diskGuardPriming'];assert prime==proof['actualPrime']and prime['source']=='ACTUAL_HOST_15S_PRIME_NO_SYNTHETIC_SEED'and prime['elapsedRealMonotonicNs']>=15000000000 and prime['historySpanNs']>=15000000000 and prime['sampleCount']>=2
cold=new.verify_journal(D/'journal','entry10-real-host','epoch',expected_commit=external['commitAnchor']);assert cold['state']=='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH'and cold['frames']==2
try:old.verify_journal(D/'journal','entry10-real-host','epoch',expected_commit=external['commitAnchor']);rejected=False
except old.VerificationError as exc:rejected=str(exc)=='DISK_GUARD_POLICY'
assert rejected
actual={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in(D/'journal').iterdir()};assert actual==proof['inventory']
rows=[]
for p in sorted((D/'journal').glob('segment-*.jsonl')):
 for line in p.open('rb'):rows.append(json.loads(line))
assert rows==proof['firstAtMost24Records']and len(rows)==cold['records'];groups={}
for row in rows:
 body=row['body']
 if body['kind']in('RX','INTENT','SENT'):groups.setdefault(body['frame'],[]).append(body)
for frame in range(2):
 rx,intent,sent=groups[frame];assert[rx['kind'],intent['kind'],sent['kind']]==['RX','INTENT','SENT'];assert base64.b64decode(rx['payload']['base64'])==('SYNTHETIC_RX_'+str(frame)).encode();raw=base64.b64decode(intent['payload']['base64']);assert raw==('SYNTHETIC_SENSOR_'+str(frame)).encode();trace=proof['mockSinkTrace'][frame];assert trace['intentSHA256']==hashlib.sha256(raw).hexdigest()and trace['sinkFsyncCount']>trace['computeFsyncCount']and trace['localSinkOnly']is True
assert proof['noAPOrEmulator']is True and proof['flightOrThirtyMinuteAccepted']is False
result={'status':'REAL_HOST_IO_ONLY_SYNTHETIC_FRAMES_COLD_PASS','frames':2,'records':len(rows),'actualPrimeNs':prime['elapsedRealMonotonicNs'],'externalCommitMatched':True,'old20ReaderRejectsNew10':True,'allOriginalJournalFileBytesSHAExact':True,'fsyncBeforeLocalSink':'RootactualFileIOhooktrace boundtosyntheticINTENTbytes; fsyncACKnotAPexecution/powerlossproof','proofFilesSHA256':{str(p.relative_to(R)):sha(p)for p in[D/'before.json',D/'proof.json',D/'external-commit.json']},'guardSampleMeaning':'Independentcoldvalidatesretainedprimereceipt/schema/wholejournal; real15s/OSfsyncobservedbyRootexecution, notindependentlyrerunbyQA.','noNewActualRunsByQA':True,'full30minAccepted':False,'AndroidAPFlight':False};(E/'qa/real-journal-cold01.json').open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],len(rows),prime['elapsedRealMonotonicNs'])
