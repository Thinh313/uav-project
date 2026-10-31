#!/usr/bin/env python3
"""Deterministic internal-intent adapter. External research is never promoted here."""
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def adapt(source):
    if source.get('version') != 1 or not source.get('owner'):
        raise ValueError('Invalid source version/owner')
    facts, ids = [], set()
    for item in source['facts']:
        if item['id'] in ids:
            raise ValueError('Duplicate fact ID')
        ids.add(item['id'])
        if not item.get('evidence'):
            raise ValueError('Evidence/context is required')
        f = {k: item[k] for k in ['id', 'key', 'status', 'evidence']}
        f['source'] = 'source_canonical/product_truth.json'
        f['scope'] = item.get('scope', 'working proposal or unknown')
        if item['status'] == 'CONFIRMED_INTENT':
            if not item.get('value') or 'user' not in f['scope'] and 'authorized' not in f['scope']:
                raise ValueError('Confirmed value must be scoped to user intent/authorization')
            f.update(value=item['value'], provenance_level='verified_primary')
        elif item['status'] in ['PROPOSED', 'UNKNOWN']:
            if 'value' in item:
                raise ValueError('Unverified fact must not expose value')
            f.update(claim=item.get('claim'), verified_value=None, provenance_level='claim')
        else:
            raise ValueError('Unsupported status')
        facts.append(f)
    return {'facts': sorted(facts, key=lambda f: f['id'])}

if __name__ == '__main__':
    source = json.loads((ROOT/'source_canonical/product_truth.json').read_text())
    target = ROOT/'registry/product_truth.yaml'
    target.write_text(yaml.safe_dump(adapt(source),allow_unicode=True,sort_keys=False),encoding='utf-8')
    print(f'Generated {target}: {len(source["facts"])} records')
