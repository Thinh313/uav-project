from pathlib import Path
import base64,hashlib,io,json,sys,tarfile,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));from pilot.betaintegrated01.cockpit04.native_stream import closed_native,IndexedNative
Q=R/'evidence/betaintegrated01-m1cockpit04/qa';O=Q/'native-stream01';O.mkdir();source=Q/'reader01/fixtures/case11';prefix='files/control-runs/run/';sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda o:json.dumps(o,separators=(',',':'),ensure_ascii=False).encode();items={}
# Reuse original synthetic segments0..16 verbatim, append a new synthetic sealed
# terminal segment, without copying another native directory or real host raw.
for n in range(17):
 for pat in [f'segment-{n:06}.jsonl',f'seal-{n:06}.json']:items[pat]=(source/pat).read_bytes()
last=json.loads(items['seal-000016.json']);lastrow=json.loads(items['segment-000016.jsonl'].splitlines()[-1]);n=last['last'];head=last['head'];now=lastrow['monotonicNs'];prior=sha(items['seal-000016.json']);first=n+1;lines=[]
for kind,data in [('HEADER',dict(format='aeris-native-segments',version=1,segment=17,previousSeal=prior)),('SESSION_CLOSE',dict(reason='CONTROL_OWNED_RESOURCES_CLOSED',authorityRestorable=False,aircraftExecutionAccepted=False))]:
 n+=1;now+=1000000;b=enc(dict(format='aeris-native-record',version=1,run='run',epoch='epoch',segment=17,n=n,previous=head,monotonicNs=now,kind=kind,base64=base64.b64encode(enc(data)).decode()));head=sha(b);lines.append(b[:-1]+b',"sha256":"'+head.encode()+b'"}\n')
body=b''.join(lines);items['segment-000017.jsonl']=body;items['seal-000017.json']=enc(dict(format='aeris-native-seal',version=1,run='run',epoch='epoch',segment=17,file='segment-000017.jsonl',bytes=len(body),sha256=sha(body),first=first,last=n,head=head,previousSeal=prior));items['session.json']=enc(dict(format='aeris-native-session',version=1,run='run',epoch='epoch',segments=18,records=n,head=head,lastSeal=sha(items['seal-000017.json']),authorityRestorable=False,publicationAllowed=False));items['writer.lock']=b'';anchor=sha(items['session.json']);path=O/'synthetic-native17MiB.tar'
with tarfile.open(path,'x')as t:
 for name,b in items.items():m=tarfile.TarInfo(prefix+name);m.size=len(b);t.addfile(m,io.BytesIO(b))
del items
results=[]
def ck(i,p,detail=None):results.append(dict(id=i,pass_=bool(p),detail=detail))
report,rows=closed_native(str(path),prefix,anchor);count=sum(1 for _ in rows);ck('newReaderBeyondOld16MiB',report['selectedRunBytes']>16*2**20 and count==report['records'],dict(records=count,bytes=report['selectedRunBytes']))
from pilot.betaintegrated01.control04.confirmation import _closed_native as old
try:old(str(path),prefix,anchor);good=False;reason='ACCEPTED'
except ValueError as e:reason=str(e);good=reason=='NATIVE_TAR_TOTAL_BOUND'
ck('old16MiBGuardActuallyRejects',good,reason)
with tarfile.open(path,'r:')as t:m=t.getmember(prefix+'segment-000017.jsonl');offset=m.offset_data+20
with path.open('r+b')as f:f.seek(offset);before=f.read(1);f.seek(offset);f.write(bytes([before[0]^1]))
try:
 try:closed_native(str(path),prefix,anchor);good=False;reason='ACCEPTED'
 except Exception as e:good=True;reason=type(e).__name__+':'+str(e)
 ck('lateSegmentCorruptionRejected',good,reason)
finally:
 with path.open('r+b')as f:f.seek(offset);f.write(before)
report,rows=closed_native(str(path),prefix,anchor);ck('restoredFullRowDrain',sum(1 for _ in rows)==count)
# Selected-run symbolic members must not silently vanish from an exact archive.
small=O/'symlink-selected.tar'
with tarfile.open(small,'x')as t:
 with tarfile.open(path,'r:')as oldtar:
  for member in oldtar:
   if member.name.startswith(prefix+'segment-')or member.name.startswith(prefix+'seal-'):continue
   b=oldtar.extractfile(member).read();t.addfile(member,io.BytesIO(b))
 bad=tarfile.TarInfo(prefix+'segment-000000.jsonl');bad.type=tarfile.SYMTYPE;bad.linkname='/untrusted';t.addfile(bad)
try:IndexedNative(str(small),prefix);good=False;reason='ACCEPTED'
except Exception as e:good=True;reason=str(e)
ck('selectedSymlinkIncompleteRunRejects',good,reason)
r=dict(status='PASS'if all(x['pass_']for x in results)else'FAIL',results=results,syntheticTarSHA256=sha(path.read_bytes()),externalSyntheticAnchor=anchor,sourceSHA256=sha((R/'pilot/betaintegrated01/cockpit04/native_stream.py').read_bytes()),scope='Synthetic current-format17MiB selected native archive, not actual30minute runtime. Original33MiB segments reused read-only; no realhostrawcopy.',servicesStarted=0);(O/'results.json').open('x').write(json.dumps(r,indent=2));print(r['status'],[(x['id'],x['pass_'])for x in results])
