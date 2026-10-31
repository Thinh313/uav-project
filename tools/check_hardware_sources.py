#!/usr/bin/env python3
"""Read-only byte and locator integrity; no hardware measurement claim."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HARDWARE=ROOT/'hardware/herahub2'
inventory=json.loads((HARDWARE/'sources/inventory.json').read_text())
records={r['absolute_path']:r for r in inventory['files'] if r['status']=='extracted'}
for name,r in records.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==r['sha256'],name+' source changed'
    extracted=json.loads((HARDWARE/'sources'/r['extraction']).read_text())
    assert extracted['source']['sha256']==r['sha256'],name+' extraction mismatch'
profile=json.loads((HARDWARE/'profile.json').read_text())
references=0
for key,field in profile['fields'].items():
    if field['status'] in ('CONFLICT','UNKNOWN','NOT_FOUND_IN_SUPPLIED_SET'):
        assert field['claim'] is None,key+' improperly resolved'
    assert field.get('measured_value') is None,key+' improperly declared measured'
    evidence=field.get('evidence',[])+[c['evidence'] for c in field.get('candidates',[])]
    for ref in evidence:
        r=records[ref['file']];assert r['sha256']==ref['sha256']
        extracted=json.loads((HARDWARE/'sources'/r['extraction']).read_text());loc=ref['location']
        if '!' in loc:
            sheet,cell=loc.split('!');assert any(s['sheet']==sheet and any(c['cell']==cell for row in s['rows'] for c in row) for s in extracted['sheets']),loc
        elif loc.startswith('page '):
            assert any(p['page']==int(loc.removeprefix('page ')) for p in extracted['pages']),loc
        else:assert any(b['location']==loc for b in extracted['blocks']),loc
        references+=1
for r in json.loads((HARDWARE/'standards/sources.json').read_text()):
    assert hashlib.sha256((HARDWARE/'standards'/r['snapshot']).read_bytes()).hexdigest()==r['sha256']
print(json.dumps({'source_files_hashed':len(records),'profile_references_checked':references,'android_captures_hashed':3,'unresolved_fields_preserved':True,'scope':'Byte/locator integrity and status policy; no semantic or hardware certification'}))
