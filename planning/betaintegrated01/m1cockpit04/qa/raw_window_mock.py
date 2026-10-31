from pathlib import Path
import sys,json,struct,hashlib,copy
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent));from combined_oracle import raw_clock_model_window,NS
R=Path(__file__).resolve().parents[4];O=R/'evidence/betaintegrated01-m1cockpit04/qa/raw-window-mock01';O.mkdir();ctx=dict(run='r',epoch='e',boot='b');tests=[]
def clock(at,i=1,foreign=False):
 raw=struct.pack('<7Q',i,at+100,at+200,0,0,0,0);return dict(body=dict(kind='EVENT',payload=dict(eventKind='CLOCK',data=dict(kind='RESPONSE',status='MATCHED',rawHex=raw.hex(),rawSHA256=hashlib.sha256(raw).hexdigest(),guestReceiveNs=at+100,guestSendNs=at+200,hostReceiveNs=at,**{**ctx,'boot':'foreign'if foreign else'b'}))))
def stage(at,frame):return dict(body=dict(kind='EVENT',payload=dict(eventKind='STAGE',data=dict(frame=frame,fields=dict(wireFrame=frame,receiveSinceOriginNs=at-NS)))))
origin=dict(body=dict(kind='EVENT',payload=dict(eventKind='TIMING_ORIGIN',data=dict(hostMonotonicNs=NS))))
def run(name,rows,start=NS,end=NS+2_000_000,reject=None):
 d=O/name;d.mkdir();(d/'segment-000000.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in rows))
 try:v=raw_clock_model_window(d,start,end,ctx);passed=reject is None;detail=v
 except Exception as e:passed=reject is not None and(reject in str(e));detail=type(e).__name__+':'+str(e)
 tests.append(dict(id=name,pass_=passed,result=detail))
base=[origin,clock(NS,1),stage(NS,0),stage(NS+1_000_000,1),clock(NS+2_000_000,2),stage(NS+2_000_000,2)];run('smallValidNotThirtyMinutes',base);run('missingOrigin',base[1:],reject='DURATION_STAGE_WITHOUT_ORIGIN');run('duplicatedOrigin',[origin,*base],reject='DURATION_MULTIPLE_ORIGIN');bad=copy.deepcopy(base);bad[2]['body']['payload']['data']['frame']=100;run('wireFrameMismatch',bad,reject='');bad=copy.deepcopy(base);bad[3]=stage(NS+1_000_000,2);run('frameJumpFastforwardRejected',bad,reject='');bad=copy.deepcopy(base);bad[1]=clock(NS,1,True);run('foreignBootRejected',bad,reject='');run('sparseEndpointsCannotClaim1800',base,end=NS+1802*NS,reject='DURATION_RAW_ENDPOINT_GAP');run('clockOnlyNoModelRejected',[origin,clock(NS),clock(NS+1802*NS,2)],end=NS+1802*NS,reject='DURATION_RAW_WINDOWS_EMPTY')
r=dict(status='PASS_BOUNDED_SYNTHETIC_COMPONENT_NOT_RUNTIME'if all(x['pass_']for x in tests)else'FAIL',tests=tests,scope='Durationcomponentonly on synthetic EVENTbodies; notcompletejournal/physics/AP. ActualCLI firstrequiresfull original journal/model/AP replay.',sourceSHA256=hashlib.sha256(Path(__file__).with_name('combined_oracle.py').read_bytes()).hexdigest(),servicesStarted=0);(O/'results.json').open('x').write(json.dumps(r,indent=2));print(r['status'],[t['id']for t in tests if not t['pass_']])
