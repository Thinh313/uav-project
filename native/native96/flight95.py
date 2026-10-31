from ui94 import *
import base64
owned();run=sys.argv[1]
out=E/'runs'/run
assert (out/'observer-ready.json').exists() and not (out/'closure.json').exists()
assert time.time()-(out/'observer.jsonl').stat().st_mtime<3
sys.dont_write_bytecode=True
import importlib.util
spec=importlib.util.spec_from_file_location('passive95',R/'pilot/apstream40/oracle-v2.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle);parser=oracle.MAVLink(None);parser.robust_parsing=True;observed={};seen96=False;noise96=bytearray()
for line in (out/'observer.jsonl').read_text().splitlines():
 row=json.loads(line)
 for f in parser.parse_buffer(bytes.fromhex(row['hex'])) or []:
  if f.get_type()=='BAD_DATA':
   assert not seen96;noise96.extend(bytes(f.data));assert len(noise96)<=1024 and all(v in[9,10,13]or 32<=v<=126 for v in noise96);continue
  seen96=True
  if f.get_srcSystem()==42 and f.get_srcComponent()==1:observed[f.get_msgId()]=row['hostMonoNs']
assert all(i in observed and time.monotonic_ns()-int(observed[i])<3e9 for i in [0,33,245]),'PASSIVE_STREAMS_NOT_FRESH_NO_GRANT'
(out/('observer-readonly-qualified%02d.json'%(1+len(list(out.glob('observer-readonly-qualified*.json')))))).open('x').write(json.dumps({'ids':observed,'transmittedPayloadBytes':0,'freshWithinMs':3000},indent=2))
def refresh():tap94('Preflight / Fly SITL')
def rawrows():
 raw=adb('exec-out','cat','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl')
 return [json.loads(x) for x in raw.splitlines()]
def events(kind):
 return [json.loads(base64.b64decode(x['dataBase64'])) for x in rawrows() if x['kind']==kind]
def wait_button(id,limit=12):
 end=time.monotonic()+limit
 while time.monotonic()<end:
  refresh();c=[x for x in last()['controls'] if x['id']==id and not x['disabled'] and not x['covered']]
  if c:return
  if events('CLOSED'):raise AssertionError('TRANSPORT_CLOSED_NO_RETRY')
  time.sleep(.3)
 raise AssertionError('UI_GATE_NOT_READY:'+id)
refresh();tap94('preflight83');wait_button('grant83')
p=events('PREFLIGHT')[-1]
assert p['assessment']['state']=='READY_SCOPED_READONLY',p['assessment']
(out/'readonly-qualified.json').open('x').write(json.dumps(p,indent=2))
capture(run+'-preflight-ready')
tap94('grant83');wait_button('upload83',5);tap94('upload83')
wait_button('arm83',8)
assert events('READBACK_VERIFIED')[-1]['matches'] is True
capture(run+'-upload-readback')
tap94('arm83');wait_button('auto83',7)
home=events('POST_ARM_HOME_REVIEW_REQUIRED')[-1]
(out/'home-review-ui.json').open('x').write(json.dumps(home,indent=2))
capture(run+'-post-arm-home-review')
tap94('auto83')
time.sleep(1)
assert events('AUTO_OBSERVED')[-1]['armed'] is True
capture(run+'-auto-observed')
tap94('close83')
adb('shell','input','tap',52,171)
time.sleep(.7)
capture(run+'-fly-main')
print('AUTO_NATIVE_DIRECT_OBSERVED',flush=True)
