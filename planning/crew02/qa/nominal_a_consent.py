from ui01 import *
owned();run=sys.argv[1];tap01('payload');select01('crew-resource','Gimbal');tap01('op-claim');tap01('op-manager');tap01('op-send-gimbal');capture(run+'-a-device1-requested-and-sent');select01('crew-resource','Camera');tap01('op-claim');tap01('op-transfer');capture(run+'-a-camera-proposal-for-b');print('A_GIMBAL_INTENT_AND_FRONT_CONSENT_PROPOSAL_SENT_VERIFY_RAW',flush=True)
