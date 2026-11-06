"""LINUXPORT01 exact patches for runtime-l14 (team decision, not the owner's).

runtime-l14 is runtime-l13 (chain m903/m904/g107 from contract-l12, with the backup17 fix)
plus one change, decided by the team on 2026-11-06 after runtime-l13 was frozen
(report 4zx): the two-boot proof check continuation_l13.require_qualification.

The owner's evidence-reference check rc01.ref_file has a 256 KiB bound (262,144 B). The
proof that g107 requires names each qualification boot's private-files TAR as its
`Private` reference, and the m802 state TAR is 263,680 B, so candidate e2d57374... would
refuse its own two-boot proof. In runtime-l14 only those two references may have up to
64 MiB, the bound the harness itself uses for this root TAR capture
(installclosure_h4._root_tar, BOUNDED_PRIVATE_TAR), and only when each one is that boot's
own capture at evidence/betarc01/<slot>/sessions/<run>/native-restart-metadata.tar and has
the SHA-256 of the pinned m802 TAR (both boots are read-only, so the state must not have
changed). Every other reference keeps the 256 KiB bound; rc01.ref_file is unchanged, and
all its other checks (under evidence/, no symlink, one link, exact size, SHA-256) still
apply to the Private references.

Every file below is generated from its runtime-l13 original by these replacements, and
test-linuxport14.py re-derives each one. Each `old` must occur exactly once.
"""

# Source modules: runtime-l13/source/aeris_runtime/<name> -> runtime-l14/source/aeris_runtime/<name>
MODULES={
 'continuation_l13.py':[
  ("original, as in resume_existing, not the current capture. Nothing here grants archive,\nresume, APPLY or flight authority, and reconcile_h7 is not imported.\n\"\"\"",
   "original, as in resume_existing, not the current capture. Nothing here grants archive,\nresume, APPLY or flight authority, and reconcile_h7 is not imported.\n"
   "runtime-l14 (team decision): require_qualification bounds each boot's Private reference (its\n"
   "private-files TAR) at 64 MiB instead of 256 KiB, only at that boot's capture path and only\n"
   "with the pinned m802 TAR SHA-256; every other reference keeps the owner's bound.\n\"\"\""),
  ("SLOTS=('m903','m904');QUALIFICATION='aeris-linuxport01-l13-root-contract-sdk-cold-acceptance'\n",
   "SLOTS=('m903','m904');QUALIFICATION='aeris-linuxport01-l13-root-contract-sdk-cold-acceptance'\n"
   "RUNS={'m903':'beta-rc01-sdk-continuation03','m904':'beta-rc01-sdk-continuation04'};PRIVATE_MAXIMUM=64*2**20\n"),
  (' """reconcile_h7.require_qualification with the team m903/m904 proof format instead of the owner\'s m701/m702."""',
   ' """reconcile_h7.require_qualification with the team m903/m904 proof format instead of the owner\'s m701/m702.\n'
   ' Each Private reference is that boot\'s own TAR of the pinned m802 state, bounded at 64 MiB (runtime-l14)."""'),
  (" for row in refs:ref_file(row['ref'])\n return {'status':'SOURCE_BOUND_L13_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'",
   " # runtime-l14: the m802 state TAR (263,680 B) is above the owner's 256 KiB ref_file bound. Only the Private refs get\n"
   " # the 64 MiB bound of the root TAR capture, and only as each boot's own capture with the pinned TAR SHA-256 and size.\n"
   " pin=(repository()/PIN).read_bytes();need(sha(pin)==PIN_SHA,'CONTRACT_PIN_SHA');state=decode(pin)['source']\n"
   " for row in refs:\n"
   "  ref=row['ref']\n"
   "  if row['role'].endswith('Private'):\n"
   "   slot=row['role'][:-len('Private')];need(type(ref)is dict and Path(str(ref.get('path'))).absolute()==repository()/'evidence/betarc01'/slot/'sessions'/RUNS[slot]/'native-restart-metadata.tar'and ref.get('sha256')==state['sha256']and ref.get('bytes')==state['bytes'],'PRIVATE_REF_IS_OWN_BOOT_TAR_OF_PINNED_STATE');ref_file(ref,maximum=PRIVATE_MAXIMUM)\n"
   "  else:ref_file(ref)\n"
   " return {'status':'SOURCE_BOUND_L13_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'"),
 ],
}

def gate(text):
 """runtime-l13/prepare-source-gate.py -> runtime-l14: the same 8 entries, now under runtime-l14."""
 assert text.count('runtime-l13')==4,'L14_GATE_BASE'
 return text.replace('runtime-l13','runtime-l14')

def apply(text,patches,name):
 for old,new in patches:
  n=text.count(old)
  if n!=1:raise ValueError('L14_PATCH_ANCHOR_NOT_UNIQUE:%s:%d:%r'%(name,n,old[:60]))
  text=text.replace(old,new)
 return text
