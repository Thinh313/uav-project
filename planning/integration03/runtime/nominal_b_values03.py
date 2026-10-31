"""Payload-only B controls while Android A owns flight; one intent each, no retries."""
from b_rpc import call,state
import time
s=state();v=s['state'];assert s['connected'] and s['authenticated'] and v['self']['joined'];core=next(x['coreSid'] for x in v['stations'] if x['session']==v['self']['session']);assert next(p for p in v['payloads'] if p['id']=='front')['cameraOwnerSid']==core,'SAME_CONSENT_FRONT_OWNERSHIP_REQUIRED'
seq=[('focus','camera:front',28,0,None),('zoom','camera:front',36,0,None),('focus','camera:front',58,0,None),('zoom','camera:front',81,0,None),('capture','camera:front',0,0,None),('claim','camera:center',0,0,None),('zoom','camera:center',58,0,None),('capture','camera:center',0,0,None),('focus','camera:center',50,0,'FOCUS_CAPABILITY_REQUIRED'),('claim','camera:rear',0,0,None),('capture','camera:rear',0,0,None),('zoom','camera:rear',30,0,'ZOOM_CAPABILITY_REQUIRED'),('claim','gimbal:center',0,0,None),('gimbal','gimbal:center',-33,78,None),('authority','gimbal:center',0,0,'AMBIGUOUS_ACK_KEY_FENCED_FOR_GENERATION')]
for op,res,a,b,error in seq:
 call('action',{'operation':op,'resource':res,'a':a,'b':b,'to':''},error);time.sleep(.35)
print('DECLARED_B_VALUES_AND_CAPABILITY_NEGATIVES_COMPLETE_VERIFY_RAW')
