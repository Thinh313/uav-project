"""LINUXPORT01 exact patches for runtime-l19 (team decisions, not the owner's).

runtime-l19 is runtime-l18 plus (A) one fix of the team VERIFY_NATIVE_UNUSED17 module and (B) a new team G1 chain
m911/m912/g111, so that the next real G1 can run. Nothing else changes. All of it was proposed by Claude and approved by the
user (Thinh) in chat on 2026-11-14, not by the owner and not by Claude alone; the owner has not been asked or told.

Why (facts, from the g110 attempt 1 record evidence/linuxport01/G110-RESULT01.json and logs 2026-11-14/36-41):
the real G1 g110 on runtime-l18 (candidate 9e93fa50...) ran both native sessions, SEAL_PRODUCT and the final-close export and
then failed at VERIFY_NATIVE_UNUSED17: the team module planning/linuxport01/runtime-l16/native-unused-l16.mjs (sha256
0b16c943..., the alias target of the owner's planning/betarc01/tar_profile_h7/native-unused-h7.mjs, pinned in every candidate
since runtime-l16) reads fs.readFileSync(new URL('./native-tar.mjs',import.meta.url)) at run time, but native-tar.mjs sits in
planning/betarc01/tar_profile_h7/, not next to the team copy (ENOENT). runtime-l16's l16_patches.py had rewritten the static
import of that file but not this read. The code never ran before (g108 and g109 failed earlier; the l16-l18 tests only import
the module). The owner's 200 ms guards held in g110. Log 2026-11-14/41 (tools/l19_verify_unused_offline.mjs) showed the unchanged
module failing with the same ENOENT and the fixed module accepting g110's real recorded inputs.

The user's words (each answered one of Claude's questions; the design Claude presented is the one in this file):
 "Yes, present design"  (after "Review close path first": a read-only review of close_native_only/close_guardian found no
                         defect and no change needed there; they are the owner's code and stay unchanged)
 "Yes, write patches"   approval of the presented design with its five points: (1) minimal scope, nothing but the fix and the
                         new slots; (2) no header comment inside the fixed module, so its text is exactly the text tested in
                         log 2026-11-14/41 (sha256 04d5bd90...); (3) run names beta-rc01-sdk-continuation11,
                         beta-rc01-sdk-continuation12 and beta-rc01-native07; (4) the next chain starts again from the pinned
                         contract-l16 state ("Path A: pinned state"): the real AVD is restored from avd-before-g110.tar
                         (= avd-after-m910.tar), because the post-g110 app data (lifetime generation count 14) is refused by
                         contract-l16 and by the fixed verifier, which requires exactly 12 earlier generations (a separate
                         real step on the user's word); (5) the optional offline check of the close_native_only conditions
                         is a separate decision, not part of this file.

A. The fix
1. runtime-l19/native-unused-l19.mjs is the runtime-l16 team module (sha256 0b16c943..., asserted) with exactly one
   replacement: the run-time read of native-tar.mjs now uses the path the static import already used,
   ../../betarc01/tar_profile_h7/native-tar.mjs (runtime-l19 sits at the same folder depth as runtime-l16). The read still
   checks that file's sha256 against the descriptor's nodeReader.sha256. Result sha256 04d5bd90d5513bf8... (asserted).
2. product_inputs.ALIASES: the key planning/betarc01/tar_profile_h7/native-unused-h7.mjs now points at the l19 file. The
   source gate (prepare-source-gate.py --write) regenerates the two pin assets; the l16 file is no longer referenced.

B. G1 chain m911/m912/g111 (as l18_patches.py did for m909/m910/g110, "Path A: pinned state")
   g110 attempt 1 failed (G110-RESULT01.json) and left the app data changed. The chain starts from the pinned contract-l16
   state (avd-before-g110.tar = avd-after-m910.tar), to which the real AVD must be restored before the first boot (a separate
   step on the user's word). The data admission stays contract-l16 (pin 15039006...), the emulator spec is unchanged.
   continuation_l19.py is continuation_l18.py moved to the new slots; the prior boot of m911 is the clean m910 boot of
   runtime-l18 (candidate 9e93fa50...), read back from its own raw records as m909 read back m908.

Everything in runtime-l18's docstring (the Linux port of the G2/G3 path, forwarder, identity check, kernel) is unchanged. The
writer limit (200 ms), the 40 MiB artifact cap, the 64 MiB Private bound, close_native_only, close_guardian,
root-owner-h10.py (byte-identical to the owner's) and every guard not named here are unchanged. Every file below is generated
from its runtime-l18 original (or from runtime-l16/native-unused-l16.mjs) by these replacements, and test-linuxport19.py
re-derives each one. Each `old` must occur exactly once, or exactly the count given as a third element.
"""

L18_CANDIDATE='9e93fa50c5957f66ce0d1c382e84f58d779c9d663686fd782f76506229fcc921'

# ---------------------------------------------------------------------------------------------------------------
# A. The fixed verifier: runtime-l16/native-unused-l16.mjs -> runtime-l19/native-unused-l19.mjs
# ---------------------------------------------------------------------------------------------------------------
VERIFIER_SOURCE='planning/linuxport01/runtime-l16/native-unused-l16.mjs'
VERIFIER_SOURCE_SHA256='0b16c943772bb7b3244a7f40747952eb35bf3cac9f6782240b8b5f8caaa43edc'
VERIFIER_NAME='native-unused-l19.mjs'
VERIFIER_SHA256='04d5bd90d5513bf88afb7444c752b08d8e392bd1968784460cb444e2b1510f87'
VERIFIER_PATCHES=[
 ("fs.readFileSync(new URL('./native-tar.mjs',import.meta.url))",
  "fs.readFileSync(new URL('../../betarc01/tar_profile_h7/native-tar.mjs',import.meta.url))"),
]

# ---------------------------------------------------------------------------------------------------------------
# Source modules: runtime-l18/source/aeris_runtime/<name> -> runtime-l19/source/aeris_runtime/<name>
# ---------------------------------------------------------------------------------------------------------------
MODULES={
 # A2 the alias of the owner's unused verifier
 'product_inputs.py':[
  ("'planning/betarc01/tar_profile_h7/native-unused-h7.mjs':'planning/linuxport01/runtime-l16/native-unused-l16.mjs'",
   "'planning/betarc01/tar_profile_h7/native-unused-h7.mjs':'planning/linuxport01/runtime-l19/native-unused-l19.mjs'"),
 ],
 # B. G1 chain m911/m912/g111
 'mission16.py':[
  ("SLOTS={'m909':180,","SLOTS={'m911':180,'m912':180,'g111':180,'m909':180,"),
 ],
 'rc01.py':[
  ("KINDS={'g110':'native',","KINDS={'g111':'native','g110':'native',"),
  ("REMAINING={'g110':0,","REMAINING={'g111':0,'g110':0,"),
  ("ARCHIVE_BOUNDARY['g110']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n",
   "ARCHIVE_BOUNDARY['g110']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\nARCHIVE_BOUNDARY['g111']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n"),
 ],
 'product_runtime.py':[
  ("'m909','m910')and not c['APStarted']","'m909','m910','m911','m912')and not c['APStarted']"),
  ("  elif self.root.name in('m909','m910'):\n   from .continuation_l18 import verify_sdk\n   verify_sdk(self,proof)\n",
   "  elif self.root.name in('m909','m910'):\n   from .continuation_l18 import verify_sdk\n   verify_sdk(self,proof)\n  elif self.root.name in('m911','m912'):\n   from .continuation_l19 import verify_sdk\n   verify_sdk(self,proof)\n"),
  ("'m909','m910')else","'m909','m910','m911','m912')else"),
  ("'m909','m910'):result.update","'m909','m910','m911','m912'):result.update"),
  ("'m909','m910'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')","'m909','m910','m911','m912'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')"),
 ],
 'product_native09.py':[
  (" if domain.get('nativeLifecycleContinuationL18')is True:\n  from .continuation_l18 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n",
   " if domain.get('nativeLifecycleContinuationL18')is True:\n  from .continuation_l18 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n if domain.get('nativeLifecycleContinuationL19')is True:\n  from .continuation_l19 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n"),
 ],
}

# ---------------------------------------------------------------------------------------------------------------
# B. New team module: runtime-l18/source/aeris_runtime/continuation_l18.py -> runtime-l19/.../continuation_l19.py
# ---------------------------------------------------------------------------------------------------------------
NEW_MODULE_SOURCE='continuation_l18.py';NEW_MODULE='continuation_l19.py'
NEW_MODULE_PATCHES=[
 ('''continuation_l17.py (runtime-l17) for a new chain (m909/m910 qualification, G1 g110) from the
same pinned 89-file state, after g109 attempt 1 failed (owner guard NAVIGATION_ACTUAL_DISPATCH200MS);
the AVD must be restored to the backup taken right after m908 before the first boot (the user's
decision "Path A: pinned state", 2026-11-12), with the unchanged team emulator spec
emulator-spec-02.json. Only the slots, the run names, the format names and the prior boot of the
first qualification boot (now the clean m908 boot of runtime-l17) change. Replaces, for these''',
  '''continuation_l18.py (runtime-l18) for a new chain (m911/m912 qualification, G1 g111) from the
same pinned 89-file state, after g110 attempt 1 failed at VERIFY_NATIVE_UNUSED17 (a team code defect in the
team verifier's run-time read path, fixed in runtime-l19); the AVD must be restored to the backup taken right
after m910 (avd-before-g110.tar) before the first boot (the user's decision "Path A: pinned state", 2026-11-12,
repeated for this chain by "Yes, write patches", 2026-11-14), with the unchanged team emulator spec
emulator-spec-02.json. Only the slots, the run names, the format names and the prior boot of the
first qualification boot (now the clean m910 boot of runtime-l18) change. Replaces, for these'''),
 ("M908='evidence/betarc01/m908';M908_RUN='beta-rc01-sdk-continuation08';L17_CANDIDATE='70af1371a616595b8b8eaba2611ea0db3967d0f0bccade8be0eb92b41d279e6e'\nSLOTS=('m909','m910');QUALIFICATION='aeris-linuxport01-l18-root-contract-sdk-cold-acceptance'\nRUNS={'m909':'beta-rc01-sdk-continuation09','m910':'beta-rc01-sdk-continuation10'}",
  "M910='evidence/betarc01/m910';M910_RUN='beta-rc01-sdk-continuation10';L18_CANDIDATE='"+L18_CANDIDATE+"'\nSLOTS=('m911','m912');QUALIFICATION='aeris-linuxport01-l19-root-contract-sdk-cold-acceptance'\nRUNS={'m911':'beta-rc01-sdk-continuation11','m912':'beta-rc01-sdk-continuation12'}"),
 ("raise ValueError('L18_'+n)","raise ValueError('L19_'+n)"),
 ("'aeris-linuxport01-l18-continuation-admission'","'aeris-linuxport01-l19-continuation-admission'"),
 # the prior boot of the first qualification boot: m908 of runtime-l17 -> m910 of runtime-l18
 ("def m908_prior():\n","def m910_prior():\n"),
 (''' """Prior boot UUID and codePath for m909, read back with the harness readers from the team m908 qualification boot of
 runtime-l17 (candidate 70af1371...): the last boot of the pinned state, to which the AVD must be restored before
 this chain (the user's decision "Path A: pinned state", 2026-11-12).
''',''' """Prior boot UUID and codePath for m911, read back with the harness readers from the team m910 qualification boot of
 runtime-l18 (candidate 9e93fa50...): the last boot of the pinned state, to which the AVD must be restored before
 this chain (the user's decision "Path A: pinned state", repeated by "Yes, write patches", 2026-11-14).
'''),
 ("repo=repository();root=repo/M908;","repo=repository();root=repo/M910;"),
 ("report.get('candidateSHA256')==L17_CANDIDATE and term.get('status')=='SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE'and term.get('candidateSHA256')==L17_CANDIDATE,'M908_QUALIFICATION_SCOPE')",
  "report.get('candidateSHA256')==L18_CANDIDATE and term.get('status')=='SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE'and term.get('candidateSHA256')==L18_CANDIDATE,'M910_QUALIFICATION_SCOPE')"),
 ("'M908_ORIGINAL_NORMAL_SDK_CLOSURE'","'M910_ORIGINAL_NORMAL_SDK_CLOSURE'"),
 ("tar=root/'sessions'/M908_RUN/'native-restart-metadata.tar'","tar=root/'sessions'/M910_RUN/'native-restart-metadata.tar'"),
 ("'M908_IS_PINNED_STATE'","'M910_IS_PINNED_STATE'"),
 ("store=root/'sessions'/M908_RUN/'android-api'","store=root/'sessions'/M910_RUN/'android-api'"),
 ("'M908_ORIGINAL_CODEPATH_BOOT'","'M910_ORIGINAL_CODEPATH_BOOT'"),
 # the chain itself
 ("reconcile_h7.require_qualification with the team m909/m910 proof format","reconcile_h7.require_qualification with the team m911/m912 proof format"),
 ("'SOURCE_BOUND_L18_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'","'SOURCE_BOUND_L19_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'"),
 ("reconcile_h7.verify_sdk for m909/m910:","reconcile_h7.verify_sdk for m911/m912:"),
 ("if owner.root.name=='m910':\n  prior=decode((owner.repo/'evidence/betarc01/m909/reports/coldboot-h7.json')","if owner.root.name=='m912':\n  prior=decode((owner.repo/'evidence/betarc01/m911/reports/coldboot-h7.json')"),
 ("'aeris-linuxport01-l18-continuation-readonly-resume'","'aeris-linuxport01-l19-continuation-readonly-resume'",2),
 ("reconcile_h7.resume_existing for g110:","reconcile_h7.resume_existing for g111:"),
 ("resumeL18Attempted","resumeL19Attempted",2),
 ("'native17-continuation-l18.json'","'native17-continuation-l19.json'",2),
 ("case['resumeL18']=proof","case['resumeL19']=proof"),
 ("'nativeLifecycleContinuationL18'","'nativeLifecycleContinuationL19'",2),
 ("'application-domain17-continuation-l18.json'","'application-domain17-continuation-l19.json'"),
]

# Qualification entry: runtime-l18/root-qualify-l18.py -> runtime-l19/root-qualify-l19.py
QUALIFY_SOURCE='planning/linuxport01/runtime-l18/root-qualify-l18.py'
QUALIFY=[
 ('"""LINUXPORT01 (team entry): fresh coldboot qualification m909/m910 checked by the m803 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, then runtime-l18/l18_patches.py. No install, Activity, AP or automatic repair."""',
  '"""LINUXPORT01 (team entry): fresh coldboot qualification m911/m912 checked by the m803 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, runtime-l18/l18_patches.py, then runtime-l19/l19_patches.py. No install, Activity, AP or automatic repair."""'),
 ("choices=('m909','m910')","choices=('m911','m912')"),
 ("proof.get('format')=='aeris-linuxport01-l18-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M908_L17_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m909'else",
  "proof.get('format')=='aeris-linuxport01-l19-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M910_L18_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m911'else"),
 (" from aeris_runtime.continuation_l18 import m908_prior,rich_table,contract_check\n priorSlot='m908'if a.slot=='m909'else'm909';priorRun='beta-rc01-sdk-continuation08'if a.slot=='m909'else'beta-rc01-sdk-continuation09';",
  " from aeris_runtime.continuation_l19 import m910_prior,rich_table,contract_check\n priorSlot='m910'if a.slot=='m911'else'm911';priorRun='beta-rc01-sdk-continuation10'if a.slot=='m911'else'beta-rc01-sdk-continuation11';"),
 (" if a.slot=='m909':\n  priorBoot,path=m908_prior()\n"," if a.slot=='m911':\n  priorBoot,path=m910_prior()\n"),
 ("priorPath=R/'evidence/betarc01/m909/reports/coldboot-h7.json'","priorPath=R/'evidence/betarc01/m911/reports/coldboot-h7.json'"),
 ("run='beta-rc01-sdk-continuation09'if a.slot=='m909'else'beta-rc01-sdk-continuation10';need(intent.get('format')=='aeris-linuxport01-l18-root-sdk-positive-intent'",
  "run='beta-rc01-sdk-continuation11'if a.slot=='m911'else'beta-rc01-sdk-continuation12';need(intent.get('format')=='aeris-linuxport01-l19-root-sdk-positive-intent'"),
 ("need(a.slot!='m910'or","need(a.slot!='m912'or"),
]

# G1 entry: runtime-l18/root-native-l18.py -> runtime-l19/root-native-l19.py
NATIVE_SOURCE='planning/linuxport01/runtime-l18/root-native-l18.py'
NATIVE=[
 ('"""LINUXPORT01 (team entry): source-held native-only G1 slot g110 from the m803 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, then runtime-l18/l18_patches.py. Never starts AP/backend or flight."""',
  '"""LINUXPORT01 (team entry): source-held native-only G1 slot g111 from the m803 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, runtime-l18/l18_patches.py, then runtime-l19/l19_patches.py. Never starts AP/backend or flight."""'),
 ("choices=('g110',)","choices=('g111',)"),
 ("from aeris_runtime.continuation_l18 import require_qualification,resume_continuation\n","from aeris_runtime.continuation_l19 import require_qualification,resume_continuation\n"),
]

def gate(text):
 """runtime-l18/prepare-source-gate.py -> runtime-l19: entries point at runtime-l19, and the two new entries replace
 root-native-l18.py and root-qualify-l18.py (they only accept the used slots g110, m909, m910). Reads are unchanged:
 contract-l16 stays pinned, and the owner's native-unused-h7.mjs stays reached through the alias, now to the l19 file
 (the closure walk pins the alias target by itself). The G2/G3 entry root-owner-h10.py stays an entry."""
 assert text.count('runtime-l18')==4,'L19_GATE_BASE'
 for a,b in(("'planning/linuxport01/runtime-l18/root-native-l18.py'","'planning/linuxport01/runtime-l19/root-native-l19.py'"),("'planning/linuxport01/runtime-l18/root-qualify-l18.py'","'planning/linuxport01/runtime-l19/root-qualify-l19.py'")):
  assert text.count(a)==1,'L19_GATE_ENTRY';text=text.replace(a,b)
 return text.replace('runtime-l18','runtime-l19')

def apply(text,patches,name):
 """Each patch is (old,new) with `old` exactly once in the text at that point, or (old,new,count)."""
 for patch in patches:
  old,new=patch[:2];count=patch[2]if len(patch)==3 else 1
  n=text.count(old)
  if n!=count:raise ValueError('L19_PATCH_ANCHOR_COUNT:%s:%d!=%d:%r'%(name,n,count,old[:60]))
  text=text.replace(old,new)
 return text
