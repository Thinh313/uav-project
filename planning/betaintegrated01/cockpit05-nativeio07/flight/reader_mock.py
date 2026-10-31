"""Synthetic native-format rejection corpus and sampler metadata seams, no device/AP."""
from pathlib import Path
from importlib import import_module
from copy import deepcopy
import json,hashlib,base64,struct,shutil
from pilot.betaintegrated01.control01.mavlink import crc
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-nativeio07.flight';N=import_module(H+'.native_chain');A=import_module(H+'.native_authority');E=R/'evidence/betaintegrated01-cockpit05-nativeio07/host/reader-mock03'
def encode(v):return json.dumps(v,separators=(',',':')).encode()
def fixture(root,mode):
 root.mkdir();wire=bytes([253,9,0,0,1,255,190,0,0,0])+struct.pack('<IBBBBB',0,6,8,0,4,3);wire+=struct.pack('<H',crc(wire[1:],50));header={'format':'aeris-native-segments','version':1,'segment':0,'previousSeal':''};events=[('HEADER',encode(header)),('TX_INTENT',wire),('TX_WRITTEN',wire),('TX_INTENT',wire)]
 refused={'wireSHA256':N.sha(wire),'intentRecordN':4,'reasonClass':'IOException','reason':'NO_FRESH_CONTROL_LEASE','disposition':'PRE_SOCKET_REFUSED','socketCallbackEntered':False,'run':'mock','epoch':'epoch'}
 if mode=='wrongordinal':refused['intentRecordN']=2
 if mode=='boolordinal':refused['intentRecordN']=True
 if mode=='callbackentered':refused['socketCallbackEntered']=True
 if mode=='foreign':refused['epoch']='other'
 if mode=='orphan':events=events[:3]
 if mode=='afterwritten':events.append(('TX_WRITTEN',wire))
 events.append(('TX_REFUSED',encode(refused)))
 if mode=='duplicate':events.append(('TX_REFUSED',encode(refused)))
 if mode=='mixed':events.append(('TX_UNKNOWN',encode({'wireSHA256':N.sha(wire),'reason':'IOException'})))
 events +=[('CONTROL_FAILURE',encode({'reason':'NO_FRESH_CONTROL_LEASE'})),('SESSION_CLOSE',encode({'reason':'CONTROL_FAILED_RESOURCES_CLOSED'if mode!='wrongclose'else'CONTROL_OWNED_RESOURCES_CLOSED','authorityRestorable':False,'aircraftExecutionAccepted':False}))]
 previous='';body=b''
 for n,(kind,payload)in enumerate(events,1):
  row={'format':'aeris-native-record','version':1,'run':'mock','epoch':'epoch','segment':0,'n':n,'previous':previous,'monotonicNs':n*1000,'kind':kind,'base64':base64.b64encode(payload).decode()};plain=encode(row);previous=N.sha(plain);body+=plain[:-1]+b',"sha256":"'+previous.encode()+b'"}\n'
 (root/'segment-000000.jsonl').write_bytes(body);seal=encode({'format':'aeris-native-seal','version':1,'run':'mock','epoch':'epoch','segment':0,'file':'segment-000000.jsonl','sha256':N.sha(body),'bytes':len(body),'previousSeal':'','first':1,'last':len(events),'head':previous});(root/'seal-000000.json').write_bytes(seal);terminal=encode({'format':'aeris-native-session','version':1,'run':'mock','epoch':'epoch','segments':1,'records':len(events),'head':previous,'lastSeal':N.sha(seal),'publicationAllowed':False,'authorityRestorable':False});(root/'session.json').write_bytes(terminal);return N.sha(terminal)
def main():
 E.mkdir(parents=True,exist_ok=False);s=E/'scratch';s.mkdir();cases=[]
 for mode in('valid','wrongordinal','boolordinal','callbackentered','foreign','orphan','afterwritten','duplicate','mixed','wrongclose'):
  root=s/mode;anchor=fixture(root,mode)
  try:result=N.native_cold(root,anchor)
  except Exception as e:
   cases.append({'case':mode,'pass':mode!='valid','reject':type(e).__name__})
  else:
   good=mode=='valid'and result['forensicOnly']is True and len(result['preSocketRefusals'])==1
   cases.append({'case':mode,'pass':good,'result':'CLOSED_FAILED_FORENSIC_ONLY_REPEAT_OLDER_RESOLVED_SHA_ALLOWED'if good else'INVALID_ACCEPTED'})
 # Input metadata raw-reader seam only, NOT full authority/flight fixture.
 obs={'kind':'IMMUTABLE_UI_TOUCH_STATE_SAMPLE_NOT_NEW_MOTION_EVENT','uiHeartbeatElapsedNs':100,'touchRevision':1,'samplerThreadId':2,'uiThreadId':1,'viewEpoch':9,'releaseFence':0};v={'sequence':1,'elapsedNs':150,'inputObservation':obs};row={'kind':'CONTROL_INPUT','n':1,'monotonicNs':200,'base64':base64.b64encode(encode(v)).decode()};assert list(A.validate_sampler_rows([row],{'expectedViewEpoch':9}))
 for fault in('staleUI','sameThread','foreignEpoch','boolFence','missing'):
  q=deepcopy(row);x=deepcopy(v)
  if fault=='staleUI':q['monotonicNs']=200000101
  if fault=='sameThread':x['inputObservation']['samplerThreadId']=1
  if fault=='foreignEpoch':x['inputObservation']['viewEpoch']=8
  if fault=='boolFence':x['inputObservation']['releaseFence']=False
  if fault=='missing':del x['inputObservation']
  q['base64']=base64.b64encode(encode(x)).decode()
  try:list(A.validate_sampler_rows([q],{'expectedViewEpoch':9}))
  except ValueError:cases.append({'case':'sampler-'+fault,'pass':True})
  else:cases.append({'case':'sampler-'+fault,'pass':False})
 removed=sum(p.stat().st_size for p in s.rglob('*')if p.is_file());shutil.rmtree(s);out={'status':'PASS'if all(x['pass']for x in cases)else'FAIL','cases':cases,'syntheticRecordsNotActualNativeFileIOExecution':True,'noAPOrAndroidOrRuntime':True,'scratchRemoved':True,'removedBytes':removed};(E/'results.json').open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['status']=='PASS'
if __name__=='__main__':main()
