"""LINUXPORT01 exact patches for runtime-l15 (team decision, not the owner's).

runtime-l15 is runtime-l14 plus one change, decided by the team on 2026-11-06 after g107
attempt 1 failed (report 4zzf, 4zzg): a read-only forensic capture m803 of the app state that
g107 left (the AERIS app had started; its STATUS reply showed a new open AJ02 journal and
lifetime generation 12, so the state no longer matches the contract-l12 pin). It follows
runtime-l12's capture m802 after g106: new slot m803, prior slot g107, run
beta-rc01-forensic-capture03, team prerequisite/intent formats. The capture code itself is
unchanged. continuation_l13.py, contract-l12, the 40 MiB artifact cap, the 200 ms writer
limit and every other guard are unchanged; this candidate is for the capture only.

Every file below is generated from its runtime-l14 original by these replacements, and
test-linuxport15.py re-derives each one. Each `old` must occur exactly once.
"""

# Source modules: runtime-l14/source/aeris_runtime/<name> -> runtime-l15/source/aeris_runtime/<name>
MODULES={
 'mission16.py':[
  ("SLOTS={'m903':180,","SLOTS={'m803':180,'m903':180,"),
 ],
 'product_runtime.py':[
  ("'m701','m702','m801','m802','m901'","'m701','m702','m801','m802','m803','m901'"),
  ("  if self.root.name in('m801','m802'):\n   from .forensic_h10 import verify_capture\n",
   "  if self.root.name in('m801','m802','m803'):\n   from .forensic_h10 import verify_capture\n"),
  ("  if self.root.name in('m801','m802'):\n   result.pop('originalPrivateBytesConserved')",
   "  if self.root.name in('m801','m802','m803'):\n   result.pop('originalPrivateBytesConserved')"),
  ("need(self.root.name in('m801','m802'),'FORENSIC_ONLY_SCOPE')","need(self.root.name in('m801','m802','m803'),'FORENSIC_ONLY_SCOPE')"),
 ],
 'forensic_h10.py':[
  ("owner.root.name in('m801','m802')and v.get('format')","owner.root.name in('m801','m802','m803')and v.get('format')"),
 ],
}

# Capture entry: runtime-l14/root-capture-l12.py (owner root-capture-h10.py plus l12_patches.CAPTURE) -> runtime-l15/root-capture-l15.py
CAPTURE_SOURCE='planning/linuxport01/runtime-l14/root-capture-l12.py'
CAPTURE=[
 ('"""LINUXPORT01 (team entry): one fresh read-only forensic capture m802 of the state after g106 attempt 1.\nOwner root-capture-h10.py plus l12_patches.py. No initial-registry semantic decoder."""',
  '"""LINUXPORT01 (team entry): one fresh read-only forensic capture m803 of the state after g107 attempt 1.\nOwner root-capture-h10.py plus l12_patches.py, then l15_patches.py. No initial-registry semantic decoder."""'),
 ("choices=('m802',)","choices=('m803',)"),
 ("prior.get('format')=='aeris-linuxport01-l12-root-forensic-prerequisite'and prior.get('version')==1 and prior.get('status')=='ROOT_COLD_VERIFIED_G106_FAILED_PHYSICALLY_CLOSED_NOT_QUALIFICATION'",
  "prior.get('format')=='aeris-linuxport01-l15-root-forensic-prerequisite'and prior.get('version')==1 and prior.get('status')=='ROOT_COLD_VERIFIED_G107_FAILED_PHYSICALLY_CLOSED_NOT_QUALIFICATION'"),
 ("prior.get('priorSlot')=='g106'","prior.get('priorSlot')=='g107'"),
 ("run='beta-rc01-forensic-capture02';need(intent.get('format')=='aeris-linuxport01-l12-root-forensic-intent'",
  "run='beta-rc01-forensic-capture03';need(intent.get('format')=='aeris-linuxport01-l15-root-forensic-intent'"),
 ("intent.get('slot')=='m802'","intent.get('slot')=='m803'"),
 ("scope=R/'evidence/betarc01/m802'","scope=R/'evidence/betarc01/m803'"),
]

def gate(text):
 """runtime-l14/prepare-source-gate.py -> runtime-l15: entries point at runtime-l15; root-capture-l15.py replaces root-capture-l12.py."""
 assert text.count('runtime-l14')==4 and text.count("'planning/linuxport01/runtime-l14/root-capture-l12.py'")==1,'L15_GATE_BASE'
 return text.replace("'planning/linuxport01/runtime-l14/root-capture-l12.py'","'planning/linuxport01/runtime-l15/root-capture-l15.py'").replace('runtime-l14','runtime-l15')

def apply(text,patches,name):
 for old,new in patches:
  n=text.count(old)
  if n!=1:raise ValueError('L15_PATCH_ANCHOR_NOT_UNIQUE:%s:%d:%r'%(name,n,old[:60]))
  text=text.replace(old,new)
 return text
