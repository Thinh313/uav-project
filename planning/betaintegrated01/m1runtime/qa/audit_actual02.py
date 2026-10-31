"""Independent cold execution and raw-native MAVLink decoding of closed actual02."""
from pathlib import Path
import base64,collections,datetime,hashlib,importlib.util,json,re,struct,sys,time
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime02.verify_capture import verify_capture
O=R/'evidence/betaintegrated01-m1runtime/actual02';C=O/'control';D=O/'raw';N=O/'native-extracted/files/runs/m1short02'
anchors=json.loads((C/'anchors-live01.json').read_text());cfg=json.loads((D/'run-config.json').read_text());run,epoch,boot=(cfg[k]for k in ['run','epoch','boot'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins=json.loads((C/'input-pins.json').read_text())['files'];before={p:sha(R/p)for p in pins};errors=[];started=time.monotonic()
def check(b,s):
 if not b:raise AssertionError(s)
check(all(anchors[k]==cfg[k]for k in ['run','epoch','boot']),'anchor context')
try:host=verify_capture(D,run,epoch,boot,expected_host_anchor=anchors['hostCommit'],expected_stage_anchor=anchors['APTerminalSHA256'],load=cfg['load'],wind=cfg['wind'],seed=cfg['seed'])
except Exception as e:host={'status':'FAIL_COLD','error':type(e).__name__+':'+str(e)};errors.append(host['error'])
spec=importlib.util.spec_from_file_location('native_independent02',R/'native/betaintegrated01/runtime/receiver.py');nr=importlib.util.module_from_spec(spec);spec.loader.exec_module(nr)
native=nr.verify(N,run,epoch,anchors['nativeSessionSHA256']);check(native['byteSequenceComplete']and native['writerCommitAttested'],'native cold')
ds=(R/'native/betaintegrated01/runtime/src/vn/rtr/aeris/native98/Dialect95.java').read_text();dialect={int(i):tuple(map(int,(a,b,c)))for i,a,b,c in re.findall(r'D.put\((\d+),new int\[\]\{(\d+),(\d+),(\d+)\}\)',ds)};offsets={k:int(v)for k,v in re.findall(r'O.put\("([^"]+)",(\d+)\)',ds)}
def crc(data,extra):
 c=65535
 for v in [*data,extra]:
  t=v^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535
 return c
class Parser:
 def __init__(self):self.pending=b'';self.frames=collections.Counter();self.banner=bytearray();self.commands=collections.Counter();self.firmware=[];self.hb_armed=[];self.parameters=set();self.targets=collections.Counter();self.lastseq=None;self.duplicates=0;self.forwardgaps=0
 def feed(self,raw,tx=False):
  self.pending+=raw
  while self.pending:
   b=self.pending
   if b[0]not in(253,254):self.banner.append(b[0]);self.pending=b[1:];check(len(self.banner)<=1024,'native banner bound');continue
   if len(b)<2:return
   h=10 if b[0]==253 else 6
   if len(b)<h:return
   length=b[1];msg=int.from_bytes(b[7:10],'little')if h==10 else b[5];minimum,maximum,extra=dialect[msg];total=h+length+2
   if len(b)<total:return
   check(1<=length<=maximum and(h==10 or length==minimum),'native dialect length');check(h!=10 or b[2]==0,'native flags');check(crc(b[1:h+length],extra)==int.from_bytes(b[h+length:total],'little'),'native CRC')
   sysid,comp=b[5:7]if h==10 else b[3:5];seq=b[4]if h==10 else b[2];p=b[h:h+length]+bytes(maximum-length);self.targets[(sysid,comp)]+=1;self.frames[msg]+=1
   if tx:
    check((sysid,comp)==(255,190),'native tx identity');check(msg in(0,20,76),'native read-only msg')
    if msg==76:
     command=struct.unpack_from('<H',p,offsets['76:command'])[0];check(command in(511,512),'flight mutation in read-only capture');self.commands[command]+=1
    if msg!=0:check(p[offsets[str(msg)+':target_system']]==42 and p[offsets[str(msg)+':target_component']]==1,'native read-only target')
   elif(sysid,comp)==(42,1):
    if self.lastseq is not None:
     delta=(seq-self.lastseq)%256
     if delta==0:self.duplicates+=1
     elif 1<delta<128:self.forwardgaps+=delta-1
    self.lastseq=seq
    if msg==148:
     version=struct.unpack_from('<I',p,offsets['148:flight_sw_version'])[0];at=offsets['148:flight_custom_version'];custom=p[at:at+8].decode('ascii');self.firmware.append({'version':version,'custom':custom});check(version == 67568127 and custom=='dbe79216','native firmware')
    if msg==0:self.hb_armed.append(bool(p[offsets['0:base_mode']]&128))
    if msg==22:
     at=offsets['22:param_id'];self.parameters.add(p[at:at+16].split(b'\0')[0].decode('ascii'))
   self.pending=b[total:]
rx,tx=Parser(),Parser();kinds=collections.Counter();raw_rx=raw_tx=0;last_review=None
for p in sorted(N.glob('segment-*.jsonl')):
 for line in p.open('rb'):
  row=json.loads(line);kind=row['kind'];kinds[kind]+=1;data=base64.b64decode(row['base64'],validate=True)
  if kind=='RX':raw_rx+=len(data);rx.feed(data)
  elif kind=='TX_WRITTEN':raw_tx+=len(data);tx.feed(data,True)
  elif kind=='REVIEW':last_review=json.loads(data)
check(rx.firmware and rx.hb_armed and not any(rx.hb_armed),'firmware/disarmed observation')
check(not any(kinds[k]for k in ['MANUAL_BINDING','MANUAL_CONSENT','TX_UNKNOWN']),'manual/unknown in read-only capture')
check(last_review and last_review['lifecycle']['phase']=='RESOURCES_CLOSED','native review boundary')
live=[json.loads(l)for l in(C/'native-live-states.jsonl').read_text().splitlines()];matching=[r for r in live if r['state'].get('run')==run];closed=[r['state']for r in matching if r['state'].get('closed')is True]
check(closed,'matching native closed observation');terminal=closed[0];check(terminal['lifecycle']['phase']=='SEALED'and terminal['lifecycle']['leaseActive']is False and terminal['manualConsent']is False,'native no authority')
check(all(x['lifecycle']['activeElapsedNs']==terminal['lifecycle']['activeElapsedNs']for x in closed),'closed elapsed changed')
backend=json.loads((D/'backend-result.json').read_text());after={p:sha(R/p)for p in pins};drift=[p for p,h in pins.items()if before[p]!=h or after[p]!=h]
host_channel=[json.loads(l)for l in(C/'backend-control-stdout.txt').read_text().splitlines()if l.startswith('{')][-1];ap_channel=[json.loads(l)for l in(C/'container-control-stdout.txt').read_text().splitlines()if l.startswith('{')][-1]
check(host_channel['commitAnchor']==anchors['hostCommit']and ap_channel['terminalSHA256']==anchors['APTerminalSHA256'],'anchors not from parent channels')
check(terminal['journal']['commitAnchor']==anchors['nativeSessionSHA256'],'native anchor not from closed live checkpoint')
check(not drift,'input pins changed')
result={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_SCOPED_ACTUAL_READONLY_SHORT'if not errors else'FAIL_COLD_SCOPE','host':host,'nativeCold':native,'nativeIndependentWire':{'rxMessageCounts':dict(rx.frames),'txMessageCounts':dict(tx.frames),'txCommands':dict(tx.commands),'firmware':rx.firmware,'heartbeatObservations':len(rx.hb_armed),'anyObservedArmed':any(rx.hb_armed),'parameterNames':sorted(rx.parameters),'RXBytes':raw_rx,'TXWrittenBytes':raw_tx,'pendingRXBytes':len(rx.pending),'pendingTXBytes':len(tx.pending),'selectedWireDuplicatesObserved':rx.duplicates,'selectedForwardSequenceGapsObserved':rx.forwardgaps,'recordKinds':dict(kinds)},'closedNative':{'matchingLiveRows':len(matching),'closedRows':len(closed),'activeElapsedNs':terminal['lifecycle']['activeElapsedNs'],'phase':terminal['lifecycle']['phase'],'leaseActive':terminal['lifecycle']['leaseActive'],'manualConsent':terminal['manualConsent'],'firmwareObserved':terminal['flight']['firmwareObserved'],'typedParameters':terminal['flight']['typedParameters']},'timing':{'backendActualRTF':backend['actualRTF'],'requestedSpeedup':backend['requestedSpeedup'],'capMs':backend['capMs'],'receiveWallSeconds':backend['receiveWallSeconds'],'modelSeconds':backend['modelSeconds'],'qualifiedDuration':'60s_requested_host/read-only_native_~35s; NOT30min'},'inputPinDrift':drift,'externalAnchorOriginVerified':True,'sourceAndReceiptHashes':{'anchors':sha(C/'anchors-live01.json'),'inputPins':sha(C/'input-pins.json'),'hostColdReceiver':sha(R/'pilot/betaintegrated01/runtime02/verify_capture.py'),'nativeColdReceiver':sha(R/'native/betaintegrated01/runtime/receiver.py')},'elapsedColdSeconds':time.monotonic()-started,'APAndroidSocketRuntimeLaunchesByQA':0,'APExitInterpretation':'-9 declared simulator forcedstop with EOF/drain; not graceful AP exit or ground/flight proof','NOT_CHECKED':['manual/assisted control and neutral takeover','AP reboot/lost-link on this revision','30min/performance qualification','media/payload/mission/fullcockpit','physicalHera/HeraHub/SDK'],'actualM1Ready':False,'BetaSIMReady':False,'publicationAllowed':False,'APExecutionAccepted':False}
(R/'evidence/betaintegrated01-m1runtime/qa/actual02-cold-audit.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'frames':host.get('frames'),'APcovered':host.get('APCoveredFrames'),'nativeRecords':native['records'],'nativeRXBytes':raw_rx,'nativeTXcommands':dict(tx.commands),'RTF':backend['actualRTF'],'inputDrift':drift}))
