from ui94 import *
from sitl_android91 import state,until,save
import shutil

def act(name,id,seconds=25):
 s=state();raw=E/'runs'/s['run']/'raw.jsonl';prior=json.loads(raw.read_text().splitlines()[-1])['n'];tap94(id);end=time.monotonic()+seconds
 while True:
  rows=[json.loads(l)for l in raw.read_text().splitlines()];hits=[r for r in rows if r['n']>prior and r['kind']in['NATIVE_OUTCOME','NATIVE_REJECTED_OR_UNKNOWN']and r['data'].get('action')==name]
  if hits:assert hits[-1]['kind']=='NATIVE_OUTCOME',hits[-1];return state()
  assert time.monotonic()<end,'OUTCOME_UNKNOWN_NO_RETRY_'+name;time.sleep(.2)
def start():
 assert shutil.disk_usage(R).free>=26*2**30;assert state()['run']is None
 pins=json.loads((E/'flight-pins.json').read_text())['files'];assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in pins.items())
 owned();adb('reverse','tcp:8874','tcp:8874');adb('shell','am','force-stop',P);token=(R/'.local/native94/bridge-token').read_text();adb('shell','am','start','-n',P+'/.ShellActivity','--es','source87','sitl','--es','bridgeToken',token);time.sleep(1);tap94('open-sitl83');capture('sitl94-local-plan-before-attestation');save('94-before-attestation',state());tap94('connect83');s=until(lambda s:s['run']is not None,40);save('94-readonly',s);print(json.dumps({'run':s['run'],'stage':'READONLY_HOST_ATTESTED','grant':s['grant']}),flush=True)
 s=until(lambda s:all(x['pass']for x in s['live']['preflight']if x['id']!='configuration'),50);s=act('preflight','preflight83');assert s['live']['preflight63']['ready'];save('94-preflight',s)
 act('grant','grant83');s=act('upload','upload83');save('94-readback',s);act('arm','arm83');s=until(lambda s:s['live'].get('postArmHomeReviewFresh'),12);save('94-postarm-home',s);s=act('auto','auto83');save('94-auto',s);s=until(lambda s:s['live']['completion'].get('takeoffWitness')is not None,30);save('94-takeoff',s);capture('sitl94-takeoff');print(json.dumps({'run':s['run'],'stage':'AUTO_TAKEOFF_OBSERVED'}),flush=True)
 s=until(lambda s:s['live']['completion'].get('complete')is True,160);save('94-terminal-ground',s);capture('sitl94-terminal-ground');tap94('complete83');s=until(lambda s:s['run']is None,40);save('94-closed',s);assert s['review']['accepted']is True;capture('sitl94-review');journal('sitl94-closed');print(json.dumps({'run':s['review']['run'],'accepted':True}),flush=True)
if __name__=='__main__':start()
