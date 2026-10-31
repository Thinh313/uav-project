from ui97 import *
owned();run=current_run();checks=[]
def check(name,b):assert b,name;checks.append({'name':name,'pass':True});print(name,flush=True)
def txs():return state(run)['transactions']
def tx(op,p='front'):return next((t for t in reversed(txs())if t['operation']==op and t['payload']==p),None)
def st():return state(run)
def rejected(button,reason):
 n=len([v for k,v in parsed(run)if k=='REJECTED']);before=len(txs());tap97(button);wait97(run,lambda p:len([v for k,v in p if k=='REJECTED'])>n);r=next(v for k,v in reversed(parsed(run))if k=='REJECTED');check('rejected '+button+' '+reason,reason in r['error']and len(txs())==before)
def command(button,op,p='front',expected='OBSERVATION_CONSISTENT_UNATTRIBUTED'):
 tap97(button);wait97(run,lambda rows:any(k=='STATE'and any(t['operation']==op and t['payload']==p and t['state']==expected for t in v['transactions'])for k,v in rows));check(p+' '+op+' '+expected,tx(op,p)['state']==expected)
try:
 tap97('discover97');wait97(run,lambda p:any(k=='STATE'and len(v['transactions'])==4 and all(t['state']=='DISCOVERY_INFORMATION_OBSERVED_NOT_ENUMERATION_PROOF'for t in v['transactions'])for k,v in p));check('explicit native discovery through actual AP',True)
 tap97('join-pilot-a');tap97('join-payload-b');tap97('claim-pilot-a');capture('97-two-stations-front-owner');command('zoom-pilot-a','zoom',expected='UNKNOWN_TIMEOUT_UNCERTAIN');check('wrong-target-only feedback never accepted',tx('zoom')['state']=='UNKNOWN_TIMEOUT_UNCERTAIN');rejected('capture-pilot-a','EXCLUSIVE_OWNER')
 tap97('claim-pilot-a');command('capture-pilot-a','capture');tap97('transfer-pilot-a');rejected('focus-pilot-a','EXCLUSIVE_OWNER');tap97('accept-payload-b');rejected('focus-pilot-a','EXCLUSIVE_OWNER');value97('value97',55);command('focus-payload-b','focus');capture('97-transfer-recipient-focus');tap97('release-payload-b');rejected('authority-payload-b','EXCLUSIVE_OWNER')
 choose97(1,'97-center');tap97('claim-pilot-a');command('zoom-pilot-a','zoom','center');command('capture-pilot-a','capture','center')
 choose97(2,'97-rear');tap97('claim-pilot-a');command('capture-pilot-a','capture','rear')
 choose97(0,'97-front');tap97('claim-pilot-a');command('authority-pilot-a','authority');value97('value97',-30);value97('yaw97',10);command('gimbal-pilot-a','gimbal');capture('97-gimbal-feedback')
 choose97(1,'97-center-shared-manager');rejected('gimbal-pilot-a','AMBIGUOUS_ACK_KEY');tap97('lose-pilot-a');time.sleep(.3);check('operator loss clears all pilot scopes',all(p['ownerSid']is None for p in st()['payloads']));rejected('capture-pilot-a','STATION_EXPLICIT_JOIN_REQUIRED')
 tap97('close97');capture('97-closed-no-authority');check('explicit close has no grants or restored identities',st()['phase']=='CLOSED'and not any(x['alive']for x in st()['stations']));
except Exception as e:
 checks.append({'name':'DRIVER_FAILURE','pass':False,'error':repr(e)});capture('97-scenario-failure');raise
finally:
 (E/'scenario01.json').open('x').write(json.dumps({'status':'PASS'if all(c['pass']for c in checks)else'FAIL','run':run,'checks':checks,'provenance':'Actual ADB UI interactions; native raw polling for qualification, no injected bridge/DOM/JavaScript'},indent=2))
