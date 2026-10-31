"""Independent read-only source-pixel and vector identity checks; no re-baseline."""
from pathlib import Path
import json,hashlib,math
from PIL import Image
R=Path(__file__).resolve().parents[1];out=R/'evidence/survey02';out.mkdir(exist_ok=True,parents=True)
sources=json.loads((R/'geodata/sources.json').read_text())
for s in sources:
 b=(R/s['path']).read_bytes();assert len(b)==s['bytes'] and hashlib.sha256(b).hexdigest()==s['sha256']
g=json.loads((R/'app/data/dsm.json').read_text());im=Image.open(R/'geodata/sources/copernicus-N10-E106.tif');assert im.mode=='F' and im.size==(3600,3600)
keys=im.tag_v2[34735];assert keys[8:12]==(1025,0,1,2) and 4326 in keys
w=g['sourcePixelWindow'];scale=im.tag_v2[33550];tie=im.tag_v2[33922]
assert g['west']==tie[3]+w['col0']*scale[0] and g['north']==tie[4]-w['row0']*scale[1]
for y in range(g['rows']):
 for x in range(g['cols']):
  value=float(im.getpixel((w['col0']+x,w['row0']+y)));expected=round(value,4) if math.isfinite(value) and -500<value<9000 else None
  assert g['values'][y*g['cols']+x]==expected
raw=json.loads((R/'geodata/sources/osm-extract.json').read_text());assert not raw.get('remark');original={f"way/{e['id']}":e for e in raw['elements']}
mapdata=json.loads((R/'app/data/basemap.json').read_text());assert len(mapdata['features'])==692
for feature in mapdata['features']:
 e=original[feature['id']];actual=feature['geometry']['coordinates'];actual=actual[0] if feature['geometry']['type']=='Polygon' else actual
 assert actual==[[p['lon'],p['lat']] for p in e['geometry']]
manifest=json.loads((R/'app/data/manifest.json').read_text());assert manifest['osmTimestamp']==raw['osm3s']['timestamp_osm_base'];assert manifest['verticalDatum']=='EGM2008' and not manifest['operational']
for n,a in manifest['assets'].items():
 b=(R/'app/data'/n).read_bytes();assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
report={'status':'PASS','raw_source_hashes':len(sources),'source_pixels_checked':g['rows']*g['cols'],'exact_osm_way_geometries_checked':len(mapdata['features']),'datum_basis':'Published Copernicus collection EGM2008; not a measured local geoid conversion','scope':'Byte, raster coordinate and source geometry integrity; no field accuracy measurement'}
(out/'geodata-integrity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
