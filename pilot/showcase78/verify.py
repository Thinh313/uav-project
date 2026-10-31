"""Read-only oracle receipts + raw SHA and preservation; write new showcase receipt only."""
import datetime,hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=R/'evidence/showcase78';rid='rad3ab2ece4a54e38a4ba';run=R/'evidence/simtrain53/runs'/rid
def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,d):
 with(E/name).open('x')as f:json.dump(d,f,indent=2,ensure_ascii=False);f.write('\n')
assert shutil.disk_usage(R).free>=20*2**30
readback=json.loads((run/'readback.json').read_text());closure=json.loads((run/'closure.json').read_text());launch=json.loads((run/'launch.json').read_text())
assert readback['status']=='PASS_RAW_CAPTURE_ORIGINAL_ORACLE_AND_CORRELATION'
assert readback['frames']==readback['exactOriginalSensorAndAuxFrames']==readback['actualAPReceiveParseFrames']==134632
assert readback['rateHz']==1200 and readback['speedup']==1 and readback['capUs']==500000
assert readback['takeoffAndLandPhysicalObservations'] and closure['backendExited'] and closure['backendExitCode']==0 and closure['ownedContainerStopped'] and closure['error'] is None
raw={n:{'expected':h,'actual':digest(run/n)}for n,h in readback['filesSha256'].items()};assert all(v['expected']==v['actual']for v in raw.values())
events=[json.loads(l)for l in(run/'mavlink.jsonl').open()];rc=[e for e in events if e['kind']=='RC_TX_INTENT' and e['data']['channels'][:4] not in [[1500]*4,[0]*4]]
assert len(rc)==readback['manualNonNeutralRCFrames']==83
channels={tuple(e['data']['channels'][:4])for e in rc}
assert {(1500,1200,1500,1500),(1500,1800,1500,1500),(1800,1500,1500,1500),(1500,1500,1500,1800)}<=channels
arms=[e for e in events if e['kind']=='GCS_TX_REQUEST' and e['data']['id']==76 and e['data']['fields']['command']==400 and e['data']['fields']['param1']==1]
assert len(arms)==1 and arms[0]['data']['fields']['param2']==0
for x in json.loads((R/'pilot/visual56/assets/replay-index.json').read_text()):assert digest(R/'pilot/visual56/assets'/x['file'])==x['sha256']
mock=json.loads((E/'input-mock.json').read_text());assert mock['scope']=='MOCK_DOM_ONLY_NO_AP_NO_PHYSICS';held=set()
for e in mock['events']:
 if e['type']=='keydown':held.add(e['code'])
 else:held.discard(e['code'])
assert not held and mock['button']=='Chạy bài điều khiển · 12 s' and 'Dừng bài điều khiển' in mock['status']
semantic=json.loads((E/'qgc-semantic.json').read_text());assert semantic['verdict']=='DIFFERENT' and semantic['differenceCount']==1 and semantic['uploaded'] is False
base=json.loads((R/'evidence/key74/preservation-before.json').read_text());pins={**base['files'],**base['live72Snapshot']}
for name in ['evidence/key74/artifact-manifest.json','evidence/simfeedback75/artifact-manifest.json','evidence/simsitl76/artifact-manifest.json','evidence/simdrop77/artifact-manifest.json']:
 p=R/name;pins.update(json.loads(p.read_text())['files']);pins[name]=digest(p)
for name in ['evidence/simsitl76/handoff-check.json','evidence/simdrop77/handoff-check.json','delivery/COMPLETION-SIMDROP77-VERIFIED.md']:pins[name]=digest(R/name)
bad=[]
for name,value in pins.items():
 try:
  expected=value['sha256']if isinstance(value,dict)else value
  if digest(R/name)!=expected:bad.append({'path':name,'status':'CHANGED'})
 except OSError:bad.append({'path':name,'status':'MISSING'})
preservation={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked':len(pins),'failures':bad,'scope':'Point-in-time existing SHA maps; manifest files observed now, not an independently pre-pinned root or continuous-presence/ENDURE acceptance claim'}
save('preservation-after.json',preservation);assert not bad
result={'status':'PASS_SCOPED_SCRIPTED_LIVE_E2E_AND_RAW_READBACK','run':rid,'raw':raw,'frames':readback['frames'],'nonNeutralRCIntentFrames':len(rc),'normalArmRequests':len(arms),'channelPatterns':[list(x)for x in sorted(channels)],'rateHz':1200,'speedup':1,'capUs':500000,'activeReceiveRTF':readback['activeReceiveRTF'],'minimumFiveSecondRTF':min(w['RTF']for w in readback['fiveSecondWindows']),'stable1xAccepted':False,'actualImages':0,'physicalHeraHub':False,'acousticListening':'NOT_CHECKED','projectorHardware':'NOT_CHECKED','manualPointerLive':'NOT_CHECKED_POINTER_MOCK_ONLY','frozenChecked':len(pins),'freeGiB':shutil.disk_usage(R).free/2**30,'sourcePins':{str(p.relative_to(R)):digest(p)for p in [R/'pilot/showcase78/controls.mjs',R/'pilot/aeris57/ui.mjs',R/'pilot/aeris57/server.mjs',R/'pilot/simtrain53/runtime.py',R/'pilot/simtrain53/link.mjs',R/'pilot/simtrain53/backend.py']},'readbackSha256':digest(run/'readback.json'),'closureSha256':digest(run/'closure.json'),'scope':'Single-agent verification; uses original-model oracle receipt and re-reads raw SHA. No independent reviewer, Hera, stable1x or full product claim.'}
save('verification.json',result);print(json.dumps({k:result[k]for k in ['status','run','frames','activeReceiveRTF','minimumFiveSecondRTF','frozenChecked','freeGiB']}))
