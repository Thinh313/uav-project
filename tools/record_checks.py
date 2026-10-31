#!/usr/bin/env python3
"""Record standard app checks and immutable source-byte manifest; no install/build copies."""
import hashlib, json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/os.environ.get('AERIS_EVIDENCE_DIR','evidence')
EVIDENCE.mkdir(parents=True,exist_ok=True)
checks=[]
for name,cmd in [('unit-tests',['npm','test']),('syntax-check',['npm','run','check'])]:
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    (EVIDENCE/f'{name}.txt').write_text(result.stdout+result.stderr)
    checks.append({'name':name,'exit_code':result.returncode,'evidence':str((EVIDENCE/f'{name}.txt').relative_to(ROOT))})
    if result.returncode:raise SystemExit(result.returncode)
files=[ROOT/'.gitignore',ROOT/'package.json',ROOT/'requirements-evidence.txt',ROOT/'AGENTS.md',ROOT/'README.md']
files.extend(ROOT/'sot'/name for name in ['PROJECT.yaml','sot.yaml','sot.hygiene.yaml','README.md'])
files.extend((ROOT/'sot/registry').glob('*.yaml'))
files.extend(p for p in (ROOT/'sot/exports').glob('*') if p.is_file())
for directory in ['app','services','reference','tests','tools','docs','delivery','research','geodata','hardware','native','sot/source_canonical','sot/adapters']:
    files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend(p for p in (ROOT/'runtime/sitl').glob('*') if p.is_file())
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
(EVIDENCE/'source-manifest.json').write_text(json.dumps({'created_at':datetime.now(timezone.utc).isoformat(),'files':manifest,'checks':checks,'scope':'Source/config/research bytes of this milestone, excludes mutable evidence logs/token and .venv'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':checks,'source_files_hashed':len(manifest)},ensure_ascii=False))
