"""Fixed read-only presence semantics, injected transport. No Android actor."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import copy,hashlib,json,os,sys
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.application09 import AndroidDomain09,PACKAGE,PRESENCE_ARGS,verify_presence_original
from aeris_runtime.metadata_budget import encoded
checks=[]
def deny(fn):
 try:fn()
 except Exception as e:return e
 raise AssertionError('negative unexpectedly admitted')
def lab(raw=b'',error=None):
 d=AndroidDomain09.__new__(AndroidDomain09);d.serial='emulator-5582';d.observer=SimpleNamespace(tag='AERIS_PRODUCT_STATUS');d.status_socket=None;d._install_authorization=None;d.last_command_ref=None;rows=[];calls=[]
 def command(args,**kw):
  assert args==list(PRESENCE_ARGS)and kw['maximum_bytes']==256;d._command_bound(args);calls.append(list(args));d.last_command_ref={'path':'receipts/command.jsonl','offset':0,'bytes':900,'sha256':'a'*64};d.last_command={'format':'aeris-command','version':3,'exit':1 if error is not None else 0,'stdoutRef':{'path':'stdout','offset':0,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'stderrRef':{'path':'stderr','offset':0,'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()},'captureComplete':True,'failure':None if error is None else str(error)}
  if error is not None:raise error
  return raw
 def receipt(name,data):rows.append(copy.deepcopy(data));return{'path':'receipts/diagnostic.jsonl','offset':0,'bytes':len(encoded(data)),'sha256':hashlib.sha256(encoded(data)).hexdigest()}
 d.command=command;d.store=SimpleNamespace(receipt=receipt);return d,rows,calls
for raw,expected in[(b'','ABSENT'),(('package:'+PACKAGE+'\n').encode(),'PRESENT')]:
 d,rows,calls=lab(raw);proof=d.package_presence(deadline_ns=1000);assert proof['classification']==expected and proof['exit']==0 and proof['authorityGranted']is False and len(calls)==1 and rows==[proof];deny(lambda:d.package_presence(deadline_ns=2000));assert len(calls)==1
 checks.append('successful_fixed_list_'+expected+'_durable_refs_one_query_no_retry')
for raw in[b'\n',b'Error: access denied\n',('package:'+PACKAGE+'0\n').encode(),('package:'+PACKAGE+'\npackage:'+PACKAGE+'\n').encode(),b'package:vn.rtr.aeris.mission\n']:
 d,rows,calls=lab(raw);deny(lambda:d.package_presence(deadline_ns=1000));assert rows[-1]['classification']=='UNKNOWN'and rows[-1]['failure']and len(calls)==1
checks.append('whitespace_error_foreign_duplicate_substring_unknown_no_absence_or_install')
original=RuntimeError('ANDROID_COMMAND_EXIT:1');d,rows,calls=lab(error=original);assert deny(lambda:d.package_presence(deadline_ns=1000))is original;assert rows[-1]['classification']=='UNKNOWN'and rows[-1]['exit']==1 and len(calls)==1;checks.append('original_nonzero_failure_propagates_unchanged_unknown_no_reclassification_or_retry')
d,rows,calls=lab();p=d.package_presence(deadline_ns=1000);original_row=copy.deepcopy(d.last_command);remote=list(PRESENCE_ARGS[1:]);stdout=b''
def cmd(root,ref):return original_row,None,remote,stdout
with patch('aeris_runtime.once_reader.read_ref',side_effect=lambda root,ref:encoded(p)),patch('aeris_runtime.status15_reader.command',side_effect=cmd):
 assert verify_presence_original('INJECTED_RAM_NO_DEVICE','ref')==p
 for key,value in[('package','vn.rtr.aeris.mission'),('classification','UNKNOWN'),('authorityGranted',True),('exit',1)]:
  before=p[key];p[key]=value;deny(lambda:verify_presence_original('RAM','ref'));p[key]=before
 remote[:]=['pm','path',PACKAGE];deny(lambda:verify_presence_original('RAM','ref'));remote[:]=list(PRESENCE_ARGS[1:]);original_row['stdoutRef']={**original_row['stdoutRef'],'sha256':'f'*64};deny(lambda:verify_presence_original('RAM','ref'))
checks.append('cold_original_proof_requires_fixed_list_argv_package_output_status_and_exact_refs')
d,_,_=lab()
for args in[['shell','pm','list','packages','--user','10',PACKAGE],['shell','pm','list','packages'],['shell','pm','list','packages','--user','0','vn.rtr.aeris.mission']]:deny(lambda:d._command_bound(args))
checks.append('no_generic_package_listing_user_or_old_application_allowlist_expansion')
p=T/'source/aeris_runtime/application09.py';out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/application09-presence01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-fixed-application-presence-source-qa','status':'PASS_RAM_TRANSPORT_CONTRACT_NOT_ACTUAL_ADB_OR_INSTALL','checks':checks,'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'fixtureSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actorsStarted':False,'underlyingCommandReaderInjected':True,'freshAndroidInstallAccepted':False}));print(json.dumps({'path':str(out.relative_to(R)),'checks':len(checks),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
