"""Second byte/frame verifier. Does not replace JS semantic Arbiter replay or signatures."""
import argparse,base64,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('packages',nargs='+');p.add_argument('--output',required=True);a=p.parse_args()
H=lambda b:hashlib.sha256(b).hexdigest()
C=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
rows=[]
for name in a.packages:
 path=Path(name);assert path.stat().st_size<=24*1024**2;raw=path.read_bytes();d=json.loads(raw);assert set(d)=={'body','sha256'};b=d['body'];assert C(d)==raw and H(C(b))==d['sha256'];assert b['format']=='aeris-archive69' and b['version']==1 and b['authorityRestorable'] is False and b['actualImages']==0
 assert 3<=len(b['files'])<=34;names=set();files={}
 for e in b['files']:
  assert set(e)=={'name','bytes','sha256'};assert e['name'] not in names and re.fullmatch(r'(store\.json|catalog\.wal|run-[a-f0-9]{32}\.wal)',e['name']);names.add(e['name'])
  r=base64.b64decode(b['data'][e['name']],validate=True);assert base64.b64encode(r).decode()==b['data'][e['name']] and len(r)==e['bytes'] and H(r)==e['sha256'];files[e['name']]=r
 assert names==set(b['data']) and sum(map(len,files.values()))<=16*1024**2
 scans={}
 for filename,r in files.items():
  if not filename.endswith('.wal'):continue
  offset=0;seq=0;prev='ROOT';records=[];tail=False
  while offset<len(r):
   if len(r)-offset<9:tail=True;break
   header=r[offset:offset+9];assert re.fullmatch(rb'[0-9a-f]{8}:',header);n=int(header[:8],16);assert 1<=n<=16384;end=offset+9+n+66
   if end>len(r):tail=True;break
   recordraw=r[offset+9:offset+9+n];record=json.loads(recordraw);suffix=r[offset+9+n:end];assert C(record)==recordraw and suffix==b'#'+H(recordraw).encode()+b'\n';seq+=1;assert record['seq']==seq and record['previous']==prev and record['format']=='J68/1';prev=H(recordraw);records.append(record);offset=end
  scans[filename]={'records':len(records),'tail':tail,'fileSha256':H(r)}
 rows.append({'path':str(path),'pass':True,'packageSha256':H(raw),'files':len(files),'frameScans':scans})
out={'status':'PASS_PYTHON_BYTE_FRAME_SHA','rows':rows,'scope':'Second implementation canonical package/base64/entry/frame/chain verification; semantic replay remains pinned JS Arbiter; no independent auditor/provenance claim'}
with Path(a.output).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({'passed':len(rows),'total':len(rows)}))
