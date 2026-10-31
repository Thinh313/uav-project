"""Read-only second implementation for control/selection and frozen/seed byte anchors.
Does not replace semantic JS replay, operator authentication or an external signature.
"""
import argparse,hashlib,json,re,stat
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('roots',nargs='+');p.add_argument('--output',required=True);a=p.parse_args()
H=lambda b:hashlib.sha256(b).hexdigest()
C=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
G=lambda g:isinstance(g,str) and re.fullmatch(r'g-[a-f0-9]{32}',g)
def regular(p,maxsize=16777216):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_nlink==1 and s.st_size<=maxsize;return p.read_bytes()
def js(p):
 b=regular(p,32768);v=json.loads(b);assert C(v)==b;return v,b
pins=json.loads(Path('evidence/journal68/runtime-snapshot-replay.json').read_text())['pins'];actual={n:H(regular(Path('native')/n)) for n in pins['files']};assert actual==pins['files'] and H(C(actual))==pins['sourceSha256']
rows=[]
for name in a.roots:
 root=Path(name);assert root.resolve()==root.absolute() and not root.is_symlink();assert {p.name for p in root.iterdir()}=={'identity.json','writer.lock','control','generations'};assert regular(root/'writer.lock',0)==b''
 ident,_=js(root/'identity.json');assert H(C(ident['body']))==ident['sha256'] and ident['body']['sourceSha256']==pins['sourceSha256']
 selected=None;head='ROOT';seq=0;pending={};begins={};stages={};frozen={};selections=[]
 for file in sorted((root/'control').iterdir()):
  r,raw=js(file);assert set(r)=={'format','seq','previous','type','op','body'};seq+=1;assert r['format']=='rotate70-control/1' and r['seq']==seq and r['previous']==head and file.name==f'{seq:08d}-{H(raw)}.json';b=r['body'];op=r['op'];assert re.fullmatch(r'op-[a-f0-9]{32}',op)
  if r['type']=='BEGIN':
   assert op not in begins and b['kind'] in ['INIT','ROTATE','ROLLBACK'] and G(b['newGeneration']);assert b['sourceSha256']==pins['sourceSha256'] and b['from']==(selected['body']['to'] if selected else None) and b['parentSelectionSha256']==(selected['hash'] if selected else 'ROOT');assert all(x in pending for x in b['supersedes']);begins[op]=r;pending[op]=r
  elif r['type']=='FREEZE':
   assert op in pending and b['generation']==begins[op]['body']['from'] and b['generation'] not in frozen;frozen[b['generation']]=b
  elif r['type']=='STAGE':
   assert op in pending and b['generation']==begins[op]['body']['newGeneration'] and b['basis']==begins[op]['body']['basis'] and op not in stages;stages[op]={'body':b,'hash':H(raw)}
  elif r['type']=='SELECT':
   assert op in pending;begin=begins[op]['body'];assert b['kind']==begin['kind'] and b['from']==begin['from'] and b['to']==begin['newGeneration'] and b['basis']==begin['basis'] and b['stageSha256']==stages[op]['hash'] and b['parentSelectionSha256']==(selected['hash'] if selected else 'ROOT') and b['supersedes']==begin['supersedes'];assert b['from'] is None or b['from'] in frozen;assert b['basis'] is None or b['basis'] in frozen;pending.pop(op)
   for old in b['supersedes']:pending.pop(old)
   selected={**r,'hash':H(raw)};selections.append(selected)
  else:raise AssertionError('UNKNOWN_CONTROL_TYPE')
  head=H(raw)
 assert selected is not None and not pending
 registered={r['body']['newGeneration'] for r in begins.values()};assert {p.name for p in (root/'generations').iterdir()}<=registered
 def verify_manifest(g,manifest,prefix=False):
  d=root/'generations'/g;assert d.resolve()==d.absolute() and d.is_dir();assert regular(d/'writer.lock',0)==b'';names={p.name for p in d.iterdir() if p.name!='writer.lock'};assert all(n in ['store.json','catalog.wal'] or re.fullmatch(r'run-[a-f0-9]{32}\.wal',n) for n in names)
  for e in manifest:
   assert e['name'] in names;raw=regular(d/e['name']);b=raw[:e['bytes']] if prefix and e['name']=='catalog.wal' else raw;assert len(b)==e['bytes'] and H(b)==e['sha256']
  if not prefix:assert names=={e['name'] for e in manifest}
 for g,b in frozen.items():verify_manifest(g,b['manifest'])
 for op,stage in stages.items():
  g=stage['body']['generation']
  if g not in frozen:verify_manifest(g,stage['body']['manifest'],prefix=any(s['body']['to']==g for s in selections))
 rows.append({'path':name,'pass':True,'events':seq,'selectionSha256':selected['hash'],'selected':selected['body']['to'],'kind':selected['body']['kind'],'frozen':len(frozen),'generations':len(registered),'pending':0})
with Path(a.output).open('x') as f:json.dump({'status':'PASS_SECOND_IMPLEMENTATION_CONTROL_BYTES','rows':rows,'scope':'SHA/canonical selection bindings plus frozen/seed byte anchors and source pins; semantic replay remains JS; no independent auditor/signature/powercut claim'},f,indent=2)
print(json.dumps({'passed':len(rows),'total':len(rows)}))
