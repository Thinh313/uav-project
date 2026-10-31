import json,hashlib,urllib.request,concurrent.futures
from pathlib import Path
from datetime import datetime,timezone
r=Path('research/geo-quality-20261013');(r/'snapshots').mkdir(parents=True,exist_ok=True)
urls=[('mavlink-common','https://mavlink.io/en/messages/common.html','mavlink-common.html','mavlink-upstream'),('copernicus-datum','https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM','copernicus.html','copernicus-dataspace'),('usgs-datum','https://www.usgs.gov/about/organization/science-support/office-science-quality-and-integrity/guidance-use-and','usgs.html','usgs-datum-guidance')]
def fetch(row):
 name,url,file,origin=row
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 AERIS-engineering-research'}),timeout=30) as response:
  raw=response.read(16*1024**2+1);assert len(raw)<=16*1024**2
  if response.status!=200:return {'id':name,'url':url,'status':'failed','http_status':response.status,'fetched_at':datetime.now(timezone.utc).isoformat(),'detail':'Raw HTTP not successful; official web-tool excerpt captured separately'}
  (r/'snapshots'/file).write_bytes(raw)
  return {'id':name,'url':url,'status':'captured','http_status':200,'capture_format':'Raw HTTP response bytes','snapshot':file,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'fetched_at':datetime.now(timezone.utc).isoformat(),'origin_id':origin,'content_type':response.headers.get('Content-Type'),'final_url':response.url}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(fetch,urls))
excerpt='If ellipsoid heights are established by using a GNSS survey and converted to elevations (orthometric heights) for publication, reference information should include the geoid model used in the conversion in addition to the vertical datum.\n'
raw=excerpt.encode();(r/'snapshots/usgs-web-extract.txt').write_bytes(raw);records.append({'id':'usgs-web-extract','url':urls[2][1],'status':'captured','snapshot':'usgs-web-extract.txt','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'origin_id':'usgs-datum-guidance','fetched_at':datetime.now(timezone.utc).isoformat(),'capture_format':'Official page excerpt returned by web tool; not raw HTTP capture','content_type':'text/plain'})
(r/'sources.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps([{'id':x['id'],'status':x['status'],'bytes':x.get('bytes'),'sha256':x.get('sha256')} for x in records]))
