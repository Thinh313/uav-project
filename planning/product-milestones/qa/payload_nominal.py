from ui01 import *
owned();run=sys.argv[1];out=E/'runs'/run;wait98(run,'TAKEOFF_GEOMETRY_OBSERVED',seconds=30)
tap01('payload');tap01('op-claim');tap01('op-manager')
for preset in ['oblique','nadir','horizon']:
 tap01('op-preset-'+preset);tap01('op-send-gimbal')
for step in ['minus','plus']:tap01('op-focus-'+step);tap01('op-send-focus')
tap01('op-close')
for _ in range(2):tap01('zoom-in');time.sleep(.3)
for _ in range(3):tap01('shutter');time.sleep(1.05)
s=state98(run);counts={op:sum(t['operation']==op and t['attempted']for t in s['transactions'])for op in ['capture','zoom','focus','gimbal']};assert all(counts[k]>=v for k,v in {'capture':3,'zoom':2,'focus':2,'gimbal':3}.items()),counts
capture(run+'-main-fly-repeated-controls');(out/'main-controls.json').open('x').write(json.dumps({'status':'PASS_COUNTS_NATIVE_RAW_PENDING_INDEPENDENT_RECEIVER','counts':counts,'state':s,'actualImages':0,'executionProven':False},indent=2));print(json.dumps(counts),flush=True)
tap01('payload');
s=state98(run)
if next(p for p in s['payloads']if p['id']=='front')['ownerSid'] is not None:tap01('op-release')
tap01('op-claim');tap01('op-transfer');select01('op-actor','Payload B');tap01('op-accept')
s=state98(run);owner=next(p for p in s['payloads']if p['id']=='front')['ownerSid'];assert next(a for a in s['stations']if a['sid']==owner)['actor']=='payload-b'
capture(run+'-explicit-handover-consent');tap01('op-close');tap01('shutter');time.sleep(.3);s=state98(run);assert any(t['payload']=='front'and t['operation']=='capture'and t['ownerSid']==owner and t['attempted']for t in s['transactions']);(out/'handover-ui.json').open('x').write(json.dumps({'status':'PASS_REAL_ANDROID_LOCAL_ROLE_HANDOVER','device2Proof':'SEPARATE_LOSS_GENERATION_REQUIRED','explicitRecipientConsent':True,'state':s,'notRemoteTwoOperatorProof':True},indent=2));print('EXPLICIT_HANDOVER_FROM_MAIN_FLY',flush=True)
