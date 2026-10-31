"""Curated PHONE06 mock cockpit; no whole-project copy; owned stage removed on exit."""
from pathlib import Path
import sys,json,re,shutil,subprocess,hashlib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'native/phone06'))
from overlay import stage

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--evidence-root',type=Path,required=True);p.add_argument('--resume-workspace',type=Path);a=p.parse_args();out=a.evidence_root.resolve()
 if not out.is_relative_to(R/'evidence/payload-gateway01')or out==R/'evidence/payload-gateway01'or out.exists():raise ValueError('NEW_OWNED_EVIDENCE_DIRECTORY')
 if shutil.disk_usage(R).free<20*2**30+128*2**20:raise ValueError('RESOURCE_ADMISSION')
 w=R/'.local/payload-gateway01/stage'
 if w.exists():raise ValueError('OWNED_STAGE_EXISTS_NO_OVERWRITE')
 w.mkdir(parents=True)
 try:
  pins=stage(w)
  # Native sources are not needed for this host-only runtime.
  shutil.rmtree(w/'src')
  for name in ['index.html','sitl.html']:
   f=w/'assets'/name;s=f.read_text();s=re.sub(r'<script\b[^>]*>.*?</script>','',s,flags=re.S)
   s=s.replace('</head>','<link rel="stylesheet" href="/big02/media.css"><link rel="stylesheet" href="/gateway/gateway.css"></head>')
   s=s.replace('</main>','<section id="media-review" class="glass-surface" hidden><h2>Hồ sơ ảnh</h2><p>Chưa có camera thật.</p><div id="media-captures"></div></section></main>')
   s=s.replace('</body>','<script type="module" src="/gateway/cockpit.mjs"></script></body>')
   for old,new in [('Đang đọc journal…','GATEWAY01 · mock · không quyền bay'),('Telemetry mẫu · mới','Không có telemetry bay'),('Video mẫu · mới','Video chưa bắt đầu'),('Payload mẫu · mới','Payload chưa discovery'),('HERA 01','UAV mock'),('Giữ vị trí','Không điều khiển bay'),('Phi công A','Mock operator'),('Bay chưa cấp · P1 chưa cấp','Chưa cấp quyền'),('12 ảnh mẫu','0 ảnh mock')]:s=s.replace(old,new)
   s=re.sub(r'(<strong data-live="[^"]+">)[^<]+',r'\1—',s);f.write_text(s)
  total=sum(f.stat().st_size for f in w.rglob('*')if f.is_file())
  if total>32*2**20 or shutil.disk_usage(R).free<20*2**30+128*2**20:raise ValueError('STAGE_RESOURCE_BOUND')
  out.mkdir(parents=True)
  (out/'staging.json').write_text(json.dumps({'stageBytes':total,'derivedFrom':'PHONE06 read-only overlay + BIG02 preview derivation','sourcePins':pins,'hostOnly':True},indent=2))
  extra=['--resume-workspace',str(a.resume_workspace.resolve())]if a.resume_workspace else []
  child=subprocess.Popen(['node',str(R/'payload/gateway01/server.mjs'),'--stage',str(w/'assets'),'--evidence-root',str(out),*extra],cwd=R)
  try:raise SystemExit(child.wait())
  except KeyboardInterrupt:
   child.terminate();child.wait(timeout=8)
 finally:shutil.rmtree(w)
if __name__=='__main__':main()
