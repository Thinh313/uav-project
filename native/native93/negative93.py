"""Rehash false completion claims to prove the raw receiver rejects semantics, beyond ZIP/SHA."""
from package88 import *
import subprocess
results=[]
for label in ['link','restart']:
 q=strict_json((E/(label+'-qualification.json')).read_bytes());receipt=strict_json((R/q['rawReceipt']).read_bytes());source=E/'packages'/(receipt['contentId']+'.zip')
 with zipfile.ZipFile(source)as z:files={n:z.read(n)for n in z.namelist()}
 m=strict_json(files.pop('MANIFEST88.json'));r=strict_json(files['review.json']);assert not r['accepted']and r['aborted'];r.update(accepted=True,aborted=False,failure=None);r['execution'].update(complete=True,missingNavigation=[]);files['review.json']=canon(r)
 m['files']['review.json']={'bytes':len(files['review.json']),'sha256':sha(files['review.json'])};m['totalBytes']=sum(v['bytes']for v in m['files'].values());m['contentId']=sha(canon({'run':m['run'],'receiver':m['receiver'],'nonce':m['nonce'],'files':m['files']}));dest=E/('mutant-'+label+'-false-completion.zip')
 with dest.open('xb')as sink:
  with zipfile.ZipFile(sink,'w',zipfile.ZIP_DEFLATED)as z:
   for n,b in files.items():z.writestr(n,b)
   z.writestr('MANIFEST88.json',canon(m))
 integrity=inspect(dest,m['receiver'],m['nonce']);assert integrity['status']=='INTEGRITY_VERIFIED_SEMANTIC_REPLAY_REQUIRED';p=subprocess.run(['node','native/native93/receiver_semantic88.mjs',str(dest)],cwd=R,text=True,capture_output=True,timeout=30);assert p.returncode!=0,'FALSE_COMPLETION_ACCEPTED';results.append({'case':label+' rehashed false mission completion','integrityPassed':True,'semanticRejected':True,'stderr':p.stderr[-1200:],'packageSha256':filehash(dest)})
(E/'receiver-false-completion93.json').open('x').write(json.dumps({'status':'PASS','checks':len(results),'results':results,'noReceiptPublishedForMutants':True},indent=2));print('PASS',len(results),'false completions refused')
