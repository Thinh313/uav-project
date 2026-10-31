"""Independent MANUAL_CONTROL frame oracle. No sockets/processes/device access.
Reusable for offline native-test outputs and later Root-provided exported raw.
Uses existing pinned upstream generated parser, never product encoder/decoder.
"""
from pathlib import Path
import hashlib,importlib.util,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
ORACLE=ROOT/'pilot/apstream40/oracle-v2.py'
_spec=importlib.util.spec_from_file_location('phone06_independent_upstream',ORACLE)
_m=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_m)
ORACLE_SHA256=hashlib.sha256(ORACLE.read_bytes()).hexdigest()

def decode_manual06(frame_hex):
    if type(frame_hex)is not str or not 24<=len(frame_hex)<=512 or len(frame_hex)%2:
        raise ValueError('MANUAL_FRAME_HEX_BOUND')
    try:raw=bytes.fromhex(frame_hex)
    except ValueError:raise ValueError('MANUAL_FRAME_HEX')from None
    if raw[0]!=253 or len(raw)!=raw[1]+12 or raw[2]!=0:
        raise ValueError('MANUAL_FRAME_FORMAT_OR_SIGNED_UNSUPPORTED')
    parser=_m.MAVLink(None);parser.robust_parsing=False
    messages=parser.parse_buffer(raw)
    if len(messages or[])!=1:raise ValueError('MANUAL_FRAME_COUNT')
    f=messages[0]
    if f.get_msgId()!=69 or f.get_srcSystem()!=255 or f.get_srcComponent()!=190 or f.target!=42:
        raise ValueError('MANUAL_FRAME_IDENTITY')
    if any(getattr(f,k)!=0 for k in('buttons','buttons2','enabled_extensions','s','t','aux1','aux2','aux3','aux4','aux5','aux6')):
        raise ValueError('MANUAL_UNAPPROVED_EXTENSIONS_OR_BUTTONS')
    values={k:getattr(f,k)for k in('x','y','z','r')}
    if any(type(values[k])is not int or not -1000<=values[k]<=1000 for k in('x','y','r'))or type(values['z'])is not int or not 0<=values['z']<=1000:
        raise ValueError('MANUAL_AXES_RANGE')
    return {'message':69,'sourceSystem':255,'sourceComponent':190,'target':42,**values,'sequence':f.get_seq(),'frameSha256':hashlib.sha256(raw).hexdigest(),'oracleSha256':ORACLE_SHA256}
