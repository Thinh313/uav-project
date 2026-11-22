"""LINUXPORT01 exact patches for runtime-l20 (team decisions, not the owner's).

runtime-l20 is runtime-l19 moved back to the app state from before g107 (the contract-l12 state), so that the owner's
archive maintenance can run after the next G1 and G2/G3 can start. It changes (A) the data admission, (B) the team
VERIFY_NATIVE_UNUSED17 module's fixed shape, (C) the chain slots and (D) the maintenance entry. Nothing else changes.
All of it was proposed by Claude and approved by the user (Thinh) in chat on 2026-11-22, not by the owner and not by
Claude alone; the owner has not been asked or told.

Why (facts, logs 2026-11-15/13-16 and 2026-11-22/01, handoff 25):
on runtime-l19 (candidate 7dc857fa...) the real G1 g111 passed by its script's rule, but the owner's archive maintenance
m303 (planning/betarc01/runtime-h9/root-maintenance-h9.py) failed: the app answered APPLY with FAILED_CLOSED_NO_AUTHORITY.
Journal 4ac33ff279f04d33b2e37276e794f780, opened by g107 on 2026-11-06 and never closed, is not closed in the app's
registry (log 2026-11-15/16), the pinned app's JournalRegistry17.beginArchive refuses a member that is not closed, and the
pinned app has no path that closes a generation left open by a dead process. Every state since g107 (contract-l16, m803,
the l16-l19 chains) contains it, so no archive and no G2/G3 is possible from there (the G2/G3 generation forecast needs
active + case + planned + reserve 2 <= 8, and g201 needs active <= 2). Log 2026-11-22/01 showed, with the owner's own
decoder, that in the state from before g107 (b-run02/avd-before-g107.tar = avd-after-m904.tar, e7f76f96...; its cold
export = the contract-l12 pinned TAR 76330541..., registry head 8fbdcccb...) all 3 active journals are closed (8 archived,
11 generations in all).

The user's words (each answered one of Claude's questions; the design Claude presented is the one in this file):
 "(b) Check pre-g107 state"   the read-only check of the pre-g107 state (unlogged probe), then
 "Log the probe as 01"        tools/probe_pre_g107_open_journals.py and log 2026-11-22/01 (PASS)
 "Present l20 design"         the design below
 "Yes, write patches"         approval of the presented design ("Approve the runtime-l20 design as presented?"), with
                              Claude's recommended option for each of its four choices: (1) slots m913/m914 (qualification),
                              g112 (G1), m304 (maintenance), runs beta-rc01-sdk-continuation13, beta-rc01-sdk-continuation14,
                              beta-rc01-native08, beta-rc01-maintenance02 (all checked unused); (2) the team maintenance entry
                              takes the place of the owner's root-maintenance-h9.py in the 8-entry list (root-capture-l15.py
                              stays); (3) the new verifier copy gets a corrected header comment (the inherited one describes
                              the l16 shape); (4) minimal scope, nothing beyond A-D.
The real AVD restore of avd-before-g107.tar (in place on /data, the log 2026-11-14/66 method) is a separate real step on
the user's word; so is every run. It is a reset past the g107-g111 lineage and the failed m303: the user's decision.

A. Data admission: contract-l12 again (continuation_l20.py from continuation_l19.py)
   The contract is planning/linuxport01/contract-l12 (continuation_l12.py, pin m802-continuation-pin.json 4689767d...),
   already pinned as a read input of every runtime since l12 (same verify() interface and status as contract-l16; its
   tests passed in the l19 tree, log 2026-11-14/57). The prior boot of the first qualification boot is the clean m904 of
   runtime-l14 (candidate d0cd538b..., run beta-rc01-sdk-continuation04, boot f8094b9d-...): the last boot of that state,
   read back from its own raw records as m911 read back m910 (same report formats and statuses; its TAR is the pin's
   source TAR). The runtime-l14 64 MiB Private-reference rule is kept and now binds each new boot's own TAR to the pinned
   m802 TAR SHA-256 and size (263,680 B), read from the pin as before.
B. Verifier shape (runtime-l20/native-unused-l20.mjs from runtime-l19/native-unused-l19.mjs, 04d5bd90..., which already
   carries the native-tar.mjs path fix): the earlier active journals are the 3 closed ones of the contract-l12 state
   (518ed1b9..., 6128a76b..., 3a55c840...) instead of 4 including g107's 4ac33ff2..., and the earlier generations are 11
   instead of 12; so at VERIFY it requires 13 generations, 5 active (3 earlier + the G1's 2) and 8 archived. The header
   comment says so. product_inputs.ALIASES points the owner's native-unused-h7.mjs at the l20 file.
C. Slots m913/m914 (qualification), g112 (G1, kind native, no remaining planned generations, the g111 archive boundary),
   m304 (maintenance) in mission16.py, rc01.py, product_runtime.py, product_native09.py; entries root-qualify-l20.py and
   root-native-l20.py; formats renamed to l20.
D. Maintenance entry: runtime-l20/root-maintenance-l20.py is the owner's planning/betarc01/runtime-h9/root-maintenance-h9.py
   (sha256 6701be27..., asserted) with a team docstring and the only allowed slot m304 instead of m303 (m303 is used); the
   same folder depth keeps parents[3] the repository root. maintenance.perform, close_maintenance and every owner check
   stay the owner's. prepare-source-gate.py lists it instead of the owner's entry (the graph holds at most 8 entries).

Everything in runtime-l19's and runtime-l18's docstrings (the G2/G3 port: forwarder, AP identity check, Linux kernel) is
unchanged, as are the writer limit (200 ms), the 40 MiB artifact cap, the 64 MiB Private bound, close_native_only,
close_guardian, root-owner-h10.py (byte-identical to the owner's) and every guard not named here. Every file below is
generated from its runtime-l19 original (or from the owner's maintenance entry) by these replacements, and
test-linuxport20.py re-derives each one. Each `old` must occur exactly once, or exactly the count given as a third element.
"""

L19_CANDIDATE='7dc857fa327e746284109220e5755cf8466a56709fb4ba66ff8eb643fea48448'
L14_CANDIDATE='d0cd538b2438e027f3514a6d4eba7af314b89f0666fd13250e8203e4d47c59b3'

# ---------------------------------------------------------------------------------------------------------------
# B. The verifier for the contract-l12 state: runtime-l19/native-unused-l19.mjs -> runtime-l20/native-unused-l20.mjs
# ---------------------------------------------------------------------------------------------------------------
VERIFIER_SOURCE='planning/linuxport01/runtime-l19/native-unused-l19.mjs'
VERIFIER_SOURCE_SHA256='04d5bd90d5513bf88afb7444c752b08d8e392bd1968784460cb444e2b1510f87'
VERIFIER_NAME='native-unused-l20.mjs'
VERIFIER_PATCHES=[
 ("""/* LINUXPORT01 runtime-l16 (team copy, not the owner's; l16_patches.py): the owner's module with the fixed
 * shape of the first G1 after the g103 migration (10 generations, 2 active) moved to the team's pinned
 * continuation (contract-l16, m803): 12 earlier generations, of which exactly these 4 earlier journals are
 * still active (3 closed UNUSED, 1 left open by g107), each still exactly the AJ02 header. Same checks
 * otherwise; the owner's native-unused-h7.mjs is not modified. */""",
  """/* LINUXPORT01 runtime-l20 (team copy, not the owner's; l20_patches.py): the owner's module with the fixed
 * shape of the first G1 after the g103 migration (10 generations, 2 active) moved to the team's pinned
 * continuation (contract-l12, m802, the state from before g107): 11 earlier generations, of which exactly
 * these 3 earlier journals are still active (all closed UNUSED), each still exactly the AJ02 header. Made from
 * runtime-l19/native-unused-l19.mjs (runtime-l16's copy with the fixed run-time read of native-tar.mjs).
 * Same checks otherwise; the owner's native-unused-h7.mjs is not modified. */"""),
 ("const CONTINUATION_OLD_ACTIVE=new Set(['518ed1b94ef444cc9fdf22bebc0ecca7','6128a76bf4354629a749921c8fcb35b1','3a55c84087814dfca23b8b0b496ffa64','4ac33ff279f04d33b2e37276e794f780']),CONTINUATION_PRIOR_GENERATIONS=12;",
  "const CONTINUATION_OLD_ACTIVE=new Set(['518ed1b94ef444cc9fdf22bebc0ecca7','6128a76bf4354629a749921c8fcb35b1','3a55c84087814dfca23b8b0b496ffa64']),CONTINUATION_PRIOR_GENERATIONS=11;"),
]

# ---------------------------------------------------------------------------------------------------------------
# Source modules: runtime-l19/source/aeris_runtime/<name> -> runtime-l20/source/aeris_runtime/<name>
# ---------------------------------------------------------------------------------------------------------------
MODULES={
 # B the alias of the owner's unused verifier
 'product_inputs.py':[
  ("'planning/betarc01/tar_profile_h7/native-unused-h7.mjs':'planning/linuxport01/runtime-l19/native-unused-l19.mjs'",
   "'planning/betarc01/tar_profile_h7/native-unused-h7.mjs':'planning/linuxport01/runtime-l20/native-unused-l20.mjs'"),
 ],
 # C slots m913/m914/g112 and the maintenance slot m304
 'mission16.py':[
  ("SLOTS={'m911':180,","SLOTS={'m913':180,'m914':180,'g112':180,'m304':180,'m911':180,"),
 ],
 'rc01.py':[
  ("KINDS={'g111':'native',","KINDS={'g112':'native','g111':'native',"),
  ("REMAINING={'g111':0,","REMAINING={'g112':0,'g111':0,"),
  ("ARCHIVE_BOUNDARY['g111']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n",
   "ARCHIVE_BOUNDARY['g111']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\nARCHIVE_BOUNDARY['g112']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n"),
 ],
 'product_runtime.py':[
  # D close_maintenance admits the new maintenance slot (the owner's m303 stays listed)
  ("'m202','m303','m401'","'m202','m303','m304','m401'"),
  ("'m911','m912')and not c['APStarted']","'m911','m912','m913','m914')and not c['APStarted']"),
  ("  elif self.root.name in('m911','m912'):\n   from .continuation_l19 import verify_sdk\n   verify_sdk(self,proof)\n",
   "  elif self.root.name in('m911','m912'):\n   from .continuation_l19 import verify_sdk\n   verify_sdk(self,proof)\n  elif self.root.name in('m913','m914'):\n   from .continuation_l20 import verify_sdk\n   verify_sdk(self,proof)\n"),
  ("'m911','m912')else","'m911','m912','m913','m914')else"),
  ("'m911','m912'):result.update","'m911','m912','m913','m914'):result.update"),
  ("'m911','m912'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')","'m911','m912','m913','m914'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')"),
 ],
 'product_native09.py':[
  (" if domain.get('nativeLifecycleContinuationL19')is True:\n  from .continuation_l19 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n",
   " if domain.get('nativeLifecycleContinuationL19')is True:\n  from .continuation_l19 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n if domain.get('nativeLifecycleContinuationL20')is True:\n  from .continuation_l20 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n"),
 ],
}

# ---------------------------------------------------------------------------------------------------------------
# A. New team module: runtime-l19/source/aeris_runtime/continuation_l19.py -> runtime-l20/.../continuation_l20.py
# ---------------------------------------------------------------------------------------------------------------
NEW_MODULE_SOURCE='continuation_l19.py';NEW_MODULE='continuation_l20.py'
NEW_MODULE_PATCHES=[
 ('''"""LINUXPORT01 continuation admission for the team m803 state (team code, not the owner's).

continuation_l18.py (runtime-l18) for a new chain (m911/m912 qualification, G1 g111) from the
same pinned 89-file state, after g110 attempt 1 failed at VERIFY_NATIVE_UNUSED17 (a team code defect in the
team verifier's run-time read path, fixed in runtime-l19); the AVD must be restored to the backup taken right
after m910 (avd-before-g110.tar) before the first boot (the user's decision "Path A: pinned state", 2026-11-12,
repeated for this chain by "Yes, write patches", 2026-11-14), with the unchanged team emulator spec
emulator-spec-02.json. Only the slots, the run names, the format names and the prior boot of the
first qualification boot (now the clean m910 boot of runtime-l18) change. Replaces, for these''',
  '''"""LINUXPORT01 continuation admission for the team m802 state (team code, not the owner's).

continuation_l19.py (runtime-l19) for a new chain (m913/m914 qualification, G1 g112) from the
pinned 87-file contract-l12 state, the state from before g107: every later state holds the journal g107 left
open (4ac33ff2...), which the owner's archive maintenance cannot archive (m303 attempt 1 failed, logs
2026-11-15/13-16), while in this state all active journals are closed (log 2026-11-22/01). The AVD must be
restored to avd-before-g107.tar (= avd-after-m904.tar) before the first boot (the user's decision "Yes, write
patches", 2026-11-22, a separate real step), with the unchanged team emulator spec emulator-spec-02.json.
Only the contract, the slots, the run names, the format names and the prior boot of the first qualification
boot (now the clean m904 boot of runtime-l14) change. Replaces, for these'''),
 ('''checks; only the data admission is the team contract planning/linuxport01/contract-l16 (pin
15039006..., unchanged), loaded from the frozen source graph.''',
  '''checks; only the data admission is the team contract planning/linuxport01/contract-l12 (pin
4689767d..., unchanged), loaded from the frozen source graph.'''),
 ("resume, APPLY or flight authority, closes the open journal, or imports reconcile_h7.",
  "resume, APPLY or flight authority, or imports reconcile_h7."),
 ("only with the pinned m803 TAR SHA-256 and size; every other reference keeps the owner's bound.",
  "only with the pinned m802 TAR SHA-256 and size; every other reference keeps the owner's bound."),
 ("CONTRACT='planning/linuxport01/contract-l16/continuation_l16.py'\nPIN='planning/linuxport01/contract-l16/m803-continuation-pin.json'\nPIN_SHA='15039006e060302d18acf0f45ce5304bdfb78d6fa1c4b8883f4016ee2f57ac95'\nM910='evidence/betarc01/m910';M910_RUN='beta-rc01-sdk-continuation10';L18_CANDIDATE='9e93fa50c5957f66ce0d1c382e84f58d779c9d663686fd782f76506229fcc921'\nSLOTS=('m911','m912');QUALIFICATION='aeris-linuxport01-l19-root-contract-sdk-cold-acceptance'\nRUNS={'m911':'beta-rc01-sdk-continuation11','m912':'beta-rc01-sdk-continuation12'}",
  "CONTRACT='planning/linuxport01/contract-l12/continuation_l12.py'\nPIN='planning/linuxport01/contract-l12/m802-continuation-pin.json'\nPIN_SHA='4689767d2d6368997cdd7505a409029abf1be4fa83c826084fe3e2537e08ca45'\nM904='evidence/betarc01/m904';M904_RUN='beta-rc01-sdk-continuation04';L14_CANDIDATE='"+L14_CANDIDATE+"'\nSLOTS=('m913','m914');QUALIFICATION='aeris-linuxport01-l20-root-contract-sdk-cold-acceptance'\nRUNS={'m913':'beta-rc01-sdk-continuation13','m914':'beta-rc01-sdk-continuation14'}"),
 ("raise ValueError('L19_'+n)","raise ValueError('L20_'+n)"),
 ("'linuxport01_continuation_l16'","'linuxport01_continuation_l12'"),
 (' """Admit one raw private-files TAR as the pinned m803 continuation state, or raise."""',
  ' """Admit one raw private-files TAR as the pinned m802 continuation state, or raise."""'),
 ("'aeris-linuxport01-l19-continuation-admission'","'aeris-linuxport01-l20-continuation-admission'"),
 # the prior boot of the first qualification boot: m910 of runtime-l18 -> m904 of runtime-l14
 ("def m910_prior():\n","def m904_prior():\n"),
 (''' """Prior boot UUID and codePath for m911, read back with the harness readers from the team m910 qualification boot of
 runtime-l18 (candidate 9e93fa50...): the last boot of the pinned state, to which the AVD must be restored before
 this chain (the user's decision "Path A: pinned state", repeated by "Yes, write patches", 2026-11-14).
 Its own raw records must show a normal SDK closure, its own TAR must be the pinned m803 state TAR, and both samples''',
  ''' """Prior boot UUID and codePath for m913, read back with the harness readers from the team m904 qualification boot of
 runtime-l14 (candidate d0cd538b...): the last boot of the pinned contract-l12 state, to which the AVD must be restored
 before this chain (avd-after-m904.tar = avd-before-g107.tar; the user's decision "Yes, write patches", 2026-11-22).
 Its own raw records must show a normal SDK closure, its own TAR must be the pinned m802 state TAR, and both samples'''),
 ("repo=repository();root=repo/M910;","repo=repository();root=repo/M904;"),
 ("report.get('candidateSHA256')==L18_CANDIDATE and term.get('status')=='SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE'and term.get('candidateSHA256')==L18_CANDIDATE,'M910_QUALIFICATION_SCOPE')",
  "report.get('candidateSHA256')==L14_CANDIDATE and term.get('status')=='SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE'and term.get('candidateSHA256')==L14_CANDIDATE,'M904_QUALIFICATION_SCOPE')"),
 ("'M910_ORIGINAL_NORMAL_SDK_CLOSURE'","'M904_ORIGINAL_NORMAL_SDK_CLOSURE'"),
 ("tar=root/'sessions'/M910_RUN/'native-restart-metadata.tar'","tar=root/'sessions'/M904_RUN/'native-restart-metadata.tar'"),
 ("'M910_IS_PINNED_STATE'","'M904_IS_PINNED_STATE'"),
 ("store=root/'sessions'/M910_RUN/'android-api'","store=root/'sessions'/M904_RUN/'android-api'"),
 ("'M910_ORIGINAL_CODEPATH_BOOT'","'M904_ORIGINAL_CODEPATH_BOOT'"),
 # the chain itself
 ("reconcile_h7.require_qualification with the team m911/m912 proof format","reconcile_h7.require_qualification with the team m913/m914 proof format"),
 (" Each Private reference is that boot's own TAR of the pinned m803 state, bounded at 64 MiB (runtime-l14, kept).",
  " Each Private reference is that boot's own TAR of the pinned m802 state, bounded at 64 MiB (runtime-l14, kept)."),
 (" # runtime-l14 (kept): the m803 state TAR (268,800 B) is above the owner's 256 KiB ref_file bound.",
  " # runtime-l14 (kept): the m802 state TAR (263,680 B) is above the owner's 256 KiB ref_file bound."),
 ("'SOURCE_BOUND_L19_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'","'SOURCE_BOUND_L20_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'"),
 ("reconcile_h7.verify_sdk for m911/m912:","reconcile_h7.verify_sdk for m913/m914:"),
 ("if owner.root.name=='m912':\n  prior=decode((owner.repo/'evidence/betarc01/m911/reports/coldboot-h7.json')","if owner.root.name=='m914':\n  prior=decode((owner.repo/'evidence/betarc01/m913/reports/coldboot-h7.json')"),
 ("'aeris-linuxport01-l19-continuation-readonly-resume'","'aeris-linuxport01-l20-continuation-readonly-resume'",2),
 ("reconcile_h7.resume_existing for g111:","reconcile_h7.resume_existing for g112:"),
 ("resumeL19Attempted","resumeL20Attempted",2),
 ("'native17-continuation-l19.json'","'native17-continuation-l20.json'",2),
 ("case['resumeL19']=proof","case['resumeL20']=proof"),
 ("'nativeLifecycleContinuationL19'","'nativeLifecycleContinuationL20'",2),
 ("'application-domain17-continuation-l19.json'","'application-domain17-continuation-l20.json'"),
]

# Qualification entry: runtime-l19/root-qualify-l19.py -> runtime-l20/root-qualify-l20.py
QUALIFY_SOURCE='planning/linuxport01/runtime-l19/root-qualify-l19.py'
QUALIFY=[
 ('"""LINUXPORT01 (team entry): fresh coldboot qualification m911/m912 checked by the m803 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, runtime-l18/l18_patches.py, then runtime-l19/l19_patches.py. No install, Activity, AP or automatic repair."""',
  '"""LINUXPORT01 (team entry): fresh coldboot qualification m913/m914 checked by the m802 continuation contract (contract-l12).\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, runtime-l18/l18_patches.py, runtime-l19/l19_patches.py, then runtime-l20/l20_patches.py. No install, Activity, AP or automatic repair."""'),
 ("choices=('m911','m912')","choices=('m913','m914')"),
 ("proof.get('format')=='aeris-linuxport01-l19-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M910_L18_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m911'else",
  "proof.get('format')=='aeris-linuxport01-l20-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M904_L14_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m913'else"),
 (" from aeris_runtime.continuation_l19 import m910_prior,rich_table,contract_check\n priorSlot='m910'if a.slot=='m911'else'm911';priorRun='beta-rc01-sdk-continuation10'if a.slot=='m911'else'beta-rc01-sdk-continuation11';",
  " from aeris_runtime.continuation_l20 import m904_prior,rich_table,contract_check\n priorSlot='m904'if a.slot=='m913'else'm913';priorRun='beta-rc01-sdk-continuation04'if a.slot=='m913'else'beta-rc01-sdk-continuation13';"),
 (" if a.slot=='m911':\n  priorBoot,path=m910_prior()\n"," if a.slot=='m913':\n  priorBoot,path=m904_prior()\n"),
 ("priorPath=R/'evidence/betarc01/m911/reports/coldboot-h7.json'","priorPath=R/'evidence/betarc01/m913/reports/coldboot-h7.json'"),
 ("run='beta-rc01-sdk-continuation11'if a.slot=='m911'else'beta-rc01-sdk-continuation12';need(intent.get('format')=='aeris-linuxport01-l19-root-sdk-positive-intent'",
  "run='beta-rc01-sdk-continuation13'if a.slot=='m913'else'beta-rc01-sdk-continuation14';need(intent.get('format')=='aeris-linuxport01-l20-root-sdk-positive-intent'"),
 ("need(a.slot!='m912'or","need(a.slot!='m914'or"),
]

# G1 entry: runtime-l19/root-native-l19.py -> runtime-l20/root-native-l20.py
NATIVE_SOURCE='planning/linuxport01/runtime-l19/root-native-l19.py'
NATIVE=[
 ('"""LINUXPORT01 (team entry): source-held native-only G1 slot g111 from the m803 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, runtime-l18/l18_patches.py, then runtime-l19/l19_patches.py. Never starts AP/backend or flight."""',
  '"""LINUXPORT01 (team entry): source-held native-only G1 slot g112 from the m802 continuation contract (contract-l12).\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, runtime-l18/l18_patches.py, runtime-l19/l19_patches.py, then runtime-l20/l20_patches.py. Never starts AP/backend or flight."""'),
 ("choices=('g111',)","choices=('g112',)"),
 ("from aeris_runtime.continuation_l19 import require_qualification,resume_continuation\n","from aeris_runtime.continuation_l20 import require_qualification,resume_continuation\n"),
]

# D. Maintenance entry: the owner's planning/betarc01/runtime-h9/root-maintenance-h9.py -> runtime-l20/root-maintenance-l20.py
MAINTENANCE_SOURCE='planning/betarc01/runtime-h9/root-maintenance-h9.py'
MAINTENANCE_SOURCE_SHA256='6701be278dc15ca2714b388d1cdde0bbe4f2fc0d41ebf53f231370752437c401'
MAINTENANCE_NAME='root-maintenance-l20.py'
MAINTENANCE=[
 ('"""Root-only explicit maintenance entry; same owner/guards, never Activity/AP."""',
  '"""Root-only explicit maintenance entry; same owner/guards, never Activity/AP.\nLINUXPORT01 runtime-l20 (team copy of the owner\'s planning/betarc01/runtime-h9/root-maintenance-h9.py, l20_patches.py): only the allowed slot is m304 instead of the used m303."""'),
 ('choices=("m303",)','choices=("m304",)'),
]

def gate(text):
 """runtime-l19/prepare-source-gate.py -> runtime-l20: entries point at runtime-l20; root-native-l20.py and
 root-qualify-l20.py replace the l19 entries (they only accept the used slots g111, m911, m912), and the team
 root-maintenance-l20.py replaces the owner's root-maintenance-h9.py (it only accepts the used slot m303). Reads are
 unchanged: contract-l10, contract-l12 and contract-l16 stay pinned, and the owner's native-unused-h7.mjs stays reached
 through the alias, now to the l20 file (the closure walk pins the alias target by itself). The G2/G3 entry
 root-owner-h10.py stays an entry."""
 assert text.count('runtime-l19')==4,'L20_GATE_BASE'
 for a,b in(("'planning/linuxport01/runtime-l19/root-native-l19.py'","'planning/linuxport01/runtime-l20/root-native-l20.py'"),
            ("'planning/linuxport01/runtime-l19/root-qualify-l19.py'","'planning/linuxport01/runtime-l20/root-qualify-l20.py'"),
            ("'planning/betarc01/runtime-h9/root-maintenance-h9.py'","'planning/linuxport01/runtime-l20/root-maintenance-l20.py'")):
  assert text.count(a)==1,'L20_GATE_ENTRY';text=text.replace(a,b)
 return text.replace('runtime-l19','runtime-l20')

def apply(text,patches,name):
 """Each patch is (old,new) with `old` exactly once in the text at that point, or (old,new,count)."""
 for patch in patches:
  old,new=patch[:2];count=patch[2]if len(patch)==3 else 1
  n=text.count(old)
  if n!=count:raise ValueError('L20_PATCH_ANCHOR_COUNT:%s:%d!=%d:%r'%(name,n,count,old[:60]))
  text=text.replace(old,new)
 return text
