"""Read-only independent observer state vs exact closed native-WAL prefix oracle.
No product decoder/projection invocation; pinned upstream MAVLink parser only.
"""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,math,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];UTIL=ROOT/'evidence/operator01-qa/tools/receiver04.py';UTIL_SHA='a848da18ae5a84fadc7fc3a7effe991d93f0953fdd1eaa9196db89266df3f7f2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def close(a,b,tol=1e-7):return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol
def verify(run,pins,sample,kind):
 need(sha(UTIL)==UTIL_SHA,'frozen upstream QA utility');sp=importlib.util.spec_from_file_location('obs_upstream_qa',UTIL);u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);m=u.oracle()
 raw=run/'android-raw.jsonl';rows,head,rawsha=u.chain(raw);state=sample['state'];n=state['rawRecords'];need(type(n)is int and 1<=n<=len(rows),'state prefix rowcount');prefix=rows[:n];need(state['rawHead']==prefix[-1]['sha256'],'exact state nativeWALprefix head')
 dec=lambda r:json.loads(base64.b64decode(r['dataBase64']));meta=dec(rows[0]);plan=meta['document']['compiled']['plan'];need(state['format']=='aeris-readonly-observer03' and state['version']==1,'observer schema');need(state['run']==run.name==meta['ownedLaunchAssertion']['run'] and state['nativeSourceId']==pins['sourceId']==meta['sourceId'] and state['planSha256']==pins['planSha256']==plan['sha256'],'state exact native source/run/plan');need(state['scope']=='READ_ONLY_LIVE_NATIVE_WAL_NOT_GCS_NOT_HERA_CALIBRATED_TRAINING' and state['trueSensorAndSocketToAppendDelay']=='UNKNOWN','honest source scope')
 vf=json.loads((ROOT/'evidence/integration03/observer-source-ready04.json').read_text());names=['server.mjs','client.mjs','style.css','index.html','decoder.mjs','projection.mjs','dependencies.json'];vh={}
 for name in names:
  vp=ROOT/'pilot/integration03'/name;need(sha(vp)==vf['files']['pilot/integration03/'+name],'current frozen observer dependency');vh[name]=sha(vp)
 viewerRuntimeSourceId=hashlib.sha256(json.dumps(vh,separators=(',',':')).encode()).hexdigest();need(state['viewerSourceId']==viewerRuntimeSourceId,'exact viewer runtime source set')
 selected={};frontier=None;pending=[];noise=0;frameCount=0;duplicates=0;reordered=0;closedBeforeRX=False
 for row in prefix:
  if row['kind']in('CLOSED','SOCKET_CLOSE'):closedBeforeRX=True
  if row['kind']!='RX':continue
  need(not closedBeforeRX,'no RX after closed prefix')
  pending.extend((x,row['n'],row['elapsedMs'])for x in base64.b64decode(row['dataBase64'],validate=True))
  while pending:
   if pending[0][0]not in(253,254):
    b=pending.pop(0)[0];need(frameCount==0 and (b in(9,10,13)or 32<=b<=126),'startup text only');noise+=1;need(noise<=1024,'startup bound');continue
   header=10 if pending[0][0]==253 else 6
   if len(pending)<header:break
   count=header+pending[1][0]+2+(13 if header==10 and pending[2][0]&1 else 0)
   if len(pending)<count:break
   block=pending[:count];del pending[:count];wire=bytes(x[0]for x in block);fs=m.MAVLink(None).parse_buffer(wire);need(fs and len(fs)==1,'single CRCverified frame');f=fs[0];frameCount+=1
   need(not(header==10 and wire[2]&1),'no unverified MAVLinksignature')
   if(f.get_srcSystem(),f.get_srcComponent())!=(42,1):continue
   if frontier:
    delta=(f.get_seq()-frontier[0])%256
    if delta==0:need(wire==frontier[1],'selected sequence contradiction');duplicates+=1;continue
    if delta>127:reordered+=1;continue
   frontier=(f.get_seq(),wire);msg=f.get_msgId()
   if msg not in(0,30,33):continue
   d=f.to_dict();old=selected.get(msg)
   if msg in(30,33)and old:
    need(d['time_boot_ms']>=old['fields']['time_boot_ms'],'observer bootregression')
    if d['time_boot_ms']==old['fields']['time_boot_ms']:need(d==old['fields'],'sameboot contradict');duplicates+=1;continue
   selected[msg]={'fields':d,'firstByteAtMs':block[0][2],'completeRow':row['n'],'firstByteRow':block[0][1]}
 need(frameCount==state['framesDecoded'] and duplicates==state['duplicateFrames'] and reordered==state['reorderedFrames'],'independent frame/frontier counters')
 closed=any(r['kind']in('CLOSED','SOCKET_CLOSE')for r in prefix);p=state['projected'];result={'kind':kind,'prefixRows':n,'prefixHead':state['rawHead'],'framesDecoded':frameCount,'duplicates':duplicates,'reordered':reordered,'partialFrameBytes':len(pending),'closedInPrefix':closed,'viewerRuntimeSourceId':viewerRuntimeSourceId,'viewerFreezeSourceId':vf['sourceId']}
 if kind=='terminal':
  need(closed and p['status']=='UNKNOWN' and p.get('motionAllowed')is False,'closed source must stop presentation');result.update(status='PASS_CLOSED_NATIVE_SOURCE_UNKNOWN_NO_MOTION');return result
 need(not closed and all(x in selected for x in(0,30,33)),'live sources available');pose=p['pose'];pp=selected[33];aa=selected[30];hh=selected[0];pf=pp['fields'];af=aa['fields'];hf=hh['fields'];home=plan['home'];lat=pf['lat']/1e7;lon=pf['lon']/1e7
 north=(lat-home['lat'])*111319.49079327358;east=(lon-home['lon'])*111319.49079327358*math.cos(home['lat']*math.pi/180);down=-pf['relative_alt']/1000
 roll,pitch,yaw=af['roll'],af['pitch'],af['yaw'];cr,sr,cp,ss,cy,sy=math.cos(roll/2),math.sin(roll/2),math.cos(pitch/2),math.sin(pitch/2),math.cos(yaw/2),math.sin(yaw/2);q=[cr*cp*cy+sr*ss*sy,sr*cp*cy-cr*ss*sy,cr*ss*cy+sr*cp*sy,cr*cp*sy-sr*ss*cy]
 need(pose['run']==run.name and pose['sourceId']==pins['sourceId'] and pose['planSha256']==plan['sha256'] and pose['session']==meta['session'] and pose['boot']==meta['boot'],'pose identity');need(pose['rawPositionSequence']==pp['completeRow'] and pose['rawAttitudeSequence']==aa['completeRow'] and pose['rawHeartbeatSequence']==hh['completeRow'],'exact raw selected message rows');need(pose['nativeAtMs']==min(pp['firstByteAtMs'],aa['firstByteAtMs'])and pose['nativeHeartbeatAtMs']==hh['firstByteAtMs'],'oldest source age notHBrestamped')
 need(all(close(x,y)for x,y in zip(pose['position'],[north,east,down])) and len(pose['position'])==3,'local NEDposition');need(all(close(x,y,1e-9)for x,y in zip(pose['quaternion'],q))and len(pose['quaternion'])==4 and close(math.hypot(*pose['quaternion']),1,1e-9),'quaternion WXYZ');need(close(pose['latitude'],lat)and close(pose['longitude'],lon)and close(pose['relativeAltitudeM'],pf['relative_alt']/1000)and close(pose['amslM'],pf['alt']/1000)and close(pose['speedMS'],math.hypot(pf['vx'],pf['vy'])/100),'position/speedunits');need(pose['armed']==bool(hf['base_mode']&128),'armed cachedframe binding')
 b=sample['clockBefore'];need(b==sample['clockAfter'],'clock changed duringGET, age unresolved');need(b['status']=='BOUNDED_BRACKET' and b['run']==run.name,'clock source');lo=int(b['hostBeforeMonoNs']);hi=int(b['hostAfterMonoNs']);before=int(sample['hostBeforeMonoNs']);after=int(sample['hostAfterMonoNs']);width=(hi-lo)/1e6;need(0<=width<=250 and abs(width-b['widthMs'])<=1 and hi<=before<=after and (after-hi)/1e6<=2500,'samehost monotonic clock brackets')
 nativeLow=lambda now:b['nativeElapsedMs']+(now-hi)/1e6-10
 nativeHigh=lambda now:b['nativeElapsedMs']+(now-lo)/1e6+10
 expectedUpper=(max(0,nativeHigh(before)-pose['nativeAtMs']),max(0,nativeHigh(after)-pose['nativeAtMs']));expectedLower=(max(0,nativeLow(before)-pose['nativeAtMs']),max(0,nativeLow(after)-pose['nativeAtMs']))
 need(expectedUpper[0]-1e-5<=p['ageUpperMs']<=expectedUpper[1]+1e-5 and expectedLower[0]-1e-5<=p['ageLowerMs']<=expectedLower[1]+1e-5,'native WAL append proxyage within actualrequest bracket');need(close(p['clockUncertaintyMs'],width+20,1e-5),'clock uncertainty');expectedStatus='HOLD_STALE'if p['ageUpperMs']>2000 else'STALE'if p['ageUpperMs']>1000 else'LIVE';need(p['status']==expectedStatus and p['motionAllowed']==(p['ageUpperMs']<=2000),'age gates')
 if kind=='airborne':need(p['status']=='LIVE' and p['heartbeatFresh']is True and pose['armed']is True and pose['relativeAltitudeM']>2,'actualairborne presentation sample')
 result.update(status='PASS_EXACT_NATIVE_PREFIX_POSE_AND_BOUNDED_AGE_PROXY',positionNED=[north,east,down],quaternionWXYZ=q,selectedNativeSources=selected,reportedAgeUpperMs=p['ageUpperMs'],requestBoundAgeUpperMs=list(expectedUpper),clockWidthMs=width,poseClock='NATIVE_WAL_APPEND_PROXY_NOT_SENSOR_OR_SOCKET_DELAY');return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--pins',type=Path,required=True);p.add_argument('--sample',type=Path,required=True);p.add_argument('--kind',choices=['airborne','live','terminal'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();need(not a.output.exists(),'immutableoutput')
 try:r=verify(a.run,json.loads(a.pins.read_text()),json.loads(a.sample.read_text()),a.kind);code=0
 except Exception as e:r={'status':'FAIL_OR_SCHEMA_UNSUPPORTED','errorType':type(e).__name__,'error':str(e),'kind':a.kind};code=2
 r.update(run=a.run.name,receiverSha256=sha(Path(__file__)),inputs={str(x):sha(x)for x in[a.pins,a.sample]},scope='Independent raw/pose/ageproxy binding only; no GPU/display/sensorlatency/flightauthority or physical calibration claim');a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x')as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({'status':r['status'],'error':r.get('error'),'output':str(a.output)}));return code
if __name__=='__main__':raise SystemExit(main())
