"""Second implementation: contract/binding/nonce/sequence/anchor/receipt checks.
Fixture oracle is NOT cryptographic authentication. Semantic package replay remains JS.
"""
import argparse,base64,copy,hashlib,json,stat,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('corpus');p.add_argument('--output',required=True);a=p.parse_args()
H=lambda b:hashlib.sha256(b).hexdigest()
C=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
D=lambda x:H(C(x))
def raw(p,limit=1024**2):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_nlink==1 and s.st_size<=limit;return p.read_bytes()
def obj(p,limit=1024**2):
 b=raw(p,limit);v=json.loads(b);assert C(v)==b;return v
def proof(e,o,p,role,now):
 assert set(e)=={'body','proof'} and set(e['proof'])=={'scheme','evidenceId'} and e['proof']['scheme']=='MOCK_ORACLE_73'
 b=e['body'];principal=b['sourcePrincipal'] if role=='SOURCE' else p['receiverPrincipal'];keyid=b['sourceKeyId'] if role=='SOURCE' else p['receiverKeyId']
 records={x['evidenceId']:x for x in o['records']};assert len(records)==len(o['records']);r=records[e['proof']['evidenceId']]
 assert r['bodySha256']==D(b) and r['principal']==principal and r['keyId']==keyid and r['role']==role and r['epoch']==p['trustEpoch']==o['epoch']
 k=next(k for k in o['keys'] if k['principal']==principal and k['keyId']==keyid);assert k['state']=='ACTIVE' and role in k['roles'] and k['notBeforeMs']<=now<k['notAfterMs']
def claim(m,ce,se,p,at):
 c=ce['body'];s=se['body'];assert c['format']=='auth73-challenge/1' and c['purpose']=='RECEIVER_CHALLENGE' and c['realm']==p['realm'] and c['policySha256']==D(p) and c['trustEpoch']==p['trustEpoch']
 assert c['receiverId']==m['receiverId']==p['receiverId'] and c['receiverPrincipal']==p['receiverPrincipal'] and c['receiverKeyId']==p['receiverKeyId'] and c['sourceRootId']==m['sourceRootId'] and c['manifestSha256']==D(m) and c['bundleSha256']==m['bundleSha256'] and c['transferId']==m['transferId']
 source=next(x for x in p['sources'] if x['principal']==c['sourcePrincipal'] and x['keyId']==c['sourceKeyId']);assert m['sourceRootId'] in source['roots']
 assert c['expiresAtMs']==c['issuedAtMs']+30000 and c['issuedAtMs']<=s['issuedAtMs']<=at<c['expiresAtMs'] and isinstance(s['sequence'],int) and s['sequence']>0
 expected={'format':'auth73-source/1','purpose':'ADMIT_CLOSED_PACKAGE','realm':c['realm'],'policySha256':c['policySha256'],'trustEpoch':c['trustEpoch'],'sourcePrincipal':c['sourcePrincipal'],'sourceKeyId':c['sourceKeyId'],'receiverId':c['receiverId'],'receiverPrincipal':c['receiverPrincipal'],'receiverBootId':c['receiverBootId'],'transferId':m['transferId'],'job':m['job'],'sourceRootId':m['sourceRootId'],'sourceGeneration':m['sourceGeneration'],'manifestSha256':D(m),'bundleSha256':m['bundleSha256'],'senderNonce':c['senderNonce'],'challengeId':c['challengeId'],'challengeSha256':D(c),'sequence':s['sequence'],'issuedAtMs':s['issuedAtMs'],'expiresAtMs':c['expiresAtMs']};assert s==expected
def receipt(p,ad,r):
 b=r['receiptEnvelope']['body'];m=ad['manifest'];s=ad['sourceEnvelope']['body'];r72=r['receipt72']
 expected={'format':'auth73-receipt/1','purpose':'CLOSED_PACKAGE_RECEIPT','realm':p['realm'],'policySha256':D(p),'trustEpoch':p['trustEpoch'],'sourcePrincipal':s['sourcePrincipal'],'sourceKeyId':s['sourceKeyId'],'receiverPrincipal':p['receiverPrincipal'],'receiverKeyId':p['receiverKeyId'],'receiverId':p['receiverId'],'receiverBootAtCommit':s['receiverBootId'],'transferId':m['transferId'],'job':m['job'],'sourceRootId':m['sourceRootId'],'sourceGeneration':m['sourceGeneration'],'manifestSha256':D(m),'bundleSha256':m['bundleSha256'],'senderNonce':s['senderNonce'],'sourceClaimSha256':D(ad['sourceEnvelope']),'receipt72Sha256':D(r72),'issuedAtMs':b['issuedAtMs'],'assurance':'MOCK_ONLY_NOT_AUTHENTICATED','authorityRestored':False,'actualImages':0};assert b==expected and s['issuedAtMs']<=b['issuedAtMs']<s['expiresAtMs'] and r72['sha256']==D(r72['body'])
def ledger(root,role,p,o):
 d=root/(role+'-log');identity=obj(d/'identity.json');assert identity['role']==role and identity['policySha256']==D(p)
 anchor=root/(role+'-anchor');assert obj(anchor/'identity.json')['anchorId']==identity['anchorId'];previous='ROOT';frontier=None
 for n,f in enumerate(sorted((anchor/'frontier').iterdir())):
  r=obj(f);assert r['seq']==n and r['previous']==previous and r['storeId']==identity['storeId'] and f.name==f'{n:08d}-{D(r)}.json';previous=D(r);frontier=r
 previous='ROOT';seqs={};nonces=set();claims={};intents={};receipts={};last=0;count=0
 for n,f in enumerate(sorted((d/'log').iterdir()),1):
  e=obj(f,65536);assert e['format']=='auth73-event/1' and e['seq']==n and e['previous']==previous and e['storeId']==identity['storeId'] and e['role']==role and f.name==f'{n:08d}-{D(e)}.json' and e['atMs']>=last;last=e['atMs'];previous=D(e);count=n;b=e['body'];t=e['type']
  if t=='INTENT':assert role=='sender' and b['manifest']['transferId'] not in intents;intents[b['manifest']['transferId']]=b
  elif t in ['ADMIT','CLAIM']:
   assert t==('ADMIT' if role=='receiver' else 'CLAIM');m=b['manifest'];ce=b['challengeEnvelope'];se=b['sourceEnvelope'];claim(m,ce,se,p,e['atMs']);proof(ce,o,p,'CHALLENGE',e['atMs']);proof(se,o,p,'SOURCE',e['atMs']);s=se['body'];assert s['sequence']>seqs.get(s['sourcePrincipal'],0) and s['challengeId'] not in nonces;seqs[s['sourcePrincipal']]=s['sequence'];nonces.add(s['challengeId']);claims[D(se)]=b
   if role=='sender':i=intents[m['transferId']];assert i['manifest']==m and i['senderNonce']==s['senderNonce'] and i['sourcePrincipal']==s['sourcePrincipal'] and i['sourceKeyId']==s['sourceKeyId']
  else:
   assert t==('COMMIT' if role=='receiver' else 'RECEIPT');b73=b['receiptEnvelope']['body'];ad=claims[b73['sourceClaimSha256']];receipt(p,ad,b);proof(b['receiptEnvelope'],o,p,'RECEIPT',e['atMs']);assert b['transferId'] not in receipts and b['transferId']==ad['manifest']['transferId'] and b73['issuedAtMs']<=e['atMs'];receipts[b['transferId']]=b
 assert frontier['head']==previous and frontier['seq']==count;return {'claims':claims,'receipts':receipts,'count':count,'sequences':seqs}
rows=[];bites=[];result=obj(Path(a.corpus)/'results.json');assert result['status']=='PASS_MOCK_CORPUS'
for row in result['rows']:
 root=Path(row['authDir']);p=obj(root/'policy.json');o=obj(root/'oracle-fixtures.json');assert p['mode']=='MOCK_ONLY';r=ledger(root,'receiver',p,o);s=ledger(root,'sender',p,o);assert r['receipts']==s['receipts'] and len(r['receipts'])==1
 for t,received in r['receipts'].items():
  r72=Path(row['receiverDir']);assert obj(r72/'identity.json')['body']['receiverId']==p['receiverId'];local=obj(r72/'transfers'/t/'receipt.json');assert local==received['receipt72'];m=obj(r72/'transfers'/t/'manifest.json');ad=r['claims'][received['receiptEnvelope']['body']['sourceClaimSha256']];assert ad['manifest']==m
  parts=[]
  for i,f in enumerate(sorted((r72/'transfers'/t/'chunks').iterdir())):
   b=raw(f,16384);assert f.name==f'{i:05d}' and H(b)==m['chunks'][i]['sha256'] and len(b)==m['chunks'][i]['bytes'];parts.append(b)
  wire=b''.join(parts);assert H(wire)==m['bundleSha256'] and len(wire)==m['bundleBytes'];package=raw(r72/'transfers'/t/'snapshot/capture.aeris69',24*1024**2);assert H(package)==local['body']['packageSha256'];assert json.loads(wire)['packageBase64']==base64.b64encode(package).decode()
  e=next(iter(r['claims'].values()))['sourceEnvelope'];bad=copy.deepcopy(e);bad['body']['receiverId']='r-'+'0'*32
  for variant in [bad,{'body':e['body'],'proof':{'scheme':'MOCK_ORACLE_73','evidenceId':'fixture-'+'0'*32}}]:
   refused=False
   try:proof(variant,o,p,'SOURCE',2000)
   except (AssertionError,KeyError):refused=True
   assert refused
  late=copy.deepcopy(received);late['receiptEnvelope']['body']['issuedAtMs']=ad['sourceEnvelope']['body']['expiresAtMs'];refused=False
  try:receipt(p,ad,late)
  except AssertionError:refused=True
  assert refused
  bites.append({'id':row['id'],'bodySwapRejected':True,'unknownEvidenceRejected':True,'lateReceiptRejected':True})
 rows.append({'id':row['id'],'pass':True,'receiverEvents':r['count'],'senderEvents':s['count'],'receiverId':p['receiverId'],'assurance':'MOCK_ONLY_NOT_AUTHENTICATED'})
with Path(a.output).open('x') as f:json.dump({'status':'PASS_SECOND_IMPLEMENTATION','rows':rows,'bites':bites,'scope':'Independent algorithm implementation, not independent auditor; mock evidence lookup not crypto; source signatures/TLS/true external anchor not tested'},f,indent=2)
print(json.dumps({'passed':len(rows),'total':len(rows),'negativeBites':3*len(bites)}))
