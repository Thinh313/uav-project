"""LINUXPORT01 exact text patches for the install/cold-boot entries.

Each entry is generated from the owner's H4 original by these replacements, and
test-linuxport01.py re-derives it. Each `old` must occur exactly once.

Why: the owner's m301 was a repair of a broken package state (pkg=null) and
read its prior state from his m201 repair evidence. The team AVD has a healthy
install with the owner's n02 private data loaded (evidence/linuxport01/
avd-n02-load01.json), so the install entry reads that record instead and
expects a healthy package parse. Every other check is the original.
"""

INSTALL_SOURCE='planning/betarc01/runtime-h4/root-install-h4.py'
INSTALL=[
 ('"""Source-held H4 same-APK push install plus guest barrier, never boot acceptance."""',
  '"""LINUXPORT01: source-held H4 same-APK push install plus guest barrier, never boot acceptance.\nPrior state is the team-loaded n02 record (healthy package), not the owner\'s m201 repair."""'),
 ('safe_code_path,PACKAGE,PRIVATE,STAT,COLD,need\n',
  'safe_code_path,PACKAGE,PRIVATE,STAT,COLD,need,N02_TAR_SHA\n'),
 ("m101=R/'evidence/betarc01/m201/reports/known-state-repair01.json';need(intent.get('format')=='aeris-betarc01-root-known-state-repair-intent'and intent.get('version')==1 and intent.get('status')=='ROOT_SOURCE_QUALIFIED_PERSISTENT_PUSH_INSTALL_NOT_BETA'",
  "loaded=R/'evidence/linuxport01/avd-n02-load01.json';need(intent.get('format')=='aeris-linuxport01-root-install-intent'and intent.get('version')==1 and intent.get('status')=='ROOT_SOURCE_QUALIFIED_PERSISTENT_PUSH_INSTALL_HEALTHY_N02_NOT_BETA'"),
 ("intent.get('m201ReportSHA256')==sha(m101)",
  "intent.get('loadedStateSHA256')==sha(loaded)"),
 ("prior=json.loads(m101.read_bytes());oldstore=R/'evidence/betarc01/m201/sessions/beta-rc01-known-state-repair01/android-api';_,_,oldremote,oldraw=__import__('aeris_runtime.status15_reader',fromlist=['command']).command(oldstore,prior['postDumpRef']);need(oldremote==['dumpsys','package',PACKAGE],'M201_ORIGINAL_POSTDUMP');known_path=package_state(oldraw,broken=False);",
  "prior=json.loads(loaded.read_bytes());need(prior.get('format')=='aeris-linuxport01-avd-n02-load'and prior.get('version')==1 and prior.get('package')==PACKAGE and prior.get('UID')==10141 and prior.get('APK_SHA256')==manifest['native']['APK_SHA256']and prior.get('privateTarSHA256')==N02_TAR_SHA and prior.get('privateTableEqualsOriginal')is True and prior.get('activityStarted')is False,'L1_LOADED_N02_STATE');known_path=prior['codePath'];safe_code_path(known_path);"),
 ("package_state(dumpraw,broken=True)==known_path",
  "package_state(dumpraw,broken=False)==known_path"),
 ("'backup':before,'authorityRestorable':False};auth=authorize_repair",
  "'backup':before,'priorPackageBroken':False,'authorityRestorable':False};auth=authorize_repair"),
]

# The cold-boot entry needs no change: it reads m301 by slot name, and in the
# separate work tree every m301/m302 folder is the team's own.
QUALIFY_SOURCE='planning/betarc01/runtime-h4/root-qualify-h4.py'
QUALIFY=[]

# validate_precheck runs at authorization and again at verification, so the
# expected parse state travels in the precheck record. Default stays broken.
INSTALLCLOSURE=[
 ("code=package_state(out,broken=True);",
  "code=package_state(out,broken=pre.get('priorPackageBroken',True)is not False);"),
]

def apply(text,patches):
 for old,new in patches:
  if text.count(old)!=1:raise ValueError('L1_PATCH_NOT_UNIQUE:'+old[:60])
  text=text.replace(old,new)
 return text
