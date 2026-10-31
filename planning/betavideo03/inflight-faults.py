"""One UI-triggered attempt per declared fault. No reconnection or auto-restored authority."""
import importlib.util,json,sys,subprocess,time
from pathlib import Path
sp=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
kind=sys.argv[1];assert kind in ['cut','reboot'];q.prepare('corridor');s=q.connect();run=s['flight']['run'];q.ready();q.tap('video-start');videoDeadline=time.monotonic()+10
while not q.obs()['controls']['video-capture']['enabled']:
 assert time.monotonic()<videoDeadline,'FAULT_TEST_FRESH_DECODED_VIDEO_REQUIRED';time.sleep(.2)
q.tap('b-arm');s=q.wait(lambda s:s['flight']['live']['stage']=='ARMED_HOME_REVIEW');h=s['flight']['homeReview'];end=time.monotonic()+4
while h['sha256'][:10]not in(q.obs()['homeText']or''):
 assert time.monotonic()<end;time.sleep(.2)
q.check('b-home-after');q.tap('b-auto');q.wait(lambda s:s['flight']['completion'].get('takeoffEvidence',{}).get('valid')is True,45)
q.tap('b-discover');q.tap('b-select');q.tap('b-payload-grant');q.tap('b-gimbal');captureBefore=len(q.state()['captures']);q.tap('video-capture');q.wait(lambda s:len(s['captures'])>captureBefore);preVideo=q.obs();pre=q.state();assert pre['flight']['authority']and pre['payloadAuthority']['current']['leaseCount']==1 and pre['flight']['live']['armed'] is True
q.tap('beta-faults');q.tap('b-'+kind);s=q.wait(lambda s:s['flight']['authority']is None and s['payloadAuthority']['current']['leaseCount']==0,25);q.log('INFLIGHT_FAULT_OBSERVED',{'kind':kind,'run':run,'pre':pre,'preVideoObservation':preVideo,'post':s});s=q.wait(lambda s:any(r['run']==run for r in s['reviews'])and not s.get('archivePending',True)and run in s.get('archiveCommittedRuns',[]),20);r=next(r for r in s['reviews']if r['run']==run);assert r['accepted']is False and r['authorityRestored']is False
s=q.state();assert s['flight']['authority']is None and s['payloadAuthority']['current']['leaseCount']==0
p=q.E/('inflight-'+kind+'01.json');p.open('x').write(json.dumps({'status':'PASS_INFLIGHT_FAULT_SCOPE_ONLY','kind':kind,'run':run,'preArmedObserved':True,'preLeaseCount':1,'postLeaseCount':0,'syntheticCaptureBeforeFault':True,'videoWasFreshBeforeFault':preVideo['controls']['video-capture']['enabled'],'faultVideoNominalFPSAcceptance':'NOT_CLAIMED','authorityRestored':False,'review':r},indent=2))
with(q.E/('receiver-fault-'+run+'.json')).open('x')as f:subprocess.run(['node','pilot/betavideo03/receiver.mjs',str(q.E/'history01'/(run+'.json'))],cwd=q.R,stdout=f,check=True)
print('INFLIGHT_FAULT_VERIFIED',kind,run,flush=True)
