from ui97 import *
owned();run=current_run();checks=[]
def check(n,b):assert b,n;checks.append({'name':n,'pass':True});print(n,flush=True)
def st():return state(run)
def sent(op):return next((t for t in st()['transactions']if t['operation']==op and t['payload']=='front'),None)
try:
 tap97('discover97');time.sleep(.3);tap97('join-pilot-a');value97('value97',20);capture('gimbal07-value20');tap97('claim-pilot-a');tap97('authority-pilot-a');wait97(run,lambda p:any(k=='STATE'and any(t['operation']=='authority'and t['state']=='OBSERVATION_CONSISTENT_UNATTRIBUTED'for t in s['transactions'])for k,s in p));check('native manager authority response observed, not execution',sent('authority')['state']=='OBSERVATION_CONSISTENT_UNATTRIBUTED');tap97('gimbal-pilot-a');wait97(run,lambda p:any(k=='STATE'and any(t['operation']=='gimbal'and t['state']=='OBSERVATION_CONSISTENT_UNATTRIBUTED'for t in s['transactions'])for k,s in p));check('native gimbal1 angle feedback matches through AP',sent('gimbal')['state']=='OBSERVATION_CONSISTENT_UNATTRIBUTED');capture('gimbal07-consistent')
 choose97(1,'gimbal07-shared-manager');tap97('claim-pilot-a');before=len(st()['transactions']);n=len([s for k,s in parsed(run)if k=='REJECTED']);tap97('gimbal-pilot-a');wait97(run,lambda p:len([s for k,s in p if k=='REJECTED'])>n);check('shared manager device2 ACK ambiguity blocked before send',len(st()['transactions'])==before and 'AMBIGUOUS_ACK_KEY'in next(s for k,s in reversed(parsed(run))if k=='REJECTED')['error']);tap97('lose-pilot-a');check('operator loss removes every owned payload',all(p['ownerSid']is None for p in st()['payloads']));tap97('close97');capture('gimbal07-closed');check('native raw closed without authority restore',parsed(run)[-1][0]=='CLOSED')
except Exception as e:
 checks.append({'name':'driver','pass':False,'error':repr(e)});capture('gimbal07-driver-failure');raise
finally:(E/'gimbal07.json').open('x').write(json.dumps({'status':'PASS'if all(x['pass']for x in checks)else'FAIL','run':run,'checks':checks,'source':'Actual Android UI only, raw polling for validation'},indent=2))
