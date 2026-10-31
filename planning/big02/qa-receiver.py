"""Independent synthetic capture integrity/math receiver. Never imports sender modules.
Only stdlib. JPEG validation is structural, not a decoder/security certificate.
Local replay state is receiver bookkeeping, not identity attestation/flight authority.
"""
from pathlib import Path
import json,hashlib,math,re,struct,sys,argparse,os
ID=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z');HEX=re.compile('[a-f0-9]{64}\\Z')
CTX={'runId','aircraftId','cameraId','bootId','clockDomain','feedId'}
class Refused(ValueError):pass
def need(b,r):
 if not b:raise Refused(r)
def exact(v,keys):return type(v)is dict and set(v)==set(keys)
def num(v):return type(v)in(int,float)and math.isfinite(v)
def stamp(v):return num(v)and 0<=v<=2**53-1
def identifier(v):return type(v)is str and bool(ID.fullmatch(v))
def sha(b):return hashlib.sha256(b).hexdigest()
def unique(p):
 d={}
 for k,v in p:need(k not in d,'DUPLICATE_JSON_KEY');d[k]=v
 return d
def parse(b):
 need(type(b)is bytes and len(b)<=131072,'JSON_BYTES_BOUND')
 return json.loads(b.decode('utf-8','strict'),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in()).throw(Refused('NONFINITE_JSON')))
def canonical(v):
 # Package manifest contains no floats: sorted ASCII schema keys + integer sizes.
 return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def jpeg_structure(b):
 need(20<=len(b)<=4*2**20 and b[:2]==b'\xff\xd8'and b[-2:]==b'\xff\xd9','JPEG_ENCLOSURE')
 p=2;frame=False;scan=False;markers=0
 while p<len(b):
  markers+=1;need(markers<=65536 and b[p]==255,'JPEG_MARKER');p+=1
  while p<len(b)and b[p]==255:p+=1
  need(p<len(b),'JPEG_TRUNCATED');kind=b[p];p+=1
  if kind==217:need(p==len(b)and frame and scan,'JPEG_EOI');return
  need(kind not in [0,216,*range(208,216)],'JPEG_MARKER_CONTEXT')
  if kind==1:continue
  need(p+2<=len(b),'JPEG_SEGMENT');n=int.from_bytes(b[p:p+2],'big');need(n>=2 and p+n<=len(b),'JPEG_LENGTH')
  if kind in(192,193,194):
   need(not frame and n>=11,'JPEG_SOF');h=int.from_bytes(b[p+3:p+5],'big');w=int.from_bytes(b[p+5:p+7],'big');c=b[p+7];need(1<=h<=8192 and 1<=w<=8192 and c in(1,3,4)and n==8+3*c,'JPEG_DIMENSIONS');frame=True
  elif 195<=kind<=207 and kind not in(196,200,204):raise Refused('JPEG_FRAME_UNSUPPORTED')
  if kind==218:
   need(frame and n>=6 and n==6+2*b[p+2],'JPEG_SOS');scan=True;p+=n
   while p<len(b):
    if b[p]!=255:p+=1;continue
    need(p+1<len(b),'JPEG_ENTROPY_TRUNCATED');z=b[p+1]
    if z==0 or 208<=z<=215:p+=2;continue
    if z==255:p+=1;continue
    break
  else:p+=n
 raise Refused('JPEG_MISSING_END')
def context(v):need(exact(v,CTX)and all(identifier(x)for x in v.values()),'CONTEXT_SCHEMA')
def same(v,c):return all(v.get(k)==c[k]for k in CTX)
def near(a,b):return num(a)and abs(a-b)<=max(1e-9,abs(b)*1e-12)
def validate_metadata(s):
 need(exact(s,['schemaVersion','kind','sourceKind','actualImages','binding','position'])and type(s['schemaVersion'])is int and s['schemaVersion']==1 and s['kind']=='AERIS_SYNTHETIC_CAPTURE_SIDECAR'and s['sourceKind']=='SYNTHETIC'and type(s['actualImages'])is int and s['actualImages']==0,'SIDECAR_SCHEMA')
 b=s['binding'];need(exact(b,['schemaVersion','sourceKind','context','event','gnss','file','policy'])and type(b['schemaVersion'])is int and b['schemaVersion']==1 and b['sourceKind']=='SYNTHETIC','BINDING_SCHEMA');c=b['context'];context(c);e=b['event']
 need(exact(e,[*CTX,'kind','captureId','frameId','exposureMonotonicMs','timeUncertaintyMs'])and e['kind']=='CAPTURE_EVENT'and same(e,c)and identifier(e['captureId'])and identifier(e['frameId']),'EXPOSURE_EVENT_IDENTITY')
 need(stamp(e['exposureMonotonicMs'])and num(e['timeUncertaintyMs'])and e['timeUncertaintyMs']>=0,'EXPOSURE_TIME')
 p=b['policy'];caps={'maxSampleAgeMs':1000,'maxBracketSpanMs':2000,'maxTimeUncertaintyMs':50};need(exact(p,caps)and all(num(p[k])and 0<p[k]<=caps[k]for k in caps),'POLICY_BOUNDS');need(e['timeUncertaintyMs']<=p['maxTimeUncertaintyMs'],'EXPOSURE_UNCERTAIN')
 f=b['file'];need(exact(f,['name','mime','sizeBytes','sha256'])and f['name']=='original.jpg'and f['mime']=='image/jpeg'and type(f['sizeBytes'])is int and 4<=f['sizeBytes']<=4*2**20 and type(f['sha256'])is str and HEX.fullmatch(f['sha256']),'FILE_DESCRIPTOR')
 g=b['gnss'];need(type(g)is list and 2<=len(g)<=256,'GNSS_COUNT');last=-1
 for x in g:
  need(exact(x,[*CTX,'monotonicMs','timeUncertaintyMs','quality','latitudeDeg','longitudeDeg','altitude'])and same(x,c),'GNSS_IDENTITY_SCHEMA');need(x['quality']=='VALID_3D'and stamp(x['monotonicMs'])and x['monotonicMs']>last,'GNSS_QUALITY_ORDER');last=x['monotonicMs'];need(num(x['timeUncertaintyMs'])and 0<=x['timeUncertaintyMs']<=p['maxTimeUncertaintyMs'],'GNSS_UNCERTAINTY');need(num(x['latitudeDeg'])and -90<=x['latitudeDeg']<=90 and num(x['longitudeDeg'])and -180<=x['longitudeDeg']<=180,'GNSS_COORDINATES');a=x['altitude'];need(exact(a,['value','unit','datum'])and num(a['value'])and -1000<=a['value']<=100000 and a['unit']=='m'and a['datum']=='WGS84_ELLIPSOID','ALTITUDE_DATUM')
 t=e['exposureMonotonicMs'];pairs=[(g[i],g[i+1])for i in range(len(g)-1)if g[i]['monotonicMs']<=t<=g[i+1]['monotonicMs']];need(bool(pairs),'NO_EXPOSURE_BRACKET');a,z=pairs[0];u=e['timeUncertaintyMs']+max(a['timeUncertaintyMs'],z['timeUncertaintyMs']);need(u<=p['maxTimeUncertaintyMs']and max(t-a['monotonicMs'],z['monotonicMs']-t)+u<=p['maxSampleAgeMs']and z['monotonicMs']-a['monotonicMs']<=p['maxBracketSpanMs'],'STALE_OR_UNCERTAIN_BRACKET');alpha=(t-a['monotonicMs'])/(z['monotonicMs']-a['monotonicMs']);delta=z['longitudeDeg']-a['longitudeDeg'];delta=(delta+180)%360-180;need(abs(delta)!=180,'ANTIPODAL_AMBIGUITY');lat=a['latitudeDeg']+(z['latitudeDeg']-a['latitudeDeg'])*alpha;lon=(a['longitudeDeg']+alpha*delta+180)%360-180;alt=a['altitude']['value']+alpha*(z['altitude']['value']-a['altitude']['value']);v=s['position'];need(exact(v,['reference','horizontalDatum','angleUnit','latitudeDeg','longitudeDeg','altitude','interpolation','bracketMonotonicMs','timeUncertaintyMs','spatialAccuracy','cameraLeverArm','targetLocation']),'POSITION_SCHEMA');need(v['reference']=='AIRCRAFT_GNSS_AT_EXPOSURE'and v['horizontalDatum']=='WGS84'and v['angleUnit']=='degree'and v['interpolation']=='LINEAR_LATITUDE_SHORTEST_LONGITUDE_ALTITUDE'and v['spatialAccuracy']=='UNKNOWN'and v['cameraLeverArm']=='UNKNOWN'and v['targetLocation']=='NOT_DETERMINED','POSITION_CLAIMS');need(near(v['latitudeDeg'],lat)and near(v['longitudeDeg'],lon)and exact(v['altitude'],['value','unit','datum'])and near(v['altitude']['value'],alt)and v['altitude']['unit']=='m'and v['altitude']['datum']=='WGS84_ELLIPSOID'and v['bracketMonotonicMs']==[a['monotonicMs'],z['monotonicMs']]and near(v['timeUncertaintyMs'],u),'POSITION_DERIVATION');return {'alpha':alpha,'latitudeDeg':lat,'longitudeDeg':lon,'altitudeM':alt,'timeUncertaintyMs':u}
def verify_bytes(files,receiver_id,sender_id,seen_transfers,seen_captures,expected_context=None):
 need(set(files)=={'manifest.json','original.jpg','sidecar.json'},'EXACT_PACKAGE_FILES');need(all(type(v)is bytes for v in files.values()),'BYTE_TYPE');need(len(files['manifest.json'])<=131072 and len(files['sidecar.json'])<=131072 and len(files['original.jpg'])<=4*2**20,'PACKAGE_BOUND');m=parse(files['manifest.json']);need(exact(m,['schemaVersion','kind','sourceKind','actualImages','transferId','senderId','receiverId','context','captureId','frameId','files','packageId'])and type(m['schemaVersion'])is int and m['schemaVersion']==1 and m['kind']=='AERIS_SYNTHETIC_CAPTURE_PACKAGE'and m['sourceKind']=='SYNTHETIC'and type(m['actualImages'])is int and m['actualImages']==0,'MANIFEST_SCHEMA');need(all(identifier(m[k])for k in ['transferId','senderId','receiverId','captureId','frameId'])and type(m['packageId'])is str and HEX.fullmatch(m['packageId']),'MANIFEST_IDENTIFIERS');need(m['receiverId']==receiver_id and m['senderId']==sender_id,'EXPECTED_RECEIVER_SENDER');context(m['context']);need(expected_context is None or m['context']==expected_context,'EXPECTED_CAPTURE_CONTEXT');need(len(seen_transfers)<10000 and len(seen_captures)<10000 and m['transferId']not in seen_transfers,'TRANSFER_REPLAY_OR_BOUND');base={k:v for k,v in m.items()if k!='packageId'};need(sha(canonical(base))==m['packageId'],'MANIFEST_PACKAGE_ID');need(type(m['files'])is list and len(m['files'])==2,'MANIFEST_MEMBERS')
 for f,path in zip(m['files'],['original.jpg','sidecar.json']):need(exact(f,['path','sizeBytes','sha256'])and f['path']==path and type(f['sizeBytes'])is int and f['sizeBytes']==len(files[path])and f['sha256']==sha(files[path]),'MEMBER_SHA_SIZE_PATH')
 jpeg_structure(files['original.jpg']);s=parse(files['sidecar.json']);derived=validate_metadata(s);b=s['binding'];need(m['context']==b['context']and m['captureId']==b['event']['captureId']and m['frameId']==b['event']['frameId']and b['file']['sha256']==sha(files['original.jpg'])and b['file']['sizeBytes']==len(files['original.jpg']),'MANIFEST_SIDECAR_BINDING');key=canonical({'context':m['context'],'captureId':m['captureId']}).decode();need(key not in seen_captures,'CAPTURE_REPLAY');seen_transfers.add(m['transferId']);seen_captures.add(key);return {'status':'ACCEPTED_SYNTHETIC_INTEGRITY_AND_MATH_ONLY','packageId':m['packageId'],'originalSha256':sha(files['original.jpg']),'actualImages':0,'derived':derived,'authenticity':'NOT_ATTESTED','realCameraMissionPhone':'NOT_CHECKED'}
def read_directory(p):
 need(not p.is_symlink()and p.is_dir(),'DIRECTORY');need({x.name for x in p.iterdir()}=={'manifest.json','original.jpg','sidecar.json'},'EXACT_DIRECTORY_MEMBERS');files={}
 for n,cap in [('manifest.json',131072),('sidecar.json',131072),('original.jpg',4*2**20)]:
  f=p/n;need(not f.is_symlink()and f.is_file()and 0<f.stat().st_size<=cap,'FILE_BOUND');files[n]=f.read_bytes()
 return files
def main():
 p=argparse.ArgumentParser();p.add_argument('--package-dir',type=Path,required=True);p.add_argument('--receiver-id',required=True);p.add_argument('--sender-id',required=True);p.add_argument('--state',type=Path,required=True);a=p.parse_args();transfers=set();captures=set()
 try:
  if a.state.exists():
   need(not a.state.is_symlink()and a.state.stat().st_size<=4*2**20,'REPLAY_STATE_BOUND');s=json.loads(a.state.read_text(),object_pairs_hook=unique);need(exact(s,['transfers','captures'])and type(s['transfers'])is list and type(s['captures'])is list,'REPLAY_STATE_SCHEMA');transfers=set(s['transfers']);captures=set(s['captures'])
  result=verify_bytes(read_directory(a.package_dir),a.receiver_id,a.sender_id,transfers,captures);temp=a.state.with_name(a.state.name+'.pending');fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w')as f:json.dump({'transfers':sorted(transfers),'captures':sorted(captures)},f);f.flush();os.fsync(f.fileno())
  os.replace(temp,a.state)
  directory=os.open(a.state.parent,os.O_RDONLY)
  try:os.fsync(directory)
  finally:os.close(directory)
  print(json.dumps(result));return 0
 except Exception as e:print(json.dumps({'status':'REFUSED_OR_OUTCOME_UNKNOWN','error':str(e),'actualImages':0}));return 2
if __name__=='__main__':raise SystemExit(main())
