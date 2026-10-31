"""Upstream Python packs/parses vectors independently of the JS codec; no sockets."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import importlib.util
import json
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'evidence/mavflight37'
spec = importlib.util.spec_from_file_location('flight37oracle', HERE / 'oracle.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
assert not oracle.MAVLINK_IGNORE_CRC, 'Oracle must not ignore CRC'
v1path = HERE / 'oracle-v1.py'
if not v1path.exists():
    sys.path.insert(0, str(ROOT / 'runtime/sim32-instrument01-build/ardupilot/modules/mavlink'))
    from pymavlink.generator import mavparse, mavgen_python
    parsed = []
    wanted = {0, 1, 20, 22, 24, 33, 43, 44, 47, 51, 65, 73, 77, 147, 162, 193, 242, 245}
    for name in ['minimal', 'standard', 'common', 'ardupilotmega']:
        x = mavparse.MAVXML(str(ROOT / 'reference/mavlink' / (name + '.xml')), wire_protocol_version='1.0')
        x.message = [m for m in x.message if m.id in wanted]
        x.enum = []
        parsed.append(x)
    mavgen_python.generate(str(v1path), parsed)
v1spec = importlib.util.spec_from_file_location('flight37oraclev1', v1path)
oraclev1 = importlib.util.module_from_spec(v1spec)
v1spec.loader.exec_module(oraclev1)
assert not oraclev1.MAVLINK_IGNORE_CRC
defs = json.loads((HERE / 'definitions.mjs').read_text().split('export const DEFINITIONS=')[1].rstrip(';\n'))
vectors = []
for mid, d in defs.items():
    mid = int(mid)
    for version in [1, 2]:
        for variant in range(4):
            fields = {}
            for f in d['fields']:
                if version == 1 and f['extension']:
                    continue
                typ = f['type']
                if typ == 'char':
                    x = ['', 'FENCE_ENABLE', 'ABCDEFGHIJKLMNOP', 'FS_GCS_TIMEOUT'][variant][:f['array']]
                elif typ in ['float', 'double']:
                    x = [0, 1.25, -2.5, 0.03125][variant]
                elif '64' in typ:
                    x = [0, 9007199254740993, 18446744073709551615, 65536][variant]
                elif typ.startswith('u'):
                    bits = int(typ.split('_')[0][4:])
                    x = [0, 7, 2**bits - 1, 3][variant]
                else:
                    bits = int(typ.split('_')[0][3:])
                    x = [0, -1, -(2**(bits - 1)), 2**(bits - 1) - 1][variant]
                if f['array'] and typ != 'char':
                    x = [x] * f['array']
                if mid == 0 and f['name'] == 'mavlink_version':
                    x = 3
                fields[f['name']] = x
            library = oracle if version == 2 else oraclev1
            cls = library.mavlink_map[mid]
            args = dict(fields)
            for f in d['fields']:
                if f['type'] == 'char' and f['name'] in args:
                    args[f['name']] = args[f['name']].encode('ascii')
            m = cls(**args)
            sender = library.MAVLink(None, srcSystem=1, srcComponent=1)
            sender.seq = variant + 250
            raw = m.pack(sender, force_mavlink1=version == 1)
            parsed = library.MAVLink(None).parse_char(raw)
            assert parsed and parsed.get_msgId() == mid
            normalized = parsed.to_dict()
            normalized.pop('mavpackettype')
            for f in d['fields']:
                if f['name'] not in normalized:
                    normalized[f['name']] = [0] * f['array'] if f['array'] else 0
            for f in d['fields']:
                if '64' in f['type']:
                    normalized[f['name']] = str(normalized[f['name']])
                    if f['name'] in fields:
                        fields[f['name']] = str(fields[f['name']])
            vectors.append({'id': f'{mid}-v{version}-{variant}', 'message': mid, 'fields': fields,
                'meta': {'system': 1, 'component': 1, 'seq': variant + 250, 'version': version},
                'rawHex': raw.hex(), 'decoded': normalized})
n = 1
while (OUT / f'oracle-vectors{n}.json').exists():
    n += 1
report = {'at': datetime.now(timezone.utc).isoformat(), 'origin': 'UPSTREAM_SERIALIZER_SYNTHETIC_FIELDS',
          'vectorCount': len(vectors), 'vectors': vectors, 'oracleSha256': hashlib.sha256((HERE / 'oracle.py').read_bytes()).hexdigest(),
          'oracleV1Sha256': hashlib.sha256(v1path.read_bytes()).hexdigest(),
          'schemaSha256': hashlib.sha256((HERE / 'definitions.mjs').read_bytes()).hexdigest(), 'networkSent': False}
with (OUT / f'oracle-vectors{n}.json').open('x') as f:
    json.dump(report, f, indent=2)
    f.write('\n')
print(f'Upstream oracle: {len(vectors)} vectors, MAVLink1+2, no network')
