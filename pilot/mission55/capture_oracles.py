#!/usr/bin/env python3
"""Fetch small pinned oracle assets from official sources. No installer execution."""
import ast, datetime, hashlib, io, json, os, urllib.request, zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'evidence/mission55'
SNAP=OUT/'sources';SNAP.mkdir(exist_ok=True)
receipts=[]
def get(name,url,limit=600000):
    path=SNAP/name
    if path.exists():raise SystemExit('No snapshot overwrite: '+name)
    fs=os.statvfs(ROOT)
    if fs.f_bavail*fs.f_frsize < 20*1024**3+10*1024**2:raise SystemExit('Disk floor')
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AERIS-MISSION55-oracle-capture'}),timeout=30) as r:
        data=r.read(limit+1)
        if len(data)>limit:raise SystemExit('Metadata budget')
        path.write_bytes(data)
        receipts.append({'id':name,'url':url,'fetchedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                         'status':r.status,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),
                         'bytes':len(data),'scope':'Primary-source oracle/dependency, not RAGAS behavior evidence'})
        (OUT/'oracle-sources.json').write_text(json.dumps(receipts,indent=2)+'\n')
        return data
meta=json.loads(get('geographiclib-2.1-pypi.json','https://pypi.org/pypi/geographiclib/2.1/json'))
wheel=next(x for x in meta['urls'] if x['filename']=='geographiclib-2.1-py3-none-any.whl')
data=get(wheel['filename'],wheel['url'],100000)
if hashlib.sha256(data).hexdigest()!=wheel['digests']['sha256']:raise SystemExit('Wheel digest mismatch')
vendor=HERE/'vendor';vendor.mkdir(exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as z:
    for info in z.infolist():
        parts=Path(info.filename).parts
        if '..' in parts or Path(info.filename).is_absolute():raise SystemExit('Unsafe archive path')
        if info.is_dir() or info.file_size>300000:continue
        if info.filename.startswith('geographiclib/') and info.filename.endswith('.py') or '.dist-info/' in info.filename:
            path=vendor/info.filename
            if path.exists():raise SystemExit('No vendor overwrite')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(info))
head=json.loads(get('geographiclib-head.json','https://api.github.com/repos/geographiclib/geographiclib-python/commits/main'))
code=get('geodesic-tests.py.txt',f"https://raw.githubusercontent.com/geographiclib/geographiclib-python/{head['sha']}/geographiclib/test/test_geodesic.py")
tree=ast.parse(code)
group=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='GeodesicTest')
assignment=next(x for x in group.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='testcases' for t in x.targets))
vectors=ast.literal_eval(assignment.value)
(HERE/'geodesic-vectors.json').write_text(json.dumps({'upstreamCommit':head['sha'],'snapshotSha256':hashlib.sha256(code).hexdigest(),
 'columns':['lat1','lon1','azi1','lat2','lon2','azi2','s12','a12','m12','M12','M21','S12'],
 'vectors':vectors,'scope':'Official GeographicLib tests; longitude may be unrolled in reference'},indent=2)+'\n')
get('mavlink-common.xml','https://raw.githubusercontent.com/mavlink/mavlink/master/message_definitions/v1.0/common.xml',1000000)
print(json.dumps({'captured':len(receipts),'bytes':sum(r['bytes'] for r in receipts),'geodesicVectors':len(vectors),'version':'2.1'}))
