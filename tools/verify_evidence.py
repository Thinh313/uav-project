#!/usr/bin/env python3
"""Run unchanged transfer kernels, retain receipts and always delete bite scratch data."""
import hashlib, importlib.util, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
METHOD=ROOT.parent
EVIDENCE=ROOT/os.environ.get('AERIS_EVIDENCE_DIR','evidence')
EVIDENCE.mkdir(parents=True,exist_ok=True)
SCRATCH=Path('/private/tmp')/('codex-tmp-aeris-'+EVIDENCE.name+'-'+datetime.now().strftime('%Y%m%d') if 'AERIS_EVIDENCE_DIR' in os.environ else 'codex-tmp-aeris-'+datetime.now().strftime('%Y%m%d'))
if SCRATCH.exists():
    raise SystemExit(f'Scratch already exists; inspect it before retrying: {SCRATCH}')
SCRATCH.mkdir()
env={**os.environ,'TMPDIR':str(SCRATCH),'PYTHONDONTWRITEBYTECODE':'1'}
receipts=[]
def run(name,arguments,cwd=ROOT):
    result=subprocess.run(arguments,cwd=cwd,env=env,text=True,capture_output=True)
    (EVIDENCE/f'{name}.txt').write_text(result.stdout+result.stderr)
    receipts.append({'check':name,'exit_code':result.returncode,'evidence':str((EVIDENCE/f'{name}.txt').relative_to(ROOT))})
    print(name,'PASS' if result.returncode==0 else 'FAIL')
    if result.returncode:
        raise RuntimeError(f'{name} failed: {result.stdout[-1000:]}{result.stderr[-1000:]}')
try:
    run('evidence-integrity',[sys.executable,str(ROOT/'tools/check_evidence.py')])
    run('truth-adapter',[sys.executable,str(ROOT/'sot/adapters/product_truth.py')])
    if (ROOT/'sot/source_canonical/hera_context.json').exists():
        run('hera-context-adapter',[sys.executable,str(ROOT/'sot/adapters/hera_context.py')])
        original=Path(json.loads((ROOT/'hardware/hera/bom/workbook.json').read_text())['source'])
        if original.exists():
            run('bom-integrity',[sys.executable,str(ROOT/'tools/check_bom.py')])
        else:
            run('bom-canonical-integrity',[sys.executable,str(ROOT/'tools/check_bom.py'),'--canonical-only'])
            receipts.append({'check':'bom-original-availability','exit_code':None,'status':'NOT_CHECKED','detail':'External original missing at '+str(original)+'; canonical fingerprint/cell lineage checked separately'})
    refinery=METHOD/'02_Refinery_MethodBox'
    spec=importlib.util.spec_from_file_location('refinery',refinery/'refinery.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for domain in sorted((ROOT/'research').iterdir()):
        if not (domain/'domain.yaml').is_file():
            continue
        suffix='' if domain.name=='ragas-baseline' else '-'+domain.name
        run('refinery-build'+suffix,[sys.executable,str(refinery/'refinery.py'),str(domain)])
        cfg,claims,registry,aggregates,canonical=module.run_pipeline(str(domain))
        (domain/'registry.json').write_bytes(canonical)
        run('refinery-applicable-bites'+suffix,[sys.executable,str(ROOT/'tools/refinery_project_bites.py'),str(domain)])
    sot_tools=METHOD/'01_SOT_KernelInABox/tools'
    baseline=ROOT/'sot/registry/source_hashes.yaml'
    run('sot-baseline',[sys.executable,str(sot_tools/'sot_baseline.py'),str(ROOT/'sot'),'check' if baseline.exists() else 'init'])
    run('sot-check',[sys.executable,str(sot_tools/'sot_check.py'),str(ROOT/'sot')])
    run('sot-bites',[sys.executable,str(sot_tools/'sot_bites.py'),str(ROOT/'sot')])
    run('sot-gate',[sys.executable,str(sot_tools/'sot_publish.py'),str(ROOT/'sot'),'gate'])
    run('sot-status',[sys.executable,str(sot_tools/'sot_publish.py'),str(ROOT/'sot'),'status'])
finally:
    shutil.rmtree(SCRATCH)
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'checks':receipts,'scratch_removed':str(SCRATCH),'scope':'Kernel integrity checks, not semantic/flight validation'}
    (EVIDENCE/'evidence-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
