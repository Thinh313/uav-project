"""Out-of-bound send return remains explicit UNKNOWN with zero retries."""
from pathlib import Path
import sys,json,hashlib,datetime
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.journal import SegmentedJournal,verify_journal
E=R/'evidence/betaintegrated01-m1mock/journal/send-return03';E.mkdir(exist_ok=False)
j=SegmentedJournal(E/'case','run01','epoch01');calls=[]
try:j.record_frame(0,b'r',b's',lambda b:calls.append(True)or 2**100)
except Exception as e:error=type(e).__name__+':'+str(e)
else:raise AssertionError('EXPECTED_UNKNOWN')
v=verify_journal(j.root,'run01','epoch01');assert len(calls)==1 and v['unknownSends']==1 and v['state']=='INCOMPLETE_RECORDING'and not v['publicationAllowed']
report={'status':'PASS','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error':error,'sendCalls':len(calls),'verdict':v,'sourceSHA256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in(R/'pilot/betaintegrated01/journal').glob('*.py')}}
(E/'report.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
