"""Actual SAF on owned emulator. Exports retain original failed qualification."""
import importlib.util,json,subprocess,time,os
from pathlib import Path
sp=importlib.util.spec_from_file_location('saf',Path(__file__).with_name('saf-helpers.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);q=h.q
run='sbeab5315ec874588bdf0'
assert q.state()['flight']['authority'] is None
assert not q.state().get('archivePending',True)
# Root selected exact second option using the recorded actual dropdown screenshot.
# Byte comparison below independently proves which run was exported.
q.tap('nav-review')
# Prior cancel attempt retained separately; no claim of two successful cycles.
data=h.export_document('beta-export-raw','BETA-STABILITY02-raw07.json')
original=(q.E/'history01'/(run+'.json')).read_bytes();assert data==original,'SAF_RAW_BYTES_DIFFER'
p=q.E/('android-saf-raw-'+run+'-07.json');p.open('xb').write(data)
with(q.E/'receiver-saf07.json').open('x')as f:subprocess.run(['node','pilot/betastability02/receiver.mjs',str(p)],cwd=q.R,stdout=f,check=True)
v=json.loads((q.E/'receiver-saf07.json').read_text())
h.save_receipt('saf-raw-verification07.json',{'status':'PASS_SAF_BYTES_AND_COLD_RECEIVER','run':run,'bytes':len(data),'sha256':h.sha(data),'originalSha256':h.sha(original),'cancelReopenCycles':'NOT_QUALIFIED_STALE_XML_HARNESS_INCIDENT_RETAINED','receiver':v,'videoQualification':'FAIL_RETAINED_GAP_257.861458_MS','integratedBetaReady':False,'sourceAuthenticated':False,'authorityRestored':False})
print('SAF_RAW_EXACT_AND_RECEIVER_VERIFIED',len(data),flush=True)
