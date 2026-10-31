from pathlib import Path
import sys,importlib.util,json,hashlib,copy,datetime,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];E=R/'evidence/big02-qa';spec=importlib.util.spec_from_file_location('independent_big02_receiver',R/'planning/big02/qa-receiver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);corpus=json.loads((E/'heldout01.json').read_text());v=corpus['values'];base=m.read_directory(E/'package01');context=json.loads(base['manifest.json'])['context'];receiver=v['receiver'];sender='qa-big02-sender-374c';results=[];error=None
try:
 t=set();c=set();r=m.verify_bytes(base,receiver,sender,t,c,context);expected=v['expected'];assert abs(r['derived']['latitudeDeg']-expected['latitude'])<1e-9 and abs(r['derived']['longitudeDeg']-expected['longitude'])<1e-9 and abs(r['derived']['altitudeM']-expected['altitude'])<1e-9 and r['actualImages']==0;results.append({'id':'GQ01','status':'PASS_INDEPENDENT_RECEIVER_MATH','receipt':r})
 def refuse(id,files,expect_receiver=receiver,ts=None,cs=None):
  ts=set()if ts is None else ts;cs=set()if cs is None else cs;before=(ts.copy(),cs.copy());reason=None
  try:m.verify_bytes(files,expect_receiver,sender,ts,cs,context)
  except m.Refused as x:reason=str(x)
  assert reason and (ts,cs)==before,(id,reason)
  results.append({'id':id,'status':'PASS_REFUSED','reason':reason,'replayStateUnchangedOnFailure':True})
 bad=dict(base);b=bytearray(base['original.jpg']);b[-4]^=1;bad['original.jpg']=bytes(b);refuse('GQ08',bad)
 refuse('GQ09',base,v['wrongReceiver'])
 refuse('GQ10',base,ts=t,cs=c)
 bad=dict(base);bad['original.jpg']=bad['original.jpg'][:-1];refuse('GQ11',bad)
 bad=dict(base);s=json.loads(bad['sidecar.json']);s['actualImages']=1;s['sourceKind']='REAL';bad['sidecar.json']=m.canonical(s);man=json.loads(bad['manifest.json']);man['sourceKind']='REAL';man['actualImages']=1;man['files'][1]['sizeBytes']=len(bad['sidecar.json']);man['files'][1]['sha256']=m.sha(bad['sidecar.json']);man['packageId']=m.sha(m.canonical({k:v for k,v in man.items()if k!='packageId'}));bad['manifest.json']=m.canonical(man);refuse('GQ12',bad)
except BaseException:error=traceback.format_exc()
finally:
 out={'at':datetime.datetime.now().astimezone().isoformat(),'status':'PASS_INDEPENDENT_RECEIVER'if not error else'FAIL_RETAINED','receiverSourceSHA256':m.sha((R/'planning/big02/qa-receiver.py').read_bytes()),'corpusSHA256':m.sha((E/'heldout01.json').read_bytes()),'producerFreezeSHA256':m.sha((R/'evidence/big02/geotag-source-ready01.json').read_bytes()),'packageMembers':{k:m.sha(v)for k,v in base.items()},'results':results,'error':error,'scope':'Pythonstdlib independent hash/schema/JPEGstructure/context/replay/exposuremath; never imported sender verify orgeotag implementations; noactualcamera/GNSS/phone'};(E/'receiver-heldout01.json').open('x').write(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
