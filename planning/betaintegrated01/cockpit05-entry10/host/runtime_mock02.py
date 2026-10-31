"""Synthetic byte-format fixtures/policy faults; no actual prime, runtime, AP or sockets."""
from pathlib import Path
from importlib import import_module
import base64,hashlib,json,os,shutil,zlib,copy
R=Path(__file__).resolve().parents[4]
H='planning.betaintegrated01.cockpit05-entry10'
j=import_module(H+'.runtime.journal');new=import_module(H+'.runtime.journal.receiver');p=import_module(H+'.host.policy02')
from pilot.betaintegrated01.runtime02.journal.receiver import verify_journal as old_verify
from pilot.betaintegrated01.runtime02.frame_adapter import FrameAdapter as OldAdapter
from pilot.betaintegrated01.runtime.ap_stage import canonical


def fixture(root):
    root.mkdir();run,epoch='entry10-synthetic','epoch';previous='0'*64;lines=[]
    rows=[('SEGMENT',None,{'ordinal':0,'startSequence':0,'previousSegmentSHA256':'0'*64}),('RX',0,{'base64':base64.b64encode(b'SYNTHETIC_MOCK_RX').decode()}),('INTENT',0,{'base64':base64.b64encode(b'MOCK_SENSOR').decode()}),('SENT',0,{'returnedBytes':11,'expectedBytes':11,'scope':'LOCAL_CALLBACK_RETURN_NOT_AP_EXECUTION'}),('CLOSE',None,{'completedFrames':1,'scope':'RECORDING_ONLY_NOT_FLIGHT'})]
    for n,(kind,frame,payload)in enumerate(rows):
        body={'v':2,'run':run,'epoch':epoch,'segment':0,'seq':n,'previous':previous,'kind':kind,'frame':frame,'payload':payload};raw=canonical(body);previous=hashlib.sha256(bytes.fromhex(previous)+raw).hexdigest();lines.append(canonical({'body':body,'crc32':format(zlib.crc32(raw),'08x'),'sha256':previous})+b'\n')
    segment=b''.join(lines);pol=j.Policy(segment_bytes=16384,quota_bytes=65536,max_record_bytes=2048,max_segments=4,termination_reserve_bytes=8192)
    manifest={'format':'aeris-beta-journal-runtime02','version':2,'run':run,'epoch':epoch,'policy':pol.__dict__,'scope':'HOST_RECORDING_FOUNDATION_NOT_AP_STAGE_OR_FLIGHT_ACCEPTANCE','diskGuardPolicy':dict(p.DISK_POLICY),'diskGuardPriming':{'elapsedRealMonotonicNs':15000000000,'historySpanNs':15000000000,'primed':True,'source':'ACTUAL_HOST_15S_PRIME_NO_SYNTHETIC_SEED','sampleCount':151}}
    seal={'version':2,'run':run,'epoch':epoch,'segment':0,'startSequence':0,'endSequence':4,'fileBytes':len(segment),'fileSHA256':hashlib.sha256(segment).hexdigest(),'head':previous,'previousSegmentSHA256':'0'*64,'state':'SESSION_CLOSED'}
    session={'version':2,'run':run,'epoch':epoch,'segments':1,'records':5,'head':previous,'lastSegmentSHA256':seal['fileSHA256'],'frames':1,'state':'COMPLETE_RECORDING','APExecutionAccepted':False}
    for name,value in [('manifest.json',manifest),('segment-000000.seal.json',seal),('session.json',session)]: (root/name).write_bytes(canonical(value)+b'\n')
    (root/'segment-000000.jsonl').write_bytes(segment)
    sha=lambda name:hashlib.sha256((root/name).read_bytes()).hexdigest()
    return {'version':1,'run':run,'epoch':epoch,'manifestSHA256':sha('manifest.json'),'sessionSHA256':sha('session.json'),'sealSHA256':[sha('segment-000000.seal.json')],'head':previous}


def check(output):
    output=Path(output);output.mkdir(exist_ok=False);scratch=output/'scratch';scratch.mkdir();results=[]
    def test(name,fn):
        try:results.append({'case':name,'pass':True,'detail':fn()})
        except Exception as exc:results.append({'case':name,'pass':False,'error':repr(exc)})
    def rejects(fn,part):
        try:fn()
        except Exception as exc:
            assert part in str(exc),(part,repr(exc));return str(exc)
        raise AssertionError('unexpectedacceptance')
    path=scratch/'synthetic';anchor=fixture(path)
    try:
        test('syntheticV2 entry10 complete externalanchor roundtrip',lambda:new.verify_journal(path,'entry10-synthetic','epoch',expected_commit=anchor)['state'])
        test('old20receiver strictly rejects new10manifest',lambda:rejects(lambda:old_verify(path,'entry10-synthetic','epoch',expected_commit=anchor),'DISK_GUARD_POLICY'))
        saved=(path/'manifest.json').read_bytes()
        for key,value in [('entryBytes',20*2**30),('floorBytes',9*2**30),('reserveBytes',0),('horizonNs',0)]:
            def mismatch(k=key,v=value):
                m=json.loads(saved);m['diskGuardPolicy'][k]=v;(path/'manifest.json').write_bytes(canonical(m)+b'\n')
                try:return rejects(lambda:new.verify_journal(path,'entry10-synthetic','epoch'),'DISK_GUARD_POLICY')
                finally:(path/'manifest.json').write_bytes(saved)
            test('reject mixed/wrong recording policy '+key,mismatch)
        body=(path/'segment-000000.jsonl').read_bytes();(path/'segment-000000.jsonl').write_bytes(body.replace(b'MOCK',b'NOCK',1))
        # Change one unconditionally present byte if base64 hides MOCK.
        bad=bytearray(body);offset=body.index(b'"crc32":"')+len(b'"crc32":"');bad[offset]=ord('0')if bad[offset]!=ord('0')else ord('1');(path/'segment-000000.jsonl').write_bytes(bad)
        test('retained bad bytes CRC/hash reject',lambda:rejects(lambda:new.verify_journal(path,'entry10-synthetic','epoch'),'CRC_OR_CHAIN'))
        (path/'segment-000000.jsonl').write_bytes(body)
        def identity():
            N=import_module(H+'.runtime.frame_adapter').FrameAdapter
            names=[k for k in OldAdapter.__dict__ if callable(getattr(OldAdapter,k))and k!='__init__']
            assert all(getattr(N,k)is getattr(OldAdapter,k)for k in names)
            return names
        test('all receive/model/fsync/send/failure methods inheritedexact',identity)
        def policyfaults():
            writer=import_module(H+'.runtime.journal.writer')
            rejects(lambda:writer.bounded_value({'bad':'x'*3000},2048),'PAYLOAD_')
            rejects(lambda:writer.Policy(segment_bytes=8192,quota_bytes=1).validate(),'SEGMENT_GROUP_RESERVE')
            source=(R/'pilot/betaintegrated01/runtime02/journal/writer.py').read_text().replace('from .admission import','from ...host.admission import')
            assert (R/'planning/betaintegrated01/cockpit05-entry10/runtime/journal/writer.py').read_text()==source
            return 'Oversizedpayload and invalidcapacity refuse; writer/fsync/UNKNOWN paths exact exceptguardimport'
        test('bounded payload/capacity overflow and exactwriter diff',policyfaults)
        def amendment():
            c=p.build_config(R,'nominal','entry10unit','epoch','boot',R,'case',maximum_seconds=1960);p.validate_recording_policy(c)
            for key,value in [('externalRecordingPolicy',{}),('expectedConfigSHA256','0'*64),('requestedSpeedup',2),('capMs',1000),('requestedSpeedup',True),('capMs',500.0)]:
                t=copy.deepcopy(c);t[key]=value;rejects(lambda:p.validate_recording_policy(t),'REQUIRED'if key=='externalRecordingPolicy'else'PHYSICAL_PROFILE')
            return {'typed39':'unchangedpackagedbits viafrozen05contract','profile':'nominal02','unknownPolicyFailsClosed':True}
        test('explicit amendment+source binding and physicaltyped39 mismatch refusal',amendment)
    finally:
        count=len(list(scratch.rglob('*')));size=sum(x.stat().st_size for x in scratch.rglob('*')if x.is_file());shutil.rmtree(scratch)
    result={'status':'PASS'if all(x['pass']for x in results)else'FAIL','cases':results,'fixtureProvenance':'ASSISTANT_SYNTHETIC_FORMAT_FIXTURE_INCLUDING_PRIMING_SCHEMA_NOT_REAL_HOST_PRIMING','actualPrimeRuns':0,'runtimeOrAPStarts':0,'scratchRemoved':str(scratch),'removedEntries':count,'removedBytes':size,'existsAfter':scratch.exists()}
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    result=check(R/'evidence/betaintegrated01-cockpit05-entry10/host/runtime-mock03');print(json.dumps(result,indent=2))
