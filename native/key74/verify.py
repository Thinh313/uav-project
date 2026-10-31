"""Read-only second implementation of lifecycle/anchor/scope/replay constraints.
Fixture proofs and key references are not cryptographic authentication or certificates.
"""
import argparse,copy,hashlib,json,stat
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('corpus');p.add_argument('--output',required=True);a=p.parse_args()
C=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
H=lambda b:hashlib.sha256(b).hexdigest()
D=lambda x:H(C(x))
def obj(p,limit=1024**2):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink() and s.st_size<=limit;b=p.read_bytes();v=json.loads(b);assert C(v)==b;return v
def proof(e,records,subject,key,role,epoch):
 assert set(e)=={'body','proof'} and e['proof']['scheme']=='MOCK_CA74_ORACLE';r=records[e['proof']['fixtureId']];assert r['bodySha256']==D(e['body']) and r['subject']==subject and r['keyId']==key and r['role']==role and r['epoch']==epoch
def posbody(b,scope,k):return {'format':'key74-possession/1','purpose':'SUBJECT_POSSESSION','registryId':b['registryId'],'registryBootId':b['registryBootId'],'realm':b['realm'],'authorityEpoch':b['authorityEpoch'],'principal':scope['principal'],'keyId':k['keyId'],'keyRefSha256':D(k),'scopeSha256':D(scope),'requestSha256':D(b),'issuedAtMs':b['issuedAtMs'],'expiresAtMs':b['expiresAtMs']}
def readybody(b,g,r,epoch):return {'format':'key74-ready/1','purpose':'RECEIVER_ROTATION_READY','registryId':b['registryId'],'realm':b['realm'],'authorityEpoch':b['authorityEpoch'],'securityEpoch':epoch,'receiverId':r['scope']['receiverIds'][0],'receiverPrincipal':r['scope']['principal'],'receiverKeyId':r['activeKeyId'],'targetPrincipal':g['principal'],'stageId':g['stageId'],'stageSha256':D(g),'requestSha256':D(b),'scopeSha256':g['scopeSha256'],'issuedAtMs':b['issuedAtMs'],'expiresAtMs':b['expiresAtMs']}
def counter(frontiers,nonces,direction,rid,source,sequence,nonce):
 k=direction+':'+rid+':'+source;n=k+':'+nonce;assert sequence>frontiers.get(k,0) and n not in nonces;return k,n
rows=[];bites=[];corpus=obj(Path(a.corpus)/'results.json');assert corpus['status']=='PASS_MOCK_LIFECYCLE_CORPUS'
for row in corpus['rows']:
 root=Path(row['registryDir']).parent;config=obj(root/'config.json');ca=obj(root/'ca-fixtures.json');records={r['fixtureId']:r for r in ca['records']};assert len(records)==len(ca['records']) and config['mode']=='MOCK_ONLY'
 d=Path(row['registryDir']);ident=obj(d/'identity.json');assert ident['configSha256']==D(config) and ident['format']=='key74-store/1';anchor=Path(row['anchorDir']);assert obj(anchor/'identity.json')['anchorId']==ident['anchorId']
 anchorhead='ROOT';frontier=None
 for i,f in enumerate(sorted((anchor/'frontier').iterdir())):
  v=obj(f);assert v['previous']==anchorhead and v['seq']==i and v['storeId']==ident['storeId'] and f.name==f'{i:08d}-{D(v)}.json';anchorhead=D(v);frontier=v
 subjects={};requests=set();pairs=set();keys=set();refs=set();frontiers={};nonces=set();owners={};epoch=1;previous='ROOT';last=0;first_admin=None;sample_ack=None;sample_frontier=None;seq=0
 def active(principal,key,role,rid,at):
  s=subjects[principal];k=next(k for k in s['keys'] if k['ref']['keyId']==key);assert s['status']=='ENROLLED' and s['activeKeyId']==key and k['status']=='ACTIVE' and k['ref']['notBeforeMs']<=at<k['ref']['notAfterMs'] and rid in s['scope']['receiverIds'];assert role in (['SOURCE'] if s['scope']['kind']=='SOURCE' else ['CHALLENGE','RECEIPT']);return k
 def receiver(rid,at):
  r=next(s for s in subjects.values() if s['scope']['kind']=='RECEIVER' and s['scope']['receiverIds']==[rid]);active(r['scope']['principal'],r['activeKeyId'],'RECEIPT',rid,at);return r
 for seq,f in enumerate(sorted((d/'log').iterdir()),1):
  e=obj(f,65536);assert e['seq']==seq and e['previous']==previous and e['storeId']==ident['storeId'] and e['format']=='key74-event/1' and f.name==f'{seq:08d}-{D(e)}.json' and e['atMs']>=last;previous=D(e);last=e['atMs'];at=e['atMs']
  if e['type']=='CONTROL':
   b=e['body']['adminEnvelope']['body'];payload=b['payload'];pos=e['body']['possessionEnvelope'];acks=e['body']['readyEnvelopes'];proof(e['body']['adminEnvelope'],records,config['adminId'],config['authorityKeyId'],'ADMIN',config['authorityEpoch']);assert b['format']=='key74-admin/1' and b['realm']==config['realm'] and b['registryId']==ident['registryId'] and b['configSha256']==D(config) and b['authorityId']==config['authorityId'] and b['authorityKeyId']==config['authorityKeyId'] and b['authorityEpoch']==config['authorityEpoch'] and b['expectedRevision']==seq-1 and b['requestId'] not in requests and b['issuedAtMs']<=at<b['expiresAtMs']==b['issuedAtMs']+30000;requests.add(b['requestId']);first_admin=first_admin or copy.deepcopy(e['body']['adminEnvelope']);op=b['operation']
   if op=='ENROLL':
    scope=payload['scope'];k=payload['keyRef'];q=payload['pairing'];principal=scope['principal'];assert principal not in subjects and scope['kind'] in ['SOURCE','RECEIVER'] and set(scope['roots'])<=set(config['allowedRoots']) and set(scope['receiverIds'])<=set(config['allowedReceivers']) and scope['receiverIds'] and k['scheme']=='MOCK_KEY_REFERENCE_74' and k['keyId'] not in keys and k['fixtureRef'] not in refs and k['notBeforeMs']<=at<k['notAfterMs'];assert q['pairingId'] not in pairs and q['registryId']==ident['registryId'] and q['registryBootId']==b['registryBootId'] and q['securityEpoch']==epoch and q['scopeSha256']==D(scope) and q['keyRefSha256']==D(k) and q['issuedAtMs']<=at<q['expiresAtMs']==q['issuedAtMs']+30000
    if scope['kind']=='SOURCE':
     assert scope['roots']
     for rid in scope['receiverIds']:receiver(rid,at)
    else:assert not scope['roots'] and len(scope['receiverIds'])==1 and not any(s['scope']['kind']=='RECEIVER' and s['scope']['receiverIds']==scope['receiverIds'] for s in subjects.values())
    assert pos['body']==posbody(b,scope,k) and not acks;proof(pos,records,principal,k['keyId'],'POSSESSION',config['authorityEpoch']);subjects[principal]={'scope':scope,'status':'ENROLLED','activeKeyId':k['keyId'],'version':1,'keys':[{'ref':k,'version':1,'status':'ACTIVE'}],'stage':None};keys.add(k['keyId']);refs.add(k['fixtureRef']);pairs.add(q['pairingId']);epoch+=1
   elif op=='STAGE':
    s=subjects[payload['principal']];k=payload['keyRef'];assert s['status']=='ENROLLED' and not s['stage'] and payload['oldKeyId']==s['activeKeyId'] and payload['nextVersion']==s['version']+1 and payload['scopeSha256']==D(s['scope']) and payload['expiresAtMs']==b['issuedAtMs']+60000 and k['keyId'] not in keys and k['fixtureRef'] not in refs
    for rid in s['scope']['receiverIds']:active(s['scope']['principal'],s['activeKeyId'],'SOURCE' if s['scope']['kind']=='SOURCE' else 'RECEIPT',rid,at)
    assert pos['body']==posbody(b,s['scope'],k) and not acks;proof(pos,records,s['scope']['principal'],k['keyId'],'POSSESSION',config['authorityEpoch']);s['keys'].append({'ref':k,'version':payload['nextVersion'],'status':'STAGED'});s['stage']={**payload,'requestSha256':D(b)};keys.add(k['keyId']);refs.add(k['fixtureRef'])
   elif op=='ACTIVATE':
    s=subjects[payload['principal']];g=s['stage'];assert s['status']=='ENROLLED' and g and g['stageId']==payload['stageId'] and D(g)==payload['stageSha256'] and at<g['expiresAtMs'] and pos is None and len(acks)==len(s['scope']['receiverIds']);k=next(k for k in s['keys'] if k['ref']['keyId']==g['keyRef']['keyId']);assert k['status']=='STAGED' and k['ref']['notBeforeMs']<=at<k['ref']['notAfterMs']
    for rid,ack in zip(s['scope']['receiverIds'],acks):
     r=receiver(rid,at);expected=readybody(b,g,r,epoch);assert ack['body']==expected;proof(ack,records,r['scope']['principal'],r['activeKeyId'],'RECEIVER_READY',config['authorityEpoch']);sample_ack=(ack,expected)
    next(k for k in s['keys'] if k['ref']['keyId']==s['activeKeyId'])['status']='RETIRED';k['status']='ACTIVE';s['activeKeyId']=k['ref']['keyId'];s['version']=k['version'];s['stage']=None;epoch+=1
   elif op=='REVOKE_KEY':
    s=subjects[payload['principal']];k=next(k for k in s['keys'] if k['ref']['keyId']==payload['keyId']);assert s['status']=='ENROLLED' and k['status']!='REVOKED' and pos is None and not acks;k['status']='REVOKED'
    if s['activeKeyId']==payload['keyId']:s['activeKeyId']=None;s['stage']=None
    epoch+=1
   else:raise AssertionError('Unexpected corpus operation')
  else:
   assert e['type']=='FRONTIER';body=e['body'];direction=body['direction'];p=body['policy'];ad=body['admission'];claim=ad['sourceEnvelope']['body'];challenge=ad['challengeEnvelope']['body'];m=ad['manifest'];r=receiver(p['receiverId'],at);assert p['trustEpoch']==epoch and p['realm']==config['realm'] and p['receiverPrincipal']==r['scope']['principal'] and p['receiverKeyId']==r['activeKeyId']
   for source in p['sources']:
    s=subjects[source['principal']];assert s['scope']['roots']==source['roots'];active(source['principal'],source['keyId'],'SOURCE',p['receiverId'],at)
   assert claim['policySha256']==D(p) and claim['trustEpoch']==epoch and claim['receiverId']==p['receiverId']==m['receiverId'] and claim['manifestSha256']==D(m)==challenge['manifestSha256'] and claim['bundleSha256']==m['bundleSha256'] and claim['challengeId']==challenge['challengeId'] and claim['challengeSha256']==D(challenge) and claim['issuedAtMs']<=at<claim['expiresAtMs'];k,n=counter(frontiers,nonces,direction,p['receiverId'],claim['sourcePrincipal'],claim['sequence'],claim['challengeId']);frontiers[k]=claim['sequence'];nonces.add(n);owner=(claim['sourcePrincipal'],D(m));ownerkey=p['receiverId']+':'+m['transferId'];assert ownerkey not in owners or owners[ownerkey]==owner;owners[ownerkey]=owner;sample_frontier=sample_frontier or (direction,p['receiverId'],claim['sourcePrincipal'],claim['sequence'],claim['challengeId'])
 assert frontier['seq']==seq and frontier['head']==previous;view=obj(root/'final-view.json');assert view['revision']==seq and view['securityEpoch']==epoch and view['subjects']==list(subjects.values()) and view['frontiers']==frontiers and view['productionAuthenticated'] is False
 assert subjects[row['rotatedPrincipal']]['keys'][-1]['status']=='REVOKED' and subjects[row['rotatedPrincipal']]['activeKeyId'] is None and subjects[row['rotatedPrincipal']]['version']==2
 refused=0
 for kind in ['admin-body','unknown-proof','wrong-receiver','sequence-reset','nonce-reuse']:
  try:
   if kind in ['admin-body','unknown-proof']:
    bad=copy.deepcopy(first_admin)
    if kind=='admin-body':bad['body']['realm']='wrong-realm'
    else:bad['proof']['fixtureId']='fixture-'+'0'*32
    proof(bad,records,config['adminId'],config['authorityKeyId'],'ADMIN',config['authorityEpoch'])
   elif kind=='wrong-receiver':bad=copy.deepcopy(sample_ack[0]['body']);bad['receiverId']='r-'+'0'*32;assert bad==sample_ack[1]
   else:
    direction,rid,principal,sequence,nonce=sample_frontier;counter(frontiers,nonces,direction,rid,principal,sequence if kind=='sequence-reset' else 100,nonce)
  except (AssertionError,KeyError,StopIteration):refused+=1
 assert refused==5;bites.append({'id':row['id'],'rejected':refused,'total':5});rows.append({'id':row['id'],'pass':True,'registryEvents':seq,'securityEpoch':epoch,'terminalRevokedKey':row['revokedKeyId'],'historicalGenerations':len(row['generations']),'productionAuthenticated':False})
with Path(a.output).open('x') as f:json.dump({'status':'PASS_SECOND_IMPLEMENTATION_LIFECYCLE','rows':rows,'bites':bites,'scope':'Mock CA lookup/anchor/lifecycle/receiver/replay checks, not cryptographic authentication or independent auditor'},f,indent=2)
print(json.dumps({'passed':len(rows),'total':len(rows),'negativeBites':sum(b['rejected'] for b in bites)}))
