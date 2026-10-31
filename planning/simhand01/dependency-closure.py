"""Explicit offline runtime closure, not a project copy. No SDK/keys/raw flights."""
from pathlib import Path
import ast,hashlib,json,re,stat,sys
from support import ROOT,E,sha,put
manual=['pilot/simtrain53/backend.py','pilot/simtrain53/runtime.py','pilot/simtrain53/link.mjs','pilot/simtrain53/authority.mjs','pilot/simtrain53/rc.mjs','pilot/simtrain53/readback.py','pilot/sim32-pipe03/fast_physics.py','pilot/sim32-pipe03/epoch.py','pilot/sim32-pipe03/clock_host.py','pilot/sim32-pipe03/clock_client.mjs','pilot/sim32-pipe03/entry.sh','pilot/sim32-pipe03/clockprobe','pilot/sim32-pipe03/traceflush','pilot/sim32-journal04/wal_journal.py','pilot/sim32/_sim32_kernel.cpython-314-darwin.so','pilot/sim32/sitl.parm','runtime/sim32-pipe03-build/host-native/_sim32_integrator.cpython-314-darwin.so','runtime/sim32-instrument01-build/ardupilot/build/sitl/bin/arducopter','runtime/sitl/copter.parm','evidence/sim32/source-final/pilot/sim32/physics.py','evidence/simhand01/source-baseline01.json','pilot/visual56/assets/cesium-drone.glb','pilot/visual56/assets/outdoor.hdr','pilot/visual56/assets/outdoor-background.jpg','pilot/visual56/assets/asphalt-color.jpg','pilot/visual56/assets/asphalt-normal.jpg','pilot/visual56/assets/asphalt-rough.jpg','native/crew02/assets/fonts/Barlow-Medium.ttf','native/crew02/assets/fonts/Barlow-SemiBold.ttf','native/crew02/assets/fonts/Barlow-Bold.ttf','pilot/visual56/assets/fonts/OFL.txt','pilot/visual56/credits.html','pilot/sim32/KERNEL-LICENSE.txt','pilot/sim32/viewer/vendor/three.module.js','pilot/sim32/viewer/vendor/three.core.js','pilot/sim32/viewer/vendor/THREE-LICENSE.txt','native/simhand01/dist/aeris-simhand01-development01.apk','native/simhand01/AndroidManifest.xml','native/simhand01/OperationGate.java']
# This exact component is licensed offline; exclude all unrelated replay assets.
manual += [str(p.relative_to(ROOT))for p in(ROOT/'pilot/visual56/vendor/addons').rglob('*.js')]
manual += [str(p.relative_to(ROOT))for p in(ROOT/'pilot/simhand01').rglob('*')if p.is_file()]
manual += [str(p.relative_to(ROOT))for p in(ROOT/'native/simhand01/src').rglob('*.java')]
for p in(ROOT/'planning/simhand01').iterdir():
 if p.is_file()and p.suffix in['.py','.json','.md','.command']and p.name not in['dependencies.json']and'console'not in p.name and'result'not in p.name:manual.append(str(p.relative_to(ROOT)))
seen=set();missing=[];pending=list(manual)
def allowed(n):
 p=Path(n)
 if p.is_absolute()or'..'in p.parts or any(x in p.parts for x in['.git','.local','__pycache__','.build']):return False
 if p.suffix.lower()in['.p12','.pem','.key','.keystore']or p.name.startswith('.env')or any(w in p.name.lower()for w in['password','credential','secret']):return False
 if n.startswith('evidence/')and n not in['evidence/sim32/source-final/pilot/sim32/physics.py','evidence/simhand01/source-baseline01.json']:return False
 return True
while pending:
 n=pending.pop();n=Path(n).as_posix()
 if n=='pilot/simhand01/authority.mjs':n='pilot/simtrain53/authority.mjs' # Static projection literal, actual imported file stays frozen.
 if n in seen:continue
 if not allowed(n):raise RuntimeError('CLOSURE_FORBIDDEN_PATH:'+n)
 p=ROOT/n
 if not p.is_file()or p.is_symlink():missing.append(n);continue
 seen.add(n)
 if p.suffix in['.mjs','.js']:
  text=p.read_text()
  for rel in re.findall(r"(?:from\s*|import\s*\(|new URL\s*\()\s*['\"](\.[^'\"]+)['\"]",text):
   target=(p.parent/rel).resolve()
   if target.suffix in['.mjs','.js','.json']:
    if not target.is_relative_to(ROOT):raise RuntimeError('CLOSURE_ESCAPES_REPOSITORY')
    pending.append(str(target.relative_to(ROOT)))
 if p.suffix=='.py':
  try:tree=ast.parse(p.read_text())
  except(SyntaxError,UnicodeError):continue
  for node in ast.walk(tree):
   names=[a.name for a in node.names]if isinstance(node,ast.Import)else[node.module]if isinstance(node,ast.ImportFrom)and node.module else[]
   for name in names:
    target=p.parent/(name.split('.')[0]+'.py')
    if target.is_file():pending.append(str(target.relative_to(ROOT)))
if missing:raise RuntimeError('EXPLICIT_DEPENDENCY_MISSING:'+str(sorted(set(missing))))
files={n:{'sha256':sha(ROOT/n),'bytes':(ROOT/n).stat().st_size,'mode':stat.S_IMODE((ROOT/n).stat().st_mode)}for n in sorted(seen)}
q={'format':'aeris-simhand01-dependency-closure','version':1,'files':files,'uncompressedBytes':sum(v['bytes']for v in files.values()),'classification':'EXPLICIT_CODE_ASSETS_AP_NATIVE_EXTENSIONS_LICENSES_NO_OTHER_FLIGHT_EVIDENCE_OR_SIGNING_KEYS','externalPrerequisites':{'platform':'Darwin-arm64','Python':'3.14.6','Node':'validated24.14.1','DockerImage':'sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84','ADB':'cachedAndroidPlatformTools'},'sourceIDs':{'reference':'SIMTRAIN53_FUSED_REFERENCE_NOT_HERA','assets':'VISUAL56_OFFLINE_CACHED','font':'BarlowOFL1.1','renderer':'Three.jsMIT','model':'CesiumDroneEdMackeyAGI_CCBY4.0','environment':'PolyHavenCC0'},'packageContainsPrivateKeys':False,'downloads':False}
out=ROOT/'planning/simhand01/dependencies.json'
with out.open('x')as f:json.dump(q,f,indent=2)
print(json.dumps({'files':len(files),'uncompressedBytes':q['uncompressedBytes'],'output':str(out.relative_to(ROOT))}))
