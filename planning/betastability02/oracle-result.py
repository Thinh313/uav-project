"""Second implementation: read-only MAVLink wire parsing + Python FPS/clock join.
Protocol offsets/CRC extras were checked against retained MAVLink definitions;
this implementation imports no JavaScript verifier and makes no hardware claim.
"""
from pathlib import Path
import json,struct,hashlib,math
import sys,traceback
R=Path(__file__).resolve().parents[2];H=Path(sys.argv[1]).resolve();run=sys.argv[2];assert H.is_relative_to(R/'evidence/betastability02') and __import__('re').fullmatch('s[a-f0-9]{20}',run)
result={'status':'FAIL','implementation':'PYTHON_SECOND_IMPLEMENTATION_NO_JS_VERIFIER_IMPORT','source':'RETAINED_ACTUAL_ANDROID_SITL_RAW_AND_BROWSER_SAMPLES','independentHumanQA':False,'physicalLatency':'NOT_MEASURED','run':run}
try:
 rows=[json.loads(x)for x in(H/'flight/runs'/run/'raw.jsonl').read_text().splitlines()];declared=json.loads((H/('auto-video-qualification-'+run+'.json')).read_text())
 extra={0:50,33:104,76:152,245:130}
 class Wire:
  def __init__(self):self.buf=b'';self.checked=0
  def feed(self,chunk):
   self.buf+=chunk;out=[]
   while self.buf:
    if self.buf[0]not in(253,254):self.buf=self.buf[1:];continue
    v2=self.buf[0]==253;h=10 if v2 else 6
    if len(self.buf)<h:break
    n=self.buf[1];signed=v2 and self.buf[2]&1;total=h+n+2+(13 if signed else 0)
    if len(self.buf)<total:break
    b=self.buf[:total];self.buf=self.buf[total:];mid=int.from_bytes(b[7:10],'little')if v2 else b[5]
    if mid not in extra:continue
    assert not signed,'SIGNED_FRAME_NOT_SUPPORTED'
    c=65535
    for v in b[1:h+n]+bytes([extra[mid]]):
     t=(v^(c&255));t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535
    assert c==int.from_bytes(b[h+n:h+n+2],'little'),'WIRE_CRC'
    self.checked+=1;out.append((mid,b[5 if v2 else 3],b[6 if v2 else 4],b[h:h+n]+bytes(64)))
   return out
 rx=Wire();tx=Wire();start=None;end=None;auto=False;air=False;armed=None;landed=None
 for row in rows:
  t=int(row['hostNs'])/1e6
  if row['kind']=='TX_RAW':
   for mid,sy,co,p in tx.feed(bytes.fromhex(row['data']['rawHex'])):
    if mid==76 and struct.unpack_from('<H',p,28)[0]==176 and struct.unpack_from('<f',p,4)[0]==3 and p[30:32]==bytes([42,1]) and start is None:start=t
  if row['kind']!='RX_RAW' or start is None:continue
  for mid,sy,co,p in rx.feed(bytes.fromhex(row['data']['rawHex'])):
   if(sy,co)!=(42,1):continue
   if mid==0:
    armed=bool(p[6]&128)
    if armed and struct.unpack_from('<I',p)[0]==3:auto=True
   if mid==33 and struct.unpack_from('<i',p,16)[0]>2000:air=True
   if mid==245:landed=p[1]
   if auto and air and landed==1 and armed is False and end is None:end=t
 assert start is not None and end is not None and auto and air
 frames=[];reports=[]
 for binding in sorted(H.glob('binding-report-*.json')):
  b=json.loads(binding.read_text())
  if b['flight']['run']!=run:continue
  p=H/'media'/b['rawReport']['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==b['rawReport']['sha256'];r=json.loads(p.read_text());reports.append(r)
  for s in r['samples']:
   lo=s['latencyLowerMs']+s['sourceHostBounds']['upperMs'];hi=s['latencyUpperMs']+s['sourceHostBounds']['lowerMs'];assert lo<=hi;frames.append((lo,hi,s['latencyUpperMs']))
 assert len(reports)==6 and frames and frames[0][1]<=start and frames[-1][0]>=end,'SIX_REPORTS_FULL_AUTO_COVERAGE'
 required=['apiFailures','decoderErrors','consumerDrops','timestampMisses','unexpectedFreeze']
 identity=None
 for report in reports:
  scope=tuple(report[k]for k in ['serverBoot','run','boot','configId','feed','profileId'])
  if identity is None:identity=scope
  assert scope==identity,'REPORT_SOURCE_CONTEXT'
  assert report['sourceKind']=='SYNTHETIC' and report['actualImages']==0,'REPORT_SOURCE_SCOPE'
  assert report['foregroundOnly'] is True and report['visualForeground'] is True and report['overflow']==0 and report['stopReason']is None,'REPORT_COVERAGE'
  assert report['sampleCount']==len(report['samples']) and 30000<=report['durationMs']<=60050,'REPORT_SAMPLE_DURATION'
  for key in required:assert report['counters'][key]-report['counterBaseline'][key]==0,'COUNTER_DELTA:'+key
 assert all(a[0]<=a[1] and b[0]>=a[0] and b[1]>=a[1]for a,b in zip(frames,frames[1:])),'FRAME_CLOCK_ORDER'
 
 inside=[s for s in frames if s[0]>=start and s[1]<=end];near=[s for s in frames if s[1]>=start-250 and s[0]<=end+250];fps=len(inside)*1000/(end-start);lat=sorted(s[2]for s in inside)[math.ceil(len(inside)*.95)-1];gap=max(b[1]-a[0]for a,b in zip(near,near[1:]));bins=[];t=start
 while t+5000<=end:
  bins.append(sum(1 for lo,hi,_ in inside if lo>=t and hi<t+5000)/5);t+=5000
 assert start==declared['startHostMs']and end==declared['endHostMs']and len(inside)==declared['frames']
 assert abs(fps-declared['displayedFps'])<1e-9 and lat==declared['latencyP95UpperMs']and gap==declared['maximumConservativeGapMs']
 gates={'fps':fps>=24,'everyFull5s':min(bins)>=24,'latencyP95Upper':lat<=300,'maximumGap':gap<=250}
 result.update({'wireMessagesCRCChecked':rx.checked+tx.checked,'startHostMs':start,'endHostMs':end,'frames':len(inside),'displayedFps':fps,'minimum5sFps':min(bins),'latencyP95UpperMs':lat,'maximumConservativeGapMs':gap,'gates':gates,'reportCount':len(reports)})
 result['status']='PASS'if all(gates.values())else'FAIL'
except BaseException as e:
 result.update(error=repr(e),failureTrace=traceback.format_exc())
 for key in ['start','end','fps','gap','lat','bins','gates']:
  if key in locals():result.setdefault('partialMetrics',{})[key]=locals()[key]
target=R/('evidence/betastability02/oracle-result-'+run+'.json')
with target.open('x')as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
if result['status']!='PASS':sys.exit(1)
