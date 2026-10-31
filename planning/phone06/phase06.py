"""Resource/source declaration, not a cryptographic simulator or safety attestation."""
from pathlib import Path
import json,hashlib,time,re,shutil,datetime
R=Path(__file__).resolve().parents[2];AP_SHA='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'
def unique(pairs):
 q={}
 for k,v in pairs:
  if k in q:raise ValueError('DUPLICATE_JSON_KEY')
  q[k]=v
 return q
def read_json(p,limit=65536):
 p=Path(p)
 if p.is_symlink()or not p.is_file()or not 1<=p.stat().st_size<=limit:raise ValueError('PHONE_JSON_FILE_BOUND')
 return json.loads(p.read_text(),object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in()).throw(ValueError(v)))
def pin(relative,expected,limit):
 p=(R/relative).resolve()
 if not p.is_relative_to(R)or p.is_symlink()or not p.is_file()or p.stat().st_size>limit or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError('PHONE_PHASE_PIN:'+str(relative))
 return p
def validate_phase(path,require_resource=True):
 q=read_json(path);now=time.time();start=datetime.datetime.fromisoformat(q['issuedAt']).timestamp();end=datetime.datetime.fromisoformat(q['expiresAt']).timestamp()
 if q.get('format')!='aeris-phone06-phase-admission'or q.get('status')!='PHASE_ADMITTED'or not start<=now<end or not 0<end-start<=3600 or q.get('package')!='vn.rtr.aeris.phone06'or q.get('binarySha256')!=AP_SHA:raise ValueError('PHONE_PHASE_CONTEXT')
 runs=q['allowedRuns']
 if not isinstance(runs,list)or not 1<=len(runs)<=3 or len(set(runs))!=len(runs)or any(not re.fullmatch('s[a-f0-9]{20}',x)for x in runs):raise ValueError('PHONE_PHASE_RUN_BUDGET')
 if not re.fullmatch('[A-Za-z0-9._-]{1,128}',q['selectedSerial'])or q['selectedSerial'].startswith('emulator-')or q.get('manualActualQualified')is not False or q.get('qualificationIssuance')!='UNSUPPORTED_PENDING_ACTUAL_PROOF':raise ValueError('PHONE_PHYSICAL_SERIAL_OR_QUALIFICATION')
 if q.get('runtimeGuardBytes')!=21*2**30 or q.get('minAdmissionBytes',0)<22*2**30 or q.get('remainingForecastBytes',-1)<0 or q.get('reserveBytes',0)<2**30 or q['minAdmissionBytes']<20*2**30+q['remainingForecastBytes']+q['reserveBytes']:raise ValueError('PHONE_PHASE_RESOURCE_BUDGET')
 if require_resource and shutil.disk_usage(R).free<q['minAdmissionBytes']:raise ValueError('PHONE_PHASE_FREE_DISK')
 apk=q['apk'];pin(apk['path'],apk['sha256'],12*2**20);build=read_json(R/q['buildReceipt']);
 if build['sha256']!=apk['sha256']or build['sourceId']!=q['nativeSourceId']:raise ValueError('PHONE_PHASE_BUILD_BINDING')
 pin('runtime/sitl/arducopter',AP_SHA,100*2**20)
 return q
