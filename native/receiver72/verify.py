"""Read-only second implementation of transport chunks, receipt, proof and custody SHA.
JS performs semantic replay. This is not an independent auditor or origin signature.
"""
import argparse,base64,hashlib,json,re,stat
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('receiver');p.add_argument('--output',required=True);a=p.parse_args()
H=lambda b:hashlib.sha256(b).hexdigest()
C=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def raw(p,maxsize=34*1024**2):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_nlink==1 and s.st_size<=maxsize;return p.read_bytes()
def obj(p,maxsize=1024**2):
 b=raw(p,maxsize);v=json.loads(b);assert C(v)==b;return v
root=Path(a.receiver);identity=obj(root/'identity.json');assert H(C(identity['body']))==identity['sha256'];receiver=identity['body']['receiverId'];rows=[]
for d in sorted((root/'transfers').iterdir()):
 m=obj(d/'manifest.json');assert m['transferId']==d.name and m['receiverId']==receiver and m['chunkBytes']==16384
 cs=sorted((d/'chunks').iterdir());assert len(cs)==len(m['chunks']);parts=[]
 for i,c in enumerate(cs):
  b=raw(c,16384);assert c.name==f'{i:05d}' and len(b)==m['chunks'][i]['bytes'] and H(b)==m['chunks'][i]['sha256'];parts.append(b)
 wire=b''.join(parts);assert len(wire)==m['bundleBytes'] and H(wire)==m['bundleSha256'];v=json.loads(wire);assert C(v)==wire
 package=base64.b64decode(v['packageBase64'],validate=True);proofraw=base64.b64decode(v['proofBase64'],validate=True);custodyraw=base64.b64decode(v['custodyBase64'],validate=True)
 s=d/'snapshot';assert raw(s/'capture.aeris69')==package and raw(s/'proof.json')==proofraw and raw(s/'custody.json')==custodyraw
 proof=json.loads(proofraw);custody=json.loads(custodyraw);pkg=json.loads(package);assert C(proof)==proofraw and C(custody)==custodyraw and C(pkg)==package and H(C(pkg['body']))==pkg['sha256']
 assert proof['job']==m['job']==custody['job'] and proof['rootId']==m['sourceRootId']==custody['sourceRootId'] and proof['generation']==m['sourceGeneration']==custody['sourceGeneration']
 assert custody['sourceProofSha256']==H(proofraw) and proof['packageSha256']==custody['packageSha256']==H(package) and custody['manifestSha256']==H(C(proof['manifest']))
 assert proof['authorityRestorable'] is False and custody['authorityRestorable'] is False and proof['actualImages']==custody['actualImages']==0
 rid=json.loads(base64.b64decode(proof['rootIdentityBase64'],validate=True));assert H(C(rid['body']))==rid['sha256'] and rid['body']['rootId']==proof['rootId'] and rid['body']['sourceSha256']==identity['body']['sourceSha256']==proof['sourceSha256']
 head='ROOT';seq=0;frozen={};selected=None
 for control in proof['controls']:
  b=base64.b64decode(control['base64'],validate=True);assert raw(s/'proof-control'/control['name'])==b and len(b)==control['bytes'] and H(b)==control['sha256'];r=json.loads(b);seq+=1;assert C(r)==b and r['seq']==seq and r['previous']==head and control['name']==f'{seq:08d}-{H(b)}.json';head=H(b)
  if r['type']=='FREEZE':frozen[r['body']['generation']]={'hash':head,'body':r['body']}
  if r['type']=='SELECT':selected={'hash':head,'body':r['body']}
 assert selected['hash']==proof['selectionSha256'] and selected['body']['to']!=proof['generation'] and head==proof['controlHead']
 frozen=frozen[proof['generation']];assert frozen['hash']==proof['freezeSha256'] and frozen['body']['closure']==proof['closure']=='CLEAN_CLOSED' and frozen['body']['manifest']==proof['manifest'] and frozen['body']['inspection']==proof['inspection']
 assert pkg['body']['files']==proof['manifest'] and pkg['body']['authorityRestorable'] is False and pkg['body']['actualImages']==0
 for e in pkg['body']['files']:
  b=base64.b64decode(pkg['body']['data'][e['name']],validate=True);assert len(b)==e['bytes'] and H(b)==e['sha256']
 receipt=obj(d/'receipt.json');body={'format':'receiver72-receipt/1','receiverId':receiver,'transferId':d.name,'job':m['job'],'sourceRootId':m['sourceRootId'],'sourceGeneration':m['sourceGeneration'],'bundleSha256':H(wire),'packageSha256':H(package),'manifestSha256':H(C(proof['manifest'])),'proofSha256':H(proofraw),'custodySha256':H(custodyraw),'inspectionSha256':H(C(proof['inspection'])),'authorityRestored':False,'actualImages':0,'signature':'NONE_HOST_MOCK_CONSISTENCY_ONLY'}
 assert receipt['body']==body and receipt['sha256']==H(C(body))
 rows.append({'transferId':d.name,'pass':True,'receiptSha256':receipt['sha256'],'packageSha256':H(package),'chunks':len(cs)})
assert len(rows)>0
with Path(a.output).open('x') as f:json.dump({'status':'PASS','rows':rows,'scope':'Second byte/hash/control/receipt implementation; semantic replay remains frozen JS, no independent auditor or authenticated origin'},f,indent=2)
print(json.dumps({'passed':len(rows),'total':len(rows)}))
