#!/usr/bin/env python3
"""Read-only capture integrity and internal adapter checks; not semantic verification."""
import hashlib, importlib.util, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sources=[]
for domain in sorted((ROOT/'research').iterdir()):
    if not (domain/'sources.json').is_file():
        continue
    records = json.loads((domain/'sources.json').read_text())
    sources.extend(records)
    for record in records:
        if record['status'] != 'captured':
            continue
        path = domain/'snapshots'/record['snapshot']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], f'Capture changed: {path}'
spec=importlib.util.spec_from_file_location('truth_adapter',ROOT/'sot/adapters/product_truth.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
source=json.loads((ROOT/'sot/source_canonical/product_truth.json').read_text())
first=adapter.adapt(source)
reversed_source={**source,'facts':list(reversed(source['facts']))}
assert first==adapter.adapt(reversed_source),'Adapter depends on input order'
bad=json.loads(json.dumps(source));bad['facts'][3]['value']='unauthorized elevation'
try:adapter.adapt(bad)
except ValueError:pass
else:raise AssertionError('Adapter accepted exposed unverified value')
bad=json.loads(json.dumps(source));bad['facts'].append(bad['facts'][0])
try:adapter.adapt(bad)
except ValueError:pass
else:raise AssertionError('Adapter accepted duplicate ID')
print(json.dumps({'capture_hashes_checked':sum(s['status']=='captured' for s in sources),'adapter_deterministic':True,'unverified_value_rejected':True,'duplicate_id_rejected':True,'scope':'byte integrity/adapter only'},ensure_ascii=False))
