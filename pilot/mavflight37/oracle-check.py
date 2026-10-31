"""Decode JS frames with separate upstream v1/v2 Python parser; no transport."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import importlib.util
import json
import hashlib
import math
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'evidence/mavflight37'
libs = {}
for version, name in [(1, 'oracle-v1.py'), (2, 'oracle.py')]:
    spec = importlib.util.spec_from_file_location('oracle37_' + str(version), HERE / name)
    lib = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lib)
    assert not lib.MAVLINK_IGNORE_CRC
    libs[version] = lib
defs = json.loads((HERE / 'definitions.mjs').read_text().split('export const DEFINITIONS=')[1].rstrip(';\n'))

def normalized(obj, mid):
    obj.pop('mavpackettype', None)
    for f in defs[str(mid)]['fields']:
        k = f['name']
        obj.setdefault(k, [0] * f['array'] if f['array'] else 0)
        if '64' in f['type']:
            obj[k] = str(obj[k])
        if isinstance(obj[k], float) and not math.isfinite(obj[k]):
            obj[k] = None
        if isinstance(obj[k], list):
            obj[k] = [None if isinstance(x, float) and not math.isfinite(x) else x for x in obj[k]]
    return obj

results = []
inputs = ['js-vectors4.json', 'dialogue-vectors2.json']
for name in inputs:
    data = json.loads((OUT / name).read_text())
    frames = data.get('vectors', data.get('frames'))
    for i, row in enumerate(frames):
        raw = bytes.fromhex(row['rawHex'])
        version = 2 if raw[0] == 253 else 1
        rejected = False
        try:
            m = libs[version].MAVLink(None).parse_char(raw)
        except Exception:
            m = None
            rejected = True
        expected = row['expected']
        if name.startswith('js-'):
            passed = m is not None and m.get_msgId() == row['message'] and normalized(m.to_dict(), row['message']) == expected
        elif expected is None:
            passed = m is None
        else:
            passed = m is not None and m.get_msgId() == expected['id'] and normalized(m.to_dict(), expected['id']) == expected['fields']
            if m is not None:
                passed = passed and m.get_srcSystem() == expected['system'] and m.get_srcComponent() == expected['component'] and m.get_seq() == expected['sequence']
        results.append({'input': name, 'index': i, 'pass': passed, 'CRCRejected': rejected})
n = 1
while (OUT / f'oracle-check{n}.json').exists():
    n += 1
report = {'at': datetime.now(timezone.utc).isoformat(), 'status': 'PASS' if all(x['pass'] for x in results) else 'FAIL',
          'checks': len(results), 'passed': sum(x['pass'] for x in results), 'results': results,
          'inputHashes': {str((OUT / name).relative_to(ROOT)): hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in inputs},
          'oracleHashes': {str((HERE / name).relative_to(ROOT)): hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ['oracle.py', 'oracle-v1.py', 'oracle-check.py']},
          'method': 'Separate upstream parser/CRC implementation, same-agent verification', 'networkSent': False}
with (OUT / f'oracle-check{n}.json').open('x') as f:
    json.dump(report, f, indent=2)
    f.write('\n')
print(json.dumps({'status': report['status'], 'checks': report['checks'], 'passed': report['passed'], 'failures': [r for r in results if not r['pass']][:5]}))
assert report['status'] == 'PASS'
