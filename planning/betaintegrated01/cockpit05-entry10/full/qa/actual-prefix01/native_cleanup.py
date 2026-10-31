from pathlib import Path
from importlib import import_module
import json,sys,base64,struct,hashlib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[6];sys.path.insert(0,str(R));E=R/'evidence/betaintegrated01-cockpit05-entry10-flight';C=E/'actual-combined01/control';A=R/'evidence/betaintegrated01-cockpit05-closure01/native-private02.tar';O=E/'qa/actual-prefix01';auth=json.loads((O/'native-external02.json').read_text());ns=import_module('pilot.betaintegrated01.cockpit04.revision02.native_stream');rel=import_module('pilot.betaintegrated01.cockpit04.revision02.native_release');Framer=import_module('pilot.betaintegrated01.control01.mavlink').Framer
cold,rows=ns.closed_native(str(A),'files/control-runs/cockpit05-entry10-combined-01/',auth['derivedSessionSHA256']);tx,hb=rel.native_wire_evidence(rows);source=ns.IndexedNative(A,'files/control-runs/cockpit05-entry10-combined-01/');decoder=Framer();commands=[]
for row in source.rows():
 if row['kind']!='TX_WRITTEN':continue
 raw=base64.b64decode(row['base64'],validate=True)
 for f in decoder.feed(raw,row['monotonicNs']):
  p=f['payload'];k=f['id'];obj={'record':row['n'],'guestNs':row['monotonicNs'],'id':k,'SHA256':hashlib.sha256(raw).hexdigest()}
  if k==11:obj.update(kind='MODE',mode=struct.unpack_from('<I',p)[0])
  elif k==70:
   channels=list(struct.unpack_from('<8H',p))+list(struct.unpack_from('<10H',p,18));obj.update(kind='RC',channels=channels)
  elif k==76:obj.update(kind='COMMAND',command=struct.unpack_from('<H',p,28)[0],params=list(struct.unpack_from('<7f',p)))
  else:continue
  commands.append(obj)
brakes=[c for c in commands if c.get('mode')==17 or c.get('command')==176 and c['params'][1]==17];assert len(brakes)==1;b=brakes[0];after=[c for c in commands if c['record']>b['record']and c['kind']=='RC'];assert len(after)==2;n,r=after;assert n['channels']==[1500]*4+[65535]*14 and r['channels']==[0]*8+[65534]*10
assert not any(c.get('mode')==9 or c.get('command')==21 for c in commands)
intent=[]
for c in[n,r]:
 v=tx[c['SHA256']];assert len(v)==1;entry=v[0];latest=[h for h in hb if h['record']<entry[0]][-1];assert latest['validType']and latest['armed']and latest['mode']==17 and b['record']<latest['record']and 0<=entry[1]-latest['guestNs']<=1500000000;intent.append({'cleanupIntent':entry[0],'cleanupWritten':entry[2],'latestCRCMode17Record':latest['record']})
assert len(auth['UP'])==1 and auth['UP'][0]['record']<b['record']and r['record']<auth['consents'][1]['record']
result={'status':'NATIVE_UP_BRAKE_NEUTRAL_RELEASE_REGRANT_CAUSAL_PREFIX_VERIFIED','brake':b,'cleanup':intent,'secondConsentRecord':auth['consents'][1]['record'],'distinctLeases':auth['consents'][0]['event']['leaseId']!=auth['consents'][1]['event']['leaseId'],'nativeUserLANDSent':False,'allOwnCRCFrameSource':'ExternallydeviceSHAmatchedcompleteclosednativejournal; noHost/guestabsolutetimecomparison','actualIntentionalLinkCut':False,'actualThirtyMinuteAccepted':False,'doesNotProveAirborneDurationOrPostFlightGround':True};(O/'native-cleanup.json').open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'])
