"""Receive-only bounded MAVLink framing/observation, using cached dialect pins.

No encoder, send, heartbeat, request or authority API is provided.
"""
import json
from pathlib import Path
import struct

DIALECT_PATH=Path(__file__).with_name('dialect.json')
DEFINITIONS={int(k):tuple(v) for k,v in json.loads(DIALECT_PATH.read_text())['definitions'].items()}


def crc(data, extra):
    value=0xffff
    for byte in (*data,extra):
        tmp=byte^(value&0xff);tmp^=(tmp<<4)&0xff
        value=((value>>8)^(tmp<<8)^(tmp<<3)^(tmp>>4))&0xffff
    return value


class FramingError(ValueError):pass


class Framer:
    def __init__(self):
        self.pending=b'';self.pending_at=None;self.last=None;self.frames=0
        self.failed=None

    def tick(self,now_ns):
        if self.failed:raise FramingError('FRAMER_FAILED:'+self.failed)
        if type(now_ns)is not int or now_ns<0 or (self.last is not None and now_ns<self.last):
            self.failed='MONOTONIC';raise FramingError(self.failed)
        self.last=now_ns
        if self.pending_at is not None and now_ns-self.pending_at>1_500_000_000:
            self.failed='PARTIAL_STALE';raise FramingError(self.failed)

    def feed(self,raw,now_ns):
        self.tick(now_ns)
        if type(raw)is not bytes or len(raw)>4096 or len(self.pending)+len(raw)>8192:
            self.failed='BUFFER_BOUND';raise FramingError(self.failed)
        if raw and not self.pending:self.pending_at=now_ns
        self.pending+=raw;result=[]
        try:
            while self.pending:
                magic=self.pending[0]
                if magic not in (0xfe,0xfd):raise FramingError('NON_MAVLINK_BYTE')
                header=10 if magic==0xfd else 6
                if len(self.pending)<header:break
                length=self.pending[1]
                if magic==0xfd:
                    incompat=self.pending[2]
                    if incompat:raise FramingError('SIGNED_OR_UNSUPPORTED_INCOMPAT_FLAGS')
                    seq,system,component=self.pending[4:7]
                    msgid=int.from_bytes(self.pending[7:10],'little')
                else:
                    seq,system,component,msgid=self.pending[2:6]
                if msgid not in DEFINITIONS:raise FramingError('UNKNOWN_DIALECT_ID_'+str(msgid))
                minimum,maximum,extra=DEFINITIONS[msgid]
                if (magic==0xfe and length!=minimum) or (magic==0xfd and not 1<=length<=maximum):
                    raise FramingError('PAYLOAD_LENGTH')
                size=header+length+2
                if len(self.pending)<size:break
                packet=self.pending[:size]
                expected=crc(packet[1:header+length],extra)
                if int.from_bytes(packet[-2:],'little')!=expected:raise FramingError('CRC')
                payload=packet[header:header+length]+b'\0'*(maximum-length)
                result.append({'id':msgid,'system':system,'component':component,'wireSequence':seq,
                               'monotonicNs':now_ns,'wireHex':packet.hex(),'payloadLength':length,
                               'wireVersion':2 if magic==0xfd else 1,'payload':payload})
                self.pending=self.pending[size:];self.frames+=1
                self.pending_at=now_ns if self.pending else None
        except FramingError as exc:
            self.failed=str(exc);raise
        return result

    def snapshot(self):
        return {'frames':self.frames,'pendingBytes':len(self.pending),'failed':self.failed,
                'pendingPrefixHex':self.pending[:512].hex(),'applicationTXBytes':0}


def observe(frame):
    """CRC-verified protocol observations, not execution or identity authentication."""
    ident=frame['id'];p=frame['payload']
    result={k:v for k,v in frame.items() if k not in ('payload',)}
    result['expectedAPSource']=frame['system']==42 and frame['component']==1
    fields=None
    if ident==0:
        custom,typ,autopilot,base,status,version=struct.unpack_from('<IBBBBB',p)
        fields={'kind':'HEARTBEAT','customMode':custom,'armed':bool(base&128),'type':typ,
                'autopilot':autopilot,'baseMode':base,'systemStatus':status,'mavlinkVersion':version}
    elif ident==1:
        fields={'kind':'SYS_STATUS','present':struct.unpack_from('<I',p,0)[0],
                'enabled':struct.unpack_from('<I',p,4)[0],'healthy':struct.unpack_from('<I',p,8)[0],
                'voltageBatteryMilliVolt':struct.unpack_from('<H',p,14)[0],
                'currentBatteryCentiAmp':struct.unpack_from('<h',p,16)[0],
                'batteryRemainingPercent':struct.unpack_from('<b',p,30)[0]}
    elif ident==2:
        unix_us,boot_ms=struct.unpack_from('<QI',p)
        fields={'kind':'SYSTEM_TIME','unixUsec':unix_us,'bootMs':boot_ms}
    elif ident==24:
        fields={'kind':'GPS_RAW_INT','timeUsec':struct.unpack_from('<Q',p)[0],
                'latitudeE7':struct.unpack_from('<i',p,8)[0],'longitudeE7':struct.unpack_from('<i',p,12)[0],
                'altitudeAMSLmm':struct.unpack_from('<i',p,16)[0],
                'ephCenti':struct.unpack_from('<H',p,20)[0],'fixType':p[28],'satellites':p[29]}
    elif ident==30:
        boot,roll,pitch,yaw,rs,ps,ys=struct.unpack_from('<Iffffff',p)
        fields={'kind':'ATTITUDE','bootMs':boot,'rollRad':roll,'pitchRad':pitch,'yawRad':yaw,
                'rollRateRadS':rs,'pitchRateRadS':ps,'yawRateRadS':ys}
    elif ident==33:
        boot,lat,lon,alt,relative,vx,vy,vz,heading=struct.unpack_from('<IiiiihhhH',p)
        fields={'kind':'GLOBAL_POSITION_INT','bootMs':boot,'latitudeE7':lat,'longitudeE7':lon,
                'altitudeAMSLmm':alt,'relativeAltitudeMm':relative,'vxCms':vx,'vyCms':vy,'vzCms':vz,
                'headingCentiDeg':heading}
    elif ident==32:
        boot,x,y,z,vx,vy,vz=struct.unpack_from('<Iffffff',p)
        fields={'kind':'LOCAL_POSITION_NED','bootMs':boot,'northM':x,'eastM':y,'downM':z,
                'northMs':vx,'eastMs':vy,'downMs':vz}
    elif ident==65:
        fields={'kind':'RC_CHANNELS','bootMs':struct.unpack_from('<I',p)[0],
                'channels':list(struct.unpack_from('<18H',p,4)),'channelCount':p[40],'rssi':p[41]}
    elif ident==74:
        air,ground,alt,climb,heading,throttle=struct.unpack_from('<ffffhH',p)
        fields={'kind':'VFR_HUD','airspeedMs':air,'groundspeedMs':ground,'altitudeAMSLm':alt,
                'climbMs':climb,'headingDeg':heading,'throttlePercent':throttle}
    elif ident==77:
        fields={'kind':'COMMAND_ACK','command':struct.unpack_from('<H',p)[0],'result':p[2],
                'executionProven':False}
    elif ident==193:
        fields={'kind':'EKF_STATUS_REPORT','flags':struct.unpack_from('<H',p,20)[0]}
    elif ident==242:
        lat,lon,alt=struct.unpack_from('<iii',p)
        fields={'kind':'HOME_POSITION','latitudeE7':lat,'longitudeE7':lon,'altitudeAMSLmm':alt,
                'timeUsec':struct.unpack_from('<Q',p,52)[0],
                'APTimeExtensionPresent':frame['payloadLength']>52}
    elif ident==245:
        fields={'kind':'EXTENDED_SYS_STATE','vtolState':p[0],'landedState':p[1]}
    elif ident==253:
        fields={'kind':'STATUSTEXT','severity':p[0],'text':p[1:51].split(b'\0')[0].decode('utf-8','replace'),
                'id':struct.unpack_from('<H',p,51)[0],'chunkSequence':p[53]}
    result['fields']=fields
    result['authorityGranted']=False
    return result
