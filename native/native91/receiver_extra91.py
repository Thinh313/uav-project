"""Adversarial receiver seams beyond byte SHA: no extraction or success publication."""
from receiver91 import *
import copy
E=R/'evidence/native91';raw=(E/'saf05-sitl-nominal.zip').read_bytes();d=strict((E/'saf05-sitl-nominal-descriptor.json').read_bytes());c=d['context'];allowed={strict(p.read_bytes())['sourceId'] for p in E.glob('build[0-9][0-9].json')};files=unzip(raw,MAX,26);results=[]
def pack(f,symlink=None,compression=zipfile.ZIP_STORED):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w',compression=compression)as z:
  for n,v in f.items():
   if n==symlink:
    info=zipfile.ZipInfo(n);info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,v)
   else:z.writestr(n,v)
 return b.getvalue()
def test(name,b,ids=allowed):
 try:verify(b,c['receiver'],c['nonce'],ids)
 except Exception as e:results.append({'case':name,'rejected':True,'reason':str(e)[:180]})
 else:raise AssertionError('ACCEPTED '+name)
test('Unknown source allowlist',raw,set());test('ZIP symlink member',pack(files,symlink='workspace.zip'))
f=copy.deepcopy(files);f['manifest.json']=b'{"format":0,"format":1}';test('Duplicate JSON manifest key',pack(f))
f=copy.deepcopy(files);f['bomb']=bytes(2*2**20);test('Inflation ratio admission',pack(f,compression=zipfile.ZIP_DEFLATED))
f=copy.deepcopy(files);f['manifest.json']=b'{"bad":NaN}';test('Nonfinite JSON',pack(f))
f=copy.deepcopy(files);m=strict(f['manifest.json']);m['files'].append(m['files'][0]);f['manifest.json']=json.dumps(m).encode();test('Duplicate manifest inventory',pack(f))
# Rehash every outer row and member: semantic oracle still rejects a false current-review link.
f=copy.deepcopy(files);m=strict(f['manifest.json']);found=False
for e in m['files']:
 if not e['name'].startswith('diagnostics/'):continue
 rows=[];previous='';changed=False
 for line in f[e['name']].splitlines():
  v=strict(line);p=strict(base64.b64decode(v['payloadBase64']))
  if p['kind']=='WORKSPACE_REVIEW_LINK'and p['data']['reference'].get('phase')=='CLOSED_SITL':p['data']['reference']['missionSha256']='0'*64;changed=True;found=True
  v['previous']=previous;v['payloadBase64']=base64.b64encode(json.dumps(p,separators=(',',':'),ensure_ascii=False).encode()).decode();body={k:v[k] for k in ['n','elapsedMs','previous','payloadBase64']};v['sha256']=sha(json.dumps(body,separators=(',',':'),ensure_ascii=False).encode());previous=v['sha256'];rows.append(json.dumps(v,separators=(',',':')))
 if changed:
  f[e['name']]=('\n'.join(rows)+'\n').encode();e.update(bytes=len(f[e['name']]),sha256=sha(f[e['name']]),head=previous)
assert found;f['manifest.json']=json.dumps(m).encode();test('Rehashed current-review mission substitution',pack(f))
r={'status':'PASS','checks':len(results),'results':results,'failureSuccessReceiptsCreated':0};(E/'receiver-extra-negative.json').open('x').write(json.dumps(r,indent=2));print(json.dumps(r))
