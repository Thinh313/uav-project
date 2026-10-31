import base64,hashlib,struct,json
from pilot.betaintegrated01.control01.mavlink import Framer

def native_wire_evidence(rows):
    """Full-chain caller verified; retain intent and written boundaries, all own HB states."""
    tx={};heartbeats=[];rx=Framer();seq=None;pending=None
    for row in rows:
        payload=base64.b64decode(row['base64'],validate=True)
        if row['kind']=='TX_INTENT':
            if pending is not None:raise ValueError('NATIVE_RELEASE_OVERLAPPING_INTENT')
            pending=(payload,row['n'],row['monotonicNs'])
        if row['kind']=='TX_WRITTEN':
            if pending is None or pending[0]!=payload:raise ValueError('NATIVE_RELEASE_INTENT_WRITTEN_MISMATCH')
            tx.setdefault(hashlib.sha256(payload).hexdigest(),[]).append((pending[1],pending[2],row['n'],row['monotonicNs']));pending=None
        if row['kind']=='TX_REFUSED':
            v=json.loads(payload)
            if pending is None or type(v.get('intentRecordN'))is not int or v['intentRecordN']!=pending[1]or v.get('wireSHA256')!=hashlib.sha256(pending[0]).hexdigest()or v.get('disposition')!='PRE_SOCKET_REFUSED'or v.get('socketCallbackEntered')is not False:raise ValueError('NATIVE_REFUSED_INTENT_CONTEXT')
            pending=None
        if row['kind']=='TX_UNKNOWN':
            if pending is None:raise ValueError('NATIVE_RELEASE_UNKNOWN_WITHOUT_INTENT')
            pending=None
        if row['kind']!='RX':continue
        for f in rx.feed(payload,row['monotonicNs']):
            if f['system']!=42 or f['component']!=1:continue
            delta=None if seq is None else(f['wireSequence']-seq)&255
            if delta==0 or delta is not None and delta>=128:continue
            seq=f['wireSequence']
            if f['id']==0:
                valid_type=f['payload'][4:6]==bytes([2,3])
                heartbeats.append({'record':row['n'],'guestNs':row['monotonicNs'],'mode':struct.unpack_from('<I',f['payload'])[0],
                                   'armed':bool(f['payload'][6]&128),'validType':valid_type,
                                   'wireSHA256':hashlib.sha256(bytes.fromhex(f['wireHex'])).hexdigest()})
    if pending is not None:raise ValueError('NATIVE_RELEASE_PENDING_INTENT')
    return tx,heartbeats
