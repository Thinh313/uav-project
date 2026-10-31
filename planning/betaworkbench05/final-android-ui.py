from pathlib import Path
import importlib.util,time,json
p=Path(__file__).with_name('actual-ui-journey.py');s=importlib.util.spec_from_file_location('q',p);q=importlib.util.module_from_spec(s);s.loader.exec_module(q);q.step=5000
old=q.tap
def tap(name):
 end=time.monotonic()+5
 while not q.obs()['controls'].get(name,{}).get('enabled',False):
  assert time.monotonic()<end,'DISABLED_'+name;time.sleep(.1)
 old(name)
q.tap=tap
results=[]
def screenshot(name):
 time.sleep(.6);(q.E/name).open('xb').write(q.adb('exec-out','screencap','-p'))
try:
 q.tap('nav-plan');q.check('datum');q.tap('compile');q.prepare();s=q.connect();assert s['flight']['source']=='MOCK_PROTOCOL_NOT_ARDUPILOT';q.tap('b-preflight');q.tap('b-grant')
 for n in ['b-discover','b-select','b-payload-grant','b-gimbal']:q.tap(n)
 s=q.state();assert s['payloadAuthority']['current']['leaseCount']==1;screenshot('android-current-granted01.png');results.append({'case':'current-granted-not-old-receipt','current':s['payloadAuthority']['current'],'oldReceiptCount':s['payloadAuthority']['last']['post']['leaseCount']})
 q.tap('b-payload-revoke');s=q.state();assert s['payloadAuthority']['current']['leaseCount']==0;screenshot('android-current-revoked01.png');results.append({'case':'explicit-revoke','current':s['payloadAuthority']['current']})
 for n in ['b-discover','b-select','b-payload-grant']:q.tap(n)
 assert q.state()['payloadAuthority']['current']['leaseCount']==1
 q.adb('shell','am','force-stop','vn.rtr.aeris.betaworkbench05');q.adb('shell','am','start','-W','-n','vn.rtr.aeris.betaworkbench05/.ShellActivity');time.sleep(3.5);s=q.state();assert s['flight']['authority']is None and s['payloadAuthority']['current']['leaseCount']==0;results.append({'case':'android-restart-no-authority','current':s['payloadAuthority']['current']});q.tap('nav-fly');screenshot('android-restart-no-authority01.png');q.tap('b-activate');q.tap('beta-faults');q.tap('b-abort');q.wait(lambda s:s['flight']['run']is None)
 for theme in ['night','day']:
  if theme=='day':q.tap('theme')
  for view in ['plan','preflight','fly','review']:
   q.tap('nav-'+view);v=q.obs();assert not v['geometry']['horizontalOverflow']and not v['geometry']['panelOverflow'];screenshot('android-final-'+theme+'-'+view+'.png');results.append({'case':'ui-'+theme+'-'+view,'geometry':v['geometry'],'viewport':v['viewport']})
 (q.E/'android-final-ui01.json').open('x').write(json.dumps({'status':'PASS_MOCK_ANDROID_OBSERVATION_ONLY','actualAP':0,'results':results,'authorityRestored':False},indent=2));print('FINAL_ANDROID_PERMISSION_AND_LAYOUT_PASS',flush=True)
except BaseException as e:q.log('FINAL_UI_FAILURE',{'error':str(e)});raise
