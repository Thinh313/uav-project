#!/usr/bin/env python3
"""One-time explicit117module/9JS source-only isolation. Never freeze or launch."""
from pathlib import Path
import hashlib,json,os,re
R=Path(__file__).resolve().parents[3];N=R/'planning/navfix13';O=R/'planning/vidlife12';B=R/'evidence/vidlife12/candidates/afe0878d1b98751f66c657c8eed6653d28d59778c46de012b2a16e8a8ef43395'
H=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((B/'candidate.json').read_bytes());assert len(m['sourceSHA256'])==117
assert not(N/'isolation-before-patches.json').exists(),'ONE_TIME_ISOLATION_NO_OVERWRITE'
rows=[]
for rel,h in m['sourceSHA256'].items():
 src=B/'source'/rel;data=src.read_bytes();assert H(data)==h;dst=N/'runtime/source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();dst.write_bytes(data);assert dst.stat().st_ino!=src.stat().st_ino
 rows.append({'original':str(src.relative_to(R)),'selected':str(dst.relative_to(R)),'sha256':h,'independentInode':True})
selected=['product/main-session-codec09c.mjs','product/beta-client-codec09.mjs','product/media-panel.mjs','product/media-server-codec09.mjs','product/server-codec09c.mjs','runtime/root-wire-media09c.mjs','runtime/scene-feed.mjs','runtime/product-companion-codec09.mjs','runtime/verified-loader.mjs'];mapping={str((O/x).relative_to(R)):str((N/x).relative_to(R))for x in selected}
pattern=re.compile(r"((?:\bfrom\s*|\bimport\s*\(\s*|\bimport\s*)['\"])(\.[^'\"]+)(['\"])")
for rel in selected:
 src=O/rel;dst=N/rel;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();text=src.read_text()
 def remap(a):
  old=(src.parent/a[2]).resolve();logical=str(old.relative_to(R));target=R/mapping.get(logical,logical);spec=os.path.relpath(target,dst.parent);return a[1]+(spec if spec.startswith('.')else'./'+spec)+a[3]
 text=pattern.sub(remap,text)
 # Exact pathname literals for selected product reads; readonly predecessor deps stay.
 for a,b in mapping.items():text=text.replace(a,b)
 dst.write_text(text);rows.append({'original':str(src.relative_to(R)),'selected':str(dst.relative_to(R)),'originalSHA256':H(src.read_bytes()),'selectedSHA256':H(dst.read_bytes()),'independentInode':dst.stat().st_ino!=src.stat().st_ino})
for rel in ['root-owner-vidlife12-r02.py','passive-vidlife12.py','preview-admission.py','prepare-source-gate-r02.py']:
 src=O/'runtime'/rel;name=rel.replace('root-owner-vidlife12-r02','root-owner-navfix13').replace('passive-vidlife12','passive-navfix13').replace('prepare-source-gate-r02','prepare-source-gate');dst=N/'runtime'/name;assert not dst.exists();s=src.read_text().replace('planning/vidlife12','planning/navfix13').replace('evidence/vidlife12','evidence/navfix13').replace('root-owner-vidlife12-r02.py','root-owner-navfix13.py').replace('passive-vidlife12.py','passive-navfix13.py').replace('scenario-app09-r02.py','scenario-navfix13.py');dst.write_text(s)
for dst in (N/'runtime/source').rglob('*.py'):
 if dst.name=='candidate.py':continue
 text=dst.read_text().replace('planning/vidlife12','planning/navfix13').replace('evidence/vidlife12','evidence/navfix13');dst.write_text(text)
# Newcandidate keeps every oldpool and adds its own scope; oldpaths never edited.
p=N/'runtime/source/aeris_runtime/candidate.py';s=p.read_text();s=s.replace(" if root==repo/'evidence/vidlife12/candidates':return", " if root==repo/'evidence/navfix13/candidates':return(*artifact_roots(repo/'evidence/vidlife12/candidates'),root)\n if root==repo/'evidence/vidlife12/candidates':return",1)
# Extend selectedpositive reuse scopes, preservingall olderorderedpools.
s=s.replace("repo/'evidence/vidlife12/candidates')", "repo/'evidence/vidlife12/candidates',repo/'evidence/navfix13/candidates')")
s=s.replace("if root==repo/'evidence/vidlife12/candidates'else[])","if root in(repo/'evidence/vidlife12/candidates',repo/'evidence/navfix13/candidates')else[]);pool_roots+=([repo/'evidence/vidlife12/candidates/objects']if root==repo/'evidence/navfix13/candidates'else[])")
s=s.replace("root!=repo/'evidence/vidlife12/candidates'","root!=repo/'evidence/navfix13/candidates'")
s=s.replace("repository()/'evidence/vidlife12/candidates')","repository()/'evidence/vidlife12/candidates',repository()/'evidence/navfix13/candidates')")
s=s.replace(" if path.parent==repository()/'evidence/vidlife12/candidates':expected+=['evidence/hostdiag11/candidates/objects']", " if path.parent in(repository()/'evidence/vidlife12/candidates',repository()/'evidence/navfix13/candidates'):expected+=['evidence/hostdiag11/candidates/objects']\n  if path.parent==repository()/'evidence/navfix13/candidates':expected+=['evidence/vidlife12/candidates/objects']")
s=s.replace("artifact_roots(repo/'evidence/vidlife12/candidates',repo/'evidence/navfix13/candidates')","artifact_roots(repo/'evidence/vidlife12/candidates')")
p.write_text(s)
(N/'isolation-before-patches.json').write_text(json.dumps({'format':'aeris-navfix13-isolation','selectedFrozenCandidate':str(B.relative_to(R)),'copiedRuntimeFiles':117,'selectedJSFiles':9,'mapping':mapping,'receipts':rows,'actorsStarted':False,'candidateFreezePerformed':False},indent=2)+'\n')
print(json.dumps({'runtimeFiles':117,'JSFiles':9,'bytes':sum(x.stat().st_size for x in N.rglob('*')if x.is_file()),'candidateFreezePerformed':False}))
