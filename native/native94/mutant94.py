from pathlib import Path
import json,hashlib,zipfile
E=Path(__file__).resolve().parents[2]/'evidence/native94'
sha=lambda b:hashlib.sha256(b).hexdigest()
def stable(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
# JS stable/number spelling must come from existing independent Node canonicalizer.
import subprocess
z=zipfile.ZipFile(E/'offline94-workspace.zip');files={n:z.read(n)for n in z.namelist()if n!='MANIFEST'};head=files['HEAD'].decode().strip();key=[n for n in files if n.endswith('-'+head+'.bin')][0];parts=files.pop(key).split(b'\n',6)
script="""import fs from'node:fs';import{sha,stable}from'./pilot/mapping51/common.mjs';let w=JSON.parse(fs.readFileSync(0,'utf8'));let p=w.compiled.plan;p.compiled.items.find(x=>x.command===206&&x.param1>0).param1=0;p.missionSha256=sha(p.compiled.items);let{sha256,...body}=p;p.sha256=sha(body);process.stdout.write(JSON.stringify(w));"""
body=subprocess.check_output(['node','--input-type=module','-e',script],input=parts[6]);parts[3]=sha(body).encode();parts[4]=str(len(body)).encode();parts[6]=body;raw=b'\n'.join(parts);new=sha(raw);files[key[:13]+new+'.bin']=raw;files['HEAD']=(new+'\n').encode();manifest='AERISARCHIVE83\n'+new+'\nauthority=false\n'+''.join(f'{n} {len(b)} {sha(b)}\n'for n,b in sorted(files.items()))
with zipfile.ZipFile(E/'NATIVE94-mutant.zip','x',compression=zipfile.ZIP_DEFLATED)as out:
 for n,b in files.items():out.writestr(n,b)
 out.writestr('MANIFEST',manifest)
(E/'mutant94.json').open('x').write(json.dumps({'name':'CAMERA_ZERO_WITH_ALL_HASHES_RESEALED','originalHead':head,'mutantHead':new,'scope':'INTENTIONAL_NEGATIVE_FIXTURE_NOT_EXECUTION'},indent=2))
