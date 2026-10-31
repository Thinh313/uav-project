from pathlib import Path
import json
h=Path('evidence/missionbeta01/launches/20261025T190658Z-3e11db24/host');run='s2e2c548222f5419788da';quality=json.load((h/('auto-video-qualification-'+run+'.json')).open());samples=[];requests=[]
for p in sorted((h/'media').glob('report-*.json')):
 q=json.load(p.open());requests+=q['transportDiagnostics']['latest128']
 for s in q['samples']:
  lo=s['latencyLowerMs']+s['sourceHostBounds']['upperMs'];hi=s['latencyUpperMs']+s['sourceHostBounds']['lowerMs'];samples.append((s,lo,hi,p.name))
near=[s for s in samples if s[2]>=quality['startHostMs']-250 and s[1]<=quality['endHostMs']+250];findings=[]
for a,b in zip(near,near[1:]):
 gap=b[2]-a[1]
 if gap<=250:continue
 x,y=a[0],b[0];overlap=[r for r in requests if r['startBrowserMs']<=y['displayBrowserMs'] and r['bodyBrowserMs']>=x['displayBrowserMs']];seen=set();overlap=[r for r in overlap if (key:=(r['route'],r['startBrowserMs']))not in seen and not seen.add(key)]
 findings.append({'reports':[a[3],b[3]],'frames':[x['frameId'],y['frameId']],'conservativeDisplayGapMs':gap,'displayGapMs':y['displayBrowserMs']-x['displayBrowserMs'],'sourceTimestampStepMs':(y['sourceTimestampUs']-x['sourceTimestampUs'])/1000,'relayReceiptStepMs':y['pipeline'][0]-x['pipeline'][0],'decodeDurationMs':[x['decodeMs'],y['decodeMs']],'decodeStartHostBounds':[x['pipeline'][1:],y['pipeline'][1:]],'retainedHttpOverlaps':overlap,'httpTraceCoverage':'LATEST128_PER_WINDOW_ONLY_NOT_FULL_INTERVAL','causality':'NOT_ISOLATED_NO_SINGLE_ROOT_CAUSE_CLAIM'})
out={'status':'DIAGNOSED_MULTISTAGE_GAPS_NOT_FIXED','run':run,'actualAndroidSITL':True,'originalQualityStatus':quality['status'],'thresholdMs':250,'findings':findings,'nextMeasurement':'Full bounded source/HTTP/decode/UI event-loop and durable-writer spans; independent clocks; no relaxed gate or frame omission'};Path('evidence/missionbeta01/gap-analysis07.json').open('x').write(json.dumps(out,indent=2));print('GAPS',len(findings),'MAX',max(f['conservativeDisplayGapMs']for f in findings))
