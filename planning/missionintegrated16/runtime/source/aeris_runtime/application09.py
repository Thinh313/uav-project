"""Exactly one separate development APPLICATION domain, same owned emulator.
This is not migration/rotation or a reset of any existing filesDir/counter.
"""
from .android import AndroidDevice
LEGACY_PACKAGE='vn.rtr.aeris.mission'
PACKAGE='vn.rtr.aeris.betasim09'
ACTIVITY=PACKAGE+'/vn.rtr.aeris.mission.ProductActivity'
RECEIVER=PACKAGE+'/vn.rtr.aeris.mission.ProductStatusReceiver'
ACTION=LEGACY_PACKAGE+'.PRODUCT_STATUS'
PRESENCE_ARGS=('shell','pm','list','packages','--user','0',PACKAGE)
COLD_ABSENCE_SCRIPT='if pidof '+PACKAGE+' >/dev/null; then echo RUNNING; else echo ABSENT; fi'
class AndroidDomain09(AndroidDevice):
 APPLICATION_PACKAGE=PACKAGE
 PRODUCT_ACTIVITY_COMPONENT=ACTIVITY
 PRODUCT_STATUS_COMPONENT=RECEIVER
 PRODUCT_STATUS_ACTION=ACTION
 COLD_ABSENCE_PREDICATE=COLD_ABSENCE_SCRIPT
 def _command_bound(self,args):
  if self.serial!='emulator-5582' or self.observer is None or self.observer.tag!='AERIS_PRODUCT_STATUS':raise ValueError('DOMAIN09_OWNED_PRODUCT_DEVICE_ONLY')
  if args==list(PRESENCE_ARGS):return 256
  if args==['shell','run-as',PACKAGE,'pwd','-P']:return 256
  if any('CockpitActivity'in str(v)or v in('missionAction','missionRequestBase64')for v in args):raise ValueError('DOMAIN09_NO_LEGACY_M1_PROTOCOL')
  auth=getattr(self,'_fresh_domain_install_authorization',None)
  if len(args)==2 and args[0]=='install'and auth is not None and args[1]==auth['APKPath']:return 2048
  return super()._command_bound(args)

 def package_presence(self,*,deadline_ns):
  # No command retry and no relaxation of AndroidDevice's exit/stderr contract.
  # An empty successful list is valid ABSENT; pm path is never an absence test.
  import json
  if getattr(self,'_presence_attempted',False):raise ValueError('APPLICATION09_ONE_PRESENCE_QUERY_NO_RETRY')
  self._presence_attempted=True
  previous=getattr(self,'last_command_ref',None);raw=None;primary=None;classification='UNKNOWN';command_ref=None;row=None
  try:
   raw=self.command(list(PRESENCE_ARGS),deadline_ns=deadline_ns,maximum_bytes=256)
   if raw==b'':classification='ABSENT'
   elif raw==('package:'+PACKAGE+'\n').encode():classification='PRESENT'
   else:raise ValueError('APPLICATION09_PRESENCE_UNEXPECTED_OUTPUT_UNKNOWN')
  except BaseException as error:primary=error
  current=getattr(self,'last_command_ref',None)
  if current is not None and current!=previous:
   command_ref=current;row=self.last_command
  if row is None:
   classification='UNKNOWN'
   if primary is None:primary=RuntimeError('APPLICATION09_NO_FRESH_ORIGINAL_PRESENCE_COMMAND')
  proof={'format':'aeris-fixed-development-application-presence','version':1,'package':PACKAGE,'user':0,'classification':classification,'originalCommandRef':command_ref,'stdoutRef':None if row is None else row['stdoutRef'],'stderrRef':None if row is None else row['stderrRef'],'exit':None if row is None else row['exit'],'captureComplete':False if row is None else row['captureComplete'],'failure':None if primary is None else type(primary).__name__+':'+str(primary)[:256],'noRetry':True,'authorityGranted':False}
  try:self.last_presence_ref=self.store.receipt('application-domain09-presence.json',proof)
  except BaseException as storage:
   if primary is None:primary=storage
   else:primary.add_note('APPLICATION_PRESENCE_PROOF_UNDURABLE:'+type(storage).__name__+':'+str(storage)[:128])
  if primary is not None:raise primary
  return proof

def verify_presence_original(root,ref):
 import json
 from .once_reader import read_ref,unique
 from .status15_reader import command
 proof=json.loads(read_ref(root,ref),object_pairs_hook=unique)
 if proof.get('format')!='aeris-fixed-development-application-presence'or proof.get('version')!=1 or proof.get('package')!=PACKAGE or proof.get('user')!=0 or proof.get('classification')not in('ABSENT','PRESENT')or proof.get('failure')is not None or proof.get('authorityGranted')is not False:raise ValueError('APPLICATION09_ORIGINAL_PRESENCE_PROOF')
 row,argv,remote,stdout=command(root,proof['originalCommandRef'])
 if remote!=list(PRESENCE_ARGS[1:])or stdout!=(b''if proof['classification']=='ABSENT'else('package:'+PACKAGE+'\n').encode())or any(proof[k]!=row[k]for k in('stdoutRef','stderrRef','exit','captureComplete')):raise ValueError('APPLICATION09_ORIGINAL_PRESENCE_COMMAND_JOIN')
 return proof
