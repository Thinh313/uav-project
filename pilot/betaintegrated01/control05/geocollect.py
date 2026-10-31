"""Same frozen geography collector, with explicit pre-MAV startup-envelope decoding."""
from pathlib import Path
import struct
from pilot.betaintegrated01.control01.mavlink import Framer
from pilot.betaintegrated01.control01.oracles03 import events
from pilot.betaintegrated01.control04.geography import DATUM,POLICY,integer
from .bootstrap import StartupEnvelope

def collect(out,run,epoch,boot):
    """Additional CRC reconstruction, including bad/foreign/reordered observations."""
    framer=Framer();envelope=StartupEnvelope();rows=[];seq=None;last_host=-1;last_boot=None
    for kind,data in events(Path(out)/'transport-journal'):
        if data.get('_boot')!=boot:raise ValueError('FOREIGN_TRANSPORT_BOOT')
        now=data.get('_observedHostNs');integer(now,0,2**63-1,'TRANSPORT_CLOCK')
        if now<last_host:raise ValueError('TRANSPORT_CLOCK_REORDER')
        last_host=now
        if kind!='PASSIVE_RX':continue
        mav,_=envelope.feed(bytes.fromhex(data['rawHex']),data['hostNs'])
        for frame in framer.feed(mav,data['hostNs']):
            row={'run':run,'epoch':epoch,'boot':boot,'hostNs':frame['monotonicNs'],'wireSHA256':__import__('hashlib').sha256(bytes.fromhex(frame['wireHex'])).hexdigest()}
            if frame['system']!=42 or frame['component']!=1:row.update(kind='invalid',reason='FOREIGN_AP_SOURCE')
            else:
                delta=None if seq is None else(frame['wireSequence']-seq)&255
                if delta==0 or delta is not None and delta>=128:
                    row.update(kind='invalid',reason='AP_DUPLICATE_OR_REORDER')
                else:
                    seq=frame['wireSequence'];p=frame['payload'];ident=frame['id'];row['wireSequence']=seq
                    if ident==0:row.update(kind='heartbeat',mode=struct.unpack_from('<I',p)[0],armed=bool(p[6]&128))
                    elif ident==33:
                        b,lat,lon,amsl,rel,vx,vy,vz,hdg=struct.unpack_from('<IiiiihhhH',p)
                        row.update(kind='position',bootMs=b,latE7=lat,lonE7=lon,altAMSLmm=amsl,relativeMm=rel,vxCms=vx,vyCms=vy,vzCms=vz,headingCentiDeg=hdg)
                        if last_boot is not None and b<last_boot:row.update(kind='invalid',reason='BOOT_REGRESSION')
                        last_boot=b
                    elif ident==24:row.update(kind='gps',fix=p[28],satellites=p[29],hdop=struct.unpack_from('<H',p,20)[0])
                    elif ident==193:row.update(kind='ekf',flags=struct.unpack_from('<H',p,20)[0])
                    elif ident==242:
                        lat,lon,alt=struct.unpack_from('<iii',p);row.update(kind='home',home={'latE7':lat,'lonE7':lon,'altMSLmm':alt,'datum':DATUM})
                    else:continue
            rows.append(row)
            if len(rows)>POLICY['maxRows']:raise ValueError('GEOGRAPHY_ROWS_BOUND')
    return rows
