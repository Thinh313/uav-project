"""Rehash hostile semantic traces: byte integrity alone must not give acceptance."""
from verify_trace import *
E=R/'evidence/native89';Q=E/'negative-fixtures';Q.mkdir();source=load('android89-after-process-restart01.tar');session=next(s for s,v in source.items()if any(r['data']['kind']=='VIDEO_STALE'for r in v['rows']));original=source[session];semantics(original['rows']);checks=[]
def encode(rows):
 previous='';out=[]
 for n,r in enumerate(rows,1):
  p=json.dumps(r['data'],ensure_ascii=False,separators=(',',':')).encode();b={'n':n,'elapsedMs':r['elapsedMs'],'previous':previous,'payloadBase64':base64.b64encode(p).decode()};previous=hashlib.sha256(json.dumps(b,separators=(',',':')).encode()).hexdigest();b['sha256']=previous;out.append(json.dumps(b,separators=(',',':')).encode()+b'\n')
 return b''.join(out)
def reject(name,raw):
 (Q/(name+'.jsonl')).open('xb').write(raw)
 try:semantics(decode(raw,session))
 except (AssertionError,ValueError,KeyError)as e:checks.append({'name':name,'rejected':True,'reason':type(e).__name__+':'+str(e)[:160]})
 else:raise AssertionError('FALSE_ACCEPTANCE_'+name)
reject('torn-tail',original['raw'][:-1]);v=bytearray(original['raw']);v[30]^=1;reject('raw-digest-tamper',bytes(v));reject('duplicate-record',original['raw']+original['raw'].splitlines(keepends=True)[-1])
def mutate(name,kind,fn):
 a=copy.deepcopy(original['rows']);d=next(r['data']for r in a if r['data']['kind']==kind);fn(d);reject(name,encode(a))
mutate('foreign-session','MOCK_ACQUIRED',lambda d:d.update(session='00000000-0000-0000-0000-000000000000'))
mutate('fake-physical-input','MOCK_ACQUIRED',lambda d:d['snapshot'].update(physicalInputVerified=True))
mutate('fake-camera-latency','FRAME_CALLBACK',lambda d:d['snapshot']['video'].update(cameraToDisplayLatencyMs=0))
mutate('mixed-key-clock','ANDROID_KEY_UNATTESTED',lambda d:d.update(clockDomain='ANDROID_ELAPSED_REALTIME'))
mutate('future-key-fake-zero-delay','ANDROID_KEY_UNATTESTED',lambda d:d.update(eventUptimeMs=d['callbackUptimeMs']+1,dispatchDelayMs=0))
mutate('false-art-verdict','ART_SELF_TEST',lambda d:d.update(checks=999))
mutate('false-ended-frame-count','VIDEO_ENDED',lambda d:d['snapshot']['video'].update(frameCallbacks=0))
a=copy.deepcopy(original['rows']);frames=[r['data']for r in a if r['data']['kind']=='FRAME_CALLBACK'];frames[1]['textureTimestampNs']=frames[0]['textureTimestampNs'];frames[1]['snapshot']['video']['producerTimestampNs']=frames[0]['textureTimestampNs'];reject('duplicate-producer-timestamp',encode(a))
a=copy.deepcopy(original['rows']);stale=next(i for i,r in enumerate(a)if r['data']['kind']=='VIDEO_STALE');fake=copy.deepcopy(next(r for r in a if r['data']['kind']=='FRAME_CALLBACK'));fake['elapsedMs']=a[stale]['elapsedMs']+1;fake['data']['snapshot']['video']['frameCallbacks']+=1;a.insert(stale+1,fake);reject('old-frame-after-stale',encode(a))
(E/'negative-verification.json').open('x').write(json.dumps({'status':'PASS','checks':checks,'count':len(checks),'scope':'Actual Android trace mutations, semantic variants rehashed; not source authentication'},indent=2));print('NEGATIVE_PASS',len(checks))
