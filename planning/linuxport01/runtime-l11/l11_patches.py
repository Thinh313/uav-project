"""LINUXPORT01 exact text patches for runtime-l11 (team decision, not the owner's).

runtime-l11 is runtime-l10 plus the G1 continuation (step 3 of the owner's
docs/handoff/NEXT-MILESTONE.md). Every file below is generated from its original
by these replacements, and test-linuxport11.py re-derives it. Each `old` must
occur exactly once.

Why: the owner's G1 chain is two SDK cold boots of the same candidate (H8
m601/m602, H9 m701/m702) and then the G1 slot (g104, g105). Those entries admit
the private data with reconcile_h7.reconcile, the 75-file post-g103 decoder,
which the owner forbids for the 83-file state. Here the same entries start from
the team continuation contract (planning/linuxport01/contract-l10, pin
b5318c62...) instead, through the new team module continuation_l11.py. New slot
names: m901, m902 (qualification) and g106 (G1). Everything else is unchanged.
"""

# Source modules: runtime-l10/source/aeris_runtime/<name> -> runtime-l11/source/aeris_runtime/<name>
MODULES={
 'mission16.py':[
  ("SLOTS={'m801':180,","SLOTS={'m901':180,'m902':180,'g106':180,'m801':180,"),
 ],
 'rc01.py':[
  ("KINDS={'g105':'native',","KINDS={'g106':'native','g105':'native',"),
  ("REMAINING={'g105':0,","REMAINING={'g106':0,'g105':0,"),
  ("ARCHIVE_BOUNDARY['g105']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n",
   "ARCHIVE_BOUNDARY['g105']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\nARCHIVE_BOUNDARY['g106']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n"),
 ],
 'product_runtime.py':[
  ("self.root.name in('m101','m102','m201','m202','m303','m401','m402','m501','m502','m701','m702','m801')",
   "self.root.name in('m101','m102','m201','m202','m303','m401','m402','m501','m502','m701','m702','m801','m901','m902')"),
  ("  elif self.root.name in('m701','m702'):\n   from .reconcile_h7 import verify_sdk\n   verify_sdk(self,proof)\n",
   "  elif self.root.name in('m701','m702'):\n   from .reconcile_h7 import verify_sdk\n   verify_sdk(self,proof)\n  elif self.root.name in('m901','m902'):\n   from .continuation_l11 import verify_sdk\n   verify_sdk(self,proof)\n"),
  ("if self.root.name in('m401','m402','m501','m502','m701','m702')else",
   "if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902')else"),
  ("  if self.root.name in('m401','m402','m501','m502','m701','m702'):result.update",
   "  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902'):result.update"),
  ("  need(self.root.name in('m401','m402','m501','m502','m701','m702'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')",
   "  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')"),
 ],
 'product_native09.py':[
  (" if domain.get('nativeLifecycleResumeH7')is True:\n  from .reconcile_h7 import verify_resume_domain\n  return verify_resume_domain(root,ref,manifest)\n",
   " if domain.get('nativeLifecycleResumeH7')is True:\n  from .reconcile_h7 import verify_resume_domain\n  return verify_resume_domain(root,ref,manifest)\n if domain.get('nativeLifecycleContinuationL11')is True:\n  from .continuation_l11 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n"),
 ],
}

# G1 entry: runtime-l10/root-native-h10.py (byte-identical to the owner's runtime-h10) -> runtime-l11/root-native-l11.py
NATIVE_SOURCE='planning/linuxport01/runtime-l10/root-native-h10.py'
NATIVE=[
 ('"""Source-held native-only migration slot. Never starts AP/backend or flight."""',
  '"""LINUXPORT01 (team entry): source-held native-only G1 slot g106 from the m801 continuation contract.\nOwner root-native-h10.py plus l11_patches.py. Never starts AP/backend or flight."""'),
 ("choices=('g105',)","choices=('g106',)"),
 ("from aeris_runtime.reconcile_h7 import require_qualification,resume_existing\n",
  "from aeris_runtime.continuation_l11 import require_qualification,resume_continuation\n"),
 ("post=resume_existing(owner,case,","post=resume_continuation(owner,case,"),
]

# Qualification entry: owner planning/betarc01/runtime-h9/root-reconcile-h9.py -> runtime-l11/root-qualify-l11.py
QUALIFY_SOURCE='planning/betarc01/runtime-h9/root-reconcile-h9.py'
QUALIFY=[
 ('"""Fresh coldboot qualification only; no install, Activity, AP or automatic repair."""',
  '"""LINUXPORT01 (team entry): fresh coldboot qualification m901/m902 checked by the m801 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py. No install, Activity, AP or automatic repair."""'),
 ("choices=('m701','m702')","choices=('m901','m902')"),
 ("proof.get('format')=='aeris-h7-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_PRIOR_OBSERVATION_NOT_CLEAN_CLOSE'if a.slot=='m701'else",
  "proof.get('format')=='aeris-linuxport01-l11-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M801_FORENSIC_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m901'else"),
 (" from aeris_runtime.reconcile_h7 import originals,rich_table,reconcile\n original=originals();priorSlot='g103'if a.slot=='m701'else'm701';priorRun='beta-rc01-native01'if a.slot=='m701'else'beta-rc01-sdk-reconcile01';",
  " from aeris_runtime.continuation_l11 import m801_prior,rich_table,contract_check\n priorSlot='m801'if a.slot=='m901'else'm901';priorRun='beta-rc01-forensic-capture01'if a.slot=='m901'else'beta-rc01-sdk-continuation01';"),
 (" if a.slot=='m701':\n  priorBoot=original['priorKernelBootUUID'];path=original['baseAPK'][:-9]\n",
  " if a.slot=='m901':\n  priorBoot,path=m801_prior()\n"),
 ("priorPath=R/'evidence/betarc01/m701/reports/coldboot-h7.json'","priorPath=R/'evidence/betarc01/m901/reports/coldboot-h7.json'"),
 ("run='beta-rc01-sdk-reconcile01'if a.slot=='m701'else'beta-rc01-sdk-reconcile02';need(intent.get('format')=='aeris-h7-root-sdk-positive-intent'",
  "run='beta-rc01-sdk-continuation01'if a.slot=='m901'else'beta-rc01-sdk-continuation02';need(intent.get('format')=='aeris-linuxport01-l11-root-sdk-positive-intent'"),
 ("semantic=reconcile(backup['path'],backup['sha256'],source_candidate=a.candidate_sha,native_apk_sha=manifest['native']['APK_SHA256'],native_source_sha=manifest['native']['sourceSHA256']);need(a.slot!='m702'or",
  "semantic=contract_check(backup['path'],backup['sha256'],manifest);need(a.slot!='m902'or"),
 ("'reconciliation':semantic,","'continuation':semantic,"),
]


def apply(text,patches,name):
 for old,new in patches:
  n=text.count(old)
  if n!=1:raise ValueError('L11_PATCH_ANCHOR_NOT_UNIQUE:%s:%d:%r'%(name,n,old[:60]))
  text=text.replace(old,new)
 return text
