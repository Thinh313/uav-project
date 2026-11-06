"""LINUXPORT01 exact patches for runtime-l16 (team decisions, not the owner's).

runtime-l16 is runtime-l15 plus the next team G1 chain from the post-g107 state: qualification
boots m905, m906 and the G1 slot g108 on one candidate, as runtime-l13 did for m903/m904/g107,
with two changes (decided 2026-11-07 by Claude under the user's delegation, report 4zzq):

1. The data admission is contract-l16 (pin 15039006..., the 89-file state captured as m803,
   with the journal g107 left committed and open) instead of contract-l12. The new team
   module continuation_l16.py is continuation_l13.py moved to that contract, its m803
   capture as the prior state, and the new slots; the runtime-l14 Private bound (64 MiB,
   own TAR path, pinned SHA/size) is kept and now binds the pinned m803 TAR.
2. The owner's final G1 check VERIFY_NATIVE_UNUSED17 (planning/betarc01/tar_profile_h7/
   native-unused-h7.mjs, "Strict initial UNUSED lifecycle/restart proof") fixes the shape of
   the first G1 after the g103 migration: 10 lifetime generations, exactly the 2 new journals
   active, 10 journals. No G1 from a continued state can pass it (g106 would end 12/4, g107
   13/5, g108 14/6). The product input graph maps that module, through the owner's own alias
   mechanism (product_inputs.ALIASES), to the team copy native-unused-l16.mjs: the owner's file
   with the shape moved to the pinned continuation, as strict: exactly 14 reserved and committed
   generations, 0 records, the 2 selected new journals plus exactly the 4 pinned earlier active
   journals (3 closed UNUSED, 1 open), each still exactly the AJ02 header, 14 journals, 6 active,
   8 archived. Every other check of the owner's verifier is unchanged; the owner's file is
   not modified.

The writer limit (200 ms), the 40 MiB artifact cap and every other guard are unchanged.
Every file below is generated from its runtime-l15 (or owner) original by these
replacements, and test-linuxport16.py re-derives each one. In MODULES, the entries and NODE
each `old` must occur exactly once; in NEW_MODULE each `old` must occur exactly the given
number of times.
"""

# Source modules: runtime-l15/source/aeris_runtime/<name> -> runtime-l16/source/aeris_runtime/<name>
MODULES={
 'mission16.py':[
  ("SLOTS={'m803':180,","SLOTS={'m905':180,'m906':180,'g108':180,'m803':180,"),
 ],
 'rc01.py':[
  ("KINDS={'g107':'native',","KINDS={'g108':'native','g107':'native',"),
  ("REMAINING={'g107':0,","REMAINING={'g108':0,'g107':0,"),
  ("ARCHIVE_BOUNDARY['g107']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n",
   "ARCHIVE_BOUNDARY['g107']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\nARCHIVE_BOUNDARY['g108']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n"),
 ],
 'product_runtime.py':[
  ("'m801','m802','m803','m901','m902','m903','m904')and not c['APStarted']","'m801','m802','m803','m901','m902','m903','m904','m905','m906')and not c['APStarted']"),
  ("  elif self.root.name in('m903','m904'):\n   from .continuation_l13 import verify_sdk\n   verify_sdk(self,proof)\n",
   "  elif self.root.name in('m903','m904'):\n   from .continuation_l13 import verify_sdk\n   verify_sdk(self,proof)\n  elif self.root.name in('m905','m906'):\n   from .continuation_l16 import verify_sdk\n   verify_sdk(self,proof)\n"),
  ("if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904')else",
   "if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906')else"),
  ("  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904'):result.update",
   "  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906'):result.update"),
  ("  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')",
   "  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')"),
 ],
 'product_native09.py':[
  (" if domain.get('nativeLifecycleContinuationL13')is True:\n  from .continuation_l13 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n",
   " if domain.get('nativeLifecycleContinuationL13')is True:\n  from .continuation_l13 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n if domain.get('nativeLifecycleContinuationL16')is True:\n  from .continuation_l16 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n"),
 ],
 'product_inputs.py':[
  ("'planning/nativejournal17/native-cold17.mjs':'planning/betarc01/tar_profile_h7/native-cold-h7.mjs',",
   "'planning/nativejournal17/native-cold17.mjs':'planning/betarc01/tar_profile_h7/native-cold-h7.mjs','planning/betarc01/tar_profile_h7/native-unused-h7.mjs':'planning/linuxport01/runtime-l16/native-unused-l16.mjs',"),
 ],
}

# New team module: runtime-l15/source/aeris_runtime/continuation_l13.py -> runtime-l16/source/aeris_runtime/continuation_l16.py
NEW_MODULE_SOURCE='continuation_l13.py';NEW_MODULE='continuation_l16.py'
NEW_MODULE_PATCHES=[
 ('''"""LINUXPORT01 continuation admission for the team m802 state (team code, not the owner's).

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
runtime-l14 (team decision): require_qualification bounds each boot's Private reference (its
private-files TAR) at 64 MiB instead of 256 KiB, only at that boot's capture path and only
with the pinned m802 TAR SHA-256; every other reference keeps the owner's bound.
"""''','''"""LINUXPORT01 continuation admission for the team m803 state (team code, not the owner's).

continuation_l13.py (runtime-l15) for the next chain (m905/m906 qualification, G1 g108) from
the 89-file state left by g107 attempt 1, which includes one journal the app committed and
never closed. Replaces, for these slots only, the three places where the owner's chain
admits the private data with reconcile_h7.reconcile (the post-g103 75-file decoder): the SDK
boot check (owner: verify_sdk for m701/m702), the G1 start (owner: resume_existing) and the
cold domain check (owner: verify_resume_domain). Each keeps the owner's original command,
order, capture and closure checks; only the data admission is the team contract
planning/linuxport01/contract-l16 (pin 15039006...), loaded from the frozen source graph.
As in continuation_l13, case['backup17'] is the owner's n02 pre-migration original.
Nothing here grants archive, resume, APPLY or flight authority, closes the open journal, or
imports reconcile_h7.
runtime-l14 (team decision, kept): require_qualification bounds each boot's Private reference
(its private-files TAR) at 64 MiB instead of 256 KiB, only at that boot's capture path and
only with the pinned m803 TAR SHA-256 and size; every other reference keeps the owner's bound.
"""''',1),
 ("CONTRACT='planning/linuxport01/contract-l12/continuation_l12.py'\nPIN='planning/linuxport01/contract-l12/m802-continuation-pin.json'\nPIN_SHA='4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45'\nM802='evidence/betarc01/m802';M802_RUN='beta-rc01-forensic-capture02'\nSLOTS=('m903','m904');QUALIFICATION='aeris-linuxport01-l13-root-contract-sdk-cold-acceptance'\nRUNS={'m903':'beta-rc01-sdk-continuation03','m904':'beta-rc01-sdk-continuation04'}",
  "CONTRACT='planning/linuxport01/contract-l16/continuation_l16.py'\nPIN='planning/linuxport01/contract-l16/m803-continuation-pin.json'\nPIN_SHA='15039006e060302d18acf0f45ce5304bdfb78d6fa1c4b8883f4016ee2f57ac95'\nM803='evidence/betarc01/m803';M803_RUN='beta-rc01-forensic-capture03'\nSLOTS=('m905','m906');QUALIFICATION='aeris-linuxport01-l16-root-contract-sdk-cold-acceptance'\nRUNS={'m905':'beta-rc01-sdk-continuation05','m906':'beta-rc01-sdk-continuation06'}",1),
 ("raise ValueError('L13_'+n)","raise ValueError('L16_'+n)",1),
 ("'linuxport01_continuation_l12'","'linuxport01_continuation_l16'",1),
 ("as the pinned m802 continuation state","as the pinned m803 continuation state",1),
 ("'aeris-linuxport01-l13-continuation-admission'","'aeris-linuxport01-l16-continuation-admission'",1),
 ('def m802_prior():\n """Prior boot UUID and codePath for m903, read back from the team m802 forensic capture with the harness readers."""',
  'def m803_prior():\n """Prior boot UUID and codePath for m905, read back from the team m803 forensic capture with the harness readers."""',1),
 ("root=repo/M802;","root=repo/M803;",1),
 ("'M802_FORENSIC_SCOPE'","'M803_FORENSIC_SCOPE'",1),
 ("'M802_ORIGINAL_NORMAL_SDK_CLOSURE'","'M803_ORIGINAL_NORMAL_SDK_CLOSURE'",1),
 ("'M802_IS_PINNED_CAPTURE'","'M803_IS_PINNED_CAPTURE'",1),
 ("store=root/'sessions'/M802_RUN/'android-api'","store=root/'sessions'/M803_RUN/'android-api'",1),
 ("'M802_ORIGINAL_CODEPATH_BOOT'","'M803_ORIGINAL_CODEPATH_BOOT'",1),
 (" \"\"\"reconcile_h7.require_qualification with the team m903/m904 proof format instead of the owner's m701/m702.\n Each Private reference is that boot's own TAR of the pinned m802 state, bounded at 64 MiB (runtime-l14).\"\"\"",
  " \"\"\"reconcile_h7.require_qualification with the team m905/m906 proof format instead of the owner's m701/m702.\n Each Private reference is that boot's own TAR of the pinned m803 state, bounded at 64 MiB (runtime-l14, kept).\"\"\"",1),
 (" # runtime-l14: the m802 state TAR (263,680 B) is above the owner's 256 KiB ref_file bound."," # runtime-l14 (kept): the m803 state TAR (268,800 B) is above the owner's 256 KiB ref_file bound.",1),
 ("'SOURCE_BOUND_L13_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'","'SOURCE_BOUND_L16_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'",1),
 ("reconcile_h7.verify_sdk for m903/m904:","reconcile_h7.verify_sdk for m905/m906:",1),
 ("if owner.root.name=='m904':\n  prior=decode((owner.repo/'evidence/betarc01/m903/reports/coldboot-h7.json')","if owner.root.name=='m906':\n  prior=decode((owner.repo/'evidence/betarc01/m905/reports/coldboot-h7.json')",1),
 ("'aeris-linuxport01-l13-continuation-readonly-resume'","'aeris-linuxport01-l16-continuation-readonly-resume'",2),
 ("reconcile_h7.resume_existing for g107:","reconcile_h7.resume_existing for g108:",1),
 ("resumeL13Attempted","resumeL16Attempted",2),
 ("'native17-continuation-l13.json'","'native17-continuation-l16.json'",2),
 ("case['resumeL13']=proof","case['resumeL16']=proof",1),
 ("'nativeLifecycleContinuationL13'","'nativeLifecycleContinuationL16'",2),
 ("'application-domain17-continuation-l13.json'","'application-domain17-continuation-l16.json'",1),
]

# Qualification entry: runtime-l15/root-qualify-l13.py -> runtime-l16/root-qualify-l16.py
QUALIFY_SOURCE='planning/linuxport01/runtime-l15/root-qualify-l13.py'
QUALIFY=[
 ('"""LINUXPORT01 (team entry): fresh coldboot qualification m903/m904 checked by the m802 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, then runtime-l13/l13_patches.py. No install, Activity, AP or automatic repair."""',
  '"""LINUXPORT01 (team entry): fresh coldboot qualification m905/m906 checked by the m803 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, then runtime-l16/l16_patches.py. No install, Activity, AP or automatic repair."""'),
 ("choices=('m903','m904')","choices=('m905','m906')"),
 ("proof.get('format')=='aeris-linuxport01-l13-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M802_FORENSIC_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m903'else",
  "proof.get('format')=='aeris-linuxport01-l16-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M803_FORENSIC_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m905'else"),
 (" from aeris_runtime.continuation_l13 import m802_prior,rich_table,contract_check\n priorSlot='m802'if a.slot=='m903'else'm903';priorRun='beta-rc01-forensic-capture02'if a.slot=='m903'else'beta-rc01-sdk-continuation03';",
  " from aeris_runtime.continuation_l16 import m803_prior,rich_table,contract_check\n priorSlot='m803'if a.slot=='m905'else'm905';priorRun='beta-rc01-forensic-capture03'if a.slot=='m905'else'beta-rc01-sdk-continuation05';"),
 (" if a.slot=='m903':\n  priorBoot,path=m802_prior()\n"," if a.slot=='m905':\n  priorBoot,path=m803_prior()\n"),
 ("priorPath=R/'evidence/betarc01/m903/reports/coldboot-h7.json'","priorPath=R/'evidence/betarc01/m905/reports/coldboot-h7.json'"),
 ("run='beta-rc01-sdk-continuation03'if a.slot=='m903'else'beta-rc01-sdk-continuation04';need(intent.get('format')=='aeris-linuxport01-l13-root-sdk-positive-intent'",
  "run='beta-rc01-sdk-continuation05'if a.slot=='m905'else'beta-rc01-sdk-continuation06';need(intent.get('format')=='aeris-linuxport01-l16-root-sdk-positive-intent'"),
 ("need(a.slot!='m904'or","need(a.slot!='m906'or"),
]

# G1 entry: runtime-l15/root-native-l13.py -> runtime-l16/root-native-l16.py
NATIVE_SOURCE='planning/linuxport01/runtime-l15/root-native-l13.py'
NATIVE=[
 ('"""LINUXPORT01 (team entry): source-held native-only G1 slot g107 from the m802 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, then runtime-l13/l13_patches.py. Never starts AP/backend or flight."""',
  '"""LINUXPORT01 (team entry): source-held native-only G1 slot g108 from the m803 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, then runtime-l16/l16_patches.py. Never starts AP/backend or flight."""'),
 ("choices=('g107',)","choices=('g108',)"),
 ("from aeris_runtime.continuation_l13 import require_qualification,resume_continuation\n","from aeris_runtime.continuation_l16 import require_qualification,resume_continuation\n"),
]

# Team copy of the owner's VERIFY_NATIVE_UNUSED17 module: planning/betarc01/tar_profile_h7/native-unused-h7.mjs -> runtime-l16/native-unused-l16.mjs
NODE_SOURCE='planning/betarc01/tar_profile_h7/native-unused-h7.mjs';NODE='native-unused-l16.mjs'
OLD_ACTIVE=('518ed1b94ef444cc9fdf22bebc0ecca7','6128a76bf4354629a749921c8fcb35b1','3a55c84087814dfca23b8b0b496ffa64','4ac33ff279f04d33b2e37276e794f780')
NODE_PATCHES=[
 ("/** Strict initial UNUSED lifecycle/restart proof. No flight, signature-input,\n * physical-HID or complete-filesystem antirollback credit. Root cold ADB replay\n * remains an independent required acceptance gate. */\n",
  "/** Strict initial UNUSED lifecycle/restart proof. No flight, signature-input,\n * physical-HID or complete-filesystem antirollback credit. Root cold ADB replay\n * remains an independent required acceptance gate. */\n"
  "/* LINUXPORT01 runtime-l16 (team copy, not the owner's; l16_patches.py): the owner's module with the fixed\n"
  " * shape of the first G1 after the g103 migration (10 generations, 2 active) moved to the team's pinned\n"
  " * continuation (contract-l16, m803): 12 earlier generations, of which exactly these 4 earlier journals are\n"
  " * still active (3 closed UNUSED, 1 left open by g107), each still exactly the AJ02 header. Same checks\n"
  " * otherwise; the owner's native-unused-h7.mjs is not modified. */\n"
  "const CONTINUATION_OLD_ACTIVE=new Set(['"+"','".join(OLD_ACTIVE)+"']),CONTINUATION_PRIOR_GENERATIONS=12;\n"),
 ("import{scanNativeTar}from'./native-tar.mjs';","import{scanNativeTar}from'../../betarc01/tar_profile_h7/native-tar.mjs';"),
 ("proof.counters?.reservedGenerations===10&&proof.counters?.committedGenerations===10",
  "proof.counters?.reservedGenerations===CONTINUATION_PRIOR_GENERATIONS+2&&proof.counters?.committedGenerations===CONTINUATION_PRIOR_GENERATIONS+2"),
 ("let total=0,found=0,journals=0;","let total=0,found=0,old=0,journals=0;"),
 ("if(r.path.startsWith('files/product-input01/')){need(selected.has(r.path.slice(-37,-5)),'UNUSED17_EXACT_ACTIVE_SET');found++;}",
  "if(r.path.startsWith('files/product-input01/')){const g=r.path.slice(-37,-5);need(selected.has(g)!==CONTINUATION_OLD_ACTIVE.has(g),'UNUSED17_EXACT_ACTIVE_SET');if(selected.has(g))found++;else old++;}"),
 ("found===2&&journals===10&&scan.activeJournals===2&&scan.archivedJournals===8",
  "found===2&&old===CONTINUATION_OLD_ACTIVE.size&&journals===8+CONTINUATION_OLD_ACTIVE.size+2&&scan.activeJournals===CONTINUATION_OLD_ACTIVE.size+2&&scan.archivedJournals===8"),
]

def gate(text):
 """runtime-l15/prepare-source-gate.py -> runtime-l16: entries point at runtime-l16, the two new entries replace
 root-native-l13.py and root-qualify-l13.py (they only accept the used slots g107, m903, m904), contract-l16 is pinned,
 and the owner's native-unused-h7.mjs is no longer a read input (it is replaced through an alias, see NODE)."""
 old_reads="'planning/linuxport01/contract-l12/m802-continuation-pin.json'];"
 assert text.count('runtime-l15')==4 and text.count(old_reads)==1,'L16_GATE_BASE'
 for a,b in(("'planning/linuxport01/runtime-l15/root-native-l13.py'","'planning/linuxport01/runtime-l16/root-native-l16.py'"),("'planning/linuxport01/runtime-l15/root-qualify-l13.py'","'planning/linuxport01/runtime-l16/root-qualify-l16.py'")):
  assert text.count(a)==1,'L16_GATE_ENTRY';text=text.replace(a,b)
 text=text.replace(old_reads,"'planning/linuxport01/contract-l12/m802-continuation-pin.json','planning/linuxport01/contract-l16/continuation_l16.py','planning/linuxport01/contract-l16/m803-continuation-pin.json'];")
 # The owner's native-unused-h7.mjs is now an alias key (to native-unused-l16.mjs); the loader refuses an alias whose key
 # is held, so it leaves the tar_profile_h7 read list (nothing reads it directly; it was only imported by native-cold-h7.mjs).
 h7="(REPO/'planning/betarc01/tar_profile_h7').iterdir()if q.is_file()and q.suffix in('.py','.mjs')and not q.name.startswith('test')]"
 assert text.count(h7)==1,'L16_GATE_H7_READS';text=text.replace(h7,h7[:-1]+"and q.name!='native-unused-h7.mjs']")
 return text.replace('runtime-l15','runtime-l16')

def apply(text,patches,name):
 for old,new in patches:
  n=text.count(old)
  if n!=1:raise ValueError('L16_PATCH_ANCHOR_NOT_UNIQUE:%s:%d:%r'%(name,n,old[:60]))
  text=text.replace(old,new)
 return text

def apply_counted(text,patches,name):
 for old,new,count in patches:
  n=text.count(old)
  if n!=count:raise ValueError('L16_PATCH_ANCHOR_COUNT:%s:%d!=%d:%r'%(name,n,count,old[:60]))
  text=text.replace(old,new)
 return text
