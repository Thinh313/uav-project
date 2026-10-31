from pathlib import Path
import json,hashlib,copy
from ui_join import join
R=Path(__file__).resolve().parents[2];E=R/'evidence/isolate61';out=E/'mock/ui01';out.mkdir();rows=[[i*16.7,None if i==0 else 16.7,i,25.699999999953434]for i in range(1301)]
m={'run':'MOCK','active':False,'overflow':False,'count':len(rows),'timing':{'frames':len(rows),'measuredHz':(len(rows)-1)*1000/(rows[-1][0]-rows[0][0])},'parts':[]}
for i,start in enumerate(range(0,len(rows),500)):
 raw=json.dumps(rows[start:start+500],separators=(',',':')).encode();name=f'part{i:03}.json';(out/name).write_bytes(raw);m['parts'].append({'name':name,'start':start,'rows':len(rows[start:start+500]),'sha256':hashlib.sha256(raw).hexdigest()})
(out/'manifest.json').write_text(json.dumps(m));a,b=join(out);assert b==rows;checks=[{'name':'1301rows exact float strings/500row chunks and mean','pass':True}]
for name in ['gap','duplicate','tail','overflow','active','sha','mean']:
 d=copy.deepcopy(m)
 if name=='gap':d['parts'][1]['start']+=1
 if name=='duplicate':d['parts'][1]['name']=d['parts'][0]['name']
 if name=='tail':d['count']+=1;d['timing']['frames']+=1
 if name=='overflow':d['overflow']=True
 if name=='active':d['active']=True
 if name=='sha':d['parts'][0]['sha256']='0'*64
 if name=='mean':d['timing']['measuredHz']+=1
 (out/'manifest.json').write_text(json.dumps(d));failed=False
 try:join(out)
 except ValueError:failed=True
 assert failed;checks.append({'name':name+' refused not fabricated','pass':True})
(out/'manifest.json').write_text(json.dumps(m));assert join(out)[0]['rows']==1301
with(E/'qa-ui.json').open('x')as f:json.dump({'status':'PASS_UI_CHUNK_COVERAGE_GATES','checks':checks,'actualBrowser':False},f,indent=2)
print(json.dumps({'checks':len(checks)}))
