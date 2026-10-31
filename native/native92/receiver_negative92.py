from receiver91 import *
import copy,warnings
E=R/'evidence/native92';raw=(E/'saf92-final07.zip').read_bytes();desc=strict(unzip(raw,MAX,26)['manifest.json']);receiver=desc['context']['receiver'];nonce=desc['context']['nonce'];allowed={strict(p.read_bytes())['sourceId']for p in E.glob('build[0-9][0-9].json')};files=unzip(raw,MAX,26);results=[]
def pack(f,duplicate=False):
 out=io.BytesIO()
 with warnings.catch_warnings():
  warnings.simplefilter('ignore')
  with zipfile.ZipFile(out,'w',zipfile.ZIP_STORED)as z:
   for n,b in f.items():z.writestr(n,b)
   if duplicate:z.writestr('manifest.json',f['manifest.json'])
 return out.getvalue()
def test(name,body,who=receiver,challenge=nonce):
 try:verify(body,who,challenge,allowed)
 except Exception as e:results.append({'case':name,'rejected':True,'reason':str(e)[:160]})
 else:raise AssertionError('ACCEPTED '+name)
def changed(name,edit,update=False):
 f=copy.deepcopy(files);edit(f)
 if update:
  m=strict(f['manifest.json'])
  for entry in m['files']:
   if entry['name']in f:entry.update(bytes=len(f[entry['name']]),sha256=sha(f[entry['name']]))
  f['manifest.json']=json.dumps(m,separators=(',',':')).encode()
 test(name,pack(f))
test('wrong receiver',raw,'other-receiver');test('wrong nonce',raw,receiver,'wrong-nonce-value')
changed('missing workspace',lambda f:f.pop('workspace.zip'));changed('extra path',lambda f:f.update(extra=b'0'));changed('traversal',lambda f:f.update({'../escape':b'0'}));test('duplicate ZIP member',pack(files,True));changed('changed workspace',lambda f:f.update({'workspace.zip':f['workspace.zip']+b'x'}))
trace_name=next(n for n in files if n.startswith('diagnostics/'))
changed('torn trace with recomputed member SHA',lambda f:f.update({trace_name:f[trace_name][:-1]}),True)
changed('broken chain with recomputed member SHA',lambda f:f.update({trace_name:f[trace_name].replace(b'"sha256":"',b'"sha256":"0',1)}),True)
def scope(f):
 m=strict(f['manifest.json']);m['authorityRestorable']=True;f['manifest.json']=json.dumps(m).encode()
changed('authority restoration claim',scope)
def extent(f):
 m=strict(f['manifest.json']);next(e for e in m['files']if e['name']==trace_name)['extent']='COMPLETE_MISSION';f['manifest.json']=json.dumps(m).encode()
changed('prefix promoted to mission completion',extent)
def semantic(f):
 rows=[];previous=''
 for line in f[trace_name].splitlines():
  v=strict(line);p=strict(base64.b64decode(v['payloadBase64']))
  if p['kind']=='SESSION':p['data']['authorityRestorable']=True
  v['previous']=previous;v['payloadBase64']=base64.b64encode(json.dumps(p,separators=(',',':')).encode()).decode();body={k:v[k]for k in ['n','elapsedMs','previous','payloadBase64']};v['sha256']=sha(json.dumps(body,separators=(',',':')).encode());previous=v['sha256'];rows.append(json.dumps(v,separators=(',',':')))
 f[trace_name]=('\n'.join(rows)+'\n').encode();m=strict(f['manifest.json']);next(e for e in m['files']if e['name']==trace_name).update(head=previous);f['manifest.json']=json.dumps(m).encode()
changed('rehashed false authority',semantic,True)
try:receive(E/'saf92-final07.zip',receiver,nonce,E/'replay-other.receipt.json',allowed)
except FileExistsError:results.append({'case':'replay same nonce to another receipt','rejected':True,'reason':'EXCLUSIVE_NONCE_MARKER'})
else:raise AssertionError('REPLAY_ACCEPTED')
assert not(E/'replay-other.receipt.json').exists();r={'status':'PASS','checks':len(results),'results':results,'noFailureSuccessReceipt':True,'scope':'INDEPENDENT_RECEIVER_NEGATIVE_CORPUS'};(E/'receiver-negative.json').open('x').write(json.dumps(r,indent=2));print(json.dumps(r))
