from pathlib import Path
from html.parser import HTMLParser
import re,json,hashlib,subprocess
R=Path(__file__).resolve().parents[2];P=R/'pilot/coach01';E=R/'evidence/coach01'
class Doc(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.buttons=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.append(a['id'])
  if tag=='button':self.buttons+=1
h=Doc();h.feed((P/'index.html').read_text());assert len(h.ids)==len(set(h.ids));refs=set(re.findall(r"\$\('([^']+)'\)",(P/'app.mjs').read_text()));assert refs<=set(h.ids),refs-set(h.ids)
seen={};builtins=set()
def walk(p):
 p=p.resolve()
 if p in seen:return
 assert p.is_file()and p.is_relative_to(R),p
 t=p.read_text();seen[p]=t
 specs=re.findall(r"(?:^|[;\n])\s*(?:import|export)\s*(?:\{[^}]*\}\s*from\s*|[\w* ,]+\s+from\s*)?['\"]([^'\"]+)['\"]",t,re.M)
 for s in specs:
  if s.startswith('.'):walk(p.parent/s)
  else:builtins.add(s)
for p in P.glob('*.mjs'):walk(p)
assert all(s.startswith('node:')for s in builtins),builtins
for name in ['node:dgram','node:net','node:child_process']:
 # child_process is expected solely in the existing bounded KML XML parser adapter.
 if name!='node:child_process':assert name not in builtins,name
assert all(not any(x in str(p.relative_to(R))for x in ['actual-transport','session.mjs','gateway.mjs','runtime.py','server.mjs'])for p in seen if not p.is_relative_to(P))
assert 'node:child_process'in builtins
assert (R/'pilot/workbench01/kml.mjs')in seen
checks=[]
for p in P.glob('*.mjs'):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);assert r.returncode==0,r.stderr;checks.append(str(p.relative_to(R)))
fonts={}
for n in ['Medium','SemiBold','Bold']:
 p=R/f'native/crew02/assets/fonts/Barlow-{n}.ttf';fonts[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
receipt={'status':'PASS_STATIC_ONLY','htmlUniqueIds':len(h.ids),'referencedIds':len(refs),'buttonElements':h.buttons,'syntaxChecked':checks,'staticImportGraphModules':len(seen),'builtins':sorted(builtins),'flightRuntimeImports':False,'boundedChildProcess':'EXISTING_KML_XML_PARSER_ONLY','fontPins':fonts,'browserGeometry':'NOT_CHECKED_LOCAL_BROWSER_DISABLED','touchKeyboardInteractions':'NOT_CHECKED','pixelVisualQA':'NOT_CHECKED'}
(E/'static-ui-qa02.json').open('x').write(json.dumps(receipt,indent=2)+'\n')
inv={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(seen)}
(E/'dependency-fingerprints02.json').open('x').write(json.dumps({'format':'coach01-static-import-graph','files':inv},indent=2)+'\n');print(json.dumps(receipt,indent=2))
