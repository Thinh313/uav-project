"""Derive bounded offline assets from source bytes; no interpolation or synthetic elevations."""
import pathlib,json,hashlib,math,datetime
from PIL import Image
R=pathlib.Path(__file__).resolve().parents[1];D=R/'app/data';sources=json.loads((R/'geodata/sources.json').read_text());src={pathlib.Path(r['path']).name:r for r in sources}
for rec in sources:assert hashlib.sha256((R/rec['path']).read_bytes()).hexdigest()==rec['sha256']
raw=json.loads((R/'geodata/sources/osm-extract.json').read_text());assert not raw.get('remark'),'Overpass error/partial data'
features=[]
for e in raw['elements']:
 if e['type']!='way' or not e.get('geometry'):continue
 xy=[[p['lon'],p['lat']] for p in e['geometry'] if 'lon' in p and 'lat' in p];tags=e.get('tags',{});closed=len(xy)>3 and xy[0]==xy[-1];area=closed and not (tags.get('highway') and tags.get('area')!='yes')
 if len(xy)<2:continue
 features.append({'type':'Feature','id':f"way/{e['id']}",'properties':{k:v for k,v in tags.items() if k in ['highway','building','waterway','natural','landuse','name','name:vi']},'geometry':{'type':'Polygon' if area else 'LineString','coordinates':[xy] if area else xy}})
basemap={'type':'FeatureCollection','features':features,'source_timestamp':raw['osm3s']['timestamp_osm_base'],'coordinateSystem':'WGS84'}
im=Image.open(R/'geodata/sources/copernicus-N10-E106.tif');scale=im.tag_v2[33550];tie=im.tag_v2[33922];keys=im.tag_v2[34735];assert keys[4:8]==(1024,0,1,2),'Expected geographic CRS';assert keys[8:12]==(1025,0,1,2),'Expected PixelIsPoint'
dx,dy=scale[:2];x0,y0=tie[3:5];bbox=[106.799,10.846,106.815,10.862]
c0=math.floor((bbox[0]-x0)/dx);c1=math.ceil((bbox[2]-x0)/dx);r0=math.floor((y0-bbox[3])/dy);r1=math.ceil((y0-bbox[1])/dy)
crop=im.crop((c0,r0,c1+1,r1+1));values=[round(float(v),4) if math.isfinite(float(v)) and -500<float(v)<9000 else None for v in crop.getdata()]
grid={'version':1,'coordinateSystem':'WGS84','verticalDatum':'EGM2008','model':'DSM','unit':'m','pixelInterpretation':'point','west':x0+c0*dx,'north':y0-r0*dy,'stepLon':dx,'stepLat':dy,'cols':crop.width,'rows':crop.height,'values':values,'sourcePixelWindow':{'col0':c0,'row0':r0,'col1':c1,'row1':r1},'sourceHash':src['copernicus-N10-E106.tif']['sha256'],'nominalResolutionM':30}
prior=json.loads((D/'manifest.json').read_text()) if (D/'manifest.json').exists() else None
if prior and prior['sources']!=sources:raise SystemExit('Sources changed; review/re-baseline a new geodata revision explicitly before derivation')
created_at=prior['createdAt'] if prior else max(x['fetched_at'] for x in sources)
files={'basemap.json':basemap,'dsm.json':grid}
assets={}
for name,value in files.items():
 data=(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode();(D/name).write_bytes(data);assets[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
manifest={'format':'aeris-geodata','version':1,'id':'rtr-aeris-home-20261012','createdAt':created_at,'coverage':bbox,'coordinateSystem':'WGS84','verticalDatum':'EGM2008','model':'DSM','operational':False,'assets':assets,'sources':sources,'osmTimestamp':raw['osm3s']['timestamp_osm_base'],'attributions':[{'label':'© OpenStreetMap contributors · ODbL','url':'https://www.openstreetmap.org/copyright'},{'label':'Copernicus DEM GLO-30 / DSM · EGM2008','url':'https://registry.opendata.aws/copernicus-dem/'}],'copernicusNotice':'produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved','limitations':['DSM includes surface objects; not surveyed bare ground','No current obstacle/airspace/flight authorization','No operational launch reference or EGM2008↔autopilot geoid mapping verified','Per-pixel uncertainty and exact acquisition date unknown']}
data=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();(D/'manifest.json').write_bytes(data)
pins={'manifestSha256':hashlib.sha256(data).hexdigest(),'id':manifest['id'],'assets':assets}
(R/'app/core/geo-pins.mjs').write_text('// Derived from source-bound assets by tools/build_geodata.py; no operational authority.\nexport const GEO_PINS='+json.dumps(pins,indent=2)+';\n')
(R/'geodata/derivation.json').write_text(json.dumps({'script':'tools/build_geodata.py','sourceHashes':{k:v['sha256'] for k,v in src.items()},'pixelInterpretation':'point','grid':{k:grid[k] for k in ['west','north','stepLon','stepLat','cols','rows','sourcePixelWindow']},'heightRangeM':[min(v for v in values if v is not None),max(v for v in values if v is not None)],'featureCount':len(features),'manifestSha256':pins['manifestSha256'],'scope':'Source byte/pixel extraction, not surveyed ground accuracy'},indent=2)+'\n')
print(json.dumps({'features':len(features),'dsm':f'{crop.width}x{crop.height}','range':[min(values),max(values)],'assets':assets}))
