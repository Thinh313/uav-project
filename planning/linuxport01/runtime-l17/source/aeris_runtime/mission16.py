"""Closed nominal slots and cold metadata prerequisite. Grants no flight authority.
Root independently verifies original raw/signatures before creating this receipt.
This gate only checks its exact source/byte bindings; it is not that verifier.
"""
from pathlib import Path
import hashlib,json,re
SLOTS={'m907':180,'m908':180,'g109':180,'m905':180,'m906':180,'g108':180,'m803':180,'m903':180,'m904':180,'g107':180,'m802':180,'m901':180,'m902':180,'g106':180,'m801':180,'m601':180,'m602':180,'g105':180,'m701':180,'m702':180,'m501':180,'m502':180,'g104':180,'m401':180,'m402':180,'m301':180,'m302':180,'g103':180,'m303':180,'r301':180,'r302':180,'m101':180,'m102':180,'m201':180,'m202':180,'g101':180,'g102':180,'g201':180,'g202':180,'g203':180,'g204':180,'g301':180,'g302':180,'g303':180,'g304':180,'g401':760,'g402':760}
ROLES={'ownerterminal','case','guardian','productseal','fullraw','video','saf'}

def need(value,name):
 if not value:raise ValueError('MISSION16_'+name)
def nominal_duration(slot,seconds):
 need(type(seconds)is int and slot in SLOTS and SLOTS[slot]==seconds,'NOMINAL_SLOT_DURATION_OR_UNIMPLEMENTED_FAULT')
 return seconds
def common_bindings(manifest):
 source=manifest['sourceSHA256'];external=manifest['externalFrozenSHA256'];native=manifest['native']
 return {'nativeAPK':native['APK_SHA256'],'nativeSource':native['sourceSHA256'],'AP':external['runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03'],'physicsModel':external['pilot/betaintegrated01/runtime/physics.py'],'backend':source['aeris_runtime/backend.py'],'workbenchProfile':source['aeris_runtime/assets/workbench-profiles/nominal/typed-profile.json'],'controlProfile':source['aeris_runtime/assets/workbench-profiles/nominal/control.parm'],'mediaSelection':source['aeris_runtime/assets/media-engineering-selection.json']}
def _decode(raw):
 def pairs(items):
  out={}
  for k,v in items:
   need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in()).throw(ValueError('MISSION16_NONFINITE_JSON')))
def verify_short(path,digest,manifest,candidate,repo):
 need(type(path)is str and type(digest)is str and re.fullmatch('[a-f0-9]{64}',digest),'SHORT_REFERENCE_REQUIRED')
 repo=Path(repo).resolve();scope=repo/'evidence/betarc01';p=Path(path).absolute()
 need(not any(v.is_symlink()for v in[p,*p.parents])and p.is_file()and p.resolve().is_relative_to(scope)and 0<p.stat().st_size<=32768,'SHORT_RECEIPT_BOUND_SCOPE')
 raw=p.read_bytes();need(len(raw)<=32768 and hashlib.sha256(raw).hexdigest()==digest,'SHORT_RECEIPT_SHA');v=_decode(raw)
 need(type(v)is dict and v.get('format')=='aeris-independent-missionintegrated16-short-acceptance'and type(v.get('version'))is int and v['version']==1 and v.get('status')=='ROOT_VERIFIED_NOMINAL_ANDROID_SITL_SHORT'and v.get('candidateSHA256')==candidate and v.get('profileId')=='WORKBENCH_SIM_V1'and v.get('simulationOnly')is True,'SHORT_IDENTITY')
 need(v.get('slot')in('g201','g202','g203','g204')and type(v.get('maximumSeconds'))is int and v['maximumSeconds']==180 and v.get('expectedFault')is False and v.get('recordingStatus')=='COMPLETE_RECORDING','SHORT_NOMINAL_NOT_DIAGNOSTIC')
 need(all(v.get(k)is True for k in('normalManagedClosed','actualSignedInput','videoPayload','SAFImport','allActorsClosed')),'SHORT_ACCEPTANCE_CLAIMS')
 need(v.get('commonBindings')==common_bindings(manifest),'SHORT_COMMON_IMMUTABLE_BINDINGS')
 context=v.get('context');from .lifecycle import Context
 need(type(context)is dict and Context(**context).value()==context,'SHORT_CONTEXT')
 originals={}
 refs=v.get('originalEvidence');need(type(refs)is list and 7<=len(refs)<=16,'SHORT_REFERENCE_COUNT');seen=set();roles=set();total=0
 for ref in refs:
  need(type(ref)is dict and set(ref)=={'role','path','bytes','sha256'}and ref['role']in ROLES and type(ref['path'])is str and type(ref['bytes'])is int and 0<ref['bytes']<=512*2**20 and type(ref['sha256'])is str and re.fullmatch('[a-f0-9]{64}',ref['sha256']),'SHORT_REFERENCE_SCHEMA')
  relative=Path(ref['path']);need(not relative.is_absolute()and '..'not in relative.parts and str(relative)not in seen,'SHORT_REFERENCE_PATH');seen.add(str(relative));need(ref['role']not in roles,'SHORT_ONE_REFERENCE_PER_ROLE');roles.add(ref['role']);original=repo/relative
  need(original.is_relative_to(scope/v['slot'])and not any(z.is_symlink()for z in[original,*original.parents])and original.is_file()and original.stat().st_size==ref['bytes'],'SHORT_ORIGINAL_SCOPE_BYTES')
  h=hashlib.sha256()
  with original.open('rb')as stream:
   for chunk in iter(lambda:stream.read(65536),b''):h.update(chunk)
  need(h.hexdigest()==ref['sha256'],'SHORT_ORIGINAL_SHA');total+=ref['bytes'];need(total<=1024*2**20,'SHORT_ORIGINAL_TOTAL_BOUND')
  need(ref['bytes']<=1024*1024,'SHORT_JSON_REFERENCE_BOUND');originals[ref['role']]=_decode(original.read_bytes());need(type(originals[ref['role']])is dict,'SHORT_ORIGINAL_JSON_OBJECT')
  if ref['role']=='ownerterminal':
   need(ref['bytes']<=4096,'SHORT_TERMINAL_BOUND');t=_decode(original.read_bytes());need(t.get('status')=='UI_WORKLOAD_CLOSED_AWAITING_INDEPENDENT_BETA_ACCEPTANCE'and t.get('candidateSHA256')==candidate and t.get('normalCompletedClosureClaimed')is True and t.get('flightAcceptance')is False,'SHORT_NORMAL_TERMINAL_NOT_FAILED_DISPOSAL')
 need(roles==ROLES,'SHORT_ALL_ORIGINAL_ROLES_REQUIRED')
 _roles(originals,context,candidate,next(ref['sha256']for ref in refs if ref['role']=='fullraw'))
 return {'status':'SOURCE_BOUND_SHORT_METADATA_AND_ORIGINAL_REFS_VALIDATED_NOT_RAW_ACCEPTANCE','receiptSHA256':digest,'sourceSlot':v['slot'],'authorityGranted':False}

def _roles(rows,context,candidate,fullraw_sha):
 seal=rows['productseal'];need(seal.get('format')=='aeris-root-verified-workbench-seal'and seal.get('candidateSHA256')==candidate and seal.get('runtimeContext')==context and all(seal.get(k)is True for k in('authorityRevoked','providerClosed','journalClosed','nominalOutcomeEligible'))and seal.get('flightAcceptance')is False,'SHORT_PRODUCT_SEAL_NOMINAL')
 case=rows['case'];need(case.get('status')=='CASE_MANAGED_CLOSED_AWAITING_INDEPENDENT_ACCEPTANCE'and case.get('flightAcceptance')is False and case.get('monitor',{}).get('durablyDrained')is True and case.get('resources',{}).get('workbenchSealProof')==seal,'SHORT_CASE_NORMAL_SEAL_JOIN')
 guardian=rows['guardian'];health=guardian.get('health')or{};audit=health.get('audit')or{};need(guardian.get('failure')is None and guardian.get('exit')==0 and type(guardian.get('exit'))is int and guardian.get('durablyDrained')is True and guardian.get('exceptionalPhysicalDisposal')is False and guardian.get('cleanupNotes')==[]and health.get('failure')is None and health.get('durablyDrained')is True and audit.get('durablyDrained')is True and audit.get('pendingRows')==0,'SHORT_GUARDIAN_CLEAN')
 raw=rows['fullraw'];need(raw.get('format')=='aeris-betasim-closed-raw-manifest'and type(raw.get('version'))is int and raw['version']==1 and raw.get('context')==context and raw.get('sourceCandidateSHA256')==candidate and raw.get('authorityRestorable')is False and raw.get('allOriginalRawAndAPStateIncluded')is True and raw.get('productSemanticAndMediaIncluded')is True and raw.get('closure',{}).get('workbenchSealProof')==seal,'SHORT_FULL_RAW_CONTEXT_CLOSURE')
 video=rows['video'];interval=video.get('originalFlightInterval')or{};need(video.get('format')=='aeris-integrated-video-qualification'and video.get('status')=='PASS'and video.get('authorityRestorable')is False and interval.get('proofKind')=='ROOT_COLD_JOIN_VERIFIED_FLIGHT_INTERVAL'and interval.get('run')==context['run']and interval.get('boot')==context['boot']and interval.get('missionSHA256')==seal.get('missionSHA256'),'SHORT_VIDEO_QUALIFIED_SAME_FLIGHT')
 saf=rows['saf'];need(saf.get('format')=='aeris-independent-recipient-byte-verification'and saf.get('status')=='RECIPIENT_BYTES_COMPLETE_NOT_FLIGHT_CERTIFICATION'and saf.get('sourceCandidateSHA256')==candidate and saf.get('originalRawComplete')is True and saf.get('documentBytesVerified')is True and saf.get('actualSAFBytesVerified')is True and saf.get('authorityRestorable')is False and saf.get('manifestSHA256')==fullraw_sha,'SHORT_ACTUAL_SAF_COMPLETE_MANIFEST_JOIN')
