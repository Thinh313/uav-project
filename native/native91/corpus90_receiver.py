from receiver91 import *
import tarfile
E=R/'evidence/native91';old=R/'evidence/native90';sid=strict((old/'build08.json').read_bytes())['sourceId'];traces={}
with tarfile.open(old/'diagnostics08-final.tar')as t:
 for m in t.getmembers():
  if m.isfile()and m.name.endswith('.jsonl'):
   raw=t.extractfile(m).read();first=strict(base64.b64decode(strict(raw.splitlines()[0])['payloadBase64']))
   if first['data'].get('sourceId')==sid and b'WORKSPACE_REVIEW_LINK'in base64.b64decode(strict(raw.splitlines()[-1])['payloadBase64']):traces['diagnostics/'+Path(m.name).name]=raw
# Explicitly select the original90 trace containing a review link, even if the tail is another event.
if not traces:
 with tarfile.open(old/'diagnostics08-final.tar')as t:
  for m in t.getmembers():
   if m.isfile()and m.name.endswith('.jsonl'):
    raw=t.extractfile(m).read();rows=[strict(base64.b64decode(strict(l)['payloadBase64']))for l in raw.splitlines()]
    if rows[0]['data'].get('sourceId')==sid and any(r['kind']=='WORKSPACE_REVIEW_LINK'for r in rows):traces['diagnostics/'+Path(m.name).name]=raw
assert len(traces)==1
with tarfile.open(old/'android90-08-before-restarts.tar')as t:
 wf={Path(m.name).name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()and str(Path(m.name).parent)=='workspaces/initial'and(Path(m.name).name=='HEAD'or m.name.endswith('.bin'))}
head=wf['HEAD'].decode().strip();manifest='AERISARCHIVE83\n'+head+'\nauthority=false\n'+''.join(n+' '+str(len(b))+' '+sha(b)+'\n'for n,b in sorted(wf.items()));wf['MANIFEST']=manifest.encode();out=io.BytesIO()
with zipfile.ZipFile(out,'w')as z:
 for n,b in wf.items():z.writestr(n,b)
files={'workspace.zip':out.getvalue(),**traces};entries=[]
for n,b in files.items():
 e={'name':n,'bytes':len(b),'sha256':sha(b)}
 if n!='workspace.zip':v=trace(b,Path(n).stem,{sid});e.update(extent='COMMITTED_PREFIX',head=v['head'],records=v['records'])
 entries.append(e)
c={'workspace':'initial','workspaceHead':head,'sitlHead':'ROOT','sourceMode':'mock','sourceId':sid,'receiver':'rtr-corpus','nonce':'native90-original-corpus-20261018','captureElapsedMs':0,'authorityRestorable':False};files['manifest.json']=json.dumps({'format':'aeris-diagnostic91','version':1,'sourceAuthenticated':False,'authorityRestorable':False,'actualImages':0,'context':c,'files':entries},separators=(',',':')).encode();out=io.BytesIO()
with zipfile.ZipFile(out,'w')as z:
 for n,b in files.items():z.writestr(n,b)
p=E/'native90-original-corpus.zip';p.open('xb').write(out.getvalue());r=receive(p,c['receiver'],c['nonce'],E/'native90-corpus.receipt.json',{sid});(E/'native90-corpus-provenance.json').open('x').write(json.dumps({'status':'PASS','traceCount':len(traces),'originalSource':'NATIVE90 development08','packaging':'HOST_COMPATIBILITY_FIXTURE_FROM_RETAINED_RAW_NOT_ANDROID_CROSS_APP_MIGRATION','referencesVerified':r['currentHeadReferencesVerified'],'originalArchives':{str(p.relative_to(R)):sha(p.read_bytes())for p in[old/'diagnostics08-final.tar',old/'android90-08-before-restarts.tar']}},indent=2));print(json.dumps({'status':r['status'],'referencesVerified':r['currentHeadReferencesVerified']}))
