"""Explicit Root-only local phone cockpit preview. Mock/rehearsal, no aircraft commands."""
from pathlib import Path
import sys,shutil,http.server,socketserver,functools,re
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];N=R/'native/phone06';sys.path.insert(0,str(N));from overlay import stage
class Handler(http.server.SimpleHTTPRequestHandler):
 extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript'}
 def do_GET(self):
  if self.headers.get('Host')!='127.0.0.1:8860':self.send_error(403);return
  super().do_GET()
 def end_headers(self):self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
def main():
 if shutil.disk_usage(R).free<20*2**30+192*2**20:raise ValueError('PREVIEW_RESOURCE_GATE')
 w=R/'.local/phone06/preview';w.parent.mkdir(parents=True,exist_ok=True)
 if w.exists():raise ValueError('OWNED_PREVIEW_ALREADY_EXISTS_NO_OVERWRITE')
 w.mkdir()
 try:
  stage(w)
  for name in ['index.html','sitl.html']:
   p=w/'assets'/name;s=p.read_text();s=re.sub(r'<script\s+type="module"\s+src="[^"]+"\s*></script>','',s);s=s.replace('</body>','<script type="module" src="preview-only06.mjs"></script></body>');p.write_text(s)
  shutil.copyfile(Path(__file__).with_name('preview-only06.mjs'),w/'assets/preview-only06.mjs')
  with socketserver.TCPServer(('127.0.0.1',8860),functools.partial(Handler,directory=str(w/'assets')))as server:print('MOCK_PREVIEW_ONLY http://127.0.0.1:8860/index.html',flush=True);server.serve_forever(poll_interval=.5)
 finally:shutil.rmtree(w)
if __name__=='__main__':main()
