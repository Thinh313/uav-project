from pathlib import Path
from datetime import datetime,timezone
import urllib.request,hashlib,json
root=Path(__file__).resolve().parents[1]/'research/software-package-20261013';(root/'snapshots').mkdir(parents=True,exist_ok=True)
items=[('node-crypto','https://nodejs.org/download/release/v24.14.1/docs/api/crypto.html','node-crypto.html'),('rfc8032','https://www.rfc-editor.org/rfc/rfc8032.txt','rfc8032.txt'),('tuf-spec','https://theupdateframework.github.io/specification/latest/','tuf-spec.html')];sources=[]
for origin,url,name in items:
 record={'origin_id':origin,'url':url,'snapshot':name,'fetched_at':datetime.now(timezone.utc).isoformat()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AERIS engineering primary-source capture'}),timeout=25) as r:
   raw=r.read(5*1024**2);record['http_status']=r.status
   if r.status!=200:raise ValueError('Expected HTTP200')
  (root/'snapshots'/name).write_bytes(raw);record.update(status='captured',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 except Exception as e:record.update(status='failed',error=str(e))
 sources.append(record)
(root/'sources.json').write_text(json.dumps(sources,indent=2)+'\n');assert all(s['status']=='captured' for s in sources),sources
(root/'domain.yaml').write_text('domain: software-package-20261013\nentity_label: Signed software package definitions\nschema:\n  type_field: null\n  fields: [signature_algorithm, independent_trust, version_freshness]\nrollup_field: null\nuniverse:\n  estimate: null\n  basis: Three selected primary definitions; not a standards compliance denominator\nalias_map: {}\nambiguous_clusters: []\n')
claims=[]
for field,value,span,i in [('signature_algorithm','Node crypto supports Ed25519; implementation uses null algorithm with Ed25519 keys','Ed25519',0),('independent_trust','TUF defines trusted keys and roles; PACK15 uses only a separately supplied engineering trust anchor and is not TUF-compliant','trusted keys',2),('version_freshness','TUF addresses rollback attacks; PACK15 only enforces caller minimum sequence, expiry and an independent expected digest','Rollback attacks.',2)]:
 s=sources[i];claims.append({'entity':'Signed software package definitions','field':field,'value':value,'evidence_span':span,'extraction':'normalized','tier':'A','capture':{k:s[k] for k in ['url','fetched_at','snapshot','origin_id','sha256']},'scope':'External sourced definition only; no certification or official RtR signer identity.'})
for c in claims:c['capture']['source']=c['capture']['origin_id']
(root/'claims.jsonl').write_text(''.join(json.dumps(c)+'\n' for c in claims));print(json.dumps({'captures':len(sources),'claims':len(claims)}))
