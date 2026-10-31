#!/usr/bin/env python3
"""Explicit pre-HOLD source isolation; no runtime actors, installs or signing."""
from pathlib import Path
import hashlib,json,re,os
REPO=Path(__file__).resolve().parents[3]; NEW=REPO/'planning/vidlife12'; BASE=REPO/'evidence/hostdiag11/candidates/2bd9ba916c3db0c9907163ff7f533da857c4abb0e5a43d0d8cc0be3baaf47b87'; m=json.loads((BASE/'candidate.json').read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
old='planning/betasim-integrated01/';new='planning/vidlife12/'
selected=['product/main-session-codec09c.mjs','product/beta-client-codec09.mjs','product/media-panel.mjs','product/media-server-codec09.mjs','product/server-codec09c.mjs','runtime/root-wire-media09c.mjs','runtime/scene-feed.mjs','runtime/product-companion-codec09.mjs','runtime/verified-loader.mjs']
map12={old+n:new+n for n in selected}
assert not (NEW/'isolation-before-patches.json').exists(),'ISOLATION_ALREADY_DONE_NO_OVERWRITE'
receipts=[]
for name,digest in m['sourceSHA256'].items():
 p=BASE/'source'/name;b=p.read_bytes();assert sha(b)==digest
 out=NEW/'runtime/source'/name;out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists():assert out.read_bytes()==b
 else:out.write_bytes(b)
 receipts.append({'original':str(p.relative_to(REPO)),'selected':str(out.relative_to(REPO)),'sha256':digest,'independentInode':out.stat().st_ino!=p.stat().st_ino})
for name in selected:
 source=REPO/old/name;target=REPO/new/name;target.parent.mkdir(parents=True,exist_ok=True);s=source.read_text()
 # Rewrite literal module imports only. Browser absolute URLs remain unchanged.
 pattern=re.compile(r"((?:\bfrom\s*|\bimport\s*\(\s*|\bimport\s*)['\"])(\.[^'\"]+)(['\"])")
 def remap(a):
  spec=a[2];p=(source.parent/spec).resolve();rel=str(p.relative_to(REPO));dest=REPO/map12.get(rel,rel);r=os.path.relpath(dest,target.parent);return a[1]+(r if r.startswith('.')else'./'+r)+a[3]
 s=pattern.sub(remap,s)
 if name=='product/server-codec09c.mjs':
  s=s.replace("HERE=fileURLToPath(new URL('./',import.meta.url))","HERE=path.join(REPO,'planning/betasim-integrated01/product/')")
  for f in ['beta-client-codec09.mjs','media-panel.mjs']:
   s=s.replace("path.join(HERE,'"+f+"')","path.join(REPO,'planning/vidlife12/product/"+f+"')")
   s=s.replace("'planning/betasim-integrated01/product/"+f+"'","'planning/vidlife12/product/"+f+"'")
 if name=='runtime/product-companion-codec09.mjs':
  pass
 target.write_text(s)
 receipts.append({'original':str(source.relative_to(REPO)),'selected':str(target.relative_to(REPO)),'originalSHA256':sha(source.read_bytes()),'selectedSHA256':sha(target.read_bytes()),'independentInode':target.stat().st_ino!=source.stat().st_ino})
for n in ['root-owner-hostdiag11.py','passive-hostdiag11.py','preview-admission.py','prepare-source-gate.py']:
 p=REPO/'planning/hostdiag11/runtime'/n;t=NEW/'runtime'/n.replace('hostdiag11','vidlife12');s=p.read_text().replace('planning/hostdiag11','planning/vidlife12').replace('evidence/hostdiag11','evidence/vidlife12').replace("'evidence/hostdiag11'","'evidence/vidlife12'").replace("'planning/hostdiag11'","'planning/vidlife12'")
 for a,b in map12.items():s=s.replace(a,b)
 s=s.replace('root-owner-hostdiag11.py','root-owner-vidlife12.py').replace('passive-hostdiag11.py','passive-vidlife12.py')
 t.write_text(s)
(NEW/'isolation-before-patches.json').write_text(json.dumps({'format':'aeris-vidlife12-explicit-source-isolation','frozenCandidate':str(BASE.relative_to(REPO)),'copiedRuntimeFiles':117,'jsFiles':len(selected),'mapping':map12,'receipts':receipts},indent=2)+'\n')
print(json.dumps({'runtimeFiles':117,'jsFiles':len(selected),'bytes':sum(p.stat().st_size for p in NEW.rglob('*')if p.is_file())}))
