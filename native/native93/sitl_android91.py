"""Android UI only for actions; host HTTP observes without extending foreground lease."""
from android_qa import *
import urllib.request
TOKEN=(R/'.local/native93/bridge-token').read_text()
def state():return json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8872/state',data=b'{"observe":true}',headers={'Authorization':'Bearer '+TOKEN}),timeout=6))
def until(fn,seconds=20):
 end=time.monotonic()+seconds
 while True:
  s=state()
  if fn(s):return s
  assert time.monotonic()<end,'OBSERVE_DEADLINE'
  time.sleep(.3)
def tap(x,y):owned();adb('shell','input','tap',x,y)
def action(name,x,y,seconds=20):
 s=state();run=s['run'];out=E/'runs'/run/'raw.jsonl';prior=json.loads(out.read_text().splitlines()[-1])['n'];tap(x,y);end=time.monotonic()+seconds
 while True:
  rows=[json.loads(r)for r in out.read_text().splitlines()];hits=[r for r in rows if r['n']>prior and r['kind']in['NATIVE_OUTCOME','NATIVE_REJECTED_OR_UNKNOWN']and r['data'].get('action')==name]
  if hits:assert hits[-1]['kind']=='NATIVE_OUTCOME',hits[-1];return state()
  assert time.monotonic()<end,'ACTION_OUTCOME_DEADLINE_'+name
  time.sleep(.2)
def save(name,value):(E/(name+'.json')).open('x').write(json.dumps(value,indent=2))
