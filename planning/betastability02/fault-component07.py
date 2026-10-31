"""Isolated flight/payload authority test. Does NOT satisfy integrated video gate."""
import importlib.util,json,sys,subprocess,time,os
from pathlib import Path
sp=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
kind=sys.argv[1];assert kind in ['cut','reboot'];probe=json.loads((q.E/'android-video-probe07.json').read_text());last=probe['rows'][-1]['viewer'];assert last['active']is False and last['counters']['decoderErrors']>0,'KNOWN_VIDEO_BLOCKER_REQUIRED'
q.prepare('corridor');s=q.connect();run=s['flight']['run'];q.ready();q.tap('b-arm');s=q.wait(lambda s:s['flight']['live']['stage']=='ARMED_HOME_REVIEW');h=s['flight']['homeReview'];end=time.monotonic()+4
while h['sha256'][:10]not in(q.obs()['homeText']or''):
 assert time.monotonic()<end;time.sleep(.2)
q.check('b-home-after');q.tap('b-auto');q.wait(lambda s:s['flight']['completion'].get('takeoffEvidence',{}).get('valid')is True,45)
q.tap('b-discover');q.tap('b-select');q.tap('b-payload-grant');q.tap('b-gimbal');pre=q.state();assert pre['flight']['authority']and pre['payloadAuthority']['current']['leaseCount']==1 and pre['flight']['live']['armed']is True
q.tap('beta-faults');q.tap('b-'+kind);q.wait(lambda s:s['flight']['authority']is None and s['payloadAuthority']['current']['leaseCount']==0,25)
s=q.wait(lambda s:not s.get('archivePending',True)and run in s.get('archiveCommittedRuns',[]),25);r=next(r for r in s['reviews']if r['run']==run);assert r['accepted']is False and r['authorityRestored']is False
receipt={'status':'PASS_COMPONENT_ONLY_INTEGRATED_BETA_NOT_READY','scope':'ACTUAL_OWNED_AP_AIRBORNE_AND_MOCK_PAYLOAD_AUTHORITY_NO_VIDEO_OR_CAPTURE','kind':kind,'run':run,'preArmedObserved':True,'preLeaseCount':1,'postLeaseCount':0,'video':'FAILED_UNSUPPORTED_SOFTWARE_PROFILE_NOT_RETRIED','capture':'NOT_CHECKED_NO_VALID_DECODED_FRAME','fullNominalQualified':False,'authorityRestored':False,'review':r,'pre':pre}
with(q.E/('fault-component-'+kind+'07.json')).open('x')as f:json.dump(receipt,f,indent=2);f.flush();os.fsync(f.fileno())
with(q.E/('receiver-component-'+run+'.json')).open('x')as f:subprocess.run(['node','pilot/betastability02/receiver.mjs',str(q.E/'history01'/(run+'.json'))],cwd=q.R,stdout=f,check=True)
print('COMPONENT_FAULT_VERIFIED',kind,run,flush=True)
