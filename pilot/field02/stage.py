"""Curated PHONE07 assets, host integration overlay only. No Android/SITL launch."""
from pathlib import Path
import sys,shutil,json
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;W=P/'.stage'
def stage():
 assert not W.exists(),'Owned stage already exists; inspect before replacing'
 assert shutil.disk_usage(R).free>20*2**30+128*2**20,'20 GiB floor'
 sys.path.insert(0,str(R/'native/phone07'));from assemble import stage as previous
 W.mkdir();pins=previous(W)
 shutil.rmtree(W/'src')
 assets=W/'assets'
 for name in ['index.html','sitl.html']:
  p=assets/name;s=p.read_text().replace('<head>','<head><script src="/field-bootstrap.mjs"></script>')
  s=s.replace('<script type="module" src="phone06.mjs"></script>','').replace('<script type="module" src="fly87.mjs"></script>','').replace('PHONE07 · SIMULATION','FIELD02 · HOST / SITL')
  s=s.replace('<body ', '<body data-field-loading="true" data-field-message="Đang đọc workspace và đối chiếu dữ liệu…" ')
  s=s.replace('</head>','<link rel="stylesheet" href="/field.css"></head>');p.write_text(s)
 p=assets/'runtime82.mjs';p.write_text(p.read_text().replace('await replay94(this.doc);this.live=','await validateDocument92(this.doc);this.live='))
 (assets/'operator01.mjs').write_text("await import('/field-ui.mjs');")
 (W/'source-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
 return W
if __name__=='__main__':print(stage())
