"""Explicit SAF import of earlier corridor after creating a different polygon."""
import importlib.util,time,json
from pathlib import Path
sp=importlib.util.spec_from_file_location('saf',Path(__file__).with_name('saf-helpers.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);q=h.q
assert q.state()['flight']['authority'] is None
q.tap('nav-plan');q.tap('sample-polygon');q.check('datum');q.tap('compile');q.tap('workspace');q.tap('workspace-file');r=h.picker();filename='BETA-STABILITY02-workspace-before07.json';nodes=[x for x in r.iter('node')if x.attrib.get('text')==filename];assert len(nodes)==1,h.n.summary(r)
h.n.tap(r,**{'text':filename,'bounds':nodes[0].attrib['bounds']});time.sleep(2)
q.tap('workspace-save');data=h.export_document('workspace-export','BETA-STABILITY02-workspace-imported07.json');p=q.E/'android-saf-workspace-imported07.json';p.open('xb').write(data);original=(q.E/'android-saf-workspace-before07.json').read_bytes();assert data==original,'IMPORTED_WORKSPACE_SEMANTICS_OR_BYTES_DIFFER';q.tap('close-modal')
s=q.state();assert s['flight']['authority'] is None and s['payloadAuthority']['current']['leaseCount']==0
h.save_receipt('workspace-import-verification07.json',{'status':'PASS_ACTUAL_SAF_IMPORT_AND_EXPLICIT_SAVE_REEXPORT','workflow':'corridor saved → polygon compiled → corridor imported through SAF → explicitly saved → reexported identical','bytes':len(data),'sha256':h.sha(data),'originalSha256':h.sha(original),'authorityRestored':False,'realHardware':False})
print('WORKSPACE_IMPORT_AND_REEXPORT_VERIFIED',flush=True)
