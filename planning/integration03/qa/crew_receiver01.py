"""Independent INTEGRATION03 identity/authority/wire evidence layer, offline only.

Draft: actual closed-run schema/pins must be checked after source freeze.
This layer does NOT replace mission/Home/upload/observer, TLS negatives or UI QA.
"""
import argparse,base64,collections,hashlib,importlib.util,json,math,pathlib,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[3]
BASE=ROOT/'evidence/operator01-qa/tools/receiver04.py'
BASE_SHA='a848da18ae5a84fadc7fc3a7effe991d93f0953fdd1eaa9196db89266df3f7f2'
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,why):
 if not v:raise ValueError(why)
def strict(raw):
 def pairs(xs):
  out={}
  for k,v in xs:
   need(k not in out,'duplicate JSON key');out[k]=v
  return out
 return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def load(p):return strict(pathlib.Path(p).read_bytes())
def utils():
 need(sha(BASE.read_bytes())==BASE_SHA,'frozen P1 raw primitive source changed')
 spec=importlib.util.spec_from_file_location('p1frozen_raw_primitives',BASE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def audit(path):
 raw=path.read_bytes();need(raw.endswith(b'\n'),'audit closed newline');head='';rows=[]
 for line in raw.splitlines():
  need(line,'empty audit line');r=strict(line);need(set(r)=={'n','previous','kind','dataBase64','sha256'},'strict audit envelope');need(type(r['n']) is int and r['n']==len(rows)+1 and r['previous']==head,'audit sequence/previous');body=f"{r['n']}\n{head}\n{r['kind']}\n{r['dataBase64']}".encode();need(sha(body)==r['sha256'],'audit SHA');b=base64.b64decode(r['dataBase64'],validate=True);r['_bytes']=b;r['_data']=strict(b);rows.append(r);head=r['sha256']
 return rows,head,sha(raw)
def peer(path):
 rows=[];head='';raw=path.read_bytes();need(raw.endswith(b'\n'),'peer closed newline')
 for line in raw.splitlines():
  r=strict(line);need(set(r)=={'raw','sha256'} and sha(r['raw'].encode())==r['sha256'],'B peer SHA');q=strict(r['raw'].encode());need(q['n']==len(rows)+1 and q['previous']==head,'B peer sequence/previous');rows.append(q);head=r['sha256']
 return rows,head,sha(raw)
def public_identity(native,policy):
 der=base64.b64decode(native['certDerBase64'],validate=True);need(sha(der)==native['certSha256'],'native certificate exact pin')
 def spki(cert):
  a=subprocess.run(['openssl','x509','-inform','DER','-pubkey','-noout'],input=cert,capture_output=True,timeout=5);need(a.returncode==0,'independent DER decode');b=subprocess.run(['openssl','pkey','-pubin','-outform','DER'],input=a.stdout,capture_output=True,timeout=5);need(b.returncode==0,'independent SPKI decode');return sha(b.stdout)
 need(spki(der)==native['spkiSha256']==policy['nativeSpkiSha256'],'native independent SPKI pin');bder=base64.b64decode(policy['peerCertDerBase64'],validate=True);need(sha(bder)==policy['peerCertSha256'] and spki(bder)==policy['peerSpkiSha256'],'B independent cert/SPKI pin');need(policy['peerPrincipal']=='payload-b' and policy['realm']=='rtr-crew02-test' and policy['aircraft']=='sitl-42','declared policy identity');return {'pilot-a':native['spkiSha256'],'payload-b':policy['peerSpkiSha256']}
def verify(run,pins,auditpath,peerpath,policy,native,case,sessionpaths=(),strictheldout=False,partitioncut=None):
 base=utils();m=base.oracle();rows,head,rawsha=base.chain(run/'android-raw.jsonl');need(rows[0]['kind']=='META' and rows[-1]['kind']=='CLOSED','closed native run');decode=lambda r:base64.b64decode(r['dataBase64'],validate=True);meta=strict(decode(rows[0]));need(meta['sourceId']==pins['sourceId'] and meta['ownedLaunchAssertion']['run']==run.name,'source/run pin');apk=pathlib.Path(pins['apkPath']);apk=apk if apk.is_absolute() else ROOT/apk;need(sha(apk.read_bytes())==pins['apkSha256'],'APK exact SHA');identities=public_identity(native,policy);ar,ah,ash=audit(auditpath);br=[];peer_evidence=[]
 for pp in peerpath:
  part,bh,bsh=peer(pp);br.extend(part);peer_evidence.append({'path':str(pp),'head':bh,'sha256':bsh,'records':len(part)})
 for spath in sessionpaths:
  probe=load(spath);need(probe['status']=='PASS_ACTUAL_MTLS_JOINED_SESSION_SCOPED' and probe['run']==run.name and probe['sourceId']==pins['sourceId'] and probe['sourceUnchanged'],'session probe pin/scope')
  need(probe['tls']['clientSpkiSha256']==policy['peerSpkiSha256'],'session probe B identity')
  for log in probe['logs']:
   if log['direction']=='REQUEST':br.append({'kind':'REQUEST','data':{'body':log['body'],'requestSha256':log['sha256'],'provenance':'QA_ACTUAL_MTLS_SESSION_PROBE'}})
  peer_evidence.append({'path':str(spath),'sha256':sha(pathlib.Path(spath).read_bytes()),'records':len(probe['logs']),'scope':'ACTUAL_MTLS_SESSION_PROBE_NOT_MAIN_OPERATOR_UI'})
 audit_bytes=collections.Counter((r['kind'],r['_bytes']) for r in ar);tls=[r['_data'] for r in ar if r['kind']=='TLS'];joins={};intents={};bind={};prepared={};approvals={};crewapprovals={};flightapprovals={};events=collections.defaultdict(list);out=[];laststate=None;authority=None;pending=None;reserve=None;seqs=[];accepted_b=[];capture_sequences={}
 for r in br:
  if r['kind']=='TLS':need(r['data']['authorized'] and r['data']['serverSpkiSha256']==identities['pilot-a'] and r['data']['peerCertSha256']==policy['peerCertSha256'],'B actual TLS peer record context')
  if r['kind']=='REQUEST':
   q=r['data']['body'];b=json.dumps(q,separators=(',',':'),ensure_ascii=False).encode();need(sha(b)==r['data']['requestSha256'],'B canonical request digest');intents.setdefault(r['data']['requestSha256'],{'peer':r['data']})
  if r['kind']=='RESPONSE' and r['data'].get('ok') and r['data'].get('nativeSelfLastPresenceAtMs') is not None:accepted_b.append(r['data'])
 for r in rows:
  kind=r['kind'];raw=decode(r);at=r['elapsedMs'];q=None
  if kind not in ('RX','TX_INTENT','TX_WRITTEN'):
   try:q=strict(raw)
   except Exception:q=None
  if kind.startswith('CREW_'):
   need(q is not None,'Crew raw must be JSON');events[kind].append((r,q))
   if kind not in ('CREW_FLIGHT_APPROVAL','CREW_WIRE_BINDING','CREW_WIRE_APPROVAL'):need(audit_bytes[(kind[5:],raw)]>0,'native Crew event missing exact external audit pair: '+kind)
  if kind=='CREW_JOIN':
   need(q['principal'] in identities and q['keyFingerprint']==identities[q['principal']] and q['grantsIssued']==0,'JOIN identity and zero grants');need(q['nativeGeneration']==meta.get('generation',q['nativeGeneration']),'JOIN generation');
   if q['principal']=='payload-b':need(any(t['session']==q['session'] and t['keyFingerprint']==q['keyFingerprint'] and t['clientAuthentication'] for t in tls),'joined B requires actual native TLS session evidence')
   joins[q['session']]=q
  elif kind=='CREW_INTENT':
   b=base64.b64decode(q['requestBase64'],validate=True);request=strict(b);need(sha(b)==q['requestSha256'],'native request digest');j=joins.get(q['session']);need(j and j['principal']==q['principal'] and j['keyFingerprint']==q['keyFingerprint'],'intent native admitted identity');need(request['serverBoot']==q['serverBoot'] and request['clientBoot']==q['clientBoot'] and request['session']==q['session'] and request['generation']==q['nativeGeneration'] and request['trustEpoch']==q['trustEpoch'] and request['seq']==q['seq'] and request['revision']==q['revision'] and request['operation']==q['operation'] and request['resource']==q['resource'] and request['acknowledge'] is True,'raw request exact native binding');need(type(q['seq']) is int and 1<=q['seq']<=10000,'safe sequence');
   prior=[x for x in intents.values() if x.get('native',{}).get('session')==q['session']];need(not prior or q['seq']>max(x['native']['seq'] for x in prior),'mutating sequence monotonic, heartbeat gaps permitted');entry=intents.setdefault(q['requestSha256'],{});entry.update(native=q,row=r,request=request)
   if q['principal']=='payload-b':need('peer' in entry and entry['peer']['body']==request,'B intent must match independent process request digest/body')
   if q['resource']=='aircraft':need(q['principal']=='pilot-a','B cannot aircraft scope')
  elif kind=='CREW_AUTHORITY_STATE':authority=(r,q)
  elif kind=='CREW_WIRE_BINDING':bind[q['id']]=(r,q,authority)
  elif kind=='CREW_WIRE_APPROVAL':crewapprovals[q['id']]=(r,q)
  elif kind=='CREW_FLIGHT_APPROVAL':flightapprovals[q['wireSha256']]=(r,q,authority)
  elif kind=='PAYLOAD_TX_BINDING':prepared[q['id']]=(r,q);need(sha(bytes.fromhex(q['preparedHex']))==q['preparedSha256'],'prepared exact hash')
  elif kind=='PAYLOAD_TX_APPROVAL':approvals[q['id']]=(r,q)
  elif kind=='PAYLOAD_STATE':
   laststate=q
   for t in q.get('transactions',[]):
    if t['operation'] in ('capture','zoom','focus','gimbal'):need(t['state'] in ('PREPARED_NOT_SENT','SENT_UNATTRIBUTED') or t['state'].startswith('UNKNOWN_'),'ACK/feedback must never promote repeated operation')
  elif kind=='TX_INTENT':
   need(pending is None,'unresolved TX_INTENT requires explicit suppression before next reservation');f=base.single(m,raw);s=f.get_seq();need(reserve is None or (s-reserve)%256==1,'global sequence across all reserved frames');reserve=s;seqs.append(s);pending=(r,raw,f)
  elif kind=='TX_WRITTEN':
   need(pending is not None and pending[1]==raw,'exact durable TX_INTENT to one written frame');pr,_,f=pending;pending=None;is_payload=f.get_msgId()==287 or f.get_msgId()==76 and getattr(f,'target_component',0) in (100,101,102,154)
   if not is_payload:
    mutation=f.get_msgId() in (44,73) or f.get_msgId()==76 and f.command in (176,400)
    if mutation:
     approval=flightapprovals.get(sha(raw));need(approval is not None,'aircraft mutation must have Crew after-WAL identity approval');fr,fq,fa=approval;j=joins.get(fq['session']);need(j and j['principal']=='pilot-a' and fq['principal']=='pilot-a' and fq['keyFingerprint']==identities['pilot-a'] and fq['scope']=='aircraft','aircraft native A identity/scope');need(fa is not None and fa[1]['aircraftOwner']==fq['session'],'explicit aircraft owner before flight mutation');need(fr['n']<r['n'] and 0<=fq['presenceAgeMs']<=3000,'fresh after-WAL flight approval')
    continue
   pb=next(((i,x) for i,x in prepared.items() if x[1]['wireSha256']==sha(raw)),None);need(pb is not None,'payload written binding');tid,pb=pb
   if f.get_msgId()==76 and f.command==512:continue
   need(tid in bind,'actuator requires Crew wire identity');_,binding,auth=bind[tid];entry=intents.get(binding['requestSha256']);need(entry and entry.get('native'),'Crew wire references admitted request');q=entry['native'];request=entry['request'];j=joins[binding['session']];need(binding['principal']==q['principal']==j['principal'] and binding['keyFingerprint']==identities[q['principal']] and binding['session']==q['session'],'wire cannot alias operator');need(auth is not None,'wire must follow authority state');_,state=auth;resource=request['resource'];payload=resource.split(':')[1];p=next(p for p in state['payloads'] if p['id']==payload);scope='gimbal' if resource.startswith('gimbal:') else 'camera';need(p[scope+'OwnerSid']==j['coreSid'] and p[scope+'Proposal'] is None,'independent current owner/no transfer freeze');op=request['operation'];need(f.target_system==42 and f.target_component==({'front':100,'center':102,'rear':101}[payload] if scope=='camera' else 154),'exact selected component route');need(pr['elapsedMs']<=r['elapsedMs'],'monotonic TX reservation')
   if op=='gimbal':need(f.get_msgId()==287 and f.gimbal_device_id=={'front':1,'center':2}[payload] and f.flags==32 and abs(f.pitch-math.radians(request['a']))<1e-6 and abs(f.yaw-math.radians(request['b']))<1e-6 and math.isnan(f.pitch_rate) and math.isnan(f.yaw_rate),'device/radian/frame/rate gimbal semantics')
   else:need(f.get_msgId()==76 and f.command=={'capture':2000,'zoom':531,'focus':532,'authority':1001}[op],'camera/manager command semantics')
   if op in ('zoom','focus'):need(f.param1==2 and f.param2==request['a'] and math.isnan(f.param4),'camera percent units')
   if op=='capture':
    need(f.param3==1 and 1<=f.param4<16777216 and f.param4.is_integer() and f.param4>capture_sequences.get(f.target_component,0),'single capture monotonic request sequence');capture_sequences[f.target_component]=f.param4
   if op=='authority':need(f.param1==255 and f.param2==190 and f.param3==0 and f.param4==0 and f.param5==0 and f.param6==0 and f.param7=={'front':1,'center':2}[payload],'explicit native manager primary identity/device contract')
   out.append({'id':tid,'row':r['n'],'principal':q['principal'],'session':q['session'],'resource':resource,'operation':op,'requestedA':request['a'],'requestedB':request['b'],'wireSha256':sha(raw),'component':f.target_component,'device':getattr(f,'gimbal_device_id',None)})
  elif kind=='TX_SUPPRESSED':
   need(pending is not None and q['wireSha256']==sha(pending[1]) and q['id'] in prepared and q['wireAttempted'] is False and q['retryAllowed'] is False,'exact proven prewrite suppression');pending=None
 need(pending is None,'closed run unresolved TX intent');need(laststate and laststate['phase']=='CLOSED' and all(not s['alive'] for s in laststate['stations']) and all(p.get('cameraOwnerSid') is None and p.get('gimbalOwnerSid') is None for p in laststate['payloads']),'closed authorities not restored')
 for x in out:
  need(x['id'] in approvals and approvals[x['id']][1]['ownerSid']==joins[x['session']]['coreSid'],'written operation owner approval receipt');need(x['id'] in crewapprovals,'Crew after-WAL approval receipt');cr,cq=crewapprovals[x['id']];need(cq['session']==x['session'] and cq['principal']==x['principal'] and cq['keyFingerprint']==identities[x['principal']] and 0<=cq['presenceAgeMs']<=3000 and 0<=cq['afterWalAtMs']-cq['lastPresenceAtMs']<=3000 and cr['n']<x['row'],'Crew after-WAL presence/identity binding')
 revokes=[];unjoined_expiries=[]
 for r,q in events['CREW_REVOKE']:
  if q['principal']=='payload-b' and q['session'] not in joins and q['reason']=='PRESENCE_EXPIRED':
   need(30000<q['ageMs']<=30250 and q['atMs']-q['lastPresenceAtMs']==q['ageMs'],'unjoined challenge absolute30s expiry bound');unjoined_expiries.append({'row':r['n'],**q})
  if q['principal']=='payload-b' and q['session'] in joins and q['reason'] in ('PRESENCE_EXPIRED','PEER_CHANNEL_CLOSED') and q['ageMs']>3000:
   need(q['ageMs']<=3250 and q['atMs']-q['lastPresenceAtMs']==q['ageMs'],'joined B native authority removal bound3000+250');revokes.append({'row':r['n'],**q})
 handovers=[];rejoins=[]
 if case in ('nominal','nominal-partition'):
  for tr,tq in events['CREW_AUTHORITY_STATE']:
   if tq['operation']!='transfer' or tq['resource']!='camera:front' or tq['principal']!='pilot-a':continue
   proposal=next(p for p in tq['payloads'] if p['id']=='front')['cameraProposal'];need(proposal is not None,'native transfer proposal');recipient=next((j for j in joins.values() if j['coreSid']==proposal['to']),None);source=joins[tq['session']];need(recipient and recipient['principal']=='payload-b' and proposal['from']==source['coreSid'],'two principal consent participants')
   for ar2,aq in events['CREW_AUTHORITY_STATE']:
    if ar2['n']<=tr['n'] or aq['operation']!='accept' or aq['resource']!='camera:front' or aq['session']!=recipient['session']:continue
    entry=next((e for e in intents.values() if e.get('native',{}).get('operation')=='accept' and e['native']['session']==recipient['session'] and e['request']['to']==proposal['id'] and tr['n']<e['row']['n']<ar2['n']),None);need(entry is not None and entry['row']['elapsedMs']<proposal['untilMs'],'current recipient explicit consent to exact proposal before expiry');ap=next(p for p in aq['payloads'] if p['id']=='front');need(ap['cameraOwnerSid']==recipient['coreSid'] and ap['cameraProposal'] is None,'accepted scope owner');written=next((e for e in out if e['row']>ar2['n'] and e['session']==recipient['session'] and e['resource']=='camera:front' and e['operation'] in ('capture','zoom','focus')),None);need(written is not None,'new owner explicit camera operation after consent');handovers.append({'proposalRow':tr['n'],'acceptRow':ar2['n'],'newOwnerOperationRow':written['row'],'newOwnerOperation':written['operation'],'from':source['session'],'to':recipient['session']});break
  need(handovers,'actual A-to-B camera consent and later capture')
  need(any(e['operation']=='gimbal' and e['device'] in (1,2) for e in out),'C06 explicit gimbal device1 or2 route')
 if case in ('partition','nominal-partition'):
  need(revokes,'actual B partition native expiry bound')
  for rev in revokes:
   later=[(r,j) for r,j in events['CREW_JOIN'] if r['n']>rev['row'] and j['principal']=='payload-b' and j['session']!=rev['session']]
   if not later:continue
   jr,j=later[0];need(j['grantsIssued']==0,'fresh rejoin cannot restore authority');old=joins[rev['session']];need(j['clientBoot']!=old['clientBoot'] and j['coreSid']!=old['coreSid'],'fresh B boot/native session/core station')
   denied=[]
   for rr,rq in events['CREW_REJECTED']:
    ep=intents.get(rq['requestSha256']);body=ep.get('peer',{}).get('body',{}) if ep else {}
    if rr['n']>jr['n'] and rq['session']==j['session'] and body.get('operation')=='capture' and 'OWNER' in rq['reason']:denied.append(rr['n'])
   claims=[e for e in intents.values() if e.get('native',{}).get('session')==j['session'] and e['native']['operation']=='claim'];written=[e for e in out if e['session']==j['session'] and e['operation']=='capture'];need(denied and claims and written and min(denied)<min(e['row']['n'] for e in claims)<min(e['row'] for e in written),'fresh B denied before explicit reclaim/new capture');rejoins.append({'revokeRow':rev['row'],'joinRow':jr['n'],'deniedRows':denied,'newCaptureRows':[e['row'] for e in written]})
  need(rejoins,'explicit B newboot no grant and reclaim after partition')
 if case=='pilot-loss':need(any(q['principal']=='pilot-a' and ('BACKGROUND' in q['reason'] or 'PILOT' in q['reason']) for _,q in events['CREW_REVOKE']),'actual A loss before common close')
 if strictheldout:
  need(case in ('nominal','nominal-partition'),'strict heldout only final nominal')
  corpuspath=ROOT/'evidence/integration03-qa/heldout-corpus01.json';need(sha(corpuspath.read_bytes())=='c6aa625a315d210084bd7f33265976a52c6e7d06142e3c24b9b755d91710a493','frozen unseen corpus');angles=load(corpuspath)['inputs']['crew']['gimbalAnglesDeg']
  need(any(e['principal']=='pilot-a' and e['operation']=='gimbal' and e['device']==1 and e['requestedA']==angles[0] and e['requestedB']==angles[1] for e in out),'frozen stronger A device1 angle actual wire')
  need(any(e['principal']=='payload-b' and e['operation']=='gimbal' and e['device']==2 and e['requestedA']==angles[0] and e['requestedB']==angles[1] for e in out),'frozen stronger B device2 angle actual wire')
  need({100,101,102}<={e['component'] for e in out if e['operation'] in ('capture','zoom','focus')},'front/center/rear actual camera target proof')
  for h in handovers:
   need(any(e['principal']=='payload-b' and e['operation']=='capture' and e['resource']=='camera:front' and e['session']==h['to'] and e['row']>h['acceptRow'] for e in out),'frozen stronger recipient front capture same accepted session')
 partitionproof=None
 if case in ('partition','nominal-partition'):
  need(partitioncut is not None,'partition requires predeclared actual cut receipt');cut=load(partitioncut);before=cut['beforeState'];state=before['state'];selfq=state['self'];need(before['connected'] and before['authenticated'] and before['responseAgeMs']<1500 and state['open'] and state['apFresh'] and state['apArmedKnown'] and state['apArmed'],'fresh airborne joined B at cut');station=next(s for s in state['stations'] if s['session']==selfq['session']);need(station['alive'] and station['joined'] and selfq['principal']=='payload-b' and selfq['clientBoot']==cut['boot'],'B cut exact live identity');need(any(q.get('session')==selfq['session'] and q.get('nativeSnapshotAtMs')==state['snapshotAtMs'] and q.get('nativeSelfSeq')==selfq['lastSeq'] and q.get('nativeSelfLastPresenceAtMs')==station['lastPresenceAtMs'] for q in accepted_b),'cut native tuple backed by independent B response chain');pendingtx=[t for t in state['transactions'] if t['ownerSid']==station['coreSid'] and t['operation']=='capture' and t['state']=='SENT_UNATTRIBUTED'];need(pendingtx,'pending B capture must exist before partition');live=[p for p in state['payloads'] if p.get('cameraOwnerSid')==station['coreSid'] and p.get('leaseUntilMs',0)>state['snapshotAtMs']];need(live,'B camera lease active at cut');rev=next((x for x in revokes if x['session']==selfq['session'] and x['atMs']>=state['snapshotAtMs']),None);need(rev and rev['atMs']<max(p['leaseUntilMs'] for p in live),'B expiry before lease naturally ends');post=[(r,q) for r,q in events['PAYLOAD_STATE'] if r['n']>rev['row'] and q['phase']=='OPEN'];need(post,'A/common link remains OPEN after B-only expiry');unknown={t['id'] for _,q in post for t in q.get('transactions',[]) if t['state'].startswith('UNKNOWN_')};need(all(t['id'] in unknown for t in pendingtx),'exact pending intents UNKNOWN after B loss');need(any(s.get('alive') and s.get('actor')=='pilot-a' and s.get('sid')!=station['coreSid'] for _,q in post for s in q.get('stations',[])),'A core station remains alive');partitionproof={'cutPath':str(partitioncut),'sha256':sha(pathlib.Path(partitioncut).read_bytes()),'session':selfq['session'],'nativeCutSnapshotAtMs':state['snapshotAtMs'],'nativeLastPresenceAtMs':station['lastPresenceAtMs'],'nativeRevokeAtMs':rev['atMs'],'pendingCaptureIds':[t['id'] for t in pendingtx],'revocationAgeMs':rev['ageMs']}
 result={'status':'PASS_CREW_LAYER_ONLY','case':case,'strictHeldoutActual':strictheldout,'run':run.name,'native':{'records':len(rows),'head':head,'sha256':rawsha},'externalAudit':{'head':ah,'sha256':ash,'records':len(ar)},'independentBPeer':{'files':peer_evidence,'records':len(br),'nativeClockResponses':len(accepted_b)},'sourceId':meta['sourceId'],'apkSha256':pins['apkSha256'],'operations':out,'BPresenceRevokes':revokes,'partitionProof':partitionproof,'unjoinedChallengeExpiries':unjoined_expiries,'expiryCauseQualification':'Joined socket reader current() and 100ms sweep race; PEER_CHANNEL_CLOSED may win after current() refuses expired presence. Authority removal timing is native tuple; this layer does not infer OS SIGSTOP cause from revoke label.','consentHandovers':handovers,'explicitRejoins':rejoins,'actualImages':0,'physicalExecutionProven':False,'gimbalDevice1AngleObserved':any(e['operation']=='gimbal' and e['device']==1 for e in out),'NOT_PROVED_BY_THIS_LAYER':['actual negative TLS trials','actual UI usability/receipt expiry','mission/Home/readback/navigation/ground and AP failsafe','process/coldboot/SAF/protected SHA'],'humanReview':False}
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=pathlib.Path);p.add_argument('--pins',required=True,type=pathlib.Path);p.add_argument('--crew-audit',required=True,type=pathlib.Path);p.add_argument('--peer',required=True,type=pathlib.Path,action='append');p.add_argument('--policy',required=True,type=pathlib.Path);p.add_argument('--native-public',required=True,type=pathlib.Path);p.add_argument('--session-probe',type=pathlib.Path,action='append',default=[]);p.add_argument('--case',choices=['nominal','nominal-partition','partition','pilot-loss'],required=True);p.add_argument('--output',required=True,type=pathlib.Path);p.add_argument('--strict-heldout',action='store_true');p.add_argument('--partition-cut',type=pathlib.Path);a=p.parse_args()
 try:result=verify(a.run,load(a.pins),a.crew_audit,a.peer,load(a.policy),load(a.native_public),a.case,a.session_probe,a.strict_heldout,a.partition_cut);code=0
 except Exception as e:result={'status':'FAIL_OR_SCHEMA_UNSUPPORTED','errorType':type(e).__name__,'error':str(e),'run':str(a.run),'actualImages':0,'physicalExecutionProven':False};code=1
 result.update(receiverSHA256=sha(pathlib.Path(__file__).read_bytes()),frozenP1UtilitiesSHA256=sha(BASE.read_bytes()),executionClass='OFFLINE_CREW_LAYER_NOT_FULL_MILESTONE')
 with a.output.open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
 print(json.dumps({'status':result['status'],'output':str(a.output),'error':result.get('error')},ensure_ascii=False));return code
if __name__=='__main__':raise SystemExit(main())
