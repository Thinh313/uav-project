from pathlib import Path
import copy,datetime,hashlib,json,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control04 import confirmation as C
O=R/'evidence/betaintegrated01-m1control02/qa/confirmation02';O.mkdir();src=R/'pilot/betaintegrated01/control04/confirmation.py';before=hashlib.sha256(src.read_bytes()).hexdigest()
old=json.loads((R/'evidence/betaintegrated01-m1control02/host/old-regression01/derived-loss05-confirmation-descriptor.json').read_bytes());binding=json.loads((R/'evidence/betaintegrated01-m1control01/actual-loss05/control/launch-binding.json').read_bytes());context={k:binding[k]for k in ('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')};CTX=[context[k]for k in('run','epoch','boot')]
D,anchor=C.create_confirmation_descriptor(old['nativeTarPath'],old['prefix'],old['nativeExternalAnchor'],old['hostBracket'],context);positive=C.verify_confirmation(D,anchor,*CTX);cases=[]
def denied(label,d,external=None):
 try:C.verify_confirmation(d,C.descriptor_sha256(d)if external is None else external,*CTX)
 except Exception as e:cases.append({'id':label,'pass':True,'refusal':repr(e)});return
 cases.append({'id':label,'pass':False,'error':'invaliddescriptoraccepted'})
for prior in json.loads((R/'evidence/betaintegrated01-m1control02/qa/confirmation01/results.json').read_bytes())['cases']:
 d=copy.deepcopy(prior['descriptor']);d.update(version=2,expectedLaunchContext=copy.deepcopy(context));denied('REUSE_'+prior['id'],d)
for key,value in [('operator','foreign-operator'),('profileId','foreign-profile'),('binarySHA256','0'*64),('configSHA256','0'*64),('generation','foreign-generation'),('boot','foreign-boot'),('run','foreign-run'),('epoch','foreign-epoch')]:
 d=copy.deepcopy(D);d['expectedLaunchContext'][key]=value;denied('LAUNCH_'+key,d)
for key,value in [('prefix','files/control-runs/foreign/'),('prefix','../'),('nativeTarPath','a'*4097),('nativeTarPath',True),('nativeExternalAnchor',True),('nativeExternalAnchor','notsha'),('confirmationRecordSHA256','0'*63),('version',True)]:
 d=copy.deepcopy(D);d[key]=value;denied('BOUND_'+key+'_'+str(value)[:16],d)
d=copy.deepcopy(D);d['expectedLaunchContext']['run']='a'*65;denied('ID65_REFUSED',d)
d=copy.deepcopy(D);d['hostBracket']['beforeActionHostNs']=True;denied('BRACKET_BOOL_REFUSED',d)
d=copy.deepcopy(D);d['hostBracket']['displayedHomeHash']='0'*64;denied('BRACKET_HASH_REFUSED',d)
denied('WRONG_EXTERNAL_DESCRIPTOR_ANCHOR',D,'0'*64)
r={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if all(x['pass']for x in cases)and before==hashlib.sha256(src.read_bytes()).hexdigest()else'FAIL','baselineActualClosedNative':positive,'cases':cases,'sourceBeforeSHA256':before,'sourceAfterSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'baselineDescriptor':D,'baselineDescriptorAnchor':anchor,'scope':'Finalv2causality/context/operator/config/prefix/bounds checks; reuseassistantauthoredtars, nooldrawedit/noAP/Android/services. Geographyqualifyannouncededitseparatelynotclaimedunderthissourcepin.','newRawTarCopies':0};(O/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'groups':len(cases),'failed':[x['id']for x in cases if not x['pass']]}))
