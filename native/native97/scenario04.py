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
 check('existing explicit native discovery retained',len(txs())==4 and all(t['operation']=='discovery'and t['state']=='DISCOVERY_INFORMATION_OBSERVED_NOT_ENUMERATION_PROOF'for t in txs()))
 check('two explicit stations already joined in same raw session',len([s for s in st()['stations']if s['alive']])==2)
 if next(p for p in st()['payloads']if p['id']=='front')['ownerSid']is not None:tap97('release-pilot-a')
 tap97('claim-pilot-a');capture('final97-two-stations-front-owner');command('zoom-pilot-a','zoom',expected='UNKNOWN_TIMEOUT_UNCERTAIN');check('wrong-target-only feedback never accepted',tx('zoom')['state']=='UNKNOWN_TIMEOUT_UNCERTAIN');rejected('capture-pilot-a','EXCLUSIVE_OWNER')
 tap97('claim-pilot-a');command('capture-pilot-a','capture');tap97('transfer-pilot-a');rejected('focus-pilot-a','EXCLUSIVE_OWNER');tap97('accept-payload-b');rejected('focus-pilot-a','EXCLUSIVE_OWNER');value97('value97',55);command('focus-payload-b','focus');capture('final97-transfer-recipient-focus');tap97('release-payload-b');rejected('authority-payload-b','EXCLUSIVE_OWNER')
 choose97(1,'final97-center');tap97('claim-pilot-a');command('zoom-pilot-a','zoom','center');command('capture-pilot-a','capture','center')
 choose97(2,'final97-rear');tap97('claim-pilot-a');command('capture-pilot-a','capture','rear')
 choose97(0,'final97-front');tap97('claim-pilot-a');command('authority-pilot-a','authority');value97('value97',-30);value97('yaw97',10);command('gimbal-pilot-a','gimbal');capture('final97-gimbal-feedback')
 choose97(1,'final97-center-shared-manager');
 if next(p for p in st()['payloads']if p['id']=='center')['ownerSid']is None:tap97('claim-pilot-a')
 rejected('gimbal-pilot-a','AMBIGUOUS_ACK_KEY');tap97('lose-pilot-a');time.sleep(.3);check('operator loss clears all pilot scopes',all(p['ownerSid']is None for p in st()['payloads']));before=len(txs());tap97('capture-pilot-a');time.sleep(.4);capture('final97-lost-operator-client-refused');check('lost operator UI has no dispatch',len(txs())==before)
 tap97('close97');capture('final97-closed-no-authority');check('explicit close has no grants or restored identities',st()['phase']=='CLOSED'and not any(x['alive']for x in st()['stations']));
except Exception as e:
 checks.append({'name':'DRIVER_FAILURE','pass':False,'error':repr(e)});capture('final97-scenario03-failure');raise
finally:
 (E/'scenario04.json').open('x').write(json.dumps({'status':'PASS'if all(c['pass']for c in checks)else'FAIL','run':run,'checks':checks,'provenance':'Actual ADB UI interactions; native raw polling for qualification, no injected bridge/DOM/JavaScript'},indent=2))
