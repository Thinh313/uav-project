"""Fetch bounded public geographic inputs, no project/private content upload."""
import pathlib,urllib.request,urllib.parse,json,hashlib,datetime,concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1];D=R/'geodata/sources';D.mkdir(exist_ok=True,parents=True)
inputs=[('copernicus-N10-E106.tif','https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N10_00_E106_00_DEM/Copernicus_DSM_COG_10_N10_00_E106_00_DEM.tif',None,80*1024*1024),('osm-extract.json','https://overpass-api.de/api/interpreter','[out:json][timeout:40];(way[highway](10.846,106.799,10.862,106.815);way[building](10.846,106.799,10.862,106.815);way[waterway](10.846,106.799,10.862,106.815);way[natural=water](10.846,106.799,10.862,106.815);way[landuse](10.846,106.799,10.862,106.815););out geom;',12*1024*1024)]
def fetch(rec):
 name,url,query,limit=rec;p=D/name
 if p.exists():raise RuntimeError(f'Input exists; inspect before refreshing {p}')
 req=urllib.request.Request(url,data=urllib.parse.urlencode({'data':query}).encode() if query else None,headers={'User-Agent':'RTR-AERIS-local-geodata-evaluation/0.5 (bounded technical fixture)','Content-Type':'application/x-www-form-urlencoded'} if query else {'User-Agent':'RTR-AERIS-local-geodata-evaluation/0.5'})
 with urllib.request.urlopen(req,timeout=90) as r:
  data=r.read(limit+1);assert len(data)<=limit,'Input too large';final=r.url;kind=r.headers.get('Content-Type')
 p.write_bytes(data)
 return {'path':str(p.relative_to(R)),'url':url,'query':query,'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'content_type':kind,'final_url':final}
records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for f in pool.map(fetch,inputs):records.append(f)
(R/'geodata/sources.json').write_text(json.dumps(records,indent=2)+'\n');print([(r['path'],r['bytes']) for r in records])
