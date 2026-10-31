from pathlib import Path
import sys,json,hashlib,tarfile,io
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));from pilot.betaintegrated01.cockpit04.native_stream import closed_native,IndexedNative
O=R/'evidence/betaintegrated01-m1cockpit04/qa/native-stream02';O.mkdir();path=R/'evidence/betaintegrated01-m1cockpit04/qa/native-stream01/synthetic-native17MiB.tar';prefix='files/control-runs/run/';sha=lambda b:hashlib.sha256(b).hexdigest()
with tarfile.open(path,'r:')as t:anchor=sha(t.extractfile(prefix+'session.json').read())
results=[]
def ck(i,p,detail=None):results.append(dict(id=i,pass_=bool(p),detail=detail))
report,rows=closed_native(str(path),prefix,anchor);count=sum(1 for _ in rows);ck('newReaderBeyondOld16MiB',report['selectedRunBytes']>16*2**20 and count==report['records'],dict(records=count,bytes=report['selectedRunBytes']))
from pilot.betaintegrated01.control04.confirmation import _closed_native as old
try:old(str(path),prefix,anchor);good=False;reason='ACCEPTED'
except Exception as e:reason=type(e).__name__+':'+str(e);good=isinstance(e,AssertionError)or str(e)=='NATIVE_TAR_TOTAL_BOUND'
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
