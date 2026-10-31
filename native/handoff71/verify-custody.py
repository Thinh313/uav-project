"""Read-only second implementation: saved control/custody/package/receiver byte bindings.
Semantic execution replay remains in pinned JS, not independent auditor/signature proof.
"""
import argparse,base64,hashlib,json,re,stat
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('jobs',nargs='+');p.add_argument('--output',required=True);a=p.parse_args()
H=lambda b:hashlib.sha256(b).hexdigest()
C=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def raw(p,maxsize=24*1024**2):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_nlink==1 and s.st_size<=maxsize;return p.read_bytes()
def obj(p,maxsize=1024*1024):
 b=raw(p,maxsize);v=json.loads(b);assert C(v)==b;return v
pins=json.loads(Path('evidence/journal68/runtime-snapshot-replay.json').read_text())['pins'];actual={n:H(raw(Path('native')/n)) for n in pins['files']};assert actual==pins['files'] and H(C(actual))==pins['sourceSha256']
rows=[]
for name in a.jobs:
 d=Path(name);assert d.resolve()==d.absolute();job=d.name;assert re.fullmatch(r'j-[a-f0-9]{32}',job)
 proof=obj(d/'proof.json');assert proof['format']=='handoff71-proof/1' and proof['job']==job and proof['sourceSha256']==pins['sourceSha256'] and proof['corpusSha256']==pins['corpusSha256'] and proof['authorityRestorable'] is False and proof['actualImages']==0 and proof['closure']=='CLEAN_CLOSED'
 identity=json.loads(base64.b64decode(proof['rootIdentityBase64'],validate=True));assert H(C(identity['body']))==identity['sha256'] and identity['body']['rootId']==proof['rootId'] and identity['body']['sourceSha256']==pins['sourceSha256']
 head='ROOT';seq=0;begins={};pending={};stages={};frozen={};selected=None
 for c in proof['controls']:
  b=base64.b64decode(c['base64'],validate=True);assert len(b)==c['bytes'] and H(b)==c['sha256'] and raw(d/'proof-control'/c['name'])==b;r=json.loads(b);assert C(r)==b;seq+=1;assert r['seq']==seq and r['previous']==head and c['name']==f'{seq:08d}-{H(b)}.json';op=r['op'];v=r['body']
  if r['type']=='BEGIN':
   assert op not in begins and v['sourceSha256']==pins['sourceSha256'] and v['from']==(selected['body']['to'] if selected else None) and v['parentSelectionSha256']==(selected['hash'] if selected else 'ROOT');begins[op]=r;pending[op]=r
  elif r['type']=='FREEZE':assert op in pending and v['generation']==begins[op]['body']['from'];frozen[v['generation']]={'body':v,'hash':H(b)}
  elif r['type']=='STAGE':assert op in pending and v['generation']==begins[op]['body']['newGeneration'];stages[op]={'body':v,'hash':H(b)}
  elif r['type']=='SELECT':
   assert op in pending and v['stageSha256']==stages[op]['hash'] and v['to']==begins[op]['body']['newGeneration'] and v['parentSelectionSha256']==(selected['hash'] if selected else 'ROOT');assert v['from'] is None or v['from'] in frozen;pending.pop(op)
   for old in v['supersedes']:pending.pop(old)
   selected={**r,'hash':H(b)}
  else:raise AssertionError('UNKNOWN_CONTROL')
  head=H(b)
 assert not pending and selected and selected['hash']==proof['selectionSha256'] and head==proof['controlHead'] and selected['body']['to']!=proof['generation']
 f=frozen[proof['generation']];assert f['hash']==proof['freezeSha256'] and f['body']['manifest']==proof['manifest'] and f['body']['inspection']==proof['inspection'] and f['body']['closure']=='CLEAN_CLOSED'
 package=raw(d/'capture.aeris69');v=json.loads(package);assert C(v)==package and H(C(v['body']))==v['sha256'] and H(package)==proof['packageSha256'] and v['body']['files']==proof['manifest'];files={}
 for entry in v['body']['files']:
  n=entry['name'];assert n in ['store.json','catalog.wal'] or re.fullmatch(r'run-[a-f0-9]{32}\.wal',n);b=base64.b64decode(v['body']['data'][n],validate=True);assert len(b)==entry['bytes'] and H(b)==entry['sha256'];files[n]=b
 custody=obj(d/'custody.json');assert custody['job']==job and custody['sourceGeneration']==proof['generation'] and custody['sourceRootId']==proof['rootId'] and custody['sourceProofSha256']==H(C(proof)) and custody['packageSha256']==H(package) and custody['manifestSha256']==H(C(proof['manifest'])) and custody['authorityRestorable'] is False and custody['actualImages']==0
 bridge=d.parent.parent;rootIdentity=obj(bridge/'identity.json');assert H(C(rootIdentity['body']))==rootIdentity['sha256'];receiver=Path(rootIdentity['body']['receiverRoot']);absolute=receiver.absolute();assert str(absolute).startswith(str(Path('.local/archive69/handoff71-').absolute())) or str(absolute).startswith(str(Path('evidence/archive69/handoff71').absolute())+'/');arcIdentity=obj(receiver/'identity.json');assert arcIdentity['body']['id']==custody['archiveWorkspaceId']==rootIdentity['body']['receiverWorkspaceId']
 head='ROOT';seq=0;phase={}
 for p in sorted((bridge/'control').iterdir()):
  b=raw(p,32768);r=json.loads(b);assert C(r)==b;seq+=1;assert r['seq']==seq and r['previous']==head and p.name==f'{seq:08d}-{H(b)}.json';head=H(b)
  if r['job']==job:phase[r['phase']]=r['body']
 assert list(phase)==['START','CAPTURED','ADOPTED','EXPORTED','IMPORTED','VERIFIED'];assert phase['START']['generation']==proof['generation'] and phase['START']['proofSha256']==H(C(proof)) and phase['EXPORTED']['custodySha256']==H(C(custody)) and phase['EXPORTED']['exportId']==custody['exportId']
 g=phase['ADOPTED']['archiveGeneration'];hot=obj(receiver/'hot'/g/'identity.json');assert H(C(hot))==phase['ADOPTED']['identitySha256'] and hot['origin']['job']==job and hot['origin']['sourceProofSha256']==H(C(proof)) and hot['manifest']==proof['manifest'] and custody['archiveGeneration']==g
 assert raw(receiver/'exports'/custody['exportId']/'package.aeris69')==package
 imp=phase['IMPORTED'];receipt=obj(receiver/'receiver'/imp['importId']/'receipt.json');assert H(C(receipt))==imp['receiptSha256'] and receipt['generation']==g and receipt['exportId']==custody['exportId'] and receipt['packageSha256']==H(package) and receipt['inspection']==proof['inspection'] and receipt['authorityRestored'] is False
 for n,b in files.items():assert raw(receiver/'receiver'/imp['importId']/'data'/n)==b
 verified=phase['VERIFIED'];assert verified['importId']==imp['importId'] and verified['receiptSha256']==imp['receiptSha256'] and verified['inspectionSha256']==H(C(proof['inspection'])) and verified['authorityRestored'] is False and verified['actualImages']==0
 rows.append({'jobPath':name,'pass':True,'job':job,'sourceRootId':proof['rootId'],'sourceGeneration':proof['generation'],'packageSha256':H(package),'importId':imp['importId'],'receiverReceiptSha256':imp['receiptSha256'],'authorityRestored':False,'actualImages':0})
with Path(a.output).open('x') as f:json.dump({'status':'PASS_SECOND_IMPLEMENTATION_CUSTODY_RECEIVER_BYTES','rows':rows,'scope':'Saved canonical/control/manifest/package/source binding and exact receiver files; no live-source reobservation or signed origin/authentication/independent auditor claim'},f,indent=2)
print(json.dumps({'passed':len(rows),'total':len(rows)}))
