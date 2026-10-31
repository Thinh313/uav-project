# Mutate a real Android-delivered package, recompute byte manifest; semantic receiver must still reject.
from package88 import *
Q=E/'receiver-negative88';Q.mkdir();original=E/'android88-provider-raw01.zip';checks=[]
with zipfile.ZipFile(original)as z:base={n:z.read(n)for n in z.namelist()};manifest=strict_json(base.pop('MANIFEST88.json'))
for name,mut in [('accepted-missing-takeoff',lambda r:r['execution'].update(takeoffWitness=None)),('accepted-aborted',lambda r:r.update(aborted=True)),('wrong-session',lambda r:r.update(run='s'+'0'*20))]:
 files=dict(base);r=json.loads(files['review.json']);mut(r);files['review.json']=canon(r);m=dict(manifest);m['files']={n:{'bytes':len(b),'sha256':sha(b)}for n,b in files.items()};m['totalBytes']=sum(len(b)for b in files.values());m['contentId']=sha(canon({'run':m['run'],'receiver':m['receiver'],'nonce':m['nonce'],'files':m['files']}));dest=Q/(name+'.zip')
 with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED)as z:
  for n,b in files.items():z.writestr(n,b)
  z.writestr('MANIFEST88.json',canon(m))
 store=Q/(name+'-receiver')
 try:receive(dest,m['receiver'],m['nonce'],store)
 except Exception as e:
  assert not list(store.glob('*.receipt.json'))and not list(store.glob('*.lock'));checks.append({'name':name,'rejected':True,'receiptPublished':False,'error':str(e)[-350:]})
 else:raise AssertionError('FALSE_ACCEPTANCE_'+name)
put(E/'receiver-negative88.json',{'status':'PASS','checks':checks,'scope':'REAL_PACKAGE_WITH_RECOMPUTED_BYTE_MANIFEST_FALSE_REVIEW_SEMANTICS'});print('NEGATIVE_RECEIVER_PASS',len(checks))
