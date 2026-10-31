from pathlib import Path
import json,datetime,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/workbench01';rows=json.loads((E/'browser-layout03.json').read_text());assert len(rows)==32
for r in rows:
 assert not r['overflow'] and not r['tinyButtons'],r
 b=r['bounds'];assert abs(b['.brand']['x']-b['footer>div']['x'])<.1,r
 l=b['.left-rail'];q=b['.right-rail'];assert abs(l['y']+l['h']/2-q['y']-q['h']/2)<.1,r
 assert l['y']>=60 and q['y']>=60,r
 if r['viewport']['w']>700:
  assert b['#panel']['y']+b['#panel']['h']<b['footer']['y'],r
  assert b['#panel']['x']+b['#panel']['w']<q['x'],r
 else:assert b['#panel']['y']>=l['y']+l['h'],r
 assert r['titleColor']==('rgb(21, 34, 29)' if r['theme']=='day' else 'rgb(244, 246, 245)'),r
dialogs=json.loads((E/'dialog-layout01.json').read_text())+json.loads((E/'dialog-refly02.json').read_text())['rows']
for d in dialogs:
 assert d['x']>=0 and d['y']>=0 and d['x']+d['w']<=d['viewport']['w']+.2 and d['y']+d['h']<=d['viewport']['h']+.2,d
result={'dialogsChecked':len(dialogs),'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','combinations':32,'viewports':4,'themes':2,'screens':4,'assertions':['No horizontal overflow','All visible buttons >=48 CSS px','Telemetry first text aligned to logo within 0.1px','Detached rails same Y center within 0.1px','Panel/footer/rail separation','Day/night title colors follow body tokens'],'limits':['Not a pixel-by-pixel guarantee','Native dp/touch hardware NOT_CHECKED','No sunlight or video-background contrast measurement']};(E/(sys.argv[1] if len(sys.argv)>1 else 'layout-verification02.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
