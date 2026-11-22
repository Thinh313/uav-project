"""Source-bound gate prerequisites. Metadata validates bindings, not raw truth.
Only Root can issue acceptance after independent complete original replay.
"""
from pathlib import Path
import hashlib,json,re
from .paths import repository
from .mission16 import common_bindings
from .rc01 import need
CASE_GATES={'native':'G1','polygon':'G2','corridor':'G2','link-loss':'G3','ap-reboot':'G3','native-restart':'G3','integrated':'G4'}
PREREQUISITES={'native':set(),'polygon':{'native'},'corridor':{'native'},'link-loss':{'native','polygon','corridor'},'ap-reboot':{'native','polygon','corridor'},'native-restart':{'native','polygon','corridor'},'integrated':{'native','polygon','corridor','link-loss','ap-reboot','native-restart'}}

def original_ref(ref,scope):
 need(type(ref)is dict and set(ref)=={'role','path','bytes','sha256'}and type(ref['role'])is str and 0<len(ref['role'])<=64 and type(ref['path'])is str and type(ref['bytes'])is int and 0<ref['bytes']<=512*2**20 and re.fullmatch('[a-f0-9]{64}',ref['sha256']),'GATE_ORIGINAL_REF_SCHEMA');p=Path(ref['path']);need(not p.is_absolute()and '..'not in p.parts,'GATE_ORIGINAL_RELATIVE');p=repository()/p;need(p.is_relative_to(scope)and not any(x.is_symlink()for x in[p,*p.parents])and p.is_file()and p.stat().st_size==ref['bytes'],'GATE_ORIGINAL_SCOPE');h=hashlib.sha256()
 with p.open('rb')as stream:
  for block in iter(lambda:stream.read(65536),b''):h.update(block)
 need(h.hexdigest()==ref['sha256'],'GATE_ORIGINAL_SHA');return str(p)
def read_gate(path,digest,manifest,candidate):
 p=Path(path).absolute();scope=repository()/'evidence/betarc01';need(p.is_relative_to(scope)and p.is_file()and not any(x.is_symlink()for x in[p,*p.parents])and 0<p.stat().st_size<=32768 and re.fullmatch('[a-f0-9]{64}',digest),'GATE_METADATA_SCOPE');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==digest,'GATE_METADATA_SHA');q=json.loads(raw);kind=q.get('caseKind');need(q.get('format')=='aeris-betarc01-root-gate-acceptance'and type(q.get('version'))is int and q['version']==1 and q.get('status')=='ROOT_COLD_VERIFIED'and kind in CASE_GATES and q.get('gate')==CASE_GATES[kind]and q.get('candidateSHA256')==candidate and q.get('commonBindings')==common_bindings(manifest)and q.get('authorityRestorable')is False and q.get('physicalHardwareAccepted')is False and q.get('allActorsClosed')is True,'GATE_METADATA_IDENTITY');refs=q.get('originalEvidence');need(type(refs)is list and 3<=len(refs)<=16 and len({r.get('role')for r in refs})==len(refs),'GATE_ORIGINAL_ROLES');paths=[original_ref(r,scope)for r in refs];need(len(set(paths))==len(paths),'GATE_ORIGINAL_PATH_UNIQUE')
 if kind in('link-loss','ap-reboot','native-restart'):need(q.get('expectedInterruption')is True and q.get('normalMissionAccepted')is False and q.get('originalFaultObserved')is True and q.get('authorityRevoked')is True and q.get('interruptedReviewPreserved')is True,'GATE_REAL_FAULT_NOT_NORMAL_FLIGHT')
 elif kind in('polygon','corridor','integrated'):need(q.get('expectedInterruption')is False and q.get('normalMissionAccepted')is True and q.get('videoPayloadSameFlight')is True and q.get('actualSAFBytesVerified')is True,'GATE_COMPLETE_SAME_RUN_FLIGHT')
 else:need(q.get('expectedInterruption')is False and q.get('normalMissionAccepted')is False and q.get('nativeOnly')is True and q.get('twoOriginalNativeSessionsVerified')is True,'GATE_G1_NOT_FLIGHT')
 if kind=='ap-reboot':
  fresh=[r for r in refs if r['role']=='new-ap-observation'];need(len(fresh)==1 and fresh[0]['bytes']<=32768,'GATE_AP_REBOOT_SEPARATE_NEW_CONTEXT_OBSERVATION');observation=json.loads((repository()/fresh[0]['path']).read_bytes());prior=observation.get('oldContext');current=observation.get('newContext');need(observation.get('format')=='aeris-betarc01-readonly-new-ap-observation'and observation.get('candidateSHA256')==candidate and type(prior)is dict and type(current)is dict and prior.get('run')!=current.get('run')and prior.get('boot')!=current.get('boot')and observation.get('oldFailurePreserved')is True and observation.get('nativeActivityStarted')is False and observation.get('flightAuthorityGranted')is False and type(observation.get('observedActualAPBootMs'))is int and observation['observedActualAPBootMs']>=0 and type(observation.get('originalCRCHeartbeat'))is dict and type(observation.get('originalCRCGlobalPositionWithBootMs'))is dict,'GATE_AP_REBOOT_ACTUAL_CRC_BOOT_NOT_ROOT_LABEL')
 if kind=='integrated':need(type(q.get('continuousAirborneIntegratedNs'))is int and q['continuousAirborneIntegratedNs']>=600_000_000_000 and q.get('durationFromColdOriginals')is True,'GATE_G4_600_ORIGINAL_AIRBORNE_NOT_IDLE')
 return q

def require_prerequisites(kind,refs,manifest,candidate):
 need(kind in PREREQUISITES and type(refs)is list and len(refs)<=7,'GATE_FINITE_PREREQUISITES');rows={}
 for ref in refs:
  need(type(ref)is str and '#'in ref,'GATE_ARGUMENT_PATH_HASH');path,digest=ref.rsplit('#',1);q=read_gate(path,digest,manifest,candidate);need(q['caseKind']not in rows,'GATE_DUPLICATE_KIND');rows[q['caseKind']]=q
 need(PREREQUISITES[kind]<=set(rows),'GATE_MISSING_PREREQUISITES_'+','.join(sorted(PREREQUISITES[kind]-set(rows))));return {'status':'SOURCE_BOUND_GATE_METADATA_AND_ORIGINAL_HASHES_CHECKED_NOT_INDEPENDENT_REPLAY','required':sorted(PREREQUISITES[kind]),'observed':sorted(rows),'authorityGranted':False}

def verify_complete_release(refs,manifest,candidate):
 require_prerequisites('integrated',refs,manifest,candidate);kinds=set()
 for ref in refs:
  path,digest=ref.rsplit('#',1);kinds.add(read_gate(path,digest,manifest,candidate)['caseKind'])
 need(kinds==set(CASE_GATES),'FINAL_RELEASE_ALL_SEVEN_CASES_SAME_RELEASE');return {'status':'ALL_GATE_METADATA_ORIGINAL_HASHES_VALIDATED_ROOT_RAW_ACCEPTANCE_STILL_REQUIRED','candidateSHA256':candidate,'caseKinds':sorted(kinds),'flightAuthorityGranted':False,'physicalHardwareAccepted':False}
