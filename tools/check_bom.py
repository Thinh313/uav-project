#!/usr/bin/env python3
"""BOM mirror/cell provenance and context registry checks, no installed hardware claim."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BOM=ROOT/'hardware/hera/bom'
book=json.loads((BOM/'workbook.json').read_text());sha=book['sha256']
canonical_only='--canonical-only' in sys.argv
paths=[ROOT/'sot/source_canonical/0.BOM26.xlsx'] if canonical_only else [Path(book['source']),ROOT/'sot/source_canonical/0.BOM26.xlsx']
for p in paths:
 assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,'BOM source drift: '+str(p)
assert len(book['sheets'])==41
by_sheet={s['name']:{c['cell']:c for c in s['cells']} for s in book['sheets']}
items=json.loads((BOM/'items.json').read_text())['items'];assert len({i['id'] for i in items})==len(items)
for item in items:
 for key,loc in item['locators'].items():
  cell=loc.rsplit('!',1)[1]
  actual=by_sheet[item['sheet']].get(cell,{}).get('value')
  assert item[key]==actual or key=='part_number' and item[key]==str(actual).strip(),f'Item source mismatch: {loc}'
 assert item['verified_value'] is None and item['provenance_level']=='claim'
assert all(by_sheet[e['sheet']][e['cell']]['data_type']=='e' and by_sheet[e['sheet']][e['cell']]['value']==e['error'] for e in book['formula_errors'])
source=json.loads((ROOT/'sot/source_canonical/hera_context.json').read_text())
assert source['bom_sha256']==sha
for fact in source['facts']:
 if fact['status']=='BOM_LISTED' and 'locator' in fact:
  item=next(i for i in items if i['sheet']==fact['claim']['sheet'] and i['row']==fact['claim']['row'])
  assert fact['locator']==item['locators']
  for key,v in fact['claim'].items():assert item[key]==v
spec=importlib.util.spec_from_file_location('context_adapter',ROOT/'sot/adapters/hera_context.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a=m.adapt(source);reversed_source={**source,'facts':list(reversed(source['facts']))};assert a==m.adapt(reversed_source)
bad=json.loads(json.dumps(source));bad['facts'][0]['value']='installed'
try:m.adapt(bad)
except ValueError:pass
else:raise AssertionError('BOM adapter accepts exposed unverified capability')
print(json.dumps({'sheets':41,'bom_rows':len(items),'formula_errors_preserved':len(book['formula_errors']),'canonical_mirror_hash_matches':True,'original_and_mirror_match':None if canonical_only else True,'original_status':'NOT_CHECKED_IN_CANONICAL_MODE' if canonical_only else 'PASS','curated_context_facts':len(source['facts']),'adapter_order_independent':True,'unverified_value_rejected':True,'scope':'Document byte/cell provenance only; no live device certification'}))
