"""Pure semantic validation for retained pre-candidate input admission outcomes."""
import math,re
from .native_chain_json import strict_json
TTL=200_000_000
CTX={'run','epoch','boot','generation','operator','profileId'}
INVALID={'context','source','clockDomain','provenance','sequence','uptimeNs','elapsedNs','lastMotionUptimeNs','axes','pointers','motionAction','release','inputObservation'}
FIELDS={'reason','reasonClass','sequence','atNs','invalidInput','fullInvalidInputRetained','phase','disposition','priorLeaseId','priorExpiryNs','authorityRestorable'}
OBS={'kind','uiHeartbeatElapsedNs','touchRevision','samplerThreadId','uiThreadId','viewEpoch','releaseFence'}
REASONS={'INPUT_SAMPLE_EXPIRED','UI_OBSERVATION_EXPIRED','PRIOR_LEASE_EXPIRED_BEFORE_CANCEL_CHECK'}

def fail(s):raise ValueError('ADMISSION13:'+s)
def need(x,s):
 if not x:fail(s)
def integer(x,minimum=0):need(type(x)is int and minimum<=x<2**63,'INTEGER');return x

def _shape(i,expected,source,provenance,now,floor,latest):
 if i is None:return 'INPUT_CONTEXT_SEQUENCE_CLOCK_OR_AGE'
 if not(type(i.get('context'))is dict and i['context']=={k:expected[k]for k in CTX}and i.get('source')==source and i.get('provenance')==provenance and i.get('clockDomain')=='ANDROID_UPTIME_NS_SAMPLER'and type(i.get('sequence'))is int and i['sequence']>=0 and i['sequence']>floor and all(type(i.get(k))is int for k in('uptimeNs','elapsedNs','lastMotionUptimeNs','pointers','motionAction'))and i['uptimeNs']>=0 and(latest is None or i['uptimeNs']>=latest['uptimeNs'])and i['elapsedNs']>=0 and i['uptimeNs']<=i['elapsedNs']<=now and 0<=i['lastMotionUptimeNs']<=i['uptimeNs']and type(i['axes'])is list and len(i['axes'])==4 and 0<=i['pointers']<=2 and i['motionAction']in(-1,0,1,2,3,5,6)and type(i['release'])is bool):return 'INPUT_CONTEXT_SEQUENCE_CLOCK_OR_AGE'
 if any(type(x)not in(int,float)or not math.isfinite(x)or not -1<=x<=1 for x in i['axes']):return 'INPUT_AXIS_DOMAIN'
 if i['pointers']==0 and any(x!=0 for x in i['axes']):return 'UNHELD_NONZERO_AXES'
 if i['motionAction']==-1 and(i['pointers']!=0 or i['lastMotionUptimeNs']!=0 or i['release']):return 'NO_MOTION_STATE_INVALID'
 if i['motionAction']in(0,2,5)and i['pointers']==0:return 'ACTIVE_MOTION_WITHOUT_POINTER'
 if i['motionAction']in(1,3,6)and i['pointers']!=0:return 'RELEASE_MOTION_WITH_ACTIVE_POINTER'
 if i['release']and i['motionAction']not in(1,3,6):return 'RELEASE_WITHOUT_UP_CANCEL'
 o=i['inputObservation']
 if o is None:return 'SELECTED_SAMPLER_OBSERVATION_REQUIRED'
 if type(o)is not dict or set(o)!=OBS:return 'SAMPLER_OBSERVATION_FIELDS'
 if any(type(o[k])is not int or o[k]<0 for k in OBS-{'kind'}):return 'SAMPLER_OBSERVATION_TYPES'
 if o['kind']!='IMMUTABLE_UI_TOUCH_STATE_SAMPLE_NOT_NEW_MOTION_EVENT'or o['uiHeartbeatElapsedNs']>i['elapsedNs']or o['samplerThreadId']==o['uiThreadId']or o['samplerThreadId']<=0 or o['uiThreadId']<=0 or o['viewEpoch']<=0:return 'UI_LIVENESS_OR_SAMPLER_CONTEXT_STALE'
 if latest is not None and abs((i['elapsedNs']-i['uptimeNs'])-(latest['elapsedNs']-latest['uptimeNs']))>5_000_000:return 'GUEST_UPTIME_ELAPSED_OFFSET_STEP'
 return None

def validate(v,row_ns,expected,source,provenance,lease,expiry,last_floor,latest,last_decision,failed=False,known_release_fence=0,known_notices=()):
 need(type(v)is dict and set(v)in(FIELDS,FIELDS|{'commitReceipt'}),'SCHEMA')
 need(v['fullInvalidInputRetained']is True and v['phase']=='PRE_CANDIDATE'and v['authorityRestorable']is False,'DISPOSITION_SCOPE')
 at=integer(v['atNs']);need(at<=row_ns,'ORIGINAL_PRECHECK_CLOCK')
 need(type(v['reason'])is str and 1<=len(v['reason'])<=512 and type(v['reasonClass'])is str and 1<=len(v['reasonClass'])<=128,'REASON')
 need(type(v['priorExpiryNs'])is int and v['priorExpiryNs']==expiry and v['priorLeaseId']==lease and(v['priorLeaseId']is None or type(v['priorLeaseId'])is str),'PRIOR_AUTHORITY')
 i=v['invalidInput'];need(i is None or type(i)is dict and set(i)==INVALID,'FULL_INVALID_INPUT_SCHEMA')
 if i is not None:
  need(i['context']is None or type(i['context'])is dict and set(i['context'])==CTX and all(type(x)is str and 1<=len(x)<=128 for x in i['context'].values()),'RETAINED_CONTEXT_TYPES')
  need(all(i[k]is None or type(i[k])is str and len(i[k])<=128 for k in('source','clockDomain','provenance')),'RETAINED_STRING_TYPES')
  for k in('sequence','uptimeNs','elapsedNs','lastMotionUptimeNs'):need(type(i[k])is int and -2**63<=i[k]<2**63,'RETAINED_LONG_TYPES')
  for k in('pointers','motionAction'):need(type(i[k])is int and -2**31<=i[k]<2**31,'RETAINED_INT_TYPES')
  need(type(i['release'])is bool and(i['inputObservation']is None or type(i['inputObservation'])is dict),'RETAINED_BOOLEAN_OBSERVATION_TYPES')
  need(i['axes']is None or type(i['axes'])is list and len(i['axes'])<=8 and all(type(x)in(int,float)and math.isfinite(x)or type(x)is str and x in('NaN','Infinity','-Infinity')for x in i['axes']),'RETAINED_AXES_BOUND_AND_ENCODING')
 need(v['sequence']is None if i is None else type(v['sequence'])is int and v['sequence']==i['sequence'],'RETAINED_SEQUENCE')
 shape=_shape(i,expected,source,provenance,at,last_floor,latest)
 if v['disposition']=='EXPIRED_NO_AUTHORITY':
  need(v['reasonClass']=='AdmissionExpiry'and v['reason']in REASONS and shape is None and not failed and at>=last_decision,'TYPED_VALID_SHAPE_EXPIRY_ONLY')
  need(type(expected.get('expectedViewEpoch'))is int and i['inputObservation']['viewEpoch']==expected['expectedViewEpoch'],'SELECTED_PROVIDER_UI_EPOCH')
  observation=i['inputObservation'];old=observation['releaseFence'];need(0<=old<=known_release_fence and known_release_fence-old<=16,'KNOWN_RELEASE_FENCE_CONTEXT')
  target=old
  for item in known_notices:
   notice=item.get('value',item)
   if notice['oldFence']>=old:
    need(notice['oldFence']==target and notice['uiThreadId']==observation['uiThreadId']and notice['touchRevision']>observation['touchRevision'],'RELEASE_HISTORY_STRUCTURAL_CONTEXT');target=notice['newFence']
  need(target==known_release_fence,'KNOWN_RELEASE_HISTORY_REQUIRED')
  sample=i['elapsedNs'];ui=i['inputObservation']['uiHeartbeatElapsedNs']
  reason='INPUT_SAMPLE_EXPIRED'if at-sample>TTL else'UI_OBSERVATION_EXPIRED'if at-ui>TTL else'PRIOR_LEASE_EXPIRED_BEFORE_CANCEL_CHECK'if lease is not None and at>expiry else None
  need(v['reason']==reason,'EXPIRY_PREDICATE_OR_ORDER')
 elif v['disposition']=='INVALID_FATAL':
  need(v['reasonClass']in('IllegalArgumentException','IllegalStateException','IOException'),'GENERIC_REASON_CLASS')
  reason='AUTHORITY_FAILED_OR_CLOCK'if failed or at<last_decision else shape
  selectedContextInvalid=i is not None and(type(i.get('inputObservation'))is not dict or type(expected.get('expectedViewEpoch'))is int and i['inputObservation'].get('viewEpoch')!=expected['expectedViewEpoch'])
  sourceContextProven=v['reasonClass']=='IOException'and v['reason']=='SELECTED_SAMPLER_CONTEXT_RELEASE_FENCE_REQUIRED'and selectedContextInvalid
  need(sourceContextProven or reason is not None and v['reason']==reason,'GENERIC_REJECTION_REASON_NOT_PROVEN')
 else:fail('UNKNOWN_DISPOSITION')
 return i
