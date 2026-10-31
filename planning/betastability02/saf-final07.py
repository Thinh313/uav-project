"""Actual SAF on owned emulator. Exports retain original failed qualification."""
import importlib.util,json,subprocess,time,os
from pathlib import Path
sp=importlib.util.spec_from_file_location('saf',Path(__file__).with_name('saf-helpers.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);q=h.q
run='sbeab5315ec874588bdf0'
assert q.state()['flight']['authority'] is None
assert not q.state().get('archivePending',True)
q.tap('nav-review');h.select_review(run)
# Cancel two actual pickers, then successfully export: no busy-state reset shortcut.
for i in range(2):
 q.tap('beta-export-raw');r=h.picker();assert any(n.attrib.get('class')=='android.widget.EditText' for n in r.iter('node')),h.n.summary(r)
 q.adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(.4)
 # Native picker may first consume BACK to dismiss the keyboard.
 r=h.picker()
 if any(n.attrib.get('class')=='android.widget.EditText' for n in r.iter('node')):q.adb('shell','input','keyevent','KEYCODE_BACK')
 q.wait(lambda s:not s.get('busy',True),5);time.sleep(.8)
data=h.export_document('beta-export-raw','BETA-STABILITY02-raw07.json')
original=(q.E/'history01'/(run+'.json')).read_bytes();assert data==original,'SAF_RAW_BYTES_DIFFER'
p=q.E/('android-saf-raw-'+run+'-07.json');p.open('xb').write(data)
with(q.E/'receiver-saf07.json').open('x')as f:subprocess.run(['node','pilot/betastability02/receiver.mjs',str(p)],cwd=q.R,stdout=f,check=True)
v=json.loads((q.E/'receiver-saf07.json').read_text())
h.save_receipt('saf-raw-verification07.json',{'status':'PASS_SAF_BYTES_AND_COLD_RECEIVER','run':run,'bytes':len(data),'sha256':h.sha(data),'originalSha256':h.sha(original),'cancelReopenCycles':2,'receiver':v,'videoQualification':'FAIL_RETAINED_GAP_257.861458_MS','integratedBetaReady':False,'sourceAuthenticated':False,'authorityRestored':False})
print('SAF_RAW_EXACT_AND_RECEIVER_VERIFIED',len(data),flush=True)
