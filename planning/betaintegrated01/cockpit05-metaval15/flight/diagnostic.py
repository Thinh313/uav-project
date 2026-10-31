"""After-close-only bounded native diagnostic export, separate from flight journal."""
from pathlib import Path
import hashlib,json,re,time
from . import contract
CAP=256*1024
PHASES={'socket.read','loop.observe','loop.tick','presentation.publish','queue.apply','readonly.heartbeat','readonly.home','readonly.parameter','readonly.version','rx.apply','socket.flush','socket.write','journal.write','journal.fsync','journal.dirsync'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def diagnostic_path(run):
 if type(run)is not str or re.fullmatch('[A-Za-z0-9_.:-]{1,128}',run)is None:raise ValueError('DIAGNOSTIC_RUN')
 return 'files/native-io-diagnostics/'+run+'.json'

def verify_binding(raw,context,source_sha):
 if type(raw)is not bytes or not 1<=len(raw)<=CAP:raise ValueError('DIAGNOSTIC_256KiB_BOUND')
 v=json.loads(raw)
 if v.get('format')!='aeris-native-io-diagnostics'or type(v.get('version'))is not int or v['version']!=1:raise ValueError('DIAGNOSTIC_FORMAT')
 if v.get('context')!=context or v.get('APKSourceSHA256')!=source_sha:raise ValueError('DIAGNOSTIC_CONTEXT_OR_SOURCE')
 return v

def validate(raw,context,source_sha):
 v=verify_binding(raw,context,source_sha)
 if type(v.get('cpuUnavailableOperations'))is not int or v['cpuUnavailableOperations']!=0:raise ValueError('DIAGNOSTIC_CPU_UNAVAILABLE_OPERATIONS')
 if type(v.get('measurementErrors'))is not int or v['measurementErrors']!=0:raise ValueError('DIAGNOSTIC_MEASUREMENT_ERRORS')
 if v.get('threadCpuClock')!='android.os.Debug.threadCpuTimeNanos_CURRENT_THREAD'or v.get('wallClockDomain')!='ANDROID_ELAPSED_REALTIME_NS_CALLER_CLOCK':raise ValueError('DIAGNOSTIC_ACTUAL_ANDROID_CLOCK_REQUIRED')
 spans=v.get('recentSpans');summary=v.get('phaseSummary');queues=v.get('recentQueueEvents')
 if type(spans)is not list or not 1<=len(spans)<=256 or type(summary)is not list or not 1<=len(summary)<=32 or type(queues)is not list or len(queues)>256:raise ValueError('DIAGNOSTIC_RING_BOUND')
 if len({x.get('phase')for x in summary})!=len(summary)or any(x.get('phase')not in PHASES for x in summary):raise ValueError('DIAGNOSTIC_PHASES_UNIQUE_SOURCE_ALLOWLIST')
 if v.get('diagnosticNotAuthorityOrFlightProof')is not True or v.get('nonCPUWallCause')!='UNKNOWN_NOT_EXCLUSIVE_FILESYSTEM_OR_SCHEDULER'or type(v.get('terminalStateSHA256'))is not str or re.fullmatch('[a-f0-9]{64}',v['terminalStateSHA256'])is None:raise ValueError('DIAGNOSTIC_SCOPE_OR_CHECKSUM')
 for item in spans:
  if item.get('phase')not in {x['phase']for x in summary}:raise ValueError('DIAGNOSTIC_SPAN_PHASE')
  if any(type(item.get(k))is not int or item[k]<0 for k in('beginElapsedNs','endElapsedNs','wallNs','threadCpuNs','threadId'))or item['endElapsedNs']-item['beginElapsedNs']!=item['wallNs']:raise ValueError('DIAGNOSTIC_CPU_UNAVAILABLE_OR_SPAN_SCHEMA')
 for item in summary:
  for k in('count','wallTotalNs','wallMaxNs','cpuKnownCount','cpuTotalKnownNs','cpuMaxKnownNs'):
   if type(item.get(k))is not int or item[k]<0:raise ValueError('DIAGNOSTIC_SUMMARY_NUMERIC_TYPE')
  bins=item.get('wallHistogram')
  if type(bins)is not list or len(bins)!=8 or any(type(x)is not int or x<0 for x in bins)or sum(bins)!=item['count']or item['wallMaxNs']>item['wallTotalNs']or item['cpuMaxKnownNs']>item['cpuTotalKnownNs']:raise ValueError('DIAGNOSTIC_HISTOGRAM_OR_TOTALS')
  if type(item.get('count'))is not int or item['count']<=0 or type(item.get('cpuKnownCount'))is not int or item['cpuKnownCount']!=item['count']:raise ValueError('DIAGNOSTIC_CPU_COVERAGE_REQUIRED')
 if type(v.get('spanCount'))is not int or v['spanCount']!=sum(x['count']for x in summary)or len(spans)!=min(v['spanCount'],256)or type(v.get('queueEventCount'))is not int or len(queues)!=min(v['queueEventCount'],256)or v.get('ringCapacity')!=256:raise ValueError('DIAGNOSTIC_COUNTS_OR_RING')
 for q in queues:
  kind=q.get('kind')
  if type(kind)is not str or not(kind.startswith('OFFER_')or kind.startswith('CONSUME_')or kind=='SAMPLER_UI_LIVENESS')or not re.fullmatch('(OFFER|CONSUME)_(INPUT|MOTION|ACTION|RELEASE_NOTICE)|SAMPLER_UI_LIVENESS',kind):raise ValueError('DIAGNOSTIC_QUEUE_KIND')
  if kind.startswith('OFFER_')and q.get('consumeElapsedNs')!=-1 or kind.startswith('CONSUME_')and(type(q.get('consumeElapsedNs'))is not int or q['consumeElapsedNs']<q.get('offerElapsedNs',0)):raise ValueError('DIAGNOSTIC_QUEUE_CONSUME_TIME')
  if q.get('queueDwellThreadCPU')is not None or q.get('queueDwellMeaning')!='ELAPSED_WALL_ONLY_NO_CROSS_THREAD_CPU_SUBTRACTION'or any(type(q.get(k))is not int for k in('threadId','serial','producerElapsedNs','offerElapsedNs','consumeElapsedNs','depth'))or not 0<=q['depth']<=128 or q['offerElapsedNs']<0 or q['consumeElapsedNs']< -1 or q['consumeElapsedNs']>=0 and q['consumeElapsedNs']<q['offerElapsedNs']:raise ValueError('DIAGNOSTIC_QUEUE_CLOCK_DOMAIN')
 sampler=[q for q in queues if q['kind']=='SAMPLER_UI_LIVENESS']
 if not sampler or any(q['producerElapsedNs']<0 or not 0<=q['offerElapsedNs']-q['producerElapsedNs']<=200000000 or q['consumeElapsedNs']<q['offerElapsedNs']for q in sampler):raise ValueError('DIAGNOSTIC_DEDICATED_SAMPLER_UI_LIVENESS_REQUIRED')
 if not PHASES.issubset({i.get('phase')for i in summary}):raise ValueError('DIAGNOSTIC_REQUIRED_PHASE_MEASUREMENTS')
 if type(v.get('maximumMessagesPerOuterLoop'))is not int or not 0<=v['maximumMessagesPerOuterLoop']<=16:raise ValueError('DIAGNOSTIC_GLOBAL16_BOUND')
 return v

def certificate_sha(build):
 values=re.findall(r'^Signer #1 certificate SHA-256 digest: ([a-f0-9]{64})$',build.get('signature',''),re.MULTILINE)
 if len(values)!=1:raise ValueError('DIAGNOSTIC_SELECTED_DEVELOPMENT_CERTIFICATE_PROOF')
 return values[0]

def capture(op,C,context,resource):
 from .export_native import exports,GLOBAL
 C=Path(C);resource.check(CAP);target=C/'native-io-diagnostic-export.json'
 if target.exists()or(C/'diagnostic-attempt-start.json').exists():raise ValueError('DIAGNOSTIC_EXPORT_ONE_ATTEMPT')
 state=op.state(allow_absent=False,require_context=True)
 if state.get('closed')is not True or state.get('journal',{}).get('closed')is not True:raise ValueError('DIAGNOSTIC_ONLY_AFTER_NATIVE_CLOSE')
 outside=C/'native-last-external-observation.json'
 if not outside.is_file()or outside.stat().st_size>131072:raise ValueError('DIAGNOSTIC_OUTSIDE_NATIVE_CLOSED_PROOF_REQUIRED')
 closed=json.loads(outside.read_text())
 if closed.get('closed')is not True or closed.get('journal',{}).get('commitAnchor')!=state['journal']['commitAnchor']or any(closed.get(k)!=context[k]for k in('run','epoch','boot','generation')):raise ValueError('DIAGNOSTIC_OUTSIDE_CLOSED_CONTEXT')
 device=diagnostic_path(context['run']);used=sum(p.stat().st_size for p in exports())
 if used+CAP>GLOBAL:raise ValueError('DIAGNOSTIC_GLOBAL_EXPORT_CAP')
 build=contract.build_receipt();attempt={'context':context,'devicePath':device,'maximumBytes':CAP,'priorGlobalExportBytes':used,'selectedAPKSourceSHA256':contract.SOURCE_SHA256,'selectedAPK_SHA256':contract.APK_SHA256,'selectedBuildReceiptSHA256':contract.sha(contract.ROOT/contract.BUILD),'certificateSHA256':certificate_sha(build),'hostNs':time.monotonic_ns(),'canonicalArtifact':'RETAINED_ADB_STDOUT_NO_REDUNDANT_COPY'}
 (C/'diagnostic-attempt-start.json').open('x').write(json.dumps(attempt,indent=2)+'\n')
 commands=[]
 def call(args):
  resource.check(CAP);o=op.command(args,timeout=10,check=False);commands.append({'receipt':str(o[3]/'receipt.json'),'receiptSHA256':contract.sha(o[3]/'receipt.json')})
  if o[2]!=0:raise ValueError('DIAGNOSTIC_DEVICE_READ_FAILED')
  return o
 readiness=[];deadline=time.monotonic()+5
 while True:
  resource.check(CAP);probe=op.command(['shell','run-as',contract.PACKAGE,'wc','-c',device],timeout=3,check=False);proof={'receipt':str(probe[3]/'receipt.json'),'receiptSHA256':contract.sha(probe[3]/'receipt.json')}
  if probe[2]==0:
   commands.append(proof);size=probe[0].decode().split();break
  readiness.append(proof)
  if b'No such file or directory'not in probe[0]+probe[1]or time.monotonic()>=deadline:raise ValueError('DIAGNOSTIC_NOT_PUBLISHED_WITHIN5S_NO_RETRY_OF_FLIGHT')
  time.sleep(.1)
 if len(size)!=2 or not size[0].isdigit()or not 1<=int(size[0])<=CAP or size[1]!=device:raise ValueError('DIAGNOSTIC_DEVICE_SIZE')
 before=call(['shell','run-as',contract.PACKAGE,'sha256sum',device])[0].decode().split()
 if len(before)!=2 or re.fullmatch('[a-f0-9]{64}',before[0])is None or before[1]!=device:raise ValueError('DIAGNOSTIC_DEVICE_SHA')
 observed=call(['exec-out','run-as',contract.PACKAGE,'cat',device]);raw=observed[0];artifact=observed[3]/'stdout.bin';after=call(['shell','run-as',contract.PACKAGE,'sha256sum',device])[0].decode().split()
 if before!=after or len(raw)!=int(size[0])or sha(raw)!=before[0]:raise ValueError('DIAGNOSTIC_DEVICE_SHA_CHANGED')
 forensicOnly=bool(state.get('firstFailure'))or state.get('lifecycle',{}).get('phase')=='FAILED'
 if forensicOnly:verify_binding(raw,context,contract.SOURCE_SHA256)
 else:validate(raw,context,contract.SOURCE_SHA256)
 value={**attempt,'forensicOnly':forensicOnly,'failedSessionNeverShortSuccess':forensicOnly,'artifactPath':str(artifact),'artifactSHA256':sha(raw),'artifactBytes':len(raw),'deviceBeforeAfterSHA256':before[0],'commands':commands,'publicationReadinessReceipts':readiness,'closedNativeCommitAnchor':state['journal']['commitAnchor'],'outsideClosedProofPath':str(outside),'outsideClosedProofSHA256':contract.sha(outside),'scope':'LOCAL_DEVICE_DIAGNOSTIC_NOT_FLIGHT_AUTHORITY_OR_IO_CAUSE_ATTESTATION'}
 target.open('x').write(json.dumps(value,indent=2)+'\n');return value

def read_bounded(path,cap,root=None):
 if type(path)not in(str,Path)and not isinstance(path,Path):raise ValueError('DIAGNOSTIC_PATH_TYPE')
 path=Path(path)
 if root is not None and not path.resolve().is_relative_to(Path(root).resolve()):raise ValueError('DIAGNOSTIC_PATH_CONTAINMENT')
 if any(p.is_symlink()for p in(path,*path.parents))or not path.is_file()or not 0<=path.stat().st_size<=cap:raise ValueError('DIAGNOSTIC_FILE_TYPE_OR_BOUND')
 with path.open('rb')as f:raw=f.read(cap+1)
 if len(raw)>cap:raise ValueError('DIAGNOSTIC_FILE_GREW_PAST_BOUND')
 return raw

def verify(C,context):
 C=Path(C);v=json.loads(read_bounded(C/'native-io-diagnostic-export.json',65536,C));p=Path(v['artifactPath']);raw=read_bounded(p,CAP,C/'android')
 if not p.resolve().is_relative_to((C/'android').resolve())or p.name!='stdout.bin'or sha(raw)!=v['artifactSHA256']or sha(raw)!=v['deviceBeforeAfterSHA256']or len(raw)!=v['artifactBytes']or v['context']!=context or v['selectedAPKSourceSHA256']!=contract.SOURCE_SHA256 or v['selectedAPK_SHA256']!=contract.APK_SHA256 or v['selectedBuildReceiptSHA256']!=contract.sha(contract.ROOT/contract.BUILD)or v['certificateSHA256']!=certificate_sha(contract.build_receipt()):raise ValueError('DIAGNOSTIC_OUTSIDE_BINDING')
 closedpath=Path(v['outsideClosedProofPath'])
 closedraw=read_bounded(closedpath,131072,C)
 if closedpath.resolve()!=(C/'native-last-external-observation.json').resolve()or sha(closedraw)!=v['outsideClosedProofSHA256']:raise ValueError('DIAGNOSTIC_OUTSIDE_CLOSED_PROOF_SHA')
 closed=json.loads(closedraw)
 if closed.get('closed')is not True or closed.get('journal',{}).get('commitAnchor')!=v['closedNativeCommitAnchor']or any(closed.get(k)!=context[k]for k in('run','epoch','boot','generation')):raise ValueError('DIAGNOSTIC_OUTSIDE_CLOSED_CONTEXT')
 expected=[['shell','run-as',contract.PACKAGE,'wc','-c',v['devicePath']],['shell','run-as',contract.PACKAGE,'sha256sum',v['devicePath']],['exec-out','run-as',contract.PACKAGE,'cat',v['devicePath']],['shell','run-as',contract.PACKAGE,'sha256sum',v['devicePath']]]
 if v['devicePath']!=diagnostic_path(context['run'])or len(v['commands'])!=4:raise ValueError('DIAGNOSTIC_PATH_OR_COMMAND_COUNT')
 outputs=[]
 for proof,args in zip(v['commands'],expected):
  receipt=Path(proof['receipt']);receipt_raw=read_bounded(receipt,65536,C/'android');q=json.loads(receipt_raw);out=read_bounded(receipt.parent/'stdout.bin',CAP if args[0]=='exec-out'else 65536,C/'android')
  if not receipt.resolve().is_relative_to((C/'android').resolve())or sha(receipt_raw)!=proof['receiptSHA256']or q['argv']!=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582',*args]or q['exit']!=0 or q['timedOut']is not False or q['stdoutSHA256']!=sha(out)or q['stdoutBytes']!=len(out):raise ValueError('DIAGNOSTIC_COMMAND_PROOF')
  outputs.append(out)
 if outputs[2]!=raw or outputs[1]!=outputs[3]or outputs[1].decode().split()!=[sha(raw),v['devicePath']]or outputs[0].decode().split()!=[str(len(raw)),v['devicePath']]:raise ValueError('DIAGNOSTIC_COMMAND_OUTPUT_BINDING')
 forensic=bool(closed.get('firstFailure'))or closed.get('lifecycle',{}).get('phase')=='FAILED'
 if v.get('forensicOnly')is not forensic:raise ValueError('DIAGNOSTIC_FAILED_DISPOSITION_BINDING')
 if forensic:verify_binding(raw,context,contract.SOURCE_SHA256)
 else:validate(raw,context,contract.SOURCE_SHA256)
 return {'status':'CLOSED_FAILED_DIAGNOSTIC_FORENSICS_ONLY'if forensic else'BOUNDED_DEVICE_DIAGNOSTIC_SHA_CONTEXT_PASS_NOT_FLIGHT_ACCEPTANCE','forensicOnly':forensic,'successfulShortQualified':False,'bytes':len(raw),'sha256':sha(raw),'sourceSHA256':contract.SOURCE_SHA256,'terminalStateSHA256IsDiagnosticChecksumNotExternalTerminalProof':True,'diagnosticDeviceRestartPersistenceChecked':False,'inputAuthorityRequiresFullNativeRawOracle':True,'phaseDurations':'NESTED_INCLUSIVE_DO_NOT_SUM_TO_RUN_WALL_OR_EXCLUSIVE_BOTTLENECK','outsideClosedProofSHA256':v['outsideClosedProofSHA256']}


def verify_sampler_binding(C,sampler):
 C=Path(C);export=json.loads(read_bounded(C/'native-io-diagnostic-export.json',65536,C));raw=read_bounded(Path(export['artifactPath']),CAP,C/'android');v=verify_binding(raw,export['context'],contract.SOURCE_SHA256)
 rows=[q for q in v['recentQueueEvents']if q['kind']=='SAMPLER_UI_LIVENESS']
 if not rows or type(sampler.get('samplerThreadId'))is not int or sampler['samplerThreadId']==sampler.get('uiThreadId')or any(q['threadId']!=sampler['samplerThreadId']for q in rows):raise ValueError('DIAGNOSTIC_DEDICATED_THREAD_RAW_INPUT_BINDING')
 return {'status':'DIAGNOSTIC_DEDICATED_THREAD_MATCHES_FULL_RAW_INPUT_SAMPLER','boundedSamplerDiagnosticEvents':len(rows),'samplerThreadId':sampler['samplerThreadId'],'uiThreadId':sampler['uiThreadId'],'provenance':'LOCAL_SOURCE_BOUND_IMMUTABLE_CACHED_TOUCH_STATE_NOT_NEW_PHYSICAL_EVENT','exclusiveIOCauseOrFlightProof':False}
