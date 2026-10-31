from b_rpc import call
import time
# Public BAPI functional intents, no host flight command. Caller has fresh explicit JOIN.
seq=[('capture','camera:front',0,0,'EXCLUSIVE_OWNER_NO_TRANSFER_REQUIRED'),('claim','camera:front',0,0,None),('focus','camera:front',28,0,None),('zoom','camera:front',36,0,None),('focus','camera:front',58,0,None),('zoom','camera:front',81,0,None),('capture','camera:front',0,0,None),('claim','camera:center',0,0,None),('zoom','camera:center',58,0,None),('capture','camera:center',0,0,None),('focus','camera:center',50,0,'FOCUS_CAPABILITY_REQUIRED'),('claim','camera:rear',0,0,None),('capture','camera:rear',0,0,None),('zoom','camera:rear',30,0,'ZOOM_CAPABILITY_REQUIRED'),('claim','gimbal:center',0,0,None),('gimbal','gimbal:center',-57,72,None),('authority','gimbal:center',0,0,'AMBIGUOUS_ACK_KEY_FENCED_FOR_GENERATION'),('gimbal','gimbal:front',-57,72,'EXCLUSIVE_OWNER_NO_TRANSFER_REQUIRED')]
for op,res,a,b,error in seq:
 call('action',{'operation':op,'resource':res,'a':a,'b':b,'to':''},error);time.sleep(.35)
print('EXPLICIT_FROZEN_VALUES_AND_CAPABILITY_NEGATIVES_COMPLETE')
