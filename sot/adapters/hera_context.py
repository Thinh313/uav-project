#!/usr/bin/env python3
"""Canonical internal BOM context → conservative SOT facts, deterministic and fail-loud."""
import hashlib,json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
def adapt(source):
 if source.get('version')!=1 or not source.get('owner'):raise ValueError('Canonical context lacks version/owner')
 ids=set();out=[]
 for row in source['facts']:
  if row['id'] in ids:raise ValueError('Duplicate context id')
  ids.add(row['id'])
  if row['status'] not in ['BOM_LISTED','FLAGGED','UNKNOWN','PROPOSED'] or not row.get('evidence') or 'value' in row:raise ValueError('Unverified context must not expose value')
  r={k:row[k] for k in ['id','key','status','evidence']}
  r.update(source='source_canonical/hera_context.json',scope=row['scope'],claim=row.get('claim'),verified_value=None,provenance_level='flagged' if row['status']=='FLAGGED' else 'claim')
  if 'locator' in row:r['locator']=row['locator']
  out.append(r)
 return {'facts':sorted(out,key=lambda f:f['id'])}
if __name__=='__main__':
 source=json.loads((ROOT/'source_canonical/hera_context.json').read_text())
 (ROOT/'registry/hera_context.yaml').write_text(yaml.safe_dump(adapt(source),allow_unicode=True,sort_keys=False))
 print(f'Context adapter: {len(source["facts"])} facts; all unverified values remain null')
