from pathlib import Path
import json
E=Path(__file__).resolve().parents[2]/'evidence/native88';rows=[json.loads(x)for x in(E/'android88-measured-ui800.jsonl').read_text().splitlines()];r=[x['renderer']for x in rows];coverage=set((x['viewport']['height'],x['theme'],x['view'])for x in r)
for height in[640,800]:
 for theme in['day','night']:
  for view in['plan','preflight','fly','review']:assert(height,theme,view)in coverage
checks=0;checkboxes=set()
for x in r:
 b=x['boxes'];ph=b.get('.pane-heading');sc=b.get('.pane-scroll');f=b.get('.pane-action')
 if b.get('#task-pane')and ph and sc and f:assert ph['bottom']<=sc['y']+.5 and sc['bottom']<=f['y']+.5;checks+=1
 if x['view']in['fly','review']:assert b.get('#task-pane')is None
 if x['alignmentDelta']is not None:assert x['alignmentDelta']<=.5
 if b.get('.navrail')and b.get('.camera-tools'):
  a=b['.navrail'];z=b['.camera-tools'];assert abs(a['y']+a['height']/2-z['y']-z['height']/2)<=.5
 assert x['themeIcon']==('#i-sun'if x['theme']=='day'else'#i-moon')
 for c in x['controls']:
  if x['panel']=='#task-pane'and c['inPanel']:
   assert c['inOwnViewport'];assert not c['covered'];
   if c['id'].startswith('confirm-'):checkboxes.add(c['id'])
assert checkboxes=={'confirm-home','confirm-height','confirm-route'}
out={'status':'PASS','selectedRendererSnapshots':len(r),'coverage':[list(x)for x in sorted(coverage)],'ownedGridRowChecks':checks,'checkboxes':sorted(checkboxes),'logoTelemetryGutterMaxCssPx':max(x['alignmentDelta']or 0 for x in r),'hiddenTaskPaneRespected':True,'themeIconMatches':True,'scope':'Actual owned Android33 WebView101 self-reported rectangles plus retained screenshots; sampled states, not exhaustive pixel/FPS/hardware qualification','notes':['Some screenshot filename labels reflect requested theme around resize; actual renderer state determines coverage.','Diagnostic log reached admission bound and was retained by exact-SHA rotation; mission journals unchanged.']}
(E/'ui-verification.json').open('x').write(json.dumps(out,indent=2));print(json.dumps(out))
