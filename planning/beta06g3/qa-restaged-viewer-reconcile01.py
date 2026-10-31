"""Independent read-only ground video-start reconciliation; never dispatches input."""
from pathlib import Path
import json,hashlib,re,datetime,os
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation03'
def sha(b):return hashlib.sha256(b).hexdigest()
def rd(p):return json.loads(p.read_text())
def snap(p):
 b=p.read_bytes();return b,{'path':str(p.relative_to(R)),'bytes':len(b),'sha256':sha(b),'classification':'READ_ONLY_CAPTURED_PREFIX_AT_QA_REVIEW'if p.suffix=='.jsonl'else'RETAINED_ROOT_ARTIFACT'}
def chain(path):
 b,info=snap(path);assert b.endswith(b'\n');head='0'*64;last=-1;rows=[]
 for line in b.splitlines():
  r=json.loads(line);assert r['seq']==len(rows)+1 and r['previousSha256']==head;assert r['hostMonoMs']>=last
  exact=re.sub(rb',"sha256":"[a-f0-9]{64}"}$',b'}',line);assert sha(exact)==r['sha256'];head=r['sha256'];last=r['hostMonoMs'];rows.append(r)
 info.update(records=len(rows),head=head);return rows,info
inputs={};names=['root-restaged-viewer-reconcile01.json','g3-viewer-start-restaged-intent.json','g3-viewer-restaged-reference.json','root-controller04.jsonl','qa-adb-commands.jsonl']
for n in names:_,inputs[n]=snap(E/n)
root=rd(E/names[0]);intent=rd(E/names[1]);reference=rd(E/names[2]);before=intent['observation']['observation'];after=root['observation']['observation'];ref=reference['observed']['observation'];receipt=after['receipt'];expectedID='708f6013-ad60-4844-a74c-0e17599e852c';old='f0d3cf28-0cc6-4715-9e48-1d25841fa916';new='6013920a-4699-406b-bc86-a5eddcbf2d76'
assert intent['id']=='video-start'and intent['status']=='ONE_VISIBLE_DISPATCH_INTENT'and intent['noAutomaticRetry']is True
for label,path,wanted in [('before',Path(intent['screenshot']),intent['screenshotSha256']),('reference',Path(reference['image']),reference['imageSha256'])]:
 b,info=snap(path);assert sha(b)==wanted;inputs[label+'-screenshot']=info
keys=['documentId','clientId','clientEpoch','clientInstance','modelSha256','planSha256','viewport','tab','run','boot','payloadSelection']
assert all(before[k]==ref[k]==after[k]for k in keys)
assert before['configId']==ref['configId']==old and after['configId']==new
assert before['run']is None and before['boot']is None and before['phase']==after['phase']=='IDLE'
assert receipt['id']==expectedID and receipt['id']!=before['receipt']['id']and receipt['targetId']=='video-start'and receipt['status']=='ACKNOWLEDGED'
for k in ['documentId','clientId','clientEpoch','clientInstance','modelSha256','planSha256','run','boot']:assert receipt[k]==before[k]
assert receipt['startedAtClientMonoMs']>=before['observedAtClientMonoMs']and receipt['completedAtClientMonoMs']>=receipt['startedAtClientMonoMs']
ui,inputs['ui-wal']=chain(E/'host-app03/ui-diagnostics/overlap-events.jsonl');wal,inputs['host-wal']=chain(E/'host-app03/overlap-events.jsonl');clock,inputs['clock-wal']=chain(E/'host-app03/media/clock-events.jsonl')
matched=[r for r in ui if (r['data'].get('receipt')or{}).get('id')==expectedID];assert [r['data']['receipt']['status']for r in matched]==['DISPATCHED','ACKNOWLEDGED','ACKNOWLEDGED'];assert [r['data']['configId']for r in matched]==[old,None,new]
assert matched[0]['hostMonoMs']<matched[1]['hostMonoMs']<matched[2]['hostMonoMs']
for r in matched:
 for k in keys:assert r['data'][k]==before[k]
 assert r['data']['receipt']['targetId']=='video-start'
assert matched[-1]['data']['mediaReadiness']['previewReady']is True
assert all(r['data'].get('run')is None and r['data'].get('boot')is None for r in ui)
assert not any(r['kind']=='ACTION_BEGIN'and r['data'].get('route')=='flight'for r in wal)
assert not list((E/'flight/runs').iterdir()),'NEW_AP_REQUEST_FOUND'
s=root['state'];assert s['flight']['run']is None and s['flight']['authority']is None and s['flight']['request']['boot']is None and s['payloadLeaseObservation']['leaseCount']==0 and not s['payloadLeaseObservation']['leases']and s['transportDiagnostics']is None
assert s['client']['id']==after['clientId']and s['client']['epoch']==after['clientEpoch']and s['client']['instance']==after['clientInstance']
media=root['media']['result'];assert media['session']['configId']==new and media['session']['profileId']=='VP8-720P30-V1'and media['session']['feed']=='rgb'
sourceEvents=[r for r in clock if r['kind']=='SOURCE_MAPPING_APPLIED'and r['data'].get('configId')==new];assert sourceEvents and sourceEvents[0]['hostMonoMs']<matched[0]['hostMonoMs']
m=after['mediaReadiness'];assert m['active']and m['previewReady']and m['clockStatus']=='CALIBRATED_BOUNDS'and m['clockDegraded']is False and 0<=m['frameAgeMs']<=1000
assert m['clockMappingSampledBrowserMs']<=after['observedAtClientMonoMs']<m['clockMappingValidUntilBrowserMs']and abs(m['clockMappingValidUntilBrowserMs']-m['clockMappingSampledBrowserMs']-60000)<.001
adb=[json.loads(l)for l in(E/'qa-adb-commands.jsonl').read_text().splitlines()];screen=next(i for i,r in enumerate(adb)if r.get('stdoutSha256')==intent['screenshotSha256']and r['args']==['exec-out','screencap','-p']);taps=[r for r in adb[screen+1:]if r['args'][:3]==['shell','input','tap']];assert len(taps)==1 and taps[0]['exit']==0
# Match the expected native point from the actual reference geometry, without running any UI helper.
target=next(t for t in before['targets']if t['id']=='video-start');rect=target['rect'];mapping=reference['nativeMapping'];x,y,w,h=mapping['frame'];point=[round(x+(rect['x']+rect['width']/2)*mapping['scaleX']),round(y+(rect['y']+rect['height']/2)*mapping['scaleY'])];assert list(map(int,taps[0]['args'][-2:]))==point
controller=[json.loads(l)for l in(E/'root-controller04.jsonl').read_text().splitlines()];assert len([r for r in controller if r.get('event')=='EXPLICIT_COMMAND'and r.get('commandId')=='g3-viewer-start-restaged'])==1
pins=rd(E/'flight-pins.json');drift=[p for p,h in pins['files'].items()if sha((R/p).read_bytes())!=h];assert not drift
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_RESOLVED_GROUND_VIDEO_START_CONFIG_TRANSITION_NO_REINPUT','classification':'READONLY_ACTUAL_ANDROID_UI_RECEIPT_AND_PERSISTED_WAL_REPLAY','inputResolution':'RESOLVED_ACKNOWLEDGED_VIDEO_START_GROUND_ONLY','inputs':inputs,'binding':{k:after[k]for k in keys},'transition':{'oldConfig':old,'intermediateConfig':None,'newConfig':new,'receiptId':expectedID,'target':'video-start','statuses':[(r['seq'],r['data']['seq'],r['data']['receipt']['status'],r['data']['configId'])for r in matched],'receiptStartedAtClientMonoMs':receipt['startedAtClientMonoMs'],'receiptCompletedAtClientMonoMs':receipt['completedAtClientMonoMs'],'sourceMappingFirstHostMonoMs':sourceEvents[0]['hostMonoMs'],'dispatchWALHostMonoMs':matched[0]['hostMonoMs'],'oneActualTapAfterMatchedScreenshot':{'point':point,'at':taps[0]['at'],'exit':0},'reasonHelperStopped':'Frozen helper rejects any posttap config change. This ground video-start intentionally reset old viewer config then adopted the explicitly restaged publisher config; separately retained exact matching terminal receipt resolves the input without bypassing flight guards.'},'currentCollectedPoint':{'mediaReadiness':m,'sourceSession':media['session'],'run':None,'boot':None,'flightAuthority':None,'leaseCount':0,'newAPRequests':0},'preservation':{'frozenPins':len(pins['files']),'manifestSHA256':sha((E/'flight-pins.json').read_bytes()),'differences':drift},'disposition':'RESOLVED_INPUT_NO_REINPUT. Root must obtain a fresh full75s current-config ground gate with two periodic renewals per role before any Connect; original host/AP/deadlines/quota/arming rules unchanged. Do not pool Chrome source FPS with new IAB cohort.','limits':['No new runtime actions or helper edits by QA.','This reconciliation is a ground media input acknowledgement plus fresh-point observation, not75s admission, FPS/latency acceptance, flight or payload execution.','The unique one-tap evidence is scoped to retained adb prefix after exact matched before screenshot, corroborated by controller command and unique persisted receipt.','Source browser/IAB cohort rests on Root UI evidence and decision; protocol WAL alone does not identify a browser process.']}
out=E/'qa-restaged-viewer-reconcile01.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'sha256':sha(out.read_bytes()),'WALSeqs':[r['seq']for r in matched],'inputPoint':point,'pins':len(pins['files'])}))
