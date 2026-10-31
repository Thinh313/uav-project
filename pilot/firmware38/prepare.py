"""Pinned source interpretation and one-message upstream Python oracle; no build."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import json
import hashlib
import re
import xml.etree.ElementTree as E
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'evidence/firmware38'
assert not (HERE / 'reference.mjs').exists()
pins = json.loads((OUT / 'source-pins.json').read_text())['files']
base = ROOT / 'runtime/sim32-instrument01-build/ardupilot'
version = (base / 'ArduCopter/version.h').read_text()
assert '#define THISFIRMWARE "ArduCopter V4.7.1"' in version
assert re.search(r'class AP_Enum\s*:\s*public AP_Int8', (base / 'libraries/AP_Param/AP_Param.h').read_text())
gcs = (base / 'libraries/GCS_MAVLink/GCS_Common.cpp').read_text()
params = (base / 'libraries/GCS_MAVLink/GCS_Param.cpp').read_text()
assert 'uint64_t ret = MAV_PROTOCOL_CAPABILITY_PARAM_FLOAT |' in gcs
assert 'cast_to_float(reply.p_type)' in params and 'reply.param_index = req.param_index' in params
fence = (base / 'libraries/AC_Fence/AC_Fence.cpp').read_text()
assert '0:Above sea level, 1:Above Home, 2: Above Origin, 3: Above Terrain' in fence
specs = {
 'FENCE_ENABLE':(2,'bool',0,1), 'FENCE_TYPE':(2,'bitmask',0,15), 'FENCE_ACTION':(2,'enum',0,5),
 'FENCE_OPTIONS':(4,'bitmask',0,7), 'FENCE_AUTOENABLE':(2,'enum',0,3),
 'FENCE_ALT_MIN':(9,'m',-500,10000), 'FENCE_ALT_MAX':(9,'m',-500,10000),
 'FENCE_ALT_MIN_TP':(2,'AP_LOCATION_FRAME',0,3), 'FENCE_ALT_MAX_TP':(2,'AP_LOCATION_FRAME',0,3),
 'FENCE_MARGIN':(9,'m',0,50), 'FENCE_MARGIN_XY':(9,'m',0,50),
 'FS_GCS_ENABLE':(2,'enum',0,7), 'FS_GCS_TIMEOUT':(9,'s',0,60), 'FS_THR_ENABLE':(2,'enum',0,7),
 'RC_FS_TIMEOUT':(9,'s',0,60), 'FS_OPTIONS':(6,'bitmask',0,63), 'FS_EKF_ACTION':(2,'enum',0,3),
 'BATT_MONITOR':(2,'enum',0,32), 'BATT_CAPACITY':(6,'mAh',0,200000),
 'BATT_LOW_TYPE':(2,'enum',0,1), 'BATT_OPTIONS':(6,'bitmask',0,511),
 'BATT_LOW_VOLT':(9,'V',0,100), 'BATT_CRT_VOLT':(9,'V',0,100),
 'BATT_LOW_MAH':(9,'mAh',0,200000), 'BATT_CRT_MAH':(9,'mAh',0,200000),
 'BATT_LOW_TIMER':(2,'s',0,127), 'BATT_FS_LOW_ACT':(2,'enum',0,7), 'BATT_FS_CRT_ACT':(2,'enum',0,7)}
reference = {'format':'aeris-firmware-reference38','version':1,'sourceVersion':'ArduCopter 4.7.1 source reference',
 'flightSwVersion':(4<<24)+(7<<16)+(1<<8)+255, 'sourcePins':pins,
 'sourceBundleSha256':hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
 'legacyParameterEncoding':'PINNED_AP_C_CAST_FROM_SOURCE',
 'parameters':{k:{'type':v[0],'unit':v[1],'min':v[2],'max':v[3]} for k,v in specs.items()},
 'boundsScope':'engineering mock interpretation, not all firmware metadata ranges', 'runningFirmwareAssociation':'NOT_CHECKED'}
with (HERE/'reference.mjs').open('x') as f:f.write('export const REFERENCE='+json.dumps(reference,indent=2)+';\n')
sys.path.insert(0,str(base/'modules/mavlink'))
from pymavlink.generator import mavparse,mavgen_python
parsed=mavparse.MAVXML(str(ROOT/'reference/mavlink/standard.xml'),wire_protocol_version='2.0')
parsed.message=[m for m in parsed.message if m.id==148];parsed.enum=[]
assert len(parsed.message)==1
msg=parsed.message[0]
fields=[{'name':f.name,'type':f.type,'array':f.array_length,'offset':msg.field_offsets[f.name],
         'extension':i>=msg.extensions_start if msg.extensions_start is not None else False}
        for i,f in enumerate(msg.fields)]
with (HERE/'version-schema.mjs').open('x') as f:f.write('export const VERSION_SCHEMA='+json.dumps({'id':148,'crc':msg.crc_extra,'min':msg.wire_min_length,'max':msg.wire_length,'fields':fields},indent=2)+';\n')
mavgen_python.generate(str(HERE/'oracle-version.py'),[parsed])
with (OUT/'source-interpretation.json').open('x') as f:json.dump(reference,f,indent=2);f.write('\n')
print('Pinned source version, 28 parameter specs and AUTOPILOT_VERSION oracle; no install/compiler/runtime')
