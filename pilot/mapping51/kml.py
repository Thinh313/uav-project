"""Bounded KML2.2 AOI parser. No URL/file resolution, no flight conversion."""
import sys,json,hashlib,re,math,xml.etree.ElementTree as ET
NS='http://www.opengis.net/kml/2.2'
def parse(text):
 if not isinstance(text,str) or len(text.encode('utf-8'))>262144:raise ValueError('KML_SIZE')
 if re.search(r'<!\s*(DOCTYPE|ENTITY)',text,re.I) or '<?xml-stylesheet' in text:raise ValueError('KML_EXTERNAL_DECLARATION')
 decl=re.match(r'^\ufeff?\s*<\?xml[^?]*encoding=[\"\']([^\"\']+)',text,re.I)
 if decl and decl.group(1).lower()not in ['utf-8','utf8']:raise ValueError('KML_ENCODING_UTF8_REQUIRED')
 root=ET.fromstring(text)
 if root.tag!='{'+NS+'}kml':raise ValueError('KML_NAMESPACE')
 count=0
 def inspect(e,depth=0):
  nonlocal count
  count+=1
  if count>4096 or depth>16:raise ValueError('KML_XML_BOUND')
  if not e.tag.startswith('{'+NS+'}'):raise ValueError('KML_FOREIGN_NAMESPACE')
  if e.tag.split('}',1)[1]in ['coordinates','altitudeMode','extrude','tessellate','visibility']and(len(e)or e.attrib):raise ValueError('KML_SCALAR_CONTENT')
  for c in e:inspect(c,depth+1)
 inspect(root)
 features=[];ignored=set();coordsCount=0;ids=set()
 def tag(e):return e.tag.split('}',1)[1]
 def one(e,name,required=False):
  a=[x for x in e if tag(x)==name]
  if len(a)>1 or required and not a:raise ValueError('KML_SINGLE_'+name)
  return a[0]if a else None
 def txt(e):return ''.join(e.itertext()).strip()if e is not None else ''
 def children(e,allow):
  if set(e.attrib)-{'id'}:raise ValueError('KML_ATTRIBUTE')
  for c in e:
   if tag(c)not in allow:raise ValueError('KML_UNSUPPORTED_'+tag(c))
 def ring(e,closed=False):
  nonlocal coordsCount
  children(e,{'coordinates','tessellate','altitudeMode','extrude'})
  if closed and one(e,'altitudeMode')is not None:raise ValueError('KML_NESTED_RING_ALTITUDE_UNSUPPORTED')
  one(e,'tessellate');one(e,'extrude')
  for c in e:
   if tag(c)in ['tessellate','extrude'] and txt(c)not in ['0','1']:raise ValueError('KML_BOOLEAN')
  if txt(one(e,'extrude'))=='1':raise ValueError('KML_EXTRUSION_UNSUPPORTED')
  raw=txt(one(e,'coordinates',True));points=[]
  for token in raw.split():
   a=token.split(',')
   if len(a)not in [2,3]or any(not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?',v)for v in a):raise ValueError('KML_COORDINATE')
   p=list(map(float,a));z=p[2]if len(p)==3 else None
   if not all(math.isfinite(v)for v in p)or abs(p[0])>180 or abs(p[1])>70 or z is not None and abs(z)>20000:raise ValueError('KML_COORDINATE_RANGE')
   points.append([p[0],p[1],z]);coordsCount+=1
   if coordsCount>1024:raise ValueError('KML_TOTAL_COORDINATES')
  if len(points)<(4 if closed else 2)or len(points)>(65 if closed else 32):raise ValueError('KML_VERTEX_COUNT')
  if closed and points[0]!=points[-1]:raise ValueError('KML_RING_NOT_CLOSED')
  return points
 def geometry(e,name,visible,pmid):
  t=tag(e)
  if t=='MultiGeometry':
   children(e,{'Polygon','LineString','MultiGeometry'})
   if not len(e):raise ValueError('KML_EMPTY_MULTIGEOMETRY')
   for c in e:geometry(c,name,visible,pmid)
   return
  if t not in ['Polygon','LineString']:raise ValueError('KML_UNSUPPORTED_'+t)
  if len(features)>=16:raise ValueError('KML_FEATURE_BOUND')
  mode=txt(one(e,'altitudeMode'))or'clampToGround'
  if mode not in ['clampToGround','relativeToGround','absolute']:raise ValueError('KML_ALTITUDE_MODE')
  holes=[]
  for k in ['tessellate','extrude']:
   value=txt(one(e,k))
   if value not in ['', '0','1']:raise ValueError('KML_BOOLEAN')
  if t=='Polygon':
   children(e,{'outerBoundaryIs','innerBoundaryIs','altitudeMode','tessellate','extrude'})
   if txt(one(e,'extrude'))not in ['', '0']:raise ValueError('KML_EXTRUSION_UNSUPPORTED')
   outer=one(e,'outerBoundaryIs',True);children(outer,{'LinearRing'});points=ring(one(outer,'LinearRing',True),True)
   for h in [x for x in e if tag(x)=='innerBoundaryIs']:
    if len(holes)>=8:raise ValueError('KML_HOLE_BOUND')
    children(h,{'LinearRing'});holes.append(ring(one(h,'LinearRing',True),True))
  else:points=ring(e)
  features.append({'id':'f-'+str(len(features)+1).zfill(4),'name':name,'placemarkId':pmid,'kind':t,'visible':visible,'altitudeMode':mode,'altitudeModeDeclared':one(e,'altitudeMode')is not None,'coordinates':points,'holes':holes,'inspectionOnly':bool(holes)or mode!='clampToGround'or not visible})
 metadata={'name','description','Style','StyleMap','styleUrl','open'}
 def walk(e,visible=True):
  children(e,metadata|{'Document','Folder','Placemark','visibility'})
  vis=txt(one(e,'visibility'))
  if vis not in ['', '0','1']:raise ValueError('KML_VISIBILITY')
  visible=visible and vis!='0'
  for c in e:
   t=tag(c)
   if t in metadata:ignored.add(t);continue
   if t=='visibility':continue
   if t!='Placemark':walk(c,visible);continue
   children(c,metadata|{'visibility','Polygon','LineString','MultiGeometry'})
   pmid=c.attrib.get('id');name=txt(one(c,'name'))or'Đối tượng chưa đặt tên'
   if len(name)>200 or pmid is not None and (len(pmid)>200 or pmid in ids):raise ValueError('KML_NAME_OR_ID')
   if pmid:ids.add(pmid)
   cv=txt(one(c,'visibility'))
   if cv not in ['', '0','1']:raise ValueError('KML_VISIBILITY')
   geoms=[x for x in c if tag(x)in ['Polygon','LineString','MultiGeometry']]
   if len(geoms)!=1:raise ValueError('KML_PLACEMARK_GEOMETRY')
   for x in c:
    if tag(x)in metadata-{'name'}:ignored.add(tag(x))
   geometry(geoms[0],name,visible and cv!='0',pmid)
 walk(root)
 if not features:raise ValueError('KML_NO_FEATURE')
 return {'format':'aeris-kml-aoi51','version':1,'coordinateSystem':'WGS84','sourceSha256':hashlib.sha256(text.encode()).hexdigest(),'sourceBytes':len(text.encode()),'features':features,'ignoredPresentation':sorted(ignored),'operational':False}
if __name__=='__main__':
 try:
  b=sys.stdin.buffer.read(1048577)
  if len(b)>1048576:raise ValueError('REQUEST_SIZE')
  d=json.loads(b.decode('utf-8'))
  if set(d)!={'text'}:raise ValueError('REQUEST_FIELDS')
  print(json.dumps({'ok':True,'document':parse(d['text'])},ensure_ascii=False,allow_nan=False))
 except Exception as e:print(json.dumps({'ok':False,'error':str(e)}));sys.exit(2)
