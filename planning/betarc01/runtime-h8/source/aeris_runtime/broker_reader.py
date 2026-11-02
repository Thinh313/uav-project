"""Cold original-byte TRANSPORT13/14 proof reader, no writer/parser imports."""
import base64,hashlib,json,re,shlex
from pathlib import Path
from .once_reader import read_ref,read_receipts,unique

def _need(ok,name):
 if not ok:raise ValueError('COLD_BROKER_'+name)

def _diagnostic(root,ref):
 _need(type(ref)is dict and ref.get('path')=='receipts/diagnostic.jsonl'and type(ref.get('version'))is int and ref['version']==3,'ORIGINAL_DIAGNOSTIC_REF')
 value=json.loads(read_ref(root,ref),object_pairs_hook=unique)
 _need(sum(row==value for row in read_receipts(root,'diagnostic'))==1,'ORIGINAL_DIAGNOSTIC_MEMBERSHIP')
 return value

def _wire_proof(root,ref):
 _need(type(ref)is dict and ref.get('path')=='broker-wire.jsonl'and type(ref.get('version'))is int and ref['version']==3 and type(ref.get('bytes'))is int and 0<ref['bytes']<=1280,'ORIGINAL_WIRE_ROW_REF')
 # read_ref checks exact offset, whole-line boundaries, hash, nofollow and one
 # regular link; this proves membership without an O(n^2) complete-file scan.
 return json.loads(read_ref(root,ref),object_pairs_hook=unique)

def verify_wire_coverage(root,refs,*,allow_failed=False):
 import os,stat
 path=Path(root)/'broker-wire.jsonl'
 if not path.exists():_need(not refs,'MISSING_WIRE_JOURNAL');return
 fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0));rows=[]
 try:
  before=os.fstat(fd);_need(stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_size<=3700*1280,'WIRE_JOURNAL_BOUND_LINK')
  with os.fdopen(fd,'rb',closefd=False)as f:
   offset=0
   while True:
    raw=f.readline(1281)
    if not raw:break
    _need(len(raw)<=1280 and raw.endswith(b'\n')and b'\n'not in raw[:-1],'WIRE_WHOLE_ROW');rows.append((offset,len(raw),hashlib.sha256(raw).hexdigest()));offset+=len(raw)
    _need(len(rows)<=3700,'WIRE_ROW_COUNT')
  after=os.fstat(fd);_need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'WIRE_CHANGED_DURING_READ')
 finally:os.close(fd)
 actual=[(r['offset'],r['bytes'],r['sha256'])for r in refs]
 _need(len(set(actual))==len(actual),'WIRE_REF_REUSE')
 if allow_failed:_need(rows[:len(actual)]==actual and len(rows)-len(actual)<=1,'WIRE_FAILED_LAST_PREFIX_ONLY')
 else:_need(actual==rows,'WIRE_NO_UNREFERENCED_OR_MISSING_ROWS')

def _capture14(command,directory,limit):
 # Independent cold reconstruction. Never import the producer's renderer.
 d=directory
 prefix=''.join(': >'+d+'/'+name+' || exit 72\n'for name in('rc','h1','h2'))
 pipeline=('{ { '+command+"; t14rc=$?; printf '%s\\n' \"$t14rc\" >"+d+'/rc; } 2>&1 1>&3 | { head -c 65 >'+d+"/err; printf '%s\\n' \"$?\" >"+d+'/h2; }; } 3>&1 | { head -c '+str(limit+1)+' >'+d+"/out; printf '%s\\n' \"$?\" >"+d+'/h1; }\n')
 status=('t14d='+d+'\nfor t14status in rc h1 h2; do\n t14value=$(head -c 4 "$t14d/$t14status")\n t14size=$(wc -c <"$t14d/$t14status")\n t14size=$((t14size + 0))\n case "$t14value:$t14size" in [0-9]:2|[1-9][0-9]:3|1[0-9][0-9]:4|2[0-4][0-9]:4|25[0-5]:4) ;; *) printf \'T14_STATUS_FAILED %s\\n\' "$t14status"; cat '+d+'/out; cat '+d+'/err; exit 73 ;; esac\n case "$t14status" in rc) rc=$t14value ;; h1) h1=$t14value ;; h2) h2=$t14value ;; esac\ndone\nolen=$(wc -c <'+d+'/out)\nelen=$(wc -c <'+d+'/err)\nolen=$((olen + 0))\nelen=$((elen + 0))\n')
 return (prefix+pipeline+status).encode()

def verify_command(root,row,argv,remote,out,err,*,allow_failed=False):
 root=Path(root);proof=_wire_proof(root,row['brokerRef'])
 failed=proof.get('format')=='aeris-device-io-broker-command-failure'
 fields={'format','version','launchStore','launchRef','pid','operation'}|({'prefixIsStdoutRef','failure'}if failed else{'headerBase64','footerBase64','headExit','oversize','transportFailure'})
 _need(set(proof)==fields and type(proof['version'])is int and proof['version']==1 and proof['launchStore']=='android-api'and root.name in('android-api','android-api-restart-01'),'PROOF_SCHEMA_CASE')
 origin=root.parent/'android-api';launch=_diagnostic(origin,proof['launchRef'])
 launch_fields={'format','version','argv','pid','token','scriptBase64','scriptSHA256','startedHostNs','readyHostNs','readyRef','stderrRef','ready','failure','scratchPayloadMaximumBytes','scratchFilesystemForecastBytes','noAuthority'}
 capture=launch.get('version')
 _need(type(capture)is int and capture in(1,2)and set(launch)==launch_fields|({'captureVersion'}if capture==2 else set())and launch['format']=='aeris-device-io-broker-launch','LAUNCH_SCHEMA')
 if capture==2:_need(type(launch['captureVersion'])is int and launch['captureVersion']==2,'ANONYMOUS_CAPTURE_VERSION')
 token=launch['token'];_need(type(token)is str and re.fullmatch('[a-f0-9]{32}',token)is not None,'LAUNCH_TOKEN')
 _need(launch['argv']==[argv[0],'-s',argv[2],'shell','-T','sh']and type(launch['pid'])is int and launch['pid']>0 and type(proof['pid'])is int and proof['pid']==launch['pid'],'ACTUAL_PERSISTENT_CHILD_ARGV_PID')
 directory='/data/local/tmp/aeris-transport'+('14'if capture==2 else'13')+'-'+token
 startup=('umask 077\nmkdir '+directory+' || exit 71\nmkfifo '+directory+'/o.pipe '+directory+'/e.pipe || exit 72\nprintf '+shlex.quote('T13_READY '+token+'\n')+'\n').encode()
 if capture==2:startup=('umask 077\nmkdir '+directory+' || exit 71\n'+''.join(': >'+directory+'/'+name+' || exit 72\n'for name in('out','err','rc','h1','h2'))+'printf '+shlex.quote('T14_READY '+token+'\n')+'\n').encode()
 _need(base64.b64decode(launch['scriptBase64'],validate=True)==startup and hashlib.sha256(startup).hexdigest()==launch['scriptSHA256'],'EXACT_FIXED_START_SCRIPT')
 _need(launch['ready']is True and launch['failure']is None and launch['noAuthority']is True and type(launch['scratchPayloadMaximumBytes'])is int and launch['scratchPayloadMaximumBytes']==(16462 if capture==2 else 16450) and type(launch['scratchFilesystemForecastBytes'])is int and launch['scratchFilesystemForecastBytes']==(49152 if capture==2 else 32768) and read_ref(origin,launch['readyRef'])==(('T14_READY 'if capture==2 else'T13_READY ')+token+'\n').encode()and read_ref(origin,launch['stderrRef'])==b'','ORIGINAL_READY')
 _need(type(launch['startedHostNs'])is int and type(launch['readyHostNs'])is int and launch['startedHostNs']<=launch['readyHostNs']<=row['startedHostNs'],'LAUNCH_CLOCK')
 op=proof['operation'];_need(type(op)is dict and set(op)=={'seq','nonce','kind','scriptSHA256','startedHostNs'},'OP_SCHEMA')
 seq=op['seq'];nonce=op['nonce'];kind=op['kind'];_need(type(seq)is int and 0<seq<=3700 and type(nonce)is str and re.fullmatch('[a-f0-9]{32}',nonce)is not None and type(op['startedHostNs'])is int and row['startedHostNs']<=op['startedHostNs']<=row['endedHostNs'],'OP_ID_CLOCK')
 if len(remote)==6 and remote[:5]==['log','-p','i','-t','AERIS_MISSION']and re.fullmatch('AERIS_OBSERVER_READY_[a-f0-9]{32}',remote[5]):expected_kind,limit='MARKER',64
 elif remote==['pidof','vn.rtr.aeris.mission']:expected_kind,limit='PID',64
 elif remote==['run-as','vn.rtr.aeris.mission','cat','files/runtime/response.json']:expected_kind,limit='SNAPSHOT',16384
 elif len(remote)==12 and remote[:11]==['am','broadcast','-n','vn.rtr.aeris.mission/.CockpitActivity$StatusReceiver','-a','vn.rtr.aeris.mission.STATUS','--es','missionAction','STATUS','--es','missionRequestBase64']:
  raw=base64.b64decode(remote[11],altchars=b'-_',validate=True);request=json.loads(raw,object_pairs_hook=unique)
  _need(0<len(raw)<=512 and base64.urlsafe_b64encode(raw).decode()==remote[11]and set(request)=={'version','requestNonce'}and type(request['version'])is int and request['version']==1 and re.fullmatch('[a-f0-9]{32}',request['requestNonce'])is not None and json.dumps(request,separators=(',',':'),ensure_ascii=False).encode()==raw,'STATUS_SCHEMA');expected_kind,limit='STATUS',2048
 else:raise ValueError('COLD_BROKER_FOUR_TYPED_OPS_ONLY')
 _need(kind==expected_kind,'OP_KIND')
 # Reconstruct exact bytes sent to the owned shell independently of producer.
 d=directory
 script=(f'head -c {limit+1} <{d}/o.pipe >{d}/out &\np1=$!\nhead -c 65 <{d}/e.pipe >{d}/err &\np2=$!\n'+shlex.join(remote)+f' >{d}/o.pipe 2>{d}/e.pipe\nrc=$?\nwait "$p1"\nh1=$?\nwait "$p2"\nh2=$?\nolen=$(wc -c <{d}/out)\nelen=$(wc -c <{d}/err)\nolen=$((olen + 0))\nelen=$((elen + 0))\nprintf '+shlex.quote(f'T13 {seq} {nonce} {kind} %s %s %s %s %s\n')+f' "$rc" "$h1" "$h2" "$olen" "$elen"\ncat {d}/out\ncat {d}/err\nprintf '+shlex.quote(f'\nT13_END {seq} {nonce}\n')+'\n').encode()
 if capture==2:
  script=_capture14(shlex.join(remote),d,limit)+('printf '+shlex.quote(f'T13 {seq} {nonce} {kind} %s %s %s %s %s\n')+' "$rc" "$h1" "$h2" "$olen" "$elen"\ncat '+d+'/out\ncat '+d+'/err\nprintf '+shlex.quote(f'\nT13_END {seq} {nonce}\n')+'\n').encode()
 _need(hashlib.sha256(script).hexdigest()==op['scriptSHA256'],'EXACT_TYPED_OPERATION_SCRIPT')
 preceding=0
 if root.name=='android-api-restart-01':
  transfers=[x for x in read_receipts(root,'diagnostic')if x.get('format')=='aeris-device-io-broker-transfer']
  _need(len(transfers)==1,'ONE_TRANSPORT_TRANSFER');transfer=transfers[0]
  _need(set(transfer)=={'format','version','launchStore','launchRef','pid','oldStore','newStore','afterSequence','hostNs','authorityRestored','processIdentityRestored'}and type(transfer['version'])is int and transfer['version']==1 and transfer['launchStore']=='android-api'and transfer['launchRef']==proof['launchRef']and transfer['pid']==proof['pid']and transfer['oldStore']=='android-api'and transfer['newStore']==root.name and transfer['authorityRestored']is False and transfer['processIdentityRestored']is False and type(transfer['afterSequence'])is int and 0<=transfer['afterSequence']<seq and type(transfer['hostNs'])is int and transfer['hostNs']<=row['startedHostNs'],'TRANSFER_NO_AUTHORITY')
  originals=[_wire_proof(origin,r['brokerRef'])['operation']['seq']for r in read_receipts(origin,'command')if r.get('version')==7]
  _need(originals==list(range(1,len(originals)+1))and transfer['afterSequence']==len(originals),'TRANSFER_ORIGINAL_CONTIGUOUS_SEQUENCE');preceding=transfer['afterSequence']
 if failed:
  _need(allow_failed and row['captureComplete']is False and proof['prefixIsStdoutRef']is True and type(proof['failure'])is str and proof['failure']and len(out)<=16963,'FAILED_PREFIX_ONLY')
  return {'sequence':seq,'nonce':nonce,'pid':proof['pid'],'launchRef':proof['launchRef'],'failedPrefix':True,'precedingSequence':preceding}
 _need(proof['format']=='aeris-device-io-broker-command'and type(proof['oversize'])is bool and type(proof['headExit'])is list and len(proof['headExit'])==2 and all(type(x)is int and 0<=x<=255 for x in proof['headExit']),'FRAME_FIELDS')
 header=base64.b64decode(proof['headerBase64'],validate=True);footer=base64.b64decode(proof['footerBase64'],validate=True)
 _need(type(row['exit'])is int and 0<=row['exit']<=255 and len(out)<=limit+1 and len(err)<=65,'FRAME_LENGTHS')
 expected_header=f'T13 {seq} {nonce} {kind} {row["exit"]} {proof["headExit"][0]} {proof["headExit"][1]} {len(out)} {len(err)}\n'.encode();expected_footer=f'\nT13_END {seq} {nonce}\n'.encode()
 _need(header==expected_header and footer==expected_footer,'ORIGINAL_LENGTH_FRAMING')
 _need(proof['oversize']==(len(out)>limit or len(err)>64),'OVERSIZE_CLASSIFICATION')
 if row['failure']is None:_need(proof['headExit']==[0,0]and not proof['oversize']and proof['transportFailure']is None,'SUCCESS_NO_READER_FAILURE')
 _need(len(header+out+err+footer)<=16962,'WIRE_BOUND')
 return {'sequence':seq,'nonce':nonce,'pid':proof['pid'],'launchRef':proof['launchRef'],'failedPrefix':False,'precedingSequence':preceding}


def verify_case_closure(case_root,*,allow_failed=False):
 """After managed closure only; capture failure is never flight acceptance."""
 case=Path(case_root);origin=case/'android-api';diagnostics=read_receipts(origin,'diagnostic')
 launches=[r for r in diagnostics if r.get('format')=='aeris-device-io-broker-launch'];closes=[r for r in diagnostics if r.get('format')=='aeris-device-io-broker-close']
 _need(len(launches)==1 and len(closes)==1,'ONE_ORIGINAL_LAUNCH_CLOSE');launch=launches[0];close=closes[0]
 _need(type(close.get('version'))is int and close['version']==1 and close['pid']==launch['pid']and type(close['exit'])is int and close['drainComplete']is True and close['originalEOFDrained']is True and close['closeErrors']==[],'MANAGED_CLOSED_CHILD_AND_EOF')
 seq=[]
 for store in (origin,case/'android-api-restart-01'):
  for row in read_receipts(store,'command'):
   if row.get('version')==7:seq.append(_wire_proof(store,row['brokerRef'])['operation']['seq'])
 _need(seq==list(range(1,len(seq)+1))and type(close['operations'])is int and close['operations']==len(seq),'COMPLETE_ORIGINAL_OPERATION_COUNT')
 for key in('closePrefixRef','stdoutTailRef','stderrTailRef'):read_ref(origin,close[key])
 _need(close.get('failedCaptureDurable')is True and type(close.get('failedCaptureRefs'))is list and len(close['failedCaptureRefs'])<=1,'FAILED_PREFIX_DURABILITY')
 for item in close['failedCaptureRefs']:
  _need(type(item)is dict and set(item)=={'store','ref','uncertainPhysicalDuplicate','acceptanceEvidence'}and item['store']in('android-api','android-api-restart-01')and item['uncertainPhysicalDuplicate']is True and item['acceptanceEvidence']is False,'FAILED_PREFIX_NONACCEPTING_SCHEMA')
  _need(len(read_ref(case/item['store'],item['ref']))<=16963,'FAILED_PREFIX_BOUND')
 _need(type(close['transportStderrRefs'])is list and len(close['transportStderrRefs'])<=3 and type(close['transportStderrCapturedBytes'])is int,'STDERR_REFS_BOUNDED')
 stderr=bytearray()
 for part in close['transportStderrRefs']:
  _need(type(part)is dict and set(part)=={'store','ref'}and part['store']in('android-api','android-api-restart-01'),'STDERR_ORIGINAL_STORE')
  stderr.extend(read_ref(case/part['store'],part['ref']))
 _need(len(stderr)==close['transportStderrCapturedBytes']and len(stderr)<=4097,'STDERR_ALL_CAPTURED_BYTES_ONCE')
 if not allow_failed:
  _need(close['captureComplete']is True and close['scratchCleanupAcknowledged']is True and close['failure']is None and close['operationalFailure']is None and close['exit']==0,'ACCEPTANCE_REQUIRES_COMPLETE_CLEAN_CAPTURE')
  _need(read_ref(origin,close['stdoutTailRef'])==b''and read_ref(origin,close['stderrTailRef'])==b''and read_ref(origin,close['closePrefixRef'])==(('T14_CLOSED 'if launch['version']==2 else'T13_CLOSED ')+launch['token']+'\n').encode(),'NO_UNEXPECTED_CLOSURE_BYTES')
 return {'format':'aeris-broker-cold-managed-closure','version':1,'operations':len(seq),'pid':close['pid'],'drainComplete':True,'captureComplete':close['captureComplete'],'flightAcceptance':False}
