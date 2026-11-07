"""LINUXPORT01 exact patches for runtime-l17 (team decisions, not the owner's).

runtime-l17 is runtime-l16 plus a new team G1 chain from the same pinned state: qualification boots
m907, m908 and the G1 slot g109 on one candidate, as runtime-l16 did for m905/m906/g108. Decided
2026-11-07 by the user (Thinh) in chat, not the owner (report 4zzs):

1. g108 attempt 1 failed after native session 1 (emulator 37.2.12 most likely crashed at the app
   force-stop) and left the app data changed. The user chose path A: the AVD was restored to the
   backup taken right after m906 (avd-before-g108.tar = avd-after-m906.tar, the contract-l16
   state, 4 active journals). So the data admission stays contract-l16 (pin 15039006...) and the
   team copy of VERIFY_NATIVE_UNUSED17 stays planning/linuxport01/runtime-l16/native-unused-l16.mjs,
   both unchanged (the alias in product_inputs.py is not touched).
2. The chain runs with a new team emulator spec (emulator-spec-02.json, emulator 37.3.8). Every
   intent binds the spec SHA-256, so m905/m906 (old spec, old candidate) do not carry over and the
   used slots m905, m906, g108 cannot be reused. The new team module continuation_l17.py is
   continuation_l16.py moved to the new slots; the prior boot of m907 is the clean m906 boot of
   runtime-l16 (candidate b07badbf...), the last boot of the restored AVD state, read back from its
   own raw records with the harness readers (as m905 read back m803).

The writer limit (200 ms), the 40 MiB artifact cap, the 64 MiB Private bound (bound to the pinned
m803 TAR) and every other guard are unchanged. Every file below is generated from its runtime-l16
original by these replacements, and test-linuxport17.py re-derives each one. In MODULES and the
entries each `old` must occur exactly once; in NEW_MODULE each `old` must occur exactly the given
number of times.
"""

L16_CANDIDATE='b07badbf8e31d19d62bba7133ffd9cb34634660eb963f556d132d4a87784840d'

# Source modules: runtime-l16/source/aeris_runtime/<name> -> runtime-l17/source/aeris_runtime/<name>
MODULES={
 'mission16.py':[
  ("SLOTS={'m905':180,","SLOTS={'m907':180,'m908':180,'g109':180,'m905':180,"),
 ],
 'rc01.py':[
  ("KINDS={'g108':'native',","KINDS={'g109':'native','g108':'native',"),
  ("REMAINING={'g108':0,","REMAINING={'g109':0,'g108':0,"),
  ("ARCHIVE_BOUNDARY['g108']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n",
   "ARCHIVE_BOUNDARY['g108']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\nARCHIVE_BOUNDARY['g109']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n"),
 ],
 'product_runtime.py':[
  ("'m903','m904','m905','m906')and not c['APStarted']","'m903','m904','m905','m906','m907','m908')and not c['APStarted']"),
  ("  elif self.root.name in('m905','m906'):\n   from .continuation_l16 import verify_sdk\n   verify_sdk(self,proof)\n",
   "  elif self.root.name in('m905','m906'):\n   from .continuation_l16 import verify_sdk\n   verify_sdk(self,proof)\n  elif self.root.name in('m907','m908'):\n   from .continuation_l17 import verify_sdk\n   verify_sdk(self,proof)\n"),
  ("if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906')else",
   "if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908')else"),
  ("  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906'):result.update",
   "  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908'):result.update"),
  ("  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')",
   "  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')"),
 ],
 'product_native09.py':[
  (" if domain.get('nativeLifecycleContinuationL16')is True:\n  from .continuation_l16 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n",
   " if domain.get('nativeLifecycleContinuationL16')is True:\n  from .continuation_l16 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n if domain.get('nativeLifecycleContinuationL17')is True:\n  from .continuation_l17 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n"),
 ],
}

# New team module: runtime-l16/source/aeris_runtime/continuation_l16.py -> runtime-l17/source/aeris_runtime/continuation_l17.py
NEW_MODULE_SOURCE='continuation_l16.py';NEW_MODULE='continuation_l17.py'
OLD_PRIOR='''def m803_prior():
 """Prior boot UUID and codePath for m905, read back from the team m803 forensic capture with the harness readers."""
 repo=repository();root=repo/M803;j=lambda rel:decode((root/rel).read_bytes())
 report=j('reports/forensic-capture-h10.json');term=j('reports/owner-terminal.json');closure=j('guardian/closure.json');pin=decode((repo/PIN).read_bytes())
 need(report.get('format')=='aeris-h10-forensic-raw-observation'and report.get('status')=='COMPLETE_ORIGINAL_CAPTURE_AWAITING_GENUINE_SDK_CLOSE_AND_INDEPENDENT_SEMANTICS'and term.get('status')=='FORENSIC_CAPTURE_CLOSED_AWAITING_INDEPENDENT_SEMANTICS_NOT_QUALIFICATION_NOT_G1','M803_FORENSIC_SCOPE')
 need(type(closure.get('exit'))is int and closure['exit']==0 and closure.get('failure')is None and closure.get('exceptionalPhysicalDisposal')is False and closure.get('cleanupNotes')==[]and closure.get('durablyDrained')is True and all(v.get('captureComplete')is True and v.get('failure')is None for v in closure['outputCapture'].values()),'M803_ORIGINAL_NORMAL_SDK_CLOSURE')
 need(report['rootPrivateBackup']['sha256']==pin['source']['sha256']and sha((root/'reports/forensic-capture-h10.json').read_bytes())==pin['source']['captureReport']['sha256'],'M803_IS_PINNED_CAPTURE')
 store=root/'sessions'/M803_RUN/'android-api';last=report['samples'][-1]
 _,out,_=original_command(store,last['commandRefs']['dump'],['dumpsys','package',PACKAGE]);path=package_state(out,broken=False)
 _,out,_=original_command(store,last['commandRefs']['boot'],BOOT);boot=out.decode().strip()
 need(path==report['baseAPK']and re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',boot)is not None,'M803_ORIGINAL_CODEPATH_BOOT');return boot,path
'''
NEW_PRIOR='''def m906_prior():
 """Prior boot UUID and codePath for m907, read back with the harness readers from the team m906 qualification boot of
 runtime-l16 (candidate b07badbf...): the last boot of the pinned state, to which the AVD was restored (report 4zzs).
 Its own raw records must show a normal SDK closure, its own TAR must be the pinned m803 state TAR, and both samples
 must show the same boot (as the owner's verify_sdk requires of a qualification boot)."""
 repo=repository();root=repo/M906;j=lambda rel:decode((root/rel).read_bytes())
 report=j('reports/coldboot-h7.json');term=j('reports/owner-terminal.json');closure=j('guardian/closure.json');process=j('diagnostics/guardian-process/close.json');pin=decode((repo/PIN).read_bytes())
 need(report.get('format')=='aeris-h7-sdk-positive-observation'and report.get('status')=='SDK_ONLY_ORIGINALS_OBSERVED_AWAITING_NORMAL_CLOSE'and report.get('candidateSHA256')==L16_CANDIDATE and term.get('status')=='SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE'and term.get('candidateSHA256')==L16_CANDIDATE,'M906_QUALIFICATION_SCOPE')
 need(type(closure.get('exit'))is int and closure['exit']==0 and closure.get('failure')is None and closure.get('exceptionalPhysicalDisposal')is False and closure.get('cleanupNotes')==[]and closure.get('durablyDrained')is True and all(v.get('captureComplete')is True and v.get('failure')is None for v in closure['outputCapture'].values())and type(process.get('exit'))is int and process['exit']==0,'M906_ORIGINAL_NORMAL_SDK_CLOSURE')
 backup=report['rootPrivateBackup'];tar=root/'sessions'/M906_RUN/'native-restart-metadata.tar'
 need(backup['sha256']==pin['source']['sha256']and backup['bytes']==pin['source']['bytes']and sha(tar.read_bytes())==pin['source']['sha256'],'M906_IS_PINNED_STATE')
 store=root/'sessions'/M906_RUN/'android-api';boots=[]
 for s in report['samples']:
  _,out,_=original_command(store,s['commandRefs']['boot'],BOOT);boots.append(out.decode().strip())
 _,out,_=original_command(store,report['samples'][-1]['commandRefs']['dump'],['dumpsys','package',PACKAGE]);path=package_state(out,broken=False);boot=boots[-1]
 need(len(boots)==2 and boots[0]==boot and path==report['baseAPK']and re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',boot)is not None and boot!=report['priorKernelBootUUID'],'M906_ORIGINAL_CODEPATH_BOOT');return boot,path
'''
NEW_MODULE_PATCHES=[
 ('''"""LINUXPORT01 continuation admission for the team m803 state (team code, not the owner's).

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
"""''','''"""LINUXPORT01 continuation admission for the team m803 state (team code, not the owner's).

continuation_l16.py (runtime-l16) for a new chain (m907/m908 qualification, G1 g109) from the
same pinned 89-file state, after g108 attempt 1 failed and the AVD was restored to the backup
taken right after m906 (the user's decision, path A, report 4zzs), with the team emulator spec
emulator-spec-02.json. Only the slots, the run names, the format names and the prior boot of the
first qualification boot (now the clean m906 boot of runtime-l16) change. Replaces, for these
slots only, the three places where the owner's chain admits the private data with
reconcile_h7.reconcile (the post-g103 75-file decoder): the SDK boot check (owner: verify_sdk for
m701/m702), the G1 start (owner: resume_existing) and the cold domain check (owner:
verify_resume_domain). Each keeps the owner's original command, order, capture and closure
checks; only the data admission is the team contract planning/linuxport01/contract-l16 (pin
15039006..., unchanged), loaded from the frozen source graph. As in continuation_l13,
case['backup17'] is the owner's n02 pre-migration original. Nothing here grants archive,
resume, APPLY or flight authority, closes the open journal, or imports reconcile_h7.
runtime-l14 (team decision, kept): require_qualification bounds each boot's Private reference
(its private-files TAR) at 64 MiB instead of 256 KiB, only at that boot's capture path and
only with the pinned m803 TAR SHA-256 and size; every other reference keeps the owner's bound.
"""''',1),
 ("M803='evidence/betarc01/m803';M803_RUN='beta-rc01-forensic-capture03'\nSLOTS=('m905','m906');QUALIFICATION='aeris-linuxport01-l16-root-contract-sdk-cold-acceptance'\nRUNS={'m905':'beta-rc01-sdk-continuation05','m906':'beta-rc01-sdk-continuation06'}",
  "M906='evidence/betarc01/m906';M906_RUN='beta-rc01-sdk-continuation06';L16_CANDIDATE='"+L16_CANDIDATE+"'\nSLOTS=('m907','m908');QUALIFICATION='aeris-linuxport01-l17-root-contract-sdk-cold-acceptance'\nRUNS={'m907':'beta-rc01-sdk-continuation07','m908':'beta-rc01-sdk-continuation08'}",1),
 ("raise ValueError('L16_'+n)","raise ValueError('L17_'+n)",1),
 ("'aeris-linuxport01-l16-continuation-admission'","'aeris-linuxport01-l17-continuation-admission'",1),
 (OLD_PRIOR,NEW_PRIOR,1),
 ("reconcile_h7.require_qualification with the team m905/m906 proof format","reconcile_h7.require_qualification with the team m907/m908 proof format",1),
 ("'SOURCE_BOUND_L16_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'","'SOURCE_BOUND_L17_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'",1),
 ("reconcile_h7.verify_sdk for m905/m906:","reconcile_h7.verify_sdk for m907/m908:",1),
 ("if owner.root.name=='m906':\n  prior=decode((owner.repo/'evidence/betarc01/m905/reports/coldboot-h7.json')","if owner.root.name=='m908':\n  prior=decode((owner.repo/'evidence/betarc01/m907/reports/coldboot-h7.json')",1),
 ("'aeris-linuxport01-l16-continuation-readonly-resume'","'aeris-linuxport01-l17-continuation-readonly-resume'",2),
 ("reconcile_h7.resume_existing for g108:","reconcile_h7.resume_existing for g109:",1),
 ("resumeL16Attempted","resumeL17Attempted",2),
 ("'native17-continuation-l16.json'","'native17-continuation-l17.json'",2),
 ("case['resumeL16']=proof","case['resumeL17']=proof",1),
 ("'nativeLifecycleContinuationL16'","'nativeLifecycleContinuationL17'",2),
 ("'application-domain17-continuation-l16.json'","'application-domain17-continuation-l17.json'",1),
]

# Qualification entry: runtime-l16/root-qualify-l16.py -> runtime-l17/root-qualify-l17.py
QUALIFY_SOURCE='planning/linuxport01/runtime-l16/root-qualify-l16.py'
QUALIFY=[
 ('"""LINUXPORT01 (team entry): fresh coldboot qualification m905/m906 checked by the m803 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, then runtime-l16/l16_patches.py. No install, Activity, AP or automatic repair."""',
  '"""LINUXPORT01 (team entry): fresh coldboot qualification m907/m908 checked by the m803 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, then runtime-l17/l17_patches.py. No install, Activity, AP or automatic repair."""'),
 ("choices=('m905','m906')","choices=('m907','m908')"),
 ("proof.get('format')=='aeris-linuxport01-l16-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M803_FORENSIC_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m905'else",
  "proof.get('format')=='aeris-linuxport01-l17-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M906_L16_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m907'else"),
 (" from aeris_runtime.continuation_l16 import m803_prior,rich_table,contract_check\n priorSlot='m803'if a.slot=='m905'else'm905';priorRun='beta-rc01-forensic-capture03'if a.slot=='m905'else'beta-rc01-sdk-continuation05';",
  " from aeris_runtime.continuation_l17 import m906_prior,rich_table,contract_check\n priorSlot='m906'if a.slot=='m907'else'm907';priorRun='beta-rc01-sdk-continuation06'if a.slot=='m907'else'beta-rc01-sdk-continuation07';"),
 (" if a.slot=='m905':\n  priorBoot,path=m803_prior()\n"," if a.slot=='m907':\n  priorBoot,path=m906_prior()\n"),
 ("priorPath=R/'evidence/betarc01/m905/reports/coldboot-h7.json'","priorPath=R/'evidence/betarc01/m907/reports/coldboot-h7.json'"),
 ("run='beta-rc01-sdk-continuation05'if a.slot=='m905'else'beta-rc01-sdk-continuation06';need(intent.get('format')=='aeris-linuxport01-l16-root-sdk-positive-intent'",
  "run='beta-rc01-sdk-continuation07'if a.slot=='m907'else'beta-rc01-sdk-continuation08';need(intent.get('format')=='aeris-linuxport01-l17-root-sdk-positive-intent'"),
 ("need(a.slot!='m906'or","need(a.slot!='m908'or"),
]

# G1 entry: runtime-l16/root-native-l16.py -> runtime-l17/root-native-l17.py
NATIVE_SOURCE='planning/linuxport01/runtime-l16/root-native-l16.py'
NATIVE=[
 ('"""LINUXPORT01 (team entry): source-held native-only G1 slot g108 from the m803 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, then runtime-l16/l16_patches.py. Never starts AP/backend or flight."""',
  '"""LINUXPORT01 (team entry): source-held native-only G1 slot g109 from the m803 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, then runtime-l17/l17_patches.py. Never starts AP/backend or flight."""'),
 ("choices=('g108',)","choices=('g109',)"),
 ("from aeris_runtime.continuation_l16 import require_qualification,resume_continuation\n","from aeris_runtime.continuation_l17 import require_qualification,resume_continuation\n"),
]

def gate(text):
 """runtime-l16/prepare-source-gate.py -> runtime-l17: entries point at runtime-l17, and the two new entries replace
 root-native-l16.py and root-qualify-l16.py (they only accept the used slots g108, m905, m906). Reads are unchanged:
 contract-l16 stays pinned, and the team verifier runtime-l16/native-unused-l16.mjs stays reached through the alias."""
 assert text.count('runtime-l16')==4,'L17_GATE_BASE'
 for a,b in(("'planning/linuxport01/runtime-l16/root-native-l16.py'","'planning/linuxport01/runtime-l17/root-native-l17.py'"),("'planning/linuxport01/runtime-l16/root-qualify-l16.py'","'planning/linuxport01/runtime-l17/root-qualify-l17.py'")):
  assert text.count(a)==1,'L17_GATE_ENTRY';text=text.replace(a,b)
 return text.replace('runtime-l16','runtime-l17')

def apply(text,patches,name):
 for old,new in patches:
  n=text.count(old)
  if n!=1:raise ValueError('L17_PATCH_ANCHOR_NOT_UNIQUE:%s:%d:%r'%(name,n,old[:60]))
  text=text.replace(old,new)
 return text

def apply_counted(text,patches,name):
 for old,new,count in patches:
  n=text.count(old)
  if n!=count:raise ValueError('L17_PATCH_ANCHOR_COUNT:%s:%d!=%d:%r'%(name,n,count,old[:60]))
  text=text.replace(old,new)
 return text
