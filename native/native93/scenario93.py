"""Authorized UI taps, read-only host observation. Never calls POST control from terminal."""
from sitl_android91 import *
import shutil

def start(label):
 assert shutil.disk_usage(R).free>=26*2**30
 assert state()['run']is None
 # Restore the visible live section after prior recovery; no control request is retried.
 adb('shell','input','swipe',1000,310,1000,620,400);time.sleep(.4)
 pins=json.loads((E/'flight-pins.json').read_text())['files'];assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in pins.items())
 tap(330,393);s=until(lambda s:s['run']is not None,35);save(label+'-readonly',s);print(json.dumps({'label':label,'run':s['run'],'stage':'READONLY','grant':s['grant']}),flush=True)
 s=until(lambda s:all(x['pass']for x in s['live']['preflight']if x['id']!='configuration'),50);s=action('preflight',465,393,25);assert s['live']['preflight63']['ready'];save(label+'-preflight',s)
 s=action('grant',637,393);s=action('upload',826,393);save(label+'-readback',s);s=action('arm',989,393,25);s=until(lambda s:s['live'].get('postArmHomeReviewFresh'),12);save(label+'-postarm-home',s);s=action('auto',258,449,25);save(label+'-auto',s)
 s=until(lambda s:s['live']['completion'].get('takeoffWitness')is not None,30);save(label+'-takeoff',s);print(json.dumps({'label':label,'run':s['run'],'stage':'AUTO_TAKEOFF_OBSERVED'}),flush=True);return s

if __name__=='__main__':
 label=__import__('sys').argv[1];s=start(label);capture(label+'-airborne')
