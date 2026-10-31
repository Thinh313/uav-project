"""Actual A touch proposal then B explicit consent and immediate same-session capture. No retry."""
from ui01 import *
from b_rpc import state,call
owned();run=sys.argv[1];assert re.fullmatch('s[a-f0-9]{20}',run);out=E/'runs'/run/'same-consent03.json';assert not out.exists();proof={'run':run,'automaticRetry':False,'error':None}
try:
 s=state();v=s['state'];assert s['connected'] and s['authenticated'] and v['phase']=='OPEN' and v['self']['joined'] and v['self']['alive'];bcore=next(x['coreSid'] for x in v['stations'] if x['session']==v['self']['session']);front=next(x for x in v['payloads'] if x['id']=='front');assert front['cameraOwnerSid'] is None and front['proposal'] is None,'EXPECT_UNOWNED_CAMERA_BEFORE_EXPLICIT_A_CLAIM';proof['before']=s
 tap01('payload');select01('op-target','Trước · 100');select01('crew-resource','Camera');tap01('op-claim');tap01('op-transfer')
 deadline=time.monotonic()+2
 while True:
  s=state();v=s['state'];front=next(x for x in v['payloads'] if x['id']=='front');proposal=front['proposal']
  if proposal and proposal['to']==bcore:break
  assert time.monotonic()<deadline,'NO_FRESH_PROPOSAL_NO_CONSENT';time.sleep(.03)
 proof['proposalObserved']=s;proof['acceptedProposalId']=proposal['id'];accepted=call('action',{'operation':'accept','resource':'camera:front','a':0,'b':0,'to':proposal['id']});front=next(x for x in accepted['state']['payloads'] if x['id']=='front');assert front['cameraOwnerSid']==bcore and front['proposal'] is None;proof['accepted']=accepted
 proof['capture']=call('action',{'operation':'capture','resource':'camera:front','a':0,'b':0,'to':''});assert proof['capture']['state']['self']['session']==accepted['state']['self']['session'];capture(run+'-same-consent-b-capture');tap01('op-close')
 print('EXPLICIT_A_TO_B_CONSENT_AND_SAME_SESSION_CAPTURE_VERIFY_RAW')
except BaseException as ex:proof['error']=repr(ex);raise
finally:out.open('x').write(json.dumps(proof,indent=2)+'\n')
