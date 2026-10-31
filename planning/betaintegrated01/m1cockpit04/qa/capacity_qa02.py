from pathlib import Path
import sys,hashlib,json,inspect,ast
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.cockpit04 import capacity as c
from pilot.betaintegrated01.cockpit04.frame_adapter import FrameAdapter
from pilot.betaintegrated01.runtime02.frame_adapter import FrameAdapter as Accepted
from pilot.betaintegrated01.runtime02.journal import Policy,SegmentedJournal
from pilot.betaintegrated01.runtime02.journal.admission import DISK_POLICY
O=R/'evidence/betaintegrated01-m1cockpit04/qa/capacity02';O.mkdir();G=2**30;M=2**20;tests=[]
def ck(i,p):tests.append(dict(id=i,pass_=bool(p)))
expected={'hostMainJournalQuota':6*G,'hostSmokeLossJournalQuotas':2*384*M,'APRawAllCases':2140*1200*10*64+30*64,'APHeadersSealsTermination':16*M,'transportAllCases':320*M,'nativeAVDAllocatedGrowth':512*M,'nativeExportsAllCases':192*M,'metadataCheckpointsLogsAPK':64*M,'retainedUnit':128*M};b=c.task_budget();ck('independentAllCaseIntegerArithmetic',b['categories']==expected and b['taskHardPeakBytes']==sum(expected.values()));ck('peakBelow9point5',sum(expected.values())<19*G//2);ck('requiredFree20GiBAnd10point25Floor',b['requiredFreeBytes']==20*G and b['floorBytes']==10*G and b['reserveBytes']==256*M);ck('singleOriginalNot3copies',b['hostRawCopies']==1 and b['hostRawDuplicateOrExport']is False and b['maximumFormatDurationGuaranteed']is False);ck('nativeExportAll3Caps',sum(b['nativeExportCapsBytes'].values())==192*M);ck('free20ExactAdmitsArithmeticOnly',c.task_budget(20*G)['admitted']is True);ck('free20Minus1Rejects',c.task_budget(20*G-1)['admitted']is False)
for v in [True,-1,0.,'20']:
 try:c.task_budget(v);good=False
 except ValueError:good=True
 ck('freeWrongType'+repr(v),good)
for d in [60,90,1960]:
 p=c.journal_policy(d);t=c.transport_policy(d);ck('quota'+str(d),p.quota_bytes==(6*G if d==1960 else 384*M)and t.quota_bytes==(256*M if d==1960 else 32*M));ck('fsyncReserveBounds'+str(d),p.max_record_bytes==2048 and p.termination_reserve_bytes==16384 and t.termination_reserve_bytes==32768)
for d in [True,0,59,120,1800,1961,1960.,'1960']:
 try:c.journal_policy(d);good=False
 except ValueError:good=True
 ck('durationReject'+repr(d),good)
for name in ['receive','event','reject','close']:
 if hasattr(Accepted,name):ck('exactInherited'+name,getattr(FrameAdapter,name)is getattr(Accepted,name))
ck('onlyConstructorOverridden',{k for k,v in FrameAdapter.__dict__.items()if callable(v)}=={'__init__'})
ck('sharedGuardPolicyExact',DISK_POLICY==dict(version=2,entryBytes=20*G,floorBytes=10*G,reserveBytes=256*M,horizonNs=15000000000,samplePeriodNs=100000000,maximumCheckGapNs=2000000000,maximumSamples=192,requiresRealPriming=True,sampling='CADENCE_CAPPED_KEEP_WINDOW_BOUNDARY_PREDECESSOR',perWriteFloorAndForecast=True))
paths=[R/'pilot/betaintegrated01/cockpit04/capacity.py',R/'pilot/betaintegrated01/cockpit04/frame_adapter.py',R/'pilot/betaintegrated01/runtime02/frame_adapter.py',R/'pilot/betaintegrated01/runtime02/journal/admission.py',R/'pilot/betaintegrated01/runtime02/journal/writer.py'];r=dict(status='PASS'if all(t['pass_']for t in tests)else'FAIL',tests=tests,independentPeakBytes=sum(expected.values()),independentPeakGiB=sum(expected.values())/G,budget=b,sourceSHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths},scope='Pure integer policy/source method identity only; no actual DiskGuardprime/socket/runtime/30minute claim',admissionLimit='Every later newjournal still needs actual20GiB constructorentry. This arithmetic does not guarantee latercase entry or30minute capacity.',externalEnforcement='Root must enforce cumulative exports/caseledger/AVD growth+metadata/unit; APFS st_blocks is monitoring not exact physicalquota. Actual perwrite dfguard authoritative.',servicesStarted=0);(O/'results.json').open('x').write(json.dumps(r,indent=2));print(r['status'],len(tests),r['independentPeakGiB'])
