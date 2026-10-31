import hashlib,json,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=R/'evidence/visual56'
for name,url in [('unity-tree-main.json','https://api.github.com/repos/thedylone/unity-drone-simulator/git/trees/main?recursive=1'),('unity-README.md','https://raw.githubusercontent.com/thedylone/unity-drone-simulator/main/README.md'),('unity-LICENSE.txt','https://raw.githubusercontent.com/thedylone/unity-drone-simulator/main/LICENSE')]:
 p=E/name
 if p.exists():continue
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AERIS-VISUAL56-model-quality-review'}),timeout=30) as r:b=r.read(3000001)
  if len(b)>3000000:raise ValueError('budget')
  p.write_bytes(b);print(name,len(b))
 except Exception as e:print(name,str(e))
if (E/'unity-tree-main.json').exists():
 d=json.loads((E/'unity-tree-main.json').read_text());print([(x['path'],x.get('size')) for x in d.get('tree',[]) if ('drone model' in x['path'].lower() or 'readme' in x['path'].lower()) and not x['path'].endswith('.meta')])
