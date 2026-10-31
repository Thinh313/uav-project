"""Bounded public primary-source HTML capture; no scripts, credentials or app writes."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from html.parser import HTMLParser
import datetime,json,hashlib,shutil,concurrent.futures
R=Path(__file__).resolve().parents[2]; D=R/'research/gcs34'; S=D/'snapshots'
SOURCES=[
 ('dji-m4','https://enterprise.dji.com/matrice-4-series','Manufacturer capability claim'),
 ('dji-fh2','https://enterprise.dji.com/flighthub-2','Manufacturer capability claim'),
 ('dji-geo-new','https://www.dji.com/media-center/announcements/dji-expands-geo-system-update-to-remaining','Dated manufacturer rollout announcement,2025-11-17'),
 ('dji-geo-legacy','https://www.dji.com/flysafe/introduction','Legacy product-scoped page; not evidence of current all-product behavior'),
 ('ap-auto','https://ardupilot.org/copter/docs/auto-mode.html','Current docs, not pinned Hera firmware evidence'),
 ('ap-fence','https://ardupilot.org/copter/docs/common-geofencing-landing-page.html','Current docs, firmware-dependent'),
 ('ap-gcs-failsafe','https://ardupilot.org/copter/docs/gcs-failsafe.html','Current docs, configured autopilot policy'),
 ('ap-avoidance','https://ardupilot.org/copter/docs/common-oa-bendyruler.html','Sensor/mode/firmware-dependent'),
 ('ap-terrain','https://ardupilot.org/copter/docs/terrain-following.html','Terrain data does not detect small obstacles'),
 ('qgc-plan','https://docs.qgroundcontrol.com/Stable_V5.1/en/qgc-user-guide/plan_view/plan_view.html','Version-scoped documentation, capability-dependent'),
 ('qgc-fly','https://docs.qgroundcontrol.com/Stable_V5.1/en/qgc-user-guide/fly_view/fly_view.html','Version-scoped documentation, capability-dependent'),
 ('skydio-x10','https://www.skydio.com/x10/faqs','Manufacturer claim, not independent performance benchmark'),
 ('skydio-autonomy','https://www.skydio.com/skydio-autonomy','Mixed model ecosystem; no universal all-model inference'),
 ('android-touch','https://developer.android.com/guide/topics/ui/accessibility/views/apps-views','General Android recommendation, not glove-tested Hera UX'),
 ('nasa-interface','https://www.nasa.gov/reference/10-0-crew-interfaces-vol-2/','Human-spaceflight guidance used by analogy, not UAV certification'),
 ('vn-airspace','https://xaydungchinhsach.chinhphu.vn/huong-dan-thuc-hien-thu-tuc-cap-phep-bay-doi-voi-tau-bay-khong-nguoi-lai-va-cac-phuong-tien-bay-khac-119250616123043064.htm','Government publication directing official map; no live map ingestion verified'),
 ('rtr-public','https://www.rtrobotics.com/','Public manufacturer claims; not actual Ragas binary test'),
]
class Text(HTMLParser):
 def __init__(self):super().__init__();self.ignore=0;self.parts=[];self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.ignore+=1
  if tag=='a':
   d=dict(attrs)
   if d.get('href'):self.links.append(d['href'])
 def handle_endtag(self,tag):
  if tag in ('script','style') and self.ignore:self.ignore-=1
 def handle_data(self,s):
  if not self.ignore and s.strip():self.parts.append(s.strip())
def fetch(source):
 name,url,scope=source;p=S/(name+'.html')
 assert not p.exists(), 'No overwriting captured snapshots'
 try:
  if shutil.disk_usage(R).free<20*1024**3+128*1024**2:raise RuntimeError('Disk floor + capture budget')
  request=Request(url,headers={'User-Agent':'Mozilla/5.0 AERIS-Research/1.0','Accept':'text/html'})
  with urlopen(request,timeout=25) as response:
   body=response.read(4*1024**2+1); final=response.url; kind=response.headers.get('Content-Type',''); charset=response.headers.get_content_charset() or 'utf-8'
  if len(body)>4*1024**2 or 'text/html' not in kind:raise RuntimeError('HTML type/size gate')
  if urlparse(final).hostname!=urlparse(url).hostname and not (urlparse(final).hostname or '').endswith('.dji.com'):raise RuntimeError('Unexpected redirect owner')
  text=body.decode(charset);p.write_bytes(body); parser=Text();parser.feed(text)
  (S/(name+'.text')).write_text('\n'.join(parser.parts)+'\n')
  return {'id':name,'url':url,'finalUrl':final,'scope':scope,'status':'CAPTURED_PRIMARY_HTML','bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'charset':charset,'fetchedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'textChars':sum(map(len,parser.parts)),'links':parser.links if name=='rtr-public' else []}
 except Exception as e:return {'id':name,'url':url,'scope':scope,'status':'CAPTURE_FAILED','error':str(e)}
if __name__=='__main__':
 assert not (D/'captures.json').exists();S.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(fetch,SOURCES))
 (D/'captures.json').write_text(json.dumps({'sources':rows,'sourceBytes':sum(x.get('bytes',0) for x in rows),'method':'Public HTTPS GET, complete bounded raw HTML and derived text; no page execution'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps([{k:v for k,v in row.items() if k in ['id','status','bytes','error']} for row in rows]))
