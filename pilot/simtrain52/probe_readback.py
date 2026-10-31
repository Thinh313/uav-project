"""Read-only original-model/WAL/AP-stage validation of the bounded idle probe."""
from pathlib import Path
import collections, hashlib, importlib.util, json, math, struct, sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'pilot/sim32-journal04'))
from wal_journal import read_wal, unpack_intent


def main(rid):
    assert rid.isalnum() and len(rid)<=24
    out=R/'evidence/simtrain52-probe'/rid
    spec=importlib.util.spec_from_file_location('originalprobe52',R/'evidence/sim32/source-final/pilot/sim32/physics.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    model=original.Model(original.profile('empty','calm'))
    w=read_wal(out/'frames.wal');assert w['error'] is None
    records=w['records']; assert records[0]['kind']=='HEADER' and records[-1]['kind']=='CLOSE'
    received={}; intents={}; sent={}; frames=[]
    for record in records[1:-1]:
        frame=record['frame']; kind=record['kind']
        if kind=='RX':
            assert frame not in received
            received[frame]=json.loads(record['payload'])
            assert received[frame]['source']=='ACTUAL_PINNED_AP_IDLE_PROBE'
        elif kind=='INTENT':
            assert frame not in intents and frame in received
            row,snap=unpack_intent(record['payload']); assert not snap
            row=json.loads(row);assert row['frame']==frame and row['rate']==1200
            assert row['servoHex']==received[frame]['rawHex']
            magic,rate,counter,*pwm=struct.unpack('<HHI16H',bytes.fromhex(row['servoHex']))
            assert (magic,rate,counter)==(18458,1200,frame)
            expected='\n'+json.dumps(model.step(pwm,1/1200),separators=(',',':'),allow_nan=False)+'\n'
            assert expected==row['sensorUtf8'],('ORACLE_SENSOR',frame)
            assert json.dumps(model.snapshot(),separators=(',',':'))==json.dumps(row['modelAux'],separators=(',',':'))
            intents[frame]={'row':row,'record':record};frames.append(frame)
        elif kind=='SENT':
            assert frame in intents and frame not in sent
            data=json.loads(record['payload']);assert data['returnedBytes']==data['expectedBytes']==len(intents[frame]['row']['sensorUtf8'].encode())
            assert record['seq']>intents[frame]['record']['seq']
            assert data['hostSendReturnNs']>=intents[frame]['record']['ns']
            sent[frame]=data
        else: raise AssertionError(kind)
    assert len(frames)==4800 and frames==list(range(frames[0],frames[0]+4800))
    assert set(received)==set(intents)==set(sent)
    stages=json.loads((out/'backend-stages.json').read_text())
    assert len(stages)==4800
    for stage in stages:
        frame,rx,a,computed,barrier,send=stage
        assert rx<=a<=computed<=barrier<=send
        assert barrier>=intents[frame]['record']['ns'] and send==sent[frame]['hostSendReturnNs']
    ap=out/'ap-timing.bin';events=[]
    with ap.open('rb')as f:
        magic,capacity,count,failed,size=struct.unpack('<8s4Q',f.read(40))
        assert magic==b'AERISD02' and count<=capacity and failed==0 and size==64
        f.seek(4096)
        for i in range(count):
            event=struct.unpack('<QQIIQQQQq',f.read(64));assert event[0]==i and event[4]<=event[5]
            events.append(event)
    by_frame=collections.defaultdict(lambda:collections.defaultdict(list))
    for ev in events: by_frame[ev[1]][ev[2]].append(ev)
    intervals=[]
    for frame in frames:
        group=by_frame[frame]
        assert len(group[11])==len(group[13])==len(group[14])==1,('AP_FRAME_CORRELATION',frame)
        assert group[11][0][-1]==40 and group[13][0][-1]>0
        intervals.append((group[13][0][4]-group[11][0][4])/1e6)
    pairs=[json.loads(line)for line in(out/'clock-pairs.jsonl').read_text().splitlines()]
    matched=[p for p in pairs if p['status']=='MATCHED' and p['freshCalibration']]
    assert len(matched)>=3
    for p in matched:
        assert p['hostSendNs']<=p['hostReceiveNs'] and p['guestReceiveNs']<=p['guestSendNs']
        assert p['offsetLowNs']==p['hostSendNs']-p['guestReceiveNs']
        assert p['offsetHighNs']==p['hostReceiveNs']-p['guestSendNs']
        assert p['offsetLowNs']<=p['offsetHighNs']
    closure=json.loads((out/'closure.json').read_text());assert closure['backendExited'] and closure['backendExitCode']==0 and closure['ownedContainerStopped'] and closure['error'] is None
    result=json.loads((out/'backend-result.json').read_text());assert result['frames']==4800 and result['error'] is None
    def pct(values):
        s=sorted(values)
        return {'n':len(s),'p50':s[int((len(s)-1)*.5)],'p95':s[int((len(s)-1)*.95)],'p99':s[int((len(s)-1)*.99)],'max':max(s)}
    output={'status':'PASS_IDLE_CAPTURE_ONLY_NOT_G1_ACCEPTANCE','walVerifiedRecords':len(records),
            'originalSensorAndAuxFrames':4800,'frameContinuity':'CONSECUTIVE_NO_DUPLICATE_OR_GAP',
            'allAdmittedIntentsHaveLocalSendReturn':True,'allAdmittedFramesHaveAPReceiveAndParseStage':True,
            'apEvents':count,'apUnadmittedTailFrames':sorted(set(by_frame)-set(frames)),
            'clockPairs':dict(collections.Counter(p['status']for p in pairs)),
            'clockBracketWidthsMs':pct([(p['offsetHighNs']-p['offsetLowNs'])/1e6 for p in matched]),
            'clockQualification':'Fresh nonce host/guest offset intervals; no exact point conversion or UI clock qualification',
            'apServoSendToSensorReceiveMs':pct(intervals),
            'hostComputeMs':pct([(s[3]-s[2])/1e6 for s in stages]),
            'hostComputeEndToDurableIntentMs':pct([(s[4]-s[3])/1e6 for s in stages]),
            'hostReceiveIntervalsMs':pct([(b[1]-a[1])/1e6 for a,b in zip(stages,stages[1:])]),
            'idleReceiveRTF':result['idleReceiveRTF'],'activeReceiveWallSeconds':result['activeReceiveWallSeconds'],
            'scope':'4simseconds idle, no arm/mode/mission command, no active UI or flight workload, no1x gate acceptance',
            'journalPolicy':'fsync-before-publish','capUs':500000,'speedup':1,'rateHz':1200,
            'closure':closure,'rawSha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[out/'frames.wal',ap,out/'backend-stages.json',out/'clock-pairs.jsonl']}}
    with(out/'readback.json').open('x')as f:json.dump(output,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in output.items()if k in['status','originalSensorAndAuxFrames','idleReceiveRTF','clockPairs','apUnadmittedTailFrames']}))


if __name__=='__main__':main(sys.argv[1])
