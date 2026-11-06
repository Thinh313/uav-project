"""LINUXPORT01 exact patches for runtime-l12 (team decisions, not the owner's).

runtime-l12 is runtime-l11 plus two changes. Every file below is generated from its
runtime-l11 original by these replacements (each `old` must occur exactly once) or, for
the resource policy, by policy(); test-linuxport12.py re-derives each one.

1. Read-only forensic capture m802 of the app state left by g106 attempt 1 (team
   decision 2026-11-06, "option 2": keep that state as history and capture it, as the
   owner did with m801 after g105). New slot m802, prior slot g106, run
   beta-rc01-forensic-capture02. The capture code itself is unchanged.
2. Artifact cap 20 -> 40 MiB, authorized by the team researcher, not the owner
   (evidence/linuxport01/AUTHORIZATION-L12-ARTIFACT40.json). Applied exactly as the
   owner's H10 raised it 13 -> 20 MiB: candidate.CAP, error names, and the same
   +20 MiB in the reserve category, the hard peak and the required free disk of every
   case and of the campaign (more disk reserved, not less). The owner's amendment block
   stays byte-identical; a team block is added next to it.
"""
import hashlib,json

MIB=2**20;CAP_DELTA=20*MIB
AUTHORIZATION='evidence/linuxport01/AUTHORIZATION-L12-ARTIFACT40.json'
AUTHORIZATION_SHA='d7fe3c13c214e31900440488cf807a7f72ddd82835401e2ce0f0dfa4fad0ea07'

# Source modules: runtime-l11/source/aeris_runtime/<name> -> runtime-l12/source/aeris_runtime/<name>
MODULES={
 'mission16.py':[
  ("SLOTS={'m901':180,","SLOTS={'m802':180,'m901':180,"),
 ],
 'product_runtime.py':[
  ("self.root.name in('m101','m102','m201','m202','m303','m401','m402','m501','m502','m701','m702','m801','m901','m902')",
   "self.root.name in('m101','m102','m201','m202','m303','m401','m402','m501','m502','m701','m702','m801','m802','m901','m902')"),
  ("  if self.root.name=='m801':\n   from .forensic_h10 import verify_capture\n",
   "  if self.root.name in('m801','m802'):\n   from .forensic_h10 import verify_capture\n"),
  ("  if self.root.name=='m801':\n   result.pop('originalPrivateBytesConserved')",
   "  if self.root.name in('m801','m802'):\n   result.pop('originalPrivateBytesConserved')"),
  ("need(self.root.name=='m801','FORENSIC_ONLY_SCOPE')","need(self.root.name in('m801','m802'),'FORENSIC_ONLY_SCOPE')"),
 ],
 'forensic_h10.py':[
  ("owner.root.name=='m801'and v.get('format')","owner.root.name in('m801','m802')and v.get('format')"),
 ],
 'candidate.py':[
  ("MIB=2**20;CAP=20*MIB;",
   "# LINUXPORT01 team decision, not the owner's: 40 MiB (evidence/linuxport01/AUTHORIZATION-L12-ARTIFACT40.json)\nMIB=2**20;CAP=40*MIB;"),
  ("'CANDIDATE_PREFLIGHT_ARTIFACT20MiB_DISK10GiB:'","'CANDIDATE_PREFLIGHT_ARTIFACT40MiB_DISK10GiB:'"),
  ("'ARTIFACT20MiB_FAILED_PREFIX_RETAINED'","'ARTIFACT40MiB_FAILED_PREFIX_RETAINED'"),
 ],
}

POLICY='assets/resource-policy.json'
def policy(raw):
 """runtime-l11 resource-policy.json bytes -> runtime-l12 bytes (same compact sorted encoding)."""
 d=json.loads(raw);assert(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode()==raw,'L12_POLICY_ENCODING'
 assert d['betarc01HostCapAmendment']['artifactCapBytes']==20*MIB and'linuxport01ArtifactCapAmendment'not in d,'L12_POLICY_BASE'
 for c in d['cases'].values():
  b=c['budget'];assert b['categories']['newIsolatedAPKAndArchiveReserve']==20*MIB,'L12_POLICY_CASE_BASE'
  b['categories']['newIsolatedAPKAndArchiveReserve']+=CAP_DELTA;b['taskHardPeakBytes']+=CAP_DELTA;b['requiredFreeBytes']+=CAP_DELTA
 assert d['campaign']['newIsolatedAPKAndArchiveReserve']==20*MIB,'L12_POLICY_CAMPAIGN_BASE'
 d['campaign']['newIsolatedAPKAndArchiveReserve']+=CAP_DELTA;d['campaign']['taskHardPeakBytes']+=CAP_DELTA
 d['linuxport01ArtifactCapAmendment']={'allOtherGuardsUnchanged':True,'artifactCapBytes':40*MIB,'authorizationPath':AUTHORIZATION,'authorizationSHA256':AUTHORIZATION_SHA,
  'hostMetadataCapBytes':100*MIB,'oldArtifactCapBytes':20*MIB,'ownerAmendmentUnchanged':True,'ownerAuthorized':False,'reserveIncreaseBytes':CAP_DELTA}
 return(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode()

# Capture entry: runtime-l11/root-capture-h10.py (byte-identical to the owner's runtime-h10) -> runtime-l12/root-capture-l12.py
CAPTURE_SOURCE='planning/linuxport01/runtime-l11/root-capture-h10.py'
CAPTURE=[
 ('"""One fresh read-only forensic capture. No initial-registry semantic decoder."""',
  '"""LINUXPORT01 (team entry): one fresh read-only forensic capture m802 of the state after g106 attempt 1.\nOwner root-capture-h10.py plus l12_patches.py. No initial-registry semantic decoder."""'),
 ("choices=('m801',)","choices=('m802',)"),
 ("prior.get('format')=='aeris-h10-root-forensic-prerequisite'and prior.get('version')==1 and prior.get('status')=='ROOT_COLD_VERIFIED_G105_FAILED_PHYSICALLY_CLOSED_NOT_QUALIFICATION'",
  "prior.get('format')=='aeris-linuxport01-l12-root-forensic-prerequisite'and prior.get('version')==1 and prior.get('status')=='ROOT_COLD_VERIFIED_G106_FAILED_PHYSICALLY_CLOSED_NOT_QUALIFICATION'"),
 ("prior.get('priorSlot')=='g105'","prior.get('priorSlot')=='g106'"),
 ("run='beta-rc01-forensic-capture01';need(intent.get('format')=='aeris-h10-root-forensic-intent'",
  "run='beta-rc01-forensic-capture02';need(intent.get('format')=='aeris-linuxport01-l12-root-forensic-intent'"),
 ("intent.get('slot')=='m801'","intent.get('slot')=='m802'"),
 ("scope=R/'evidence/betarc01/m801'","scope=R/'evidence/betarc01/m802'"),
]

# Owner cap test copy: only the three cap numbers change (20 -> 40 MiB; total reserve delta vs H7 39 -> 59 MiB).
TEST_CAPS=[
 ("self.assertEqual(candidate.CAP,20*2**20)","self.assertEqual(candidate.CAP,40*2**20)"),
 ("delta=39*2**20","delta=59*2**20"),
 ("self.assertEqual(b['categories']['newIsolatedAPKAndArchiveReserve'],20*2**20)","self.assertEqual(b['categories']['newIsolatedAPKAndArchiveReserve'],40*2**20)"),
]

def gate(text):
 """runtime-l11/prepare-source-gate.py -> runtime-l12: entries point at runtime-l12; root-capture-l12.py replaces root-capture-h10.py."""
 assert text.count('runtime-l11')==4 and text.count("'planning/linuxport01/runtime-l11/root-capture-h10.py'")==1,'L12_GATE_BASE'
 return text.replace("'planning/linuxport01/runtime-l11/root-capture-h10.py'","'planning/linuxport01/runtime-l12/root-capture-l12.py'").replace('runtime-l11','runtime-l12')

def apply(text,patches,name):
 for old,new in patches:
  n=text.count(old)
  if n!=1:raise ValueError('L12_PATCH_ANCHOR_NOT_UNIQUE:%s:%d:%r'%(name,n,old[:60]))
  text=text.replace(old,new)
 return text
