"""LINUXPORT01 exact patches for runtime-l13 (team decisions, not the owner's).

runtime-l13 is runtime-l12 plus the next team G1 chain from the post-g106 state:
qualification boots m903, m904 and the G1 slot g107 on one candidate, as in plan A
(runtime-l11: m901, m902, g106), with two changes:

1. The data admission is contract-l12 (pin 4689767d..., the 87-file state captured as
   m802) instead of contract-l10 (the 83-file m801 state, which no longer exists).
2. The fix of the bug that failed g106 attempt 1. native17.archive_check keeps every file
   of case['backup17'] byte-identical after each stage. The owner's resume_existing sets
   it to the n02 pre-migration original (adoption17.retained_originals17); the team's
   continuation_l11.resume_continuation set it to the current capture, whose append-only
   registry grows in every native session. continuation_l13 uses the owner's original, and
   also takes coldProof17 and workspaceBefore17 from it, as resume_existing does.

Every file below is generated from its runtime-l12 original by these replacements, and
test-linuxport13.py re-derives each one. In MODULES and the entries each `old` must occur
exactly once; in NEW_MODULE each `old` must occur exactly the given number of times.
"""

# Source modules: runtime-l12/source/aeris_runtime/<name> -> runtime-l13/source/aeris_runtime/<name>
MODULES={
 'mission16.py':[
  ("SLOTS={'m802':180,","SLOTS={'m903':180,'m904':180,'g107':180,'m802':180,"),
 ],
 'rc01.py':[
  ("KINDS={'g106':'native',","KINDS={'g107':'native','g106':'native',"),
  ("REMAINING={'g106':0,","REMAINING={'g107':0,'g106':0,"),
  ("ARCHIVE_BOUNDARY['g106']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n",
   "ARCHIVE_BOUNDARY['g106']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\nARCHIVE_BOUNDARY['g107']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n"),
 ],
 'product_runtime.py':[
  ("self.root.name in('m101','m102','m201','m202','m303','m401','m402','m501','m502','m701','m702','m801','m802','m901','m902')",
   "self.root.name in('m101','m102','m201','m202','m303','m401','m402','m501','m502','m701','m702','m801','m802','m901','m902','m903','m904')"),
  ("  elif self.root.name in('m901','m902'):\n   from .continuation_l11 import verify_sdk\n   verify_sdk(self,proof)\n",
   "  elif self.root.name in('m901','m902'):\n   from .continuation_l11 import verify_sdk\n   verify_sdk(self,proof)\n  elif self.root.name in('m903','m904'):\n   from .continuation_l13 import verify_sdk\n   verify_sdk(self,proof)\n"),
  ("if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902')else",
   "if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904')else"),
  ("  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902'):result.update",
   "  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904'):result.update"),
  ("  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')",
   "  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')"),
 ],
 'product_native09.py':[
  (" if domain.get('nativeLifecycleContinuationL11')is True:\n  from .continuation_l11 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n",
   " if domain.get('nativeLifecycleContinuationL11')is True:\n  from .continuation_l11 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n if domain.get('nativeLifecycleContinuationL13')is True:\n  from .continuation_l13 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n"),
 ],
}

# New team module: runtime-l12/source/aeris_runtime/continuation_l11.py -> runtime-l13/source/aeris_runtime/continuation_l13.py
NEW_MODULE_SOURCE='continuation_l11.py';NEW_MODULE='continuation_l13.py'
NEW_MODULE_PATCHES=[
 ('''"""LINUXPORT01 continuation admission for the team m801 state (team code, not the owner's).

Replaces, for the new slots only, the three places where the owner's chain admits
the private data with reconcile_h7.reconcile (the post-g103 75-file decoder):
the m901/m902 SDK boot check (owner: verify_sdk for m701/m702), the G1 start
(owner: resume_existing) and the cold domain check (owner: verify_resume_domain).
Each keeps the owner's original command, order, capture and closure checks; only
the data admission is the team contract planning/linuxport01/contract-l10
(pin b5318c62...), loaded from the frozen source graph. Nothing here grants
archive, resume, APPLY or flight authority, and reconcile_h7 is not imported.
"""''','''"""LINUXPORT01 continuation admission for the team m802 state (team code, not the owner's).

continuation_l11.py for the next chain (m903/m904 qualification, G1 g107) from the
87-file state left by g106 attempt 1. Replaces, for these slots only, the three places
where the owner's chain admits the private data with reconcile_h7.reconcile (the
post-g103 75-file decoder): the SDK boot check (owner: verify_sdk for m701/m702), the G1
start (owner: resume_existing) and the cold domain check (owner: verify_resume_domain).
Each keeps the owner's original command, order, capture and closure checks; only the
data admission is the team contract planning/linuxport01/contract-l12 (pin 4689767d...),
loaded from the frozen source graph. resume_continuation also fixes the continuation_l11
bug that failed g106 attempt 1: case['backup17'] is the owner's n02 pre-migration
original, as in resume_existing, not the current capture. Nothing here grants archive,
resume, APPLY or flight authority, and reconcile_h7 is not imported.
"""''',1),
 ("CONTRACT='planning/linuxport01/contract-l10/continuation_l10.py'\nPIN='planning/linuxport01/contract-l10/m801-continuation-pin.json'\nPIN_SHA='b5318c628ae0e1a2638988752baa18b2f3dcad682bb2c649e564dd06ef2c778d'\nM801='evidence/betarc01/m801';M801_RUN='beta-rc01-forensic-capture01'\nSLOTS=('m901','m902');QUALIFICATION='aeris-linuxport01-l11-root-contract-sdk-cold-acceptance'",
  "CONTRACT='planning/linuxport01/contract-l12/continuation_l12.py'\nPIN='planning/linuxport01/contract-l12/m802-continuation-pin.json'\nPIN_SHA='4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45'\nM802='evidence/betarc01/m802';M802_RUN='beta-rc01-forensic-capture02'\nSLOTS=('m903','m904');QUALIFICATION='aeris-linuxport01-l13-root-contract-sdk-cold-acceptance'",1),
 ("raise ValueError('L11_'+n)","raise ValueError('L13_'+n)",1),
 ("'linuxport01_continuation_l10'","'linuxport01_continuation_l12'",1),
 ("as the pinned m801 continuation state","as the pinned m802 continuation state",1),
 ("'aeris-linuxport01-l11-continuation-admission'","'aeris-linuxport01-l13-continuation-admission'",1),
 ('def m801_prior():\n """Prior boot UUID and codePath for m901, read back from the team m801 forensic capture with the harness readers."""',
  'def m802_prior():\n """Prior boot UUID and codePath for m903, read back from the team m802 forensic capture with the harness readers."""',1),
 ("root=repo/M801;","root=repo/M802;",1),
 ("'M801_FORENSIC_SCOPE'","'M802_FORENSIC_SCOPE'",1),
 ("'M801_ORIGINAL_NORMAL_SDK_CLOSURE'","'M802_ORIGINAL_NORMAL_SDK_CLOSURE'",1),
 ("'M801_IS_PINNED_CAPTURE'","'M802_IS_PINNED_CAPTURE'",1),
 ("store=root/'sessions'/M801_RUN/'android-api'","store=root/'sessions'/M802_RUN/'android-api'",1),
 ("'M801_ORIGINAL_CODEPATH_BOOT'","'M802_ORIGINAL_CODEPATH_BOOT'",1),
 ("with the team m901/m902 proof format","with the team m903/m904 proof format",1),
 ("'SOURCE_BOUND_L11_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'","'SOURCE_BOUND_L13_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'",1),
 ("reconcile_h7.verify_sdk for m901/m902:","reconcile_h7.verify_sdk for m903/m904:",1),
 ("if owner.root.name=='m902':\n  prior=decode((owner.repo/'evidence/betarc01/m901/reports/coldboot-h7.json')","if owner.root.name=='m904':\n  prior=decode((owner.repo/'evidence/betarc01/m903/reports/coldboot-h7.json')",1),
 ("'aeris-linuxport01-l11-continuation-readonly-resume'","'aeris-linuxport01-l13-continuation-readonly-resume'",2),
 ("reconcile_h7.resume_existing for g106:","reconcile_h7.resume_existing for g107:",1),
 (" from .rc01 import generation_forecast\n"," from .rc01 import generation_forecast\n from .adoption17 import retained_originals17\n",1),
 ("resumeL11Attempted","resumeL13Attempted",2),
 ("'native17-continuation-l11.json'","'native17-continuation-l13.json'",2),
 ("receiver=receiver_originals(backup['path'],backup['sha256'])\n",
  "receiver=receiver_originals(backup['path'],backup['sha256'])\n"
  " # The fix of continuation_l11 (g106 attempt 1): native17.archive_check keeps every file of backup17 byte-identical\n"
  " # after each stage, so, as in the owner's resume_existing, it is the n02 pre-migration original, not this capture\n"
  " # (whose append-only registry grows in every native session). The original's receiver must be the pinned one.\n"
  " retained=retained_originals17();need(retained['receiver']['reportSHA256']==receiver['reportSHA256']and retained['receiver']['planSHA256']==receiver['planSHA256'],'RETAINED_ORIGINALS_ARE_PINNED_RECEIVER')\n",1),
 (" case['resumeL11']=proof;case['backup17']=backup;case['receiver17']=receiver;case['workspaceBefore17']=workspace17(backup['path']);",
  " case['resumeL13']=proof;case['backup17']=retained['backup'];case['coldProof17']=retained['coldProof'];case['receiver17']=receiver;case['workspaceBefore17']=workspace17(retained['backup']['path']);",1),
 ("'nativeLifecycleContinuationL11'","'nativeLifecycleContinuationL13'",2),
 ("'application-domain17-continuation-l11.json'","'application-domain17-continuation-l13.json'",1),
]

# Qualification entry: runtime-l12/root-qualify-l11.py -> runtime-l13/root-qualify-l13.py
QUALIFY_SOURCE='planning/linuxport01/runtime-l12/root-qualify-l11.py'
QUALIFY=[
 ('"""LINUXPORT01 (team entry): fresh coldboot qualification m901/m902 checked by the m801 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py. No install, Activity, AP or automatic repair."""',
  '"""LINUXPORT01 (team entry): fresh coldboot qualification m903/m904 checked by the m802 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, then runtime-l13/l13_patches.py. No install, Activity, AP or automatic repair."""'),
 ("choices=('m901','m902')","choices=('m903','m904')"),
 ("proof.get('format')=='aeris-linuxport01-l11-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M801_FORENSIC_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m901'else",
  "proof.get('format')=='aeris-linuxport01-l13-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M802_FORENSIC_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m903'else"),
 (" from aeris_runtime.continuation_l11 import m801_prior,rich_table,contract_check\n priorSlot='m801'if a.slot=='m901'else'm901';priorRun='beta-rc01-forensic-capture01'if a.slot=='m901'else'beta-rc01-sdk-continuation01';",
  " from aeris_runtime.continuation_l13 import m802_prior,rich_table,contract_check\n priorSlot='m802'if a.slot=='m903'else'm903';priorRun='beta-rc01-forensic-capture02'if a.slot=='m903'else'beta-rc01-sdk-continuation03';"),
 (" if a.slot=='m901':\n  priorBoot,path=m801_prior()\n"," if a.slot=='m903':\n  priorBoot,path=m802_prior()\n"),
 ("priorPath=R/'evidence/betarc01/m901/reports/coldboot-h7.json'","priorPath=R/'evidence/betarc01/m903/reports/coldboot-h7.json'"),
 ("run='beta-rc01-sdk-continuation01'if a.slot=='m901'else'beta-rc01-sdk-continuation02';need(intent.get('format')=='aeris-linuxport01-l11-root-sdk-positive-intent'",
  "run='beta-rc01-sdk-continuation03'if a.slot=='m903'else'beta-rc01-sdk-continuation04';need(intent.get('format')=='aeris-linuxport01-l13-root-sdk-positive-intent'"),
 ("need(a.slot!='m902'or","need(a.slot!='m904'or"),
]

# G1 entry: runtime-l12/root-native-l11.py -> runtime-l13/root-native-l13.py
NATIVE_SOURCE='planning/linuxport01/runtime-l12/root-native-l11.py'
NATIVE=[
 ('"""LINUXPORT01 (team entry): source-held native-only G1 slot g106 from the m801 continuation contract.\nOwner root-native-h10.py plus l11_patches.py. Never starts AP/backend or flight."""',
  '"""LINUXPORT01 (team entry): source-held native-only G1 slot g107 from the m802 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, then runtime-l13/l13_patches.py. Never starts AP/backend or flight."""'),
 ("choices=('g106',)","choices=('g107',)"),
 ("from aeris_runtime.continuation_l11 import require_qualification,resume_continuation\n","from aeris_runtime.continuation_l13 import require_qualification,resume_continuation\n"),
]

def gate(text):
 """runtime-l12/prepare-source-gate.py -> runtime-l13: entries point at runtime-l13, the two new entries replace
 root-native-l11.py and root-qualify-l11.py (they only accept the used slots g106, m901, m902), contract-l12 is pinned."""
 old_reads="'planning/linuxport01/contract-l10/m801-continuation-pin.json'];"
 assert text.count('runtime-l12')==4 and text.count(old_reads)==1,'L13_GATE_BASE'
 for a,b in(("'planning/linuxport01/runtime-l12/root-native-l11.py'","'planning/linuxport01/runtime-l13/root-native-l13.py'"),("'planning/linuxport01/runtime-l12/root-qualify-l11.py'","'planning/linuxport01/runtime-l13/root-qualify-l13.py'")):
  assert text.count(a)==1,'L13_GATE_ENTRY';text=text.replace(a,b)
 text=text.replace(old_reads,"'planning/linuxport01/contract-l10/m801-continuation-pin.json','planning/linuxport01/contract-l12/continuation_l12.py','planning/linuxport01/contract-l12/m802-continuation-pin.json'];")
 return text.replace('runtime-l12','runtime-l13')

def apply(text,patches,name):
 for old,new in patches:
  n=text.count(old)
  if n!=1:raise ValueError('L13_PATCH_ANCHOR_NOT_UNIQUE:%s:%d:%r'%(name,n,old[:60]))
  text=text.replace(old,new)
 return text

def apply_counted(text,patches,name):
 for old,new,count in patches:
  n=text.count(old)
  if n!=count:raise ValueError('L13_PATCH_ANCHOR_COUNT:%s:%d!=%d:%r'%(name,n,count,old[:60]))
  text=text.replace(old,new)
 return text
