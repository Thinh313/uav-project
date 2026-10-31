"""Local asset integrity and replay provenance; does not launch a simulator."""
import ast, datetime, hashlib, json, os, struct, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2]
E=R/'evidence/visual56'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()
checks=[]
def check(name, ok):
    checks.append({'check':name,'pass':bool(ok)})
for receipt in ['acquisition.json','assets-fetch.json']:
    for x in json.loads((E/receipt).read_text()):
        if 'path' not in x:continue
        check(x['path'],sha(R/x['path'])==x['sha256'])
        if 'derivedPath' in x:check(x['derivedPath'],sha(R/x['derivedPath'])==x['derivedSha256'])
sky=json.loads((E/'sky-background-source.json').read_text())
check('8K panorama SHA',sha(R/'pilot/visual56/assets/outdoor-background.jpg')==sky['sha256'])
g=(R/'pilot/visual56/assets/cesium-drone.glb').read_bytes()
magic,version,size=struct.unpack_from('<4sII',g)
chunk,kind=struct.unpack_from('<II',g,12)
doc=json.loads(g[20:20+chunk])
check('GLB header',magic==b'glTF' and version==2 and size==len(g) and kind==0x4e4f534a)
check('model embedded attribution','Ed Mackey' in doc['asset'].get('copyright','') or 'EdMackey' in doc['asset'].get('copyright',''))
check('model textures embedded',all('uri' not in x for x in doc.get('images',[])))
for entry in json.loads((R/'pilot/visual56/assets/replay-index.json').read_text()):
    check(entry['id']+' original WAL SHA',sha(R/entry['source'])==entry['sourceSha256'])
    p=R/'pilot/visual56/assets'/entry['file']
    check(entry['id']+' derivative SHA',sha(p)==entry['sha256'])
    rows=json.loads(p.read_text())['samples']
    check(entry['id']+' monotonic samples',all(a['timestamp']<b['timestamp'] for a,b in zip(rows,rows[1:])))
    check(entry['id']+' finite quaternion',all(abs(sum(v*v for v in x['quaternion'])-1)<1e-5 for x in rows))
for p in (R/'pilot/visual56').rglob('*'):
    if p.suffix in ['.mjs','.js']:
        result=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
        check(str(p.relative_to(R))+' syntax',result.returncode==0)
    if p.suffix=='.py':ast.parse(p.read_text())
size=sum(p.stat().st_size for p in (R/'pilot/visual56/assets').rglob('*') if p.is_file())
free=os.statvfs(R);free=free.f_bavail*free.f_frsize
check('asset budget100MiB',size<100*1024**2)
check('disk floor20GiB',free>=20*1024**3)
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':[x for x in checks if not x['pass']],'assetBytes':size,'freeBytes':free,'scope':'Visual module integrity only; not flight/SITL/Hera qualification'}
dest=E/'verification.json'
if dest.exists():raise SystemExit('No receipt overwrite')
dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'}))
raise SystemExit(bool(out['failed']))
