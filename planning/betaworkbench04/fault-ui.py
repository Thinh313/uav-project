from pathlib import Path
import importlib.util,time,sys
f=Path(__file__).with_name('actual-ui-journey.py');sp=importlib.util.spec_from_file_location('fault_ui04',f);q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q);fault=sys.argv[1];assert fault in['cut','reboot'];q.step=300 if fault=='cut' else 400;original=q.tap
# Require a new, settled visible UI observation for control dispatch.
def tap(name):
 end=time.monotonic()+5
 while not q.obs()['controls'].get(name,{}).get('enabled',False):
  assert time.monotonic()<end,'DISABLED_'+name;time.sleep(.1)
 return original(name)
q.tap=tap
try:
 before=len(q.state()['reviews']);q.tap('nav-fly');s=q.connect();run=s['flight']['run'];q.log('FAULT_RUN_CONNECTED',{'run':run,'fault':fault})
 def sensors(s):
  checks=s['flight']['preflight']['checks'];return all(c['pass']for c in checks if c['id']!='configuration')
 q.wait(sensors,65);q.tap('b-preflight');q.wait(lambda s:s['flight']['preflight']['ready'],20);q.tap('b-grant');q.wait(lambda s:s['flight']['authority']is not None);q.tap('b-upload');q.wait(lambda s:not s['busy']and s['flight']['live']['readback63']);q.tap('b-arm');s=q.wait(lambda s:s['flight']['live']['stage']=='ARMED_HOME_REVIEW');h=s['flight']['homeReview'];end=time.monotonic()+2
 while h['sha256'][:10]not in(q.obs()['homeText']or''):
  assert time.monotonic()<end;time.sleep(.1)
 q.check('b-home-after');q.tap('b-auto');q.wait(lambda s:s['flight']['latestPosition']['relativeHomeM']>2,30);q.tap('b-discover');q.tap('b-select');q.tap('b-payload-grant');q.tap('b-gimbal');q.log('FAULT_AIRBORNE_INTENT',{'run':run,'heightM':q.state()['flight']['latestPosition']['relativeHomeM'],'fault':fault});q.tap('b-'+fault);s=q.wait(lambda s:len(s['reviews'])>before,35);r=s['reviews'][-1];assert r['run']==run and not r['accepted']and not r['execution']['complete'];assert s['flight']['authority']is None and s['flight']['run']is None;assert s['payloadAuthority']['last']['post']['leaseCount']==0;q.log('FAULT_REVIEW_CONFIRMED',r);print('FAULT_UI_PASS '+fault,flush=True)
except BaseException as e:q.log('FAULT_UI_FAILURE',{'fault':fault,'error':str(e)});raise
