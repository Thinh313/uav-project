#!/usr/bin/env python3
"""Small public metadata/model capture; preserves each original and source hash."""
import datetime,hashlib,json,os,sys,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'evidence/visual56'
OUT.mkdir(exist_ok=True);(HERE/'assets').mkdir(exist_ok=True)
entries=[]
def get(name,url,limit=4000000,asset=False):
    fs=os.statvfs(ROOT)
    if fs.f_bavail*fs.f_frsize<20*1024**3+200*1024**2:raise SystemExit('Disk floor')
    target=(HERE/'assets' if asset else OUT)/name
    if target.exists():raise SystemExit('No overwrite '+name)
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AERIS-VISUAL56-model-research'}),timeout=35) as r:
            data=r.read(limit+1)
            if len(data)>limit:raise ValueError('Asset budget')
            target.write_bytes(data)
            entry={'url':url,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':str(target.relative_to(ROOT)),
                   'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'status':r.status}
            entries.append(entry);print(json.dumps({'file':name,'bytes':len(data)}),flush=True)
            return data
    except Exception as e:
        entries.append({'url':url,'error':str(e)});print(json.dumps({'file':name,'error':str(e)}),flush=True)
    finally:(OUT/'acquisition.json').write_text(json.dumps(entries,indent=2)+'\n')
if __name__=='__main__':
    get('cesium-drone-dir.json','https://api.github.com/repos/CesiumGS/cesium/contents/Apps/SampleData/models/CesiumDrone?ref=1.127')
    get('cesium-drone.glb','https://raw.githubusercontent.com/CesiumGS/cesium/1.127/Apps/SampleData/models/CesiumDrone/CesiumDrone.glb',12000000,True)
    get('cesium-license.txt','https://raw.githubusercontent.com/CesiumGS/cesium/1.127/LICENSE.md')
    get('unity-tree.json','https://api.github.com/repos/thedylone/unity-drone-simulator/git/trees/master?recursive=1',3000000)
    get('polyhaven-files.json','https://api.polyhaven.com/files/kloppenheim_06_puresky')
