from pathlib import Path
import shutil,json,subprocess,hashlib
R=Path(__file__).resolve().parents[2];E=R/'evidence/native83';src=E/'runs/sd76205f38a8e445298c5';out=E/'bites';out.mkdir();verifier=(R/'native/native83/raw_verify_final.mjs').read_text();results=[]
for name,mutate in [('no-takeoff',lambda r:r['execution'].__setitem__('takeoffWitness',None)),('fake-complete',lambda r:r['execution'].__setitem__('complete',False)),('readback-count',lambda r:r['readback'].__setitem__('items',999))]:
 p=out/name;p.mkdir()
 # Dataset-only fixture, no project copy; referenced files kept byte-for-byte.
 r=json.loads((src/'review.json').read_text())
 for f in r['filesSha256']:shutil.copyfile(src/f,p/f)
 mutate(r);(p/'review.json').write_text(json.dumps(r));code=verifier.replace("path.resolve('evidence/native83/runs',run)",json.dumps(str(p)))
 tool=R/'native/native83/bite_verifier.mjs';tool.write_text(code)
 v=subprocess.run(['node',str(tool),'sd76205f38a8e445298c5'],cwd=R,text=True,capture_output=True);assert v.returncode!=0 and 'AssertionError'in v.stderr,(name,v.stdout,v.stderr);results.append({'name':name,'rejected':True,'exit':v.returncode,'stderr':v.stderr[-2200:]})
(E/'cold-bites.json').open('x').write(json.dumps({'status':'PASS','cases':results,'bytes':sum(p.stat().st_size for p in out.rglob('*')if p.is_file())},indent=2));print('3 semantic receipt mutations rejected')
# Generated adapter is a temporary verification program; keep the exact programs in evidence instead.
(out/'last-verifier.mjs').write_text(tool.read_text());tool.unlink()
