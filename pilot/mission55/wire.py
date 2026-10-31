"""Bounded read-only MAVLink MISSION_ITEM_INT decoder, no encoder or sockets."""
import struct
from semantic import ContractError,require

def x25(data,crc=0xffff):
    for value in data:
        t=value^(crc&255);t^=(t<<4)&255
        crc=((crc>>8)^(t<<8)^(t<<3)^(t>>4))&0xffff
    return crc

def decode_item(text):
    require(isinstance(text,str) and len(text)<=560,'FRAME_LIMIT')
    try:b=bytes.fromhex(text)
    except ValueError as e:raise ContractError('FRAME_HEX') from e
    require(len(b)>=8,'FRAME_SHORT')
    if b[0]==253:
        require(len(b)>=12 and b[2]==0,'V2_INCOMPAT_OR_SIGNATURE_NOT_VERIFIED')
        size=b[1];require(len(b)==12+size,'FRAME_LENGTH')
        message=b[7]|b[8]<<8|b[9]<<16;system,component=b[5:7];payload=b[10:10+size]
        checked=b[1:10+size];checksum=struct.unpack('<H',b[10+size:12+size])[0]
    elif b[0]==254:
        size=b[1];require(len(b)==8+size,'FRAME_LENGTH')
        message=b[5];system,component=b[3:5];payload=b[6:6+size]
        checked=b[1:6+size];checksum=struct.unpack('<H',b[6+size:8+size])[0]
    else:raise ContractError('FRAME_MAGIC')
    require(message==73 and 1<=size<=38,'MESSAGE_OR_PAYLOAD')
    require(x25(bytes([38]),x25(checked))==checksum,'FRAME_CRC')
    fields=struct.unpack('<ffffiifHHBBBBBB',payload.ljust(38,b'\0'))
    names=['param1','param2','param3','param4','x','y','z','seq','command','target_system','target_component','frame','current','autocontinue','mission_type']
    return {'source':[system,component],'fields':dict(zip(names,fields)),
            'crc':'PASS','authentication':'NOT_VERIFIED','message':message}

def inventory_cycles(journal):
    require(isinstance(journal.get('frames'),list) and len(journal['frames'])<=20000,'JOURNAL_LIMIT')
    cycles=[];current=[];outbound=[];out_current=[];decoded_count=0;quarantined=0;metadata_only=0
    for entry in journal['frames']:
        if entry.get('id')!=73:continue
        if entry.get('sessionId')!=journal.get('sessionId'):
            quarantined+=1;continue
        if 'hex' in entry:
            decoded=decode_item(entry['hex']);decoded_count+=1
            require(set(decoded['fields'])==set(entry['fields']) and all(decoded['fields'][k]==entry['fields'][k] for k in decoded['fields']),'HISTORICAL_DECODE_METADATA_DIFF')
            if entry.get('direction')=='out':
                require(decoded['source']==[255,190],'OUTBOUND_SOURCE')
                r=decoded['fields']
                if r['seq']==0:
                    if out_current:outbound.append(out_current)
                    out_current=[]
                require(r['seq']==len(out_current),'OUTBOUND_SEQUENCE_GAP');out_current.append(r)
                continue
            require(decoded['source']==[1,1],'FRAME_SOURCE_MISMATCH');r=decoded['fields']
        else:
            require(entry.get('direction')=='in' and [entry.get('system'),entry.get('component')]==[1,1],'DECODED_METADATA_SOURCE')
            metadata_only+=1;r=entry['fields']
        if r['seq']==0:
            if current:cycles.append(current)
            current=[]
        require(r['seq']==len(current),'READBACK_SEQUENCE_GAP')
        current.append(r)
    if current:cycles.append(current)
    if out_current:outbound.append(out_current)
    return {'cycles':cycles,'outboundCycles':outbound,'decodedRawFrames':decoded_count,'metadataOnlyReadbackFrames':metadata_only,
            'foreignSessionQuarantined':quarantined,
            'scope':'Outbound CRC-decoded raw bytes; inbound retained decoded JSON lacks raw bytes. No independent inbound CRC, whole-flight completeness or signature claim'}
