from pathlib import Path
import sys,json,zipfile,copy,hashlib
sys.path.insert(0,str(Path(__file__).parent));from package88 import inspect,receive,canon,sha
R=Path(__file__).resolve().parents[2];E=R/'evidence/native88';Q=E/'package-fixtures02';Q.mkdir();receiver='fixture-receiver';nonce='fixture-nonce88'
base={n:b'{}'for n in ['plan.json','session.json','launch.json','flight-pins-at-start.json']};base['raw.jsonl']=b'';base['observer/raw.jsonl']=b'';base['observer/closure.json']=canon({'stopped':True,'error':None});base['closure.json']=canon({'stopped':True,'error':None});base['review.json']=canon({'run':'s'+'a'*20,'actualImages':0,'authorityRestorable':False})
def make(name,files=None,mut=lambda m:m,extra=None,duplicate=False):
 files=copy.deepcopy(base if files is None else files);desc={n:{'bytes':len(b),'sha256':sha(b)}for n,b in files.items()};m={'format':'aeris-flight-evidence88','version':1,'run':'s'+'a'*20,'receiver':receiver,'nonce':nonce,'files':desc,'totalBytes':sum(len(b)for b in files.values()),'authorityRestorable':False,'actualImages':0,'authenticated':False,'softwareSignature':False};m['contentId']=sha(canon({'run':m['run'],'receiver':receiver,'nonce':nonce,'files':desc}));mut(m);p=Q/(name+'.zip')
 with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED)as z:
  for n,b in files.items():z.writestr(n,b)
  z.writestr('MANIFEST88.json',canon(m))
  if extra:z.writestr(extra[0],extra[1])
  if duplicate:z.writestr('raw.jsonl',b'')
 return p
checks=[]
def reject(name,fn):
 try:fn()
 except Exception:checks.append({'name':name,'pass':True});return
 raise AssertionError(name)
p=make('intact-integrity-only');r=inspect(p,receiver,nonce);assert r['status']=='INTEGRITY_VERIFIED_SEMANTIC_REPLAY_REQUIRED'and not r['missionAccepted'];checks.append({'name':'byte integrity does not claim mission PASS','pass':True})
reject('wrong receiver',lambda:inspect(p,'wrong-receiver',nonce));reject('wrong nonce',lambda:inspect(p,receiver,'wrong-nonce'))
reject('missing declared file',lambda:inspect(make('missing',mut=lambda m:m['files'].update({'missing.bin':{'bytes':1,'sha256':'0'*64}})),receiver,nonce));reject('extra file',lambda:inspect(make('extra',extra=('extra.bin',b'x')),receiver,nonce));reject('duplicate entry',lambda:inspect(make('duplicate',duplicate=True),receiver,nonce));reject('traversal',lambda:inspect(make('traversal',extra=('../escape',b'x')),receiver,nonce));reject('absolute',lambda:inspect(make('absolute',extra=('/escape',b'x')),receiver,nonce));reject('authority restoration claim',lambda:inspect(make('authority',mut=lambda m:m.update(authorityRestorable=True)),receiver,nonce));reject('fake source authentication',lambda:inspect(make('auth',mut=lambda m:m.update(authenticated=True)),receiver,nonce));reject('wrong digest',lambda:inspect(make('sha',mut=lambda m:m['files']['raw.jsonl'].update(sha256='1'*64)),receiver,nonce));reject('missing required observer',lambda:inspect(make('missing-observer',files={n:b for n,b in base.items()if n!='observer/raw.jsonl'}),receiver,nonce));reject('semantic failure no published receipt',lambda:receive(p,receiver,nonce,Q/'receiver'));assert not list((Q/'receiver').glob('*.receipt.json'))and not list((Q/'receiver').glob('*.lock'));checks.append({'name':'no publish/lock from semantic rejection','pass':True});reject('inflated file bound before read',lambda:inspect(make('inflated',extra=('too-large.bin',bytes(17*2**20))),receiver,nonce))

reject('software signature claim without verifier',lambda:inspect(make('fake-signature',mut=lambda m:m.update(softwareSignature=True)),receiver,nonce))
pdup=Q/'duplicate-json-key.zip'
with zipfile.ZipFile(p)as src,zipfile.ZipFile(pdup,'w',compression=zipfile.ZIP_DEFLATED)as dst:
 for n in src.namelist():
  b=src.read(n)
  if n=='MANIFEST88.json':b=b'{"version":1,'+b[1:]
  dst.writestr(n,b)
reject('duplicate manifest JSON key',lambda:inspect(pdup,receiver,nonce))
plink=Q/'symlink.zip'
with zipfile.ZipFile(p)as src,zipfile.ZipFile(plink,'w',compression=zipfile.ZIP_DEFLATED)as dst:
 for n in src.namelist():dst.writestr(n,src.read(n))
 info=zipfile.ZipInfo('linked');info.create_system=3;info.external_attr=(0o120777<<16);dst.writestr(info,b'outside')
reject('symlink entry before import',lambda:inspect(plink,receiver,nonce))

(E/'package-qa02.json').open('x').write(json.dumps({'status':'PASS','checks':checks,'scope':'ADVERSARIAL_SYNTHETIC_FIXTURES_NOT_FLIGHT_ACCEPTANCE'},indent=2));print('PACKAGE_NEGATIVE_PASS',len(checks))
