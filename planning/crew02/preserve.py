from pathlib import Path
import json,hashlib,datetime,sys,os
R=Path(__file__).resolve().parents[2];E=R/'evidence/crew02';files={};bases=json.loads((R/'evidence/product-milestones/protected-manifests.json').read_text());bases['evidence/product-milestones/module-fingerprints-P1-final06.json']='TO_PIN'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
# P1 manifest itself pinned at initial scan; prior manifest SHA frozen in P1 protected registry.
p1='evidence/product-milestones/module-fingerprints-P1-final06.json'
if (E/'anchor-manifests.json').exists():anchors=json.loads((E/'anchor-manifests.json').read_text());assert set(anchors)==set(bases)
else:
 bases[p1]=sha(R/p1);anchors=bases
 (E/'anchor-manifests.json').open('x').write(json.dumps(anchors,indent=2)+'\n')
bad=[]
for mf,h in anchors.items():
 p=R/mf
 if not p.is_file() or sha(p)!=h:bad.append({'path':mf,'reason':'manifestSHA'});continue
 files[mf]=h
 data=json.loads(p.read_text())
 for name,v in data['files'].items():
  expected=v if isinstance(v,str) else v['sha256'];assert name not in files or files[name]==expected,(name,'conflictingbaseline');files[name]=expected
 for name,target in data.get('symbolicLinkTargets',{}).items():
  q=R/name
  if not q.is_symlink() or os.readlink(q)!=target:bad.append({'path':name,'reason':'symlink'})
for name,expected in files.items():
 p=R/name
 if not p.is_file():bad.append({'path':name,'reason':'missing'});continue
 if sha(p)!=expected:bad.append({'path':name,'reason':'sha'})
r={'at':datetime.datetime.now().astimezone().isoformat(),'count':len(files),'failures':bad,'status':'PASS' if not bad else 'FAIL','scope':'Full protected registry through N98verify and P1 final06 including manifest anchors; current bytes only; no continuous-path claim'}
(E/('preservation-'+sys.argv[1]+'.json')).open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps(r));sys.exit(bool(bad))
