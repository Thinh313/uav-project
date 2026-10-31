"""Pure original-tuple admission predicates; declared synthetic clocks/context."""
from pathlib import Path
from importlib import import_module
import copy,json,hashlib
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-clockterm14.flight';A=import_module(H+'.input_admission');E=R/'evidence/betaintegrated01-cockpit05-clockterm14/host'
def main():
 ctx={k:k for k in A.CTX};expected={**ctx,'expectedViewEpoch':1};source='touch-00000000-0000-0000-0000-000000000000';provenance='ROOT_INJECTED_ANDROID_TOUCH';latest=dict(sequence=50,elapsedNs=780_000_000,uptimeNs=780_000_000)
 original=dict(context=ctx,source=source,clockDomain='ANDROID_UPTIME_NS_SAMPLER',provenance=provenance,sequence=51,uptimeNs=800_000_000,elapsedNs=800_000_000,lastMotionUptimeNs=0,axes=[0,0,0,0],pointers=0,motionAction=-1,release=False,inputObservation=dict(kind='IMMUTABLE_UI_TOUCH_STATE_SAMPLE_NOT_NEW_MOTION_EVENT',uiHeartbeatElapsedNs=750_000_000,touchRevision=0,samplerThreadId=2,uiThreadId=1,viewEpoch=1,releaseFence=0))
 v=dict(reason='UI_OBSERVATION_EXPIRED',reasonClass='AdmissionExpiry',sequence=51,atNs=990_000_000,invalidInput=original,fullInvalidInputRetained=True,phase='PRE_CANDIDATE',disposition='EXPIRED_NO_AUTHORITY',priorLeaseId='lease-1-consent',priorExpiryNs=980_000_000,authorityRestorable=False)
 cases=[]
 def validate(value):return A.validate(value,991_000_000,expected,source,provenance,'lease-1-consent',980_000_000,50,latest,900_000_000)
 def check(name,value,ok=True):
  err=None
  try:validate(value);accepted=True
  except Exception as e:accepted=False;err=type(e).__name__+':'+str(e)
  cases.append(dict(case=name,expected=ok,accepted=accepted,error=err));assert accepted is ok,(name,err)
 before=json.dumps(v,sort_keys=True);check('old_queue_ui_expiry_even_newer_current_ui_exists_not_substituted',v);assert json.dumps(v,sort_keys=True)==before
 for name,key,value in [('wrong_reason_order','reason','PRIOR_LEASE_EXPIRED_BEFORE_CANCEL_CHECK'),('wrong_reason_class','reasonClass','IllegalStateException'),('pretend_fatal_expiry','disposition','INVALID_FATAL'),('missing_full_tuple','invalidInput',None),('wrong_sequence','sequence',52),('bool_sequence','sequence',True),('wrong_prior_lease','priorLeaseId',None),('wrong_prior_expiry','priorExpiryNs',-1),('retimed_precheck','atNs',700_000_000),('missing_retention','fullInvalidInputRetained',False),('auto_authority','authorityRestorable',True)]:
  bad=copy.deepcopy(v);bad[key]=value;check(name,bad,False)
 bad=copy.deepcopy(v);bad['invalidInput']['axes'][0]=2;check('invalid_shape_not_typedexpiry',bad,False)
 bad=copy.deepcopy(v);bad['invalidInput']['sequence']=bad['sequence']=50;check('replayed_sample_not_typedexpiry',bad,False)
 bad=copy.deepcopy(v);bad['invalidInput']['elapsedNs']=bad['invalidInput']['uptimeNs']=780_000_000;bad['reason']='INPUT_SAMPLE_EXPIRED';check('sample_expiry_precedes_ui_expiry',bad)
 bad=copy.deepcopy(v);bad['invalidInput']['elapsedNs']=bad['invalidInput']['uptimeNs']=950_000_000;bad['invalidInput']['inputObservation']['uiHeartbeatElapsedNs']=940_000_000;bad['reason']='PRIOR_LEASE_EXPIRED_BEFORE_CANCEL_CHECK';check('fresh_sample_ui_cannot_renew_expired_priorlease',bad)
 bad=copy.deepcopy(v);bad['invalidInput']['axes'][0]=2;bad.update(disposition='INVALID_FATAL',reasonClass='IllegalArgumentException',reason='INPUT_AXIS_DOMAIN');check('actual_invalid_axes_is_fatal_not_safeexpiry',bad)
 bad=copy.deepcopy(v);bad.update(disposition='INVALID_FATAL',reasonClass='IOException',reason='UNPROVEN_RELEASE_FENCE_CHANGE');check('unverifiable_generic_fence_reason_not_accepted_from_string',bad,False)
 result=dict(status='PASS_ORIGINAL_TUPLE_ADMISSION_PREDICATES_ONLY',cases=cases,provenance='SYNTHETIC_ORIGINAL_QUEUE_SAMPLE_UI_AND_PRIOR_LEASE_CLOCKS_NOT_ANDROID_OR_GROUP_FSYNCS',sourceSHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[Path(__file__),Path(A.__file__)]},newerHeartbeatSubstituted=False,originalInputMutated=False,runtimeExecuted=False,deviceCommands=False,strictWholeClosedNativeProjectionRequiredSeparately=True)
 (E/'admission-unit03.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=len(cases))))
if __name__=='__main__':main()
