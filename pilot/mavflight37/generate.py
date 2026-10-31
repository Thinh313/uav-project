"""Pinned XML definitions plus an upstream, stdlib-only Python serializer oracle."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import re
import xml.etree.ElementTree as E
import importlib.util
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'evidence/mavflight37'
IDS = {0, 1, 20, 22, 24, 33, 43, 44, 47, 51, 65, 73, 77, 147, 162, 193, 242, 245}
SIZE = {'char': 1, 'uint8_t': 1, 'int8_t': 1, 'uint16_t': 2, 'int16_t': 2,
        'uint32_t': 4, 'int32_t': 4, 'uint64_t': 8, 'int64_t': 8, 'float': 4, 'double': 8}

def crc(data):
    c = 65535
    for b in data:
        t = b ^ (c & 255)
        t ^= (t << 4) & 255
        c = ((c >> 8) ^ (t << 8) ^ (t << 3) ^ (t >> 4)) & 65535
    return c

assert not (HERE / 'definitions.mjs').exists(), 'Do not overwrite generation evidence'
sys.path.insert(0, str(ROOT / 'runtime/sim32-instrument01-build/ardupilot/modules/mavlink'))
from pymavlink.generator import mavparse, mavgen_python
definitions, enums, parsed, pins = {}, {}, [], {}
for name in ['minimal', 'standard', 'common', 'ardupilotmega']:
    path = ROOT / 'reference/mavlink' / (name + '.xml')
    pins[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    x = mavparse.MAVXML(str(path), wire_protocol_version='2.0')
    x.message = [m for m in x.message if m.id in IDS]
    x.enum = []  # serializer oracle only; no duplicate/enormous dialect enums
    parsed.append(x)
    upstream = {m.id: m for m in x.message}
    tree = E.parse(path)
    for en in tree.findall('./enums/enum'):
        enums.setdefault(en.attrib['name'], {}).update(
            {e.attrib['name']: int(e.attrib['value']) for e in en.findall('entry')})
    for m in tree.findall('./messages/message'):
        mid = int(m.attrib['id'])
        if mid not in IDS:
            continue
        base, ext, extension = [], [], False
        for field in m:
            if field.tag == 'extensions':
                extension = True
            if field.tag != 'field':
                continue
            t = field.attrib['type'].replace('uint8_t_mavlink_version', 'uint8_t')
            array = int(t.split('[')[1][:-1]) if '[' in t else 0
            (ext if extension else base).append({'name': field.attrib['name'], 'type': t.split('[')[0],
                'array': array, 'extension': extension, 'unit': field.attrib.get('units'),
                'invalid': field.attrib.get('invalid'), 'multiplier': field.attrib.get('multiplier')})
        order = [f['name'] for f in [*base, *ext]]
        base.sort(key=lambda f: -SIZE[f['type']])
        raw = (m.attrib['name'] + ' ').encode()
        for field in base:
            raw += (field['type'] + ' ' + field['name'] + ' ').encode()
            if field['array']:
                raw += bytes([field['array']])
        c = crc(raw)
        offset = 0
        for f in [*base, *ext]:
            f['offset'] = offset
            offset += SIZE[f['type']] * (f['array'] or 1)
        minimum = sum(SIZE[f['type']] * (f['array'] or 1) for f in base)
        d = {'name': m.attrib['name'], 'crc': (c & 255) ^ (c >> 8), 'min': minimum,
             'max': offset, 'fields': [*base, *ext], 'xmlOrder': order}
        u = upstream[mid]
        assert (u.crc_extra, u.wire_min_length, u.wire_length) == (d['crc'], minimum, offset)
        assert u.ordered_fieldnames == [f['name'] for f in d['fields']]
        definitions[mid] = d
assert set(definitions) == IDS
with (HERE / 'definitions.mjs').open('x') as f:
    f.write('// Derived from pinned official XML; see schema-generation.json.\nexport const DEFINITIONS=' +
            json.dumps(definitions, indent=2) + ';\n')
selected = {k: enums[k] for k in ['MAV_FRAME', 'MAV_MISSION_TYPE', 'MAV_MISSION_RESULT',
            'MAV_PARAM_TYPE', 'EKF_STATUS_FLAGS', 'MAV_SYS_STATUS_SENSOR', 'MAV_LANDED_STATE', 'GPS_FIX_TYPE']}
selected['FENCE_COMMANDS'] = {k: v for k, v in enums['MAV_CMD'].items() if k.startswith('MAV_CMD_NAV_FENCE_')}
with (HERE / 'enums.json').open('x') as f:
    json.dump(selected, f, indent=2)
    f.write('\n')
mavgen_python.generate(str(HERE / 'oracle.py'), parsed)
for name in ['mavparse', 'mavgen_python', 'mavtemplate', 'mavcrc']:
    p = ROOT / 'runtime/sim32-instrument01-build/ardupilot/modules/mavlink/pymavlink/generator' / (name + '.py')
    pins[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
with (OUT / 'schema-generation.json').open('x') as f:
    json.dump({'at': datetime.now(timezone.utc).isoformat(), 'messageCount': len(definitions),
        'messages': sorted(IDS), 'pins': pins, 'upstreamLayoutCRCMatches': 18,
        'oracleKind': 'UPSTREAM_PYMAVLINK_GENERATED_PYTHON_SEPARATE_SERIALIZER',
        'oracleLicense': 'Generated Python implementation: upstream GPL-3.0-or-later, test-only',
        'definitionLicense': 'MAVLink XML: reference/mavlink/COPYING',
        'builds': 0, 'installs': 0, 'runtimeLaunches': 0}, f, indent=2)
    f.write('\n')
print('18 XML layouts and CRCs match upstream parser; oracle generated without install/build')
