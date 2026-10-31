"""Cold, separately implemented MAVLink CRC/parser and behavioral readback.

Uses pinned full dialect field metadata, not the live JavaScript decoder.
Local SHA chains are not signatures; one author, no independent human review.
"""
import argparse
import hashlib
import json
import math
import pathlib
import shutil
import struct

R=pathlib.Path(__file__).resolve().parents[2]
DEFS=json.loads((R/'pilot/apstream40/definitions.mjs').read_text().split('export const DEFINITIONS=',1)[1].strip().removesuffix(';'))
FMT={'uint8_t':'B','int8_t':'b','uint16_t':'H','int16_t':'h','uint32_t':'I','int32_t':'i','uint64_t':'Q','int64_t':'q','float':'f','double':'d'}


def crc(data,extra):
    value=65535
    for b in data+bytes([extra]):
        value^=b
        for _ in range(8):value=(value>>1)^0x8408 if value&1 else value>>1
    return value


class Parser:
    def __init__(self,allow_boot_ascii=False):self.buffer=b'';self.preamble=b'';self.started=False;self.allow_boot_ascii=allow_boot_ascii;self.boot_noise=[]
    def push(self,chunk,at):
        self.buffer+=chunk;out=[]
        while self.buffer:
            if self.buffer[0] not in [253,254]:
                if self.started:
                    assert self.allow_boot_ascii and (self.buffer[0] in [9,10,13] or 32<=self.buffer[0]<=126),'NON_MAVLINK_AFTER_BOOT'
                    self.boot_noise.append((at,self.buffer[0]));assert len(self.boot_noise)<=64,'BOOT_NOISE_BOUND'
                else:
                    self.preamble+=self.buffer[:1];assert len(self.preamble)<=1024
                self.buffer=self.buffer[1:];continue
            h=10 if self.buffer[0]==253 else 6
            if len(self.buffer)<h:break
            if h==10:assert self.buffer[2]==0,'SIGNING_OR_UNSUPPORTED_FLAGS'
            size=self.buffer[1];total=h+size+2
            if len(self.buffer)<total:break
            self.started=True;b=self.buffer[:total];self.buffer=self.buffer[total:]
            id=int.from_bytes(b[7:10],'little') if h==10 else b[5];d=DEFS[str(id)]
            assert size<=d['max'] and crc(b[1:h+size],d['crc'])==int.from_bytes(b[h+size:],'little'),'CRC_OR_LENGTH'
            p=b[h:h+size]+bytes(d['max']-size);fields={}
            for f in d['fields']:
                if f['type']=='char':value=p[f['offset']:f['offset']+f['array']].split(b'\0')[0].decode('ascii')
                else:
                    code=FMT[f['type']];values=struct.unpack_from('<'+code*(f['array'] or 1),p,f['offset']);value=list(values) if f['array'] else values[0]
                fields[f['name']]=value
            out.append({'id':id,'system':b[5 if h==10 else 3],'component':b[6 if h==10 else 4],
                        'seq':b[4 if h==10 else 2],'fields':fields,'at':at,'raw':b})
        return out


def analyze(path):
    rx=Parser(allow_boot_ascii=True);txframes=[];frames=[];marks={};previous='0'*64;pending=[];count=0;sensorbatches=0
    for line in path.read_bytes().splitlines():
        row=json.loads(line);count+=1;assert row['n']==count and row['prev']==previous,'SEQUENCE_CHAIN'
        assert b',"sha256":' in line
        body=line.rsplit(b',"sha256":',1)[0]+b'}'
        assert hashlib.sha256(body).hexdigest()==row['sha256'],'SHA_CHAIN';previous=row['sha256']
        if row['kind']=='RX':frames.extend(rx.push(bytes.fromhex(row['rawHex']),row['at']))
        elif row['kind']=='TX_INTENT':
            parser=Parser();decoded=parser.push(bytes.fromhex(row['rawHex']),row['at']);assert not parser.buffer and decoded
            for f in decoded:
                assert f['system']==255 and f['component']==190
                if f['id'] not in [0,132]:assert f['fields']['target_system']==42 and f['fields']['target_component']==1
            if row['reason']=='VIRTUAL_RAYS':
                sensorbatches+=1;s=row['metadata'];assert len(decoded)==8 and s['frame']=='BODY_FRD_METRES' and s['clock']=='HOST_MONOTONIC_MS'
                assert 0<=row['at']-s['at']<=200 and len(s['ranges'])==8
                for i,f in enumerate(decoded):
                    p=f['fields'];assert f['id']==132 and p['orientation']==p['id']==i and p['min_distance']==20 and p['max_distance']==2000
                    assert p['current_distance']==min(2001,math.floor(s['ranges'][i]*100+.5))
            pending.append(row['rawHex']);txframes.extend(decoded)
        elif row['kind']=='TX_WRITE_RETURN':assert pending and pending.pop(0)==row['rawHex'],'TX_ORDER_OR_UNKNOWN_SEND'
        elif row['kind']=='MARK':marks[row['name']]=row
    assert not rx.buffer,'PARTIAL_RX_TAIL';assert not pending,'UNKNOWN_TX_OUTCOME'
    if rx.preamble:assert b'Init ArduCopter V4.7.1 (dbe79216)' in rx.preamble
    if rx.boot_noise:
        assert bytes(b for _,b in rx.boot_noise)==b'Init Gyro**\n','UNEXPECTED_BOOT_ASCII'
        arm_at=min(f['at'] for f in txframes if f['id']==76 and f['fields']['command']==400)
        assert max(t for t,_ in rx.boot_noise)<arm_at,'ASCII_AFTER_ARM'
    accepted=[];lastseq=None;foreign=0
    for f in frames:
        if f['system']!=42 or f['component']!=1:foreign+=1;continue
        if lastseq is not None:
            delta=(f['seq']-lastseq)%256
            if delta==0 or delta>128:continue
            assert delta!=128
        lastseq=f['seq'];accepted.append(f)
    versions=[f for f in accepted if f['id']==148];assert versions and all(f['fields']['flight_sw_version']==67568127 and bytes(f['fields']['flight_custom_version'])==b'dbe79216' for f in versions)
    return {'rows':count,'head':previous,'frames':accepted,'tx':txframes,'marks':marks,'sensorBatches':sensorbatches,'foreignFrames':foreign,'bootNoiseBytes':len(rx.boot_noise),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def verify_behavior(data):
    frames=data['frames'];marks=data['marks'];checks=[]
    def window(a,b):return [f for f in frames if marks[a]['at']<=f['at']<=marks[b]['at']]
    for ps,ys in [(1,1),(-1,1),(1,-1),(-1,-1)]:
        name=f'PITCH_YAW_{ps}_{ys}';w=window(name+'_START',name+'_END');a=[f['fields'] for f in w if f['id']==30]
        before=[f for f in frames if f['id']==30 and f['at']<=marks[name+'_START']['at']][-1]['fields']['pitch']
        p=max(ps*(f['pitch']-before) for f in a);y=max(ys*f['yawspeed'] for f in a)
        assert len(a)>=5 and p>.01 and y>.03
        assert all(math.isfinite(f[k]) for f in a for k in ['roll','pitch','yaw','rollspeed','pitchspeed','yawspeed'])
        assert all(abs(f['pitch'])<.6 and abs(f['roll'])<.6 for f in a)
        assert any(f['id']==65 and f['fields']['chan2_raw']==1500+ps*50 and f['fields']['chan4_raw']==1500+ys*80 for f in w)
        checks.append({'id':name,'pass':True,'peakSignedPitchDelta':p,'peakSignedYawRate':y,'attitudes':len(a)})
    base=[f['fields'] for f in window('BASELINE_START','BASELINE_END') if f['id']==32];assert max(f['x'] for f in base)>12.3
    w=window('AVOID_ENABLED_START','AVOID_ENABLED_END');positions=[f for f in w if f['id']==32]
    clear=min(12-f['fields']['x']-.3 for f in positions);tail=[f for f in positions if f['at']>=positions[-1]['at']-3000]
    speed=max(abs(f['fields']['vx']) for f in tail)
    assert clear>=1.2 and speed<=.5 and max(f['fields']['x'] for f in positions)>7
    assert any(f['id']==132 and f['fields']['orientation']==0 and f['fields']['current_distance']<350 for f in w)
    sets=[f['fields']['param_value'] for f in data['tx'] if f['id']==23 and f['fields']['param_id']=='AVOID_ENABLE'];assert sets==[0.,2.]
    typed=[f['fields'] for f in frames if f['id']==22 and f['fields']['param_id']=='AVOID_ENABLE'];assert any(p['param_type']==2 and p['param_value']==0 for p in typed) and any(p['param_type']==2 and p['param_value']==2 for p in typed)
    checks.append({'id':'AVOIDANCE_BASELINE_ENABLED','pass':True,'baselineMaxX':max(f['x'] for f in base),'minimumSurfaceClearanceM':clear,'tailMaxForwardSpeedMps':speed})
    w=window('SENSOR_DROPOUT_START','SENSOR_RESTORE');a=[f for f in w if f['id']==30][-1];d=[f for f in w if f['id']==132 and f['fields']['orientation']==0]
    assert not d or a['fields']['time_boot_ms']-d[-1]['fields']['time_boot_ms']>700
    assert any(f['id']==132 and f['fields']['orientation']==0 and f['at']>marks['SENSOR_RESTORE']['at'] for f in frames)
    checks.append({'id':'SENSOR_DROPOUT_RESTORE','pass':True,'notAircraftFailstopProof':True})
    end=marks['LANDED_DISARMED']['at'];hb=[f for f in frames if f['id']==0 and f['at']<=end][-1];land=[f for f in frames if f['id']==245 and f['at']<=end][-1]
    assert not(hb['fields']['base_mode']&128) and land['fields']['landed_state']==1
    assert any(f['id']==0 and f['fields']['base_mode']&128 for f in frames)
    checks.append({'id':'ACTUAL_ARMED_TO_LANDED_DISARMED','pass':True})
    return checks


def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args();run=pathlib.Path(a.run).resolve();out=pathlib.Path(a.out).resolve()
    assert run.is_relative_to(R/'evidence/simsitl76') and out.is_relative_to(R/'evidence/simsitl76')
    launch=json.loads((run/'launch.json').read_text());closure=json.loads((run/'closure.json').read_text());assert closure['containerRemoved'] and closure['containerId']==launch['containerId']
    data=analyze(run/'wire.jsonl');verdict='PASS_RAW_INTEGRITY_ONLY';checks=[]
    if (run/'driver-result.json').exists() and closure['driverExitCode']==0 and closure['error'] is None:
        checks=verify_behavior(data);verdict='PASS_SCOPED_INTERNAL_SITL'
    receipt={'status':verdict,'checks':checks,'rows':data['rows'],'acceptedAPFrames':len(data['frames']),'txFrames':len(data['tx']),
             'sensorBatches':data['sensorBatches'],'foreignFrames':data['foreignFrames'],'bootNoiseBytes':data['bootNoiseBytes'],'rawSha256':data['sha256'],'head':data['head'],
             'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_HERA_OR_SIM32','actualHardware':False,'independentHumanReview':False}
    assert shutil.disk_usage(R).free>20*2**30+65536
    with out.open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt))


if __name__=='__main__':main()
