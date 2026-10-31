"""Owned Android process restart, native persistence and SAF readback."""
import importlib.util,json,time
from pathlib import Path
sp=importlib.util.spec_from_file_location('saf',Path(__file__).with_name('saf-helpers.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);q=h.q
def closed_snapshot():
 s=q.state();assert s['flight']['authority'] is None and s['payloadAuthority']['current']['leaseCount']==0
 return {'reviews':[{k:r.get(k)for k in ['run','accepted','rawHead','modelSha256','planSha256']}for r in s['reviews']],'authority':None,'payloadLeases':0}
before=json.loads((q.E/'workspace-before-snapshot07.json').read_text());a=(q.E/'android-saf-workspace-before07.json').read_bytes();assert before==closed_snapshot()
q.adb('shell','am','force-stop','vn.rtr.aeris.betastability02');time.sleep(1);q.adb('shell','am','start','-W','-n','vn.rtr.aeris.betastability02/.ShellActivity');time.sleep(3)
after=closed_snapshot();assert before==after,'CLOSED_REVIEW_CHANGED_AFTER_ANDROID_RESTART';assert q.state()['client']['active'] is False,'AUTHORITY_CLIENT_REACTIVATED'
q.tap('workspace');b=h.export_document('workspace-export','BETA-STABILITY02-workspace-after07.json');(q.E/'android-saf-workspace-after07.json').open('xb').write(b);assert a==b,'WORKSPACE_CHANGED_AFTER_ANDROID_RESTART';q.tap('close-modal')
h.save_receipt('workspace-restart-verification07.json',{'status':'PASS_ANDROID_RESTART_WORKSPACE_BYTES_AND_CLOSED_REVIEWS','before':before,'after':after,'beforeSha256':h.sha(a),'afterSha256':h.sha(b),'bytes':len(a),'authorityRestored':False,'clientAutoActivated':False,'hostRestart':'NOT_THIS_TEST','sourceAuthenticated':False})
print('ANDROID_RESTART_WORKSPACE_AND_REVIEWS_VERIFIED',flush=True)
