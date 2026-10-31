from pathlib import Path
import importlib.util,json
p=Path(__file__).with_name('android-journey.py');s=importlib.util.spec_from_file_location('q',p);q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
try:
 st=q.state();run=st['flight']['run'];assert not st['flight']['live']['armed'];q.log('REALLOCATION_AS_DECLARED_REBOOT_FAULT',{'run':run,'nominalFailed':True,'AUTOObserved':st['flight']['completion']['autoObserved'],'reason':'Harness Home-text read preceded fresh UI receipt; no retry of arm/AUTO.'})
 for name in ['b-select','b-payload-grant','b-gimbal']:q.tap(name)
 before=q.state();assert before['payloadAuthority']['current']['leaseCount']==1;q.tap('beta-faults');q.tap('b-reboot');after=q.wait(lambda s:s['flight']['run']is None,35);assert after['flight']['authority']is None and after['payloadAuthority']['current']['leaseCount']==0;r=next(r for r in after['reviews']if r['run']==run);assert not r['accepted'];q.log('REBOOT_FAULT_COMPLETE',{'beforeAuthority':before['payloadAuthority']['current'],'review':r,'afterAuthority':after['payloadAuthority']});(q.E/'android-reboot-fault01.json').open('x').write(json.dumps({'status':'PASS_DISARMED_FAULT_ONLY_NOT_INFLIGHT','run':run,'review':r,'authorityRestored':False},indent=2));print('REBOOT_FAULT_COMPLETE',run,flush=True)
except BaseException as e:q.log('REBOOT_FIRST_FAILURE',{'error':repr(e)});raise
