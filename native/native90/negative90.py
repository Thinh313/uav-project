from verify_trace import *
traces=load('diagnostics08-final.tar');candidate=next(v for v in traces.values()if v['rows'][0]['data'].get('sourceId')==strict((E/'build08.json').read_bytes())['sourceId']and any(r['kind']=='VIDEO_STALE'for r in v['rows']));base=candidate['rows'];results=[]
def encode(rows):
 previous='';lines=[]
 for n,r in enumerate(rows,1):
  payload={k:r[k]for k in ['session','kind','data']};body={'n':n,'elapsedMs':r['elapsedMs'],'previous':previous,'payloadBase64':base64.b64encode(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()).decode()};previous=hashlib.sha256(json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();body['sha256']=previous;lines.append(json.dumps(body,ensure_ascii=False,separators=(',',':')))
 return ('\n'.join(lines)+'\n').encode()
def one(rows,kind):return next(r for r in rows if r['kind']==kind)
def mutate(name,fn):
 rows=copy.deepcopy(base);fn(rows);raw=encode(rows)
 try:semantics(decode(raw,rows[0]['session']))
 except (AssertionError,ValueError,KeyError)as e:results.append({'case':name,'rejected':True,'reason':str(e),'hashChainRecomputed':True})
 else:raise AssertionError('MUTANT_ACCEPTED '+name)
mutate('foreign session',lambda rows:one(rows,'FRAME_CALLBACK').update(session='0'*36))
mutate('unknown source fingerprint',lambda rows:rows[0]['data'].update(sourceId='f'*64))
mutate('fake physical mapping',lambda rows:one(rows,'MOCK_ACQUIRED')['data']['snapshot']['input'].update(physicalMappingVerified=True))
mutate('fake camera latency',lambda rows:one(rows,'FRAME_CALLBACK')['data']['snapshot']['video'].update(cameraToDisplayLatencyMs=0))
mutate('fake camera age',lambda rows:one(rows,'FRAME_CALLBACK')['data']['snapshot']['video'].update(cameraAgeMs=0))
mutate('fake display scanout',lambda rows:one(rows,'FRAME_CALLBACK')['data']['snapshot']['video'].update(displayScanoutMeasured=True))
mutate('wrong generation',lambda rows:one(rows,'FRAME_CALLBACK')['data'].update(generation=999))
mutate('frame count inflation',lambda rows:one(rows,'FRAME_CALLBACK')['data']['snapshot']['video'].update(frameCallbacks=999))
def duplicate(rows):
 frames=[r for r in rows if r['kind']=='FRAME_CALLBACK'];frames[1]['data']['mediaTimeNs']=frames[0]['data']['mediaTimeNs']
mutate('media timeline replay',duplicate)
mutate('mixed key clock',lambda rows:one(rows,'ANDROID_KEY_UNATTESTED')['data'].update(clockDomain='ELAPSED_REALTIME'))
mutate('future key false zero',lambda rows:one(rows,'ANDROID_KEY_UNATTESTED')['data'].update(eventUptimeMs=10**14,dispatchDelayMs=0))
mutate('stale marked live',lambda rows:one(rows,'VIDEO_STALE')['data']['video'].update(state='RENDER_CALLBACK_OBSERVED'))
raw=candidate['raw']
for name,changed in [('torn tail',raw[:-1]),('broken hash',raw.replace(b'"sha256":"',b'"sha256":"0',1))]:
 try:decode(changed,base[0]['session'])
 except (AssertionError,ValueError,KeyError)as e:results.append({'case':name,'rejected':True,'reason':str(e),'hashChainRecomputed':False})
 else:raise AssertionError('MUTANT_ACCEPTED '+name)
r={'status':'PASS','rejected':len(results),'cases':results,'scope':'HOST_RECEIVER_NEGATIVE_CORPUS_NO_FLIGHT_OR_EXTERNAL_SOURCE_AUTHENTICATION'};(E/'negative-verification.json').open('x').write(json.dumps(r,indent=2));print(json.dumps(r))
