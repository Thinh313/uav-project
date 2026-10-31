"""Synthetic checkpoint contract mutants, no Android or original live ACK."""
from pathlib import Path
from importlib import import_module
import copy,json,hashlib
R=Path(__file__).resolve().parents[3];E=R/'evidence/betaintegrated01-cockpit05-clockterm14/host';C=import_module('planning.betaintegrated01.cockpit05-clockterm14.flight.checkpoint')
def raw(v):return json.dumps(v,separators=(',',':')).encode()
def main():
 c={k:k+'-mock'for k in C.CONTEXT};h=C.context_hash(c);anchor='a'*64;source='b'*64
 terminal={k:c[k]for k in('run','epoch','boot','generation')};terminal.update(format='aeris-control01-state',version=1,closed=True,authorityRestorable=False,journal=dict(run=c['run'],epoch=c['epoch'],records=10,head='e'*64,publicationAllowed=False,closed=True,failed=False,commitAnchor=anchor),input=dict(consent=False,leaseId=None,authorityRestorable=False));tr=raw(terminal)
 fields=dict(context=c,contextSHA256=h,ownerIdentity=c['run']+':'+c['generation'],APKSourceSHA256=source,terminalSHA256=C.sha(tr),terminalAnchor=anchor,canonicalPath=C.CANONICAL,archivePath='files/checkpoint14/terminal-'+h+'.json',serial=1,reviewStatus='DURABLE',reviewSHA256='d'*64,authorityRestorable=False)
 status=dict(fields,format='aeris-terminal-checkpoint14-status',version=1,phase='CANDIDATE_COMMIT',scope='CANDIDATE_ONLY_REQUIRE_LATER_LIVE_ACK',history=[{k:fields[k]for k in('context','contextSHA256','ownerIdentity','APKSourceSHA256','terminalSHA256','terminalAnchor','reviewStatus','reviewSHA256')}]);sr=raw(status)
 ack=dict(fields,format='aeris-terminal-checkpoint14-ack',version=1,phase='COMMITTED',statusSHA256=C.sha(sr),canonicalDurableNs=100,ackElapsedNs=101,failure=None)
 assert C.verify(ack,tr,sr,tr,c,source,observed_ns=102)['diskStatusIsPositiveACK']is False;tests=['SYNTHETIC_VALID_TUPLE']
 for key,value in [('phase','RECOVERED_NOT_LIVE_ACK'),('phase','READY'),('version',True),('ackElapsedNs',10**99),('failure','fault'),('ownerIdentity','foreign'),('APKSourceSHA256','e'*64),('contextSHA256','f'*64),('terminalSHA256','0'*64),('terminalAnchor','0'*64),('statusSHA256','0'*64),('reviewStatus','PENDING'),('reviewSHA256',None),('canonicalDurableNs',102),('canonicalDurableNs',True),('authorityRestorable',True),('serial',2)]:
  bad=copy.deepcopy(ack);bad[key]=value
  try:C.verify(bad,tr,sr,tr,c,source,observed_ns=102);raise AssertionError('ACCEPTED:'+key)
  except ValueError:tests.append('REJECT_'+key+'_'+str(value))
 for label,t,s,a in [('ARCHIVE_DIFFERENT',tr,sr,tr+b' '),('CANONICAL_MUTATED',tr+b' ',sr,tr),('STATUS_MUTATED',tr,sr+b' ',tr)]:
  try:C.verify(ack,t,s,a,c,source,observed_ns=102);raise AssertionError(label)
  except ValueError:tests.append('REJECT_'+label)
 files={'files/workspace03/draft.json':'1'*64,C.LOCK:C.sha(b''),C.STATUS:'2'*64};cls=C.classification(files);assert len(cls['immutable'])==1 and len(cls['mutableInfrastructure'])==2;C.preserved(files,{**files,C.STATUS:'3'*64});tests.append('MUTABLE_INFRASTRUCTURE_ACCOUNTED_NOT_IMMUTABLE')
 try:C.preserved(files,{C.LOCK:C.sha(b'')});raise AssertionError('lost mission accepted')
 except ValueError:tests.append('IMMUTABLE_MISSION_LOSS_REJECTED')
 try:C.classification({'files/checkpoint14/status.json.pending':'0'*64});raise AssertionError('pending accepted')
 except ValueError:tests.append('PENDING_NOT_HIDDEN')
 v=dict(status='PASS_SYNTHETIC_CHECKPOINT_CONTRACT',cases=tests,count=len(tests),provenance='ASSISTANT_AUTHORED_SYNTHETIC_TUPLES_NOT_NATIVE_HELPER_OR_DEVICE_ACK',actualDevice=False,sourceSHA256={str(Path(p).relative_to(R)):hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in(C.__file__,__file__)})
 (E/'checkpoint-contract04.json').open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(status=v['status'],count=len(tests))))
if __name__=='__main__':main()
