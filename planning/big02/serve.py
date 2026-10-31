"""Root-only curated PHONE06 cockpit stage+HOST01 relay; owned stage always removed."""
from pathlib import Path
import sys,json,re,shutil,subprocess,hashlib,datetime
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'native/phone06'));from overlay import stage

def main():
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--evidence-root',type=Path,required=True);args=a.parse_args();out=args.evidence_root.resolve();base=(R/'evidence/big02').resolve()
 if not out.is_relative_to(base)or out==base or out.exists():raise ValueError('NEW_BOUNDED_EVIDENCE_ROOT_REQUIRED')
 if shutil.disk_usage(R).free<20*2**30+256*2**20:raise ValueError('HOST01_FLOOR_PLUS_HEADROOM')
 w=R/'.local/big02/stage'
 if w.exists():raise ValueError('OWNED_STAGE_EXISTS_NO_OVERWRITE')
 w.mkdir(parents=True)
 try:
  source_pins=stage(w)
  for name in ['index.html','sitl.html']:
   p=w/'assets'/name;s=p.read_text();s=re.sub(r'<script\s+type="module"\s+src="[^"]+"\s*></script>','',s);s=s.replace('</head>','<link rel="stylesheet" href="/big02/media.css"></head>');s=s.replace('</body>','<script type="module" src="/big02/pipeline.mjs"></script></body>');s=s.replace('<main class="stage"','<main class="stage"');s=s.replace('</main>','<section id="media-review" class="glass-surface" hidden><h2>Hồ sơ ảnh tổng hợp</h2><p>JPEG gốc và sidecar GNSS giả lập. Vị trí aircraft tại thời điểm khung, không phải vị trí mục tiêu. actualImages=0; receiver độc lập chưa chạy.</p><div id="media-captures"></div></section></main>');p.write_text(s)
  # Static truthful pre-init state; native-only actions have no handlers or bridge.
  for name in ['index.html','sitl.html']:
   p=w/'assets'/name;s=p.read_text();s=s.replace('Đang đọc journal…','HOST01 · video tổng hợp qua relay · không telemetry, điều khiển hoặc camera thực');s=s.replace('Telemetry mẫu · mới','Telemetry UNKNOWN').replace('Video mẫu · mới','Video chưa bắt đầu').replace('Payload mẫu · mới','Payload tổng hợp').replace('HERA 01','UAV tổng hợp').replace('Giữ vị trí','Không điều khiển').replace('Phi công A','Host preview').replace('Bay chưa cấp · P1 chưa cấp','Không cấp quyền bay').replace('12 ảnh mẫu','0 ảnh tổng hợp');s=re.sub(r'(<strong data-live="[^"]+">)[^<]+',r'\1—',s);p.write_text(s)
  total=sum(p.stat().st_size for p in w.rglob('*')if p.is_file())
  if total>180*2**20 or shutil.disk_usage(R).free<20*2**30+256*2**20:raise ValueError('STAGE_BYTE_OR_RESOURCE_BOUND')
  code=subprocess.call(['node',str(R/'media/big02/server.mjs'),'--stage',str(w/'assets'),'--evidence-root',str(out)],cwd=R)
  if code:raise SystemExit(code)
 finally:shutil.rmtree(w)
if __name__=='__main__':main()
