from pathlib import Path
import importlib.util,json
p=Path(__file__).with_name('android-journey.py');s=importlib.util.spec_from_file_location('q',p);q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
try:
 before=q.state();run=before['flight']['run'];assert not before['flight']['live']['armed'];q.log('REALLOCATION_AS_LINK_FAULT',{'run':run,'nominalFailed':True,'AUTOObserved':before['flight']['completion']['autoObserved'],'reason':'Fresh post-arm Home remained valid; other ten-second parameter cohort aged out. No AUTO wire was sent.'})
 for name in ['b-discover','b-select','b-payload-grant','b-gimbal']:q.tap(name)
 before=q.state();assert before['payloadAuthority']['current']['leaseCount']==1;q.tap('beta-faults');q.tap('b-cut');after=q.wait(lambda s:s['flight']['run']is None,35);assert after['flight']['authority']is None and after['payloadAuthority']['current']['leaseCount']==0;r=next(r for r in after['reviews']if r['run']==run);assert not r['accepted'];q.log('LINK_FAULT_COMPLETE',{'before':before['payloadAuthority']['current'],'review':r,'after':after['payloadAuthority']});(q.E/'android-link-fault01.json').open('x').write(json.dumps({'status':'PASS_DISARMED_FAULT_ONLY_NOT_INFLIGHT','run':run,'review':r,'authorityRestored':False},indent=2));print('LINK_FAULT_COMPLETE',run,flush=True)
except BaseException as e:q.log('LINK_FAULT_FAILURE',{'error':repr(e)});raise
