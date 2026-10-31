from pathlib import Path
from datetime import datetime,timezone
import urllib.request,hashlib,json
root=Path(__file__).resolve().parents[1]/'research/software-trust-20261013';(root/'snapshots').mkdir(parents=True,exist_ok=True)
url='https://theupdateframework.github.io/specification/latest/'
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AERIS engineering primary-source capture'}),timeout=25) as r:
 assert r.status==200;raw=r.read(5*1024**2)
(root/'snapshots/tuf-spec.html').write_bytes(raw)
s={'origin_id':'tuf-spec','source':'tuf-spec','url':url,'snapshot':'tuf-spec.html','fetched_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'status':'captured','http_status':200}
(root/'sources.json').write_text(json.dumps([s],indent=2)+'\n')
definitions=[('rotation_quorum','TUF root rotation requires unique signature thresholds of the old and new root keys','When replacing root keys'),('consecutive_version','TUF requires a consecutive root version and checks rollback','incremented by one'),('durable_root','TUF requires trusted root metadata to be persisted to non-volatile storage','non-volatile storage'),('bootstrap_boundary','TUF does not establish initial bootstrap security for arbitrary manual installation','bootstrap security')]
(root/'domain.yaml').write_text('domain: software-trust-20261013\nentity_label: Software trust definitions\nschema:\n  type_field: null\n  fields: [rotation_quorum, consecutive_version, durable_root, bootstrap_boundary]\nrollup_field: null\nuniverse:\n  estimate: null\n  basis: Four selected primary definitions; not a compliance denominator\nalias_map: {}\nambiguous_clusters: []\n')
claims=[{'entity':'Software trust definitions','field':f,'value':v,'evidence_span':span,'extraction':'normalized','tier':'A','capture':{k:s[k] for k in ['source','origin_id','url','snapshot','fetched_at','sha256']},'scope':'External sourced definitions only. TRUST16 is a custom bounded local protocol, not TUF conformance or official RtR key authority.'} for f,v,span in definitions]
(root/'claims.jsonl').write_text(''.join(json.dumps(c)+'\n' for c in claims));print(json.dumps({'captures':1,'claims':4,'sha256':s['sha256']}))
