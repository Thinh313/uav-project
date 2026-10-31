import datetime,hashlib,json,os,re,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];E=R/'evidence/visual56';entries=json.loads((E/'assets-fetch.json').read_text()) if (E/'assets-fetch.json').exists() else []
def fetch(name,url,asset=False,limit=25000000):
 p=(H/'assets' if asset else E)/name;p.parent.mkdir(exist_ok=True,parents=True)
 if p.exists():
  old=next(x for x in entries if x['path']==str(p.relative_to(R)))
  if hashlib.sha256(p.read_bytes()).hexdigest()!=old['sha256']:raise RuntimeError('EXISTING_CAPTURE_MISMATCH')
  return p.read_bytes()
 fs=os.statvfs(R)
 if fs.f_bavail*fs.f_frsize<20*1024**3+200*1024**2:raise RuntimeError('FLOOR')
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AERIS-VISUAL56-licensed-assets'}),timeout=40) as r:
  b=r.read(limit+1)
  if len(b)>limit:raise RuntimeError('BUDGET')
  p.write_bytes(b);entries.append({'url':url,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':str(p.relative_to(R)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 (E/'assets-fetch.json').write_text(json.dumps(entries,indent=2)+'\n');print(name,len(b),flush=True)
 return b
meta=json.loads(fetch('outdoor-files.json','https://api.polyhaven.com/files/kloofendal_48d_partly_cloudy'))
fetch('outdoor.hdr',meta['hdri']['2k']['hdr']['url'],True)
ground=json.loads(fetch('asphalt-files.json','https://api.polyhaven.com/files/asphalt_02'))
for key,name in [('Diffuse','asphalt-color.jpg'),('nor_gl','asphalt-normal.jpg'),('Rough','asphalt-rough.jpg')]:
 fetch(name,ground[key]['2k']['jpg']['url'],True)
fetch('polyhaven-license.html','https://polyhaven.com/license')
fetch('ccby4-license.txt','https://creativecommons.org/licenses/by/4.0/legalcode.txt')
# Match the existing pinned Three186 core; addons are vendored, no runtime CDN.
pending=['loaders/GLTFLoader.js','loaders/RGBELoader.js','objects/GroundedSkybox.js','postprocessing/EffectComposer.js','postprocessing/RenderPass.js','postprocessing/SSAOPass.js','postprocessing/OutputPass.js'];done=set()
while pending:
 path=pending.pop()
 if path in done:continue
 done.add(path)
 source=fetch('three-original/'+path,'https://raw.githubusercontent.com/mrdoob/three.js/r186/examples/jsm/'+path).decode()
 scan=re.sub(r'/\*.*?\*/','',source,flags=re.S)
 scan=re.sub(r'^\s*//.*$','',scan,flags=re.M)
 for spec in re.findall(r"(?:^|\n)\s*(?:import|export)\s+(?:\{[\s\S]*?\}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]",scan):
  if spec.startswith('.'):
   target=os.path.normpath(str(Path(path).parent/spec))
   if target.startswith('..'):raise RuntimeError('UNEXPECTED_DEPENDENCY')
   pending.append(target)
  elif spec.startswith('three/addons/'):pending.append(spec.removeprefix('three/addons/'))
  elif spec!='three':raise RuntimeError('EXTERNAL_DEPENDENCY '+spec)
 derived=re.sub(r"from\s+(['\"])three\1","from '/vendor/three.module.js'",source)
 derived=re.sub(r"from\s+(['\"])three/addons/([^'\"]+)\1",lambda m:"from '/vendor/addons/"+m[2]+"'",derived)
 target=H/'vendor/addons'/path;target.parent.mkdir(exist_ok=True,parents=True);target.write_text(derived)
 entry=next(x for x in entries if x['path']==str((E/'three-original'/path).relative_to(R)))
 entry['derivedPath']=str(target.relative_to(R));entry['derivedSha256']=hashlib.sha256(target.read_bytes()).hexdigest()
(E/'assets-fetch.json').write_text(json.dumps(entries,indent=2)+'\n')
print('addons',len(done),flush=True)
